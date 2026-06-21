from django.http import HttpResponse, HttpResponseForbidden
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from . import orthanc_client
from .models import Study
from .serializers import StudySerializer


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
