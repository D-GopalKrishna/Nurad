from rest_framework import serializers

from .models import SegmentationJob, Study


class StudySerializer(serializers.ModelSerializer):
    class Meta:
        model = Study
        fields = [
            'id',
            'study_instance_uid',
            'patient_name',
            'patient_id',
            'study_date',
            'study_description',
            'modalities',
        ]


class SegmentationJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = SegmentationJob
        fields = ['id', 'study', 'series_instance_uid', 'workflow_name', 'status', 'created_at']
