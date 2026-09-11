from django.urls import path

from .views import (
    RunSegmentationView,
    SegmentationJobStatusView,
    SegmentationReviewView,
    WorklistView,
)

urlpatterns = [
    path('worklist/', WorklistView.as_view(), name='worklist'),
    path('studies/<int:study_id>/run-segmentation/', RunSegmentationView.as_view(), name='run-segmentation'),
    path('segmentation-jobs/<int:job_id>/', SegmentationJobStatusView.as_view(), name='segmentation-job-status'),
    path('segmentation-jobs/<int:job_id>/review/', SegmentationReviewView.as_view(), name='segmentation-job-review'),
]
