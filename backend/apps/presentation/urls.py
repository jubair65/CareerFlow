from django.urls import path
from .views import (
    VideoUploadView,
    CurrentPresentationVideoView,
    PresentationVideoHistoryView,
    PresentationVideoDetailView,
    PresentationSpeechAnalysisView,
)

app_name = 'presentation'

urlpatterns = [
    path('upload/', VideoUploadView.as_view(), name='video_upload'),
    path('active/', CurrentPresentationVideoView.as_view(), name='video_active'),
    path('history/', PresentationVideoHistoryView.as_view(), name='video_history'),
    path('<int:pk>/', PresentationVideoDetailView.as_view(), name='video_detail'),
    path('<int:video_id>/speech/', PresentationSpeechAnalysisView.as_view(), name='speech_analysis'),
]
