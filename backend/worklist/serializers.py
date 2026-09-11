from rest_framework import serializers

from .models import SegmentationJob, SegmentationReview, Study


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


class SegmentationReviewSerializer(serializers.ModelSerializer):
    reviewer = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = SegmentationReview
        fields = [
            'id',
            'job',
            'reviewer',
            'verdict',
            'reviewed_seg_sop_instance_uid',
            'notes',
            'reviewed_at',
        ]
        read_only_fields = ['id', 'job', 'reviewer', 'reviewed_at']


class SegmentationJobSerializer(serializers.ModelSerializer):
    latest_review = serializers.SerializerMethodField()

    class Meta:
        model = SegmentationJob
        fields = [
            'id',
            'study',
            'series_instance_uid',
            'workflow_name',
            'status',
            'source_seg_sop_instance_uid',
            'created_at',
            'latest_review',
        ]

    def get_latest_review(self, obj):
        review = obj.reviews.first()  # SegmentationReview.Meta.ordering = -reviewed_at
        return SegmentationReviewSerializer(review).data if review else None
