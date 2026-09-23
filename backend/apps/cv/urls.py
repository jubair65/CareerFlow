from django.urls import path
from .views import (
    CVUploadView,
    CurrentCVView,
    CVHistoryView,
    CVParseView,
    ParsedCVDetailView,
)

app_name = 'cv'

urlpatterns = [
    path('upload/', CVUploadView.as_view(), name='cv_upload'),
    path('current/', CurrentCVView.as_view(), name='cv_current'),
    path('history/', CVHistoryView.as_view(), name='cv_history'),
    path('<int:cv_id>/parse/', CVParseView.as_view(), name='cv_parse'),
    path('<int:cv_id>/parsed/', ParsedCVDetailView.as_view(), name='cv_parsed_detail'),
]
