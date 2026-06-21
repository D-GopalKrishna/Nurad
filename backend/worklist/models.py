from django.conf import settings
from django.db import models


class Study(models.Model):
    """Cached metadata for a study stored in Orthanc, plus access control."""

    study_instance_uid = models.CharField(max_length=128, unique=True)
    patient_name = models.CharField(max_length=255, blank=True)
    patient_id = models.CharField(max_length=128, blank=True)
    study_date = models.CharField(max_length=32, blank=True)
    study_description = models.CharField(max_length=255, blank=True)
    modalities = models.CharField(max_length=64, blank=True)
    allowed_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name='accessible_studies', blank=True
    )

    def __str__(self):
        return f'{self.study_instance_uid} ({self.patient_name})'


class SegmentationJob(models.Model):
    """Tracks a MONAI spleen-segmentation Argo Workflow run for a study."""

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Running', 'Running'),
        ('Succeeded', 'Succeeded'),
        ('Failed', 'Failed'),
        ('Error', 'Error'),
    ]

    study = models.ForeignKey(Study, on_delete=models.CASCADE, related_name='segmentation_jobs')
    series_instance_uid = models.CharField(max_length=128)
    workflow_name = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.workflow_name} ({self.status})'
