from django.urls import path
from .views import (
    SecureFileServeView,
    AuditLogListView,
    NotificationListView,
    NotificationMarkReadView,
    NotificationMarkAllReadView,
    NotificationDetailView,
    AIConsentRecordView,
    AIConsentStatusView,
    AIConsentPolicyView,
)

app_name = 'core'

urlpatterns = [
    path('files/<path:file_path>', SecureFileServeView.as_view(), name='secure_file_serve'),
    path('audit-logs/', AuditLogListView.as_view(), name='audit_logs'),
    
    # US-34: In-app Notification endpoints
    path('notifications/', NotificationListView.as_view(), name='notification_list'),
    path('notifications/<int:pk>/read/', NotificationMarkReadView.as_view(), name='notification_mark_read'),
    path('notifications/mark-all-read/', NotificationMarkAllReadView.as_view(), name='notification_mark_all_read'),
    path('notifications/<int:pk>/', NotificationDetailView.as_view(), name='notification_detail'),

    # US-48: AI Biometric & Evaluation Consent Notice Gatekeeper
    path('ai-consent/', AIConsentRecordView.as_view(), name='ai_consent_record'),
    path('ai-consent/status/', AIConsentStatusView.as_view(), name='ai_consent_status'),
    path('ai-consent/policy/', AIConsentPolicyView.as_view(), name='ai_consent_policy'),
]
