from django.urls import path
from .views import CVUploadView, CurrentCVView, CVHistoryView

app_name = 'cv'

urlpatterns = [
    path('upload/', CVUploadView.as_view(), name='cv_upload'),
    path('current/', CurrentCVView.as_view(), name='cv_current'),
    path('history/', CVHistoryView.as_view(), name='cv_history'),
]
