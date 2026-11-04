from django.contrib import admin
from .models import DataAccessLog, Notification, AIConsentLog


@admin.register(DataAccessLog)
class DataAccessLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'action', 'status', 'resource_path', 'ip_address', 'timestamp')
    list_filter = ('action', 'status', 'timestamp')
    search_fields = ('user__email', 'resource_path', 'ip_address')
    readonly_fields = ('timestamp',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'title', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__email', 'title', 'message')


@admin.register(AIConsentLog)
class AIConsentLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'email', 'consent_type', 'policy_version', 'agreed', 'timestamp')
    list_filter = ('consent_type', 'agreed', 'timestamp')
    search_fields = ('user__email', 'email', 'consent_token')
    readonly_fields = ('timestamp',)
