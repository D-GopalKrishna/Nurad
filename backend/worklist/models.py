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
