from django.contrib import admin

from .models import SegmentationJob, SegmentationReview, Study


@admin.register(Study)
class StudyAdmin(admin.ModelAdmin):
    list_display = ('study_instance_uid', 'patient_name', 'patient_id', 'study_date')
    filter_horizontal = ('allowed_users',)


@admin.register(SegmentationJob)
class SegmentationJobAdmin(admin.ModelAdmin):
    list_display = ('workflow_name', 'study', 'status', 'created_at')


@admin.register(SegmentationReview)
class SegmentationReviewAdmin(admin.ModelAdmin):
    list_display = ('job', 'verdict', 'reviewer', 'reviewed_at')
    list_filter = ('verdict',)
