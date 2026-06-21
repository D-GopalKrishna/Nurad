from django.contrib import admin

from .models import Study


@admin.register(Study)
class StudyAdmin(admin.ModelAdmin):
    list_display = ('study_instance_uid', 'patient_name', 'patient_id', 'study_date')
    filter_horizontal = ('allowed_users',)
