from django.urls import path

from .views import RunSegmentationView, SegmentationJobStatusView, WorklistView

urlpatterns = [
    path('worklist/', WorklistView.as_view(), name='worklist'),
    path('studies/<int:study_id>/run-segmentation/', RunSegmentationView.as_view(), name='run-segmentation'),
    path('segmentation-jobs/<int:job_id>/', SegmentationJobStatusView.as_view(), name='segmentation-job-status'),
]
