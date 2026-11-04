from django.contrib import admin
from .models import CandidateCV, ParsedCV, CVFeedback, JobRequirement, CVJobMatch


@admin.register(CandidateCV)
class CandidateCVAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'original_filename', 'file_size', 'file_type', 'is_active', 'uploaded_at')
    list_filter = ('is_active', 'file_type', 'uploaded_at')
    search_fields = ('user__email', 'user__full_name', 'original_filename')


@admin.register(ParsedCV)
class ParsedCVAdmin(admin.ModelAdmin):
    list_display = ('id', 'cv', 'skills_count', 'parsed_at')
    search_fields = ('cv__user__email', 'cv__original_filename', 'raw_text')
    readonly_fields = ('parsed_at',)


@admin.register(CVFeedback)
class CVFeedbackAdmin(admin.ModelAdmin):
    list_display = ('id', 'cv', 'overall_score', 'formatting_score', 'clarity_score', 'keyword_strength_score', 'created_at')
    list_filter = ('overall_score', 'created_at')
    search_fields = ('cv__user__email', 'cv__original_filename')


@admin.register(JobRequirement)
class JobRequirementAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'company', 'role_type', 'threshold_score', 'created_by', 'created_at')
    list_filter = ('created_at', 'role_type')
    search_fields = ('title', 'company', 'description')


@admin.register(CVJobMatch)
class CVJobMatchAdmin(admin.ModelAdmin):
    list_display = ('id', 'cv', 'job_title', 'company', 'match_score', 'keyword_coverage', 'updated_at')
    list_filter = ('match_score', 'created_at')
    search_fields = ('cv__user__email', 'job_title', 'company')
