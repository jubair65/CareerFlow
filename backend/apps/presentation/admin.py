from django.contrib import admin
from .models import PresentationVideo, SpeechAnalysis, BehavioralAnalysis, PresentationScore, PresentationFeedback


@admin.register(PresentationVideo)
class PresentationVideoAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'title', 'status', 'duration_seconds', 'is_active', 'uploaded_at')
    list_filter = ('status', 'is_active', 'uploaded_at')
    search_fields = ('user__email', 'user__username', 'title', 'original_filename')


@admin.register(SpeechAnalysis)
class SpeechAnalysisAdmin(admin.ModelAdmin):
    list_display = ('id', 'video', 'words_per_minute', 'filler_word_count', 'clarity_score', 'processed_at')
    search_fields = ('video__user__email', 'transcript')


@admin.register(BehavioralAnalysis)
class BehavioralAnalysisAdmin(admin.ModelAdmin):
    list_display = ('id', 'video', 'eye_contact_score', 'posture_score', 'engagement_score', 'processed_at')
    search_fields = ('video__user__email',)


@admin.register(PresentationScore)
class PresentationScoreAdmin(admin.ModelAdmin):
    list_display = ('id', 'video', 'overall_score', 'speech_score', 'behavioral_score', 'calculated_at')
    list_filter = ('overall_score', 'calculated_at')
    search_fields = ('video__user__email',)


@admin.register(PresentationFeedback)
class PresentationFeedbackAdmin(admin.ModelAdmin):
    list_display = ('id', 'video', 'created_at')
    search_fields = ('video__user__email',)

