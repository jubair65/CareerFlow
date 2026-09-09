from django.db import models
from django.conf import settings


class DataAccessLog(models.Model):
    class Action(models.TextChoices):
        VIEW = 'VIEW', 'View Resource'
        DOWNLOAD = 'DOWNLOAD', 'Download File'
        UPLOAD = 'UPLOAD', 'Upload File'
        DELETE = 'DELETE', 'Delete Resource'

    class Status(models.TextChoices):
        GRANTED = 'GRANTED', 'Access Granted'
        DENIED = 'DENIED', 'Access Denied'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='access_logs',
        help_text="User attempting the access (null if unauthenticated)"
    )
    resource_path = models.CharField(max_length=500, help_text="Path of the requested file or resource")
    action = models.CharField(max_length=20, choices=Action.choices, default=Action.VIEW)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.GRANTED)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default='')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'careerflow_data_access_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['resource_path', 'status']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        user_repr = self.user.email if self.user else "Anonymous"
        return f"[{self.timestamp}] {user_repr} - {self.action} {self.resource_path} ({self.status})"
