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
    source_seg_sop_instance_uid = models.CharField(
        max_length=128,
        blank=True,
        help_text='SOP Instance UID of the AI-generated DICOM-SEG this job produced in Orthanc.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.workflow_name} ({self.status})'


class SegmentationReview(models.Model):
    """A radiologist's verdict on a SegmentationJob's AI-generated mask."""

    VERDICT_CHOICES = [
        ('accepted', 'Accepted as-is'),
        ('edited', 'Edited by reviewer'),
        ('rejected', 'Rejected'),
    ]

    job = models.ForeignKey(SegmentationJob, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    verdict = models.CharField(max_length=16, choices=VERDICT_CHOICES)
    reviewed_seg_sop_instance_uid = models.CharField(
        max_length=128,
        blank=True,
        help_text='SOP Instance UID of the SEG instance stored back after this review (edited or re-stored).',
    )
    notes = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-reviewed_at']

    def __str__(self):
        return f'{self.job.workflow_name} — {self.verdict} by {self.reviewer}'
