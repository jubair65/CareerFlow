from django.urls import path
from .views import (
    VideoUploadView,
    CurrentPresentationVideoView,
    PresentationVideoHistoryView,
    PresentationVideoDetailView,
    PresentationSpeechAnalysisView,
    PresentationBehavioralAnalysisView,
    PresentationScoreView,
    PresentationSuggestionsView,
    PipelineRetryView,
    PipelineStatusView,
    PipelineLogsView,
)

app_name = 'presentation'

urlpatterns = [
    path('upload/', VideoUploadView.as_view(), name='video_upload'),
    path('active/', CurrentPresentationVideoView.as_view(), name='video_active'),
    path('history/', PresentationVideoHistoryView.as_view(), name='video_history'),
    path('<int:pk>/', PresentationVideoDetailView.as_view(), name='video_detail'),
    path('<int:video_id>/speech/', PresentationSpeechAnalysisView.as_view(), name='speech_analysis'),
    path('<int:video_id>/behavioral/', PresentationBehavioralAnalysisView.as_view(), name='behavioral_analysis'),
    path('<int:video_id>/score/', PresentationScoreView.as_view(), name='presentation_score'),
    path('<int:video_id>/suggestions/', PresentationSuggestionsView.as_view(), name='presentation_suggestions'),
    path('<int:video_id>/suggestions/generate/', PresentationSuggestionsView.as_view(), name='presentation_suggestions_generate'),
    # US-40: Pipeline Resilience & Recovery Endpoints
    path('<int:video_id>/retry/', PipelineRetryView.as_view(), name='pipeline_retry'),
    path('<int:video_id>/status/', PipelineStatusView.as_view(), name='pipeline_status'),
    path('<int:video_id>/logs/', PipelineLogsView.as_view(), name='pipeline_logs'),
]
