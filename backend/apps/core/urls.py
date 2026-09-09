from django.urls import path
from .views import SecureFileServeView, AuditLogListView

app_name = 'core'

urlpatterns = [
    path('files/<path:file_path>', SecureFileServeView.as_view(), name='secure_file_serve'),
    path('audit-logs/', AuditLogListView.as_view(), name='audit_logs'),
]
