from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from . import argo_client, orthanc_client
from .models import SegmentationJob, SegmentationReview, Study
from .serializers import SegmentationJobSerializer, SegmentationReviewSerializer, StudySerializer


class WorklistView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orthanc_client.sync_studies_from_orthanc()

        user = request.user
        if user.is_staff or user.is_superuser:
            studies = Study.objects.all()
        else:
            studies = Study.objects.filter(allowed_users=user)

        return Response(StudySerializer(studies, many=True).data)


class RunSegmentationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, study_id):
        study = get_object_or_404(Study, id=study_id)

        series_instance_uid = orthanc_client.find_ct_series_instance_uid(
            study.study_instance_uid
        )
        if not series_instance_uid:
            return Response({'detail': 'No CT series found for this study'}, status=400)

        workflow_name = argo_client.submit_segmentation_workflow(
            study.study_instance_uid, series_instance_uid
        )
        job = SegmentationJob.objects.create(
            study=study,
            series_instance_uid=series_instance_uid,
            workflow_name=workflow_name,
            status='Pending',
        )
        return Response(SegmentationJobSerializer(job).data, status=201)


class SegmentationJobStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, job_id):
        job = get_object_or_404(SegmentationJob, id=job_id)
        job.status = argo_client.get_workflow_status(job.workflow_name)
        job.save(update_fields=['status', 'updated_at'])
        return Response(SegmentationJobSerializer(job).data)


class SegmentationReviewView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, job_id):
        job = get_object_or_404(SegmentationJob, id=job_id)
        reviews = job.reviews.all()
        return Response(SegmentationReviewSerializer(reviews, many=True).data)

    def post(self, request, job_id):
        job = get_object_or_404(SegmentationJob, id=job_id)
        serializer = SegmentationReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(job=job, reviewer=request.user)
        return Response(serializer.data, status=201)


@method_decorator(csrf_exempt, name='dispatch')
class DicomwebProxyView(View):
    """Plain Django view (not DRF APIView) so the Accept header (e.g.
    application/dicom+json) is forwarded untouched to Orthanc instead of
    being consumed by DRF's content negotiation."""

    def get(self, request, subpath):
        return self._proxy('GET', request, subpath)

    def post(self, request, subpath):
        return self._proxy('POST', request, subpath)

    def _proxy(self, method, request, subpath):
        try:
            auth_result = JWTAuthentication().authenticate(request)
        except AuthenticationFailed:
            auth_result = None
        if auth_result is None:
            return HttpResponseForbidden('Authentication required')

        upstream = orthanc_client.proxy_request(
            method=method,
            subpath=subpath,
            query_string=request.META.get('QUERY_STRING', '').encode(),
            body=request.body,
            headers=request.headers,
        )
        return HttpResponse(
            upstream.content,
            status=upstream.status_code,
            content_type=upstream.headers.get('Content-Type', 'application/octet-stream'),
        )
