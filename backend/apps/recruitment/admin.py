from django.contrib import admin
from .models import (
    ClientCompany,
    RecruitmentRoom,
    CandidateApplication,
    CandidateNote,
    CandidateStageHistory,
    StatusNotificationLog,
)


@admin.register(ClientCompany)
class ClientCompanyAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'industry', 'contact_person', 'contact_email', 'agency', 'is_active', 'created_at')
    list_filter = ('is_active', 'industry', 'created_at')
    search_fields = ('name', 'contact_person', 'contact_email', 'agency__email')


@admin.register(RecruitmentRoom)
class RecruitmentRoomAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'company_name', 'department', 'status', 'created_by', 'cv_weight', 'video_weight', 'created_at')
    list_filter = ('status', 'role_category', 'experience_level', 'created_at')
    search_fields = ('title', 'company_name', 'department', 'created_by__email')


@admin.register(CandidateApplication)
class CandidateApplicationAdmin(admin.ModelAdmin):
    list_display = ('id', 'candidate', 'room', 'status', 'final_score', 'stage', 'is_shortlisted', 'applied_at')
    list_filter = ('status', 'stage', 'is_shortlisted', 'hr_decision', 'applied_at')
    search_fields = ('candidate__email', 'candidate__full_name', 'room__title')


@admin.register(CandidateNote)
class CandidateNoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'application', 'author', 'created_at')
    search_fields = ('application__candidate__email', 'author__email', 'note_text')


@admin.register(CandidateStageHistory)
class CandidateStageHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'application', 'from_stage', 'to_stage', 'changed_by', 'changed_at')
    list_filter = ('from_stage', 'to_stage', 'changed_at')
    search_fields = ('application__candidate__email', 'changed_by__email')


@admin.register(StatusNotificationLog)
class StatusNotificationLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'application', 'recipient_email', 'notification_type', 'is_sent', 'created_at')
    list_filter = ('is_sent', 'notification_type', 'created_at')
    search_fields = ('recipient_email', 'application__candidate__email')
