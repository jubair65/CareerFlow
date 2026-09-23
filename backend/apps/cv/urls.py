from django.urls import path
from .views import (
    CVUploadView,
    CurrentCVView,
    CVHistoryView,
    CVParseView,
    ParsedCVDetailView,
    CVFeedbackGenerateView,
    CurrentCVFeedbackView,
    CVFeedbackDetailView,
)

app_name = 'cv'

urlpatterns = [
    path('upload/', CVUploadView.as_view(), name='cv_upload'),
    path('current/', CurrentCVView.as_view(), name='cv_current'),
    path('current/feedback/', CurrentCVFeedbackView.as_view(), name='cv_current_feedback'),
    path('history/', CVHistoryView.as_view(), name='cv_history'),
    path('<int:cv_id>/parse/', CVParseView.as_view(), name='cv_parse'),
    path('<int:cv_id>/parsed/', ParsedCVDetailView.as_view(), name='cv_parsed_detail'),
    path('<int:cv_id>/generate-feedback/', CVFeedbackGenerateView.as_view(), name='cv_generate_feedback'),
    path('<int:cv_id>/feedback/', CVFeedbackDetailView.as_view(), name='cv_feedback_detail'),
]

