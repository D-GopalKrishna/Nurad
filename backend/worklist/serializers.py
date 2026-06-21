from rest_framework import serializers

from .models import Study


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
