import uuid
from django.db import models
from django.conf import settings


def generate_consent_token():
    return uuid.uuid4().hex


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


class Notification(models.Model):
    """
    US-34: In-app and system notification model.
    Stores notifications with unread/read status, categorisation,
    and direct target URLs.
    """
    class NotificationType(models.TextChoices):
        INFO = 'INFO', 'Information'
        SUCCESS = 'SUCCESS', 'Success'
        WARNING = 'WARNING', 'Warning'
        ERROR = 'ERROR', 'Error'
        CV_ANALYSIS_COMPLETE = 'CV_ANALYSIS_COMPLETE', 'CV Analysis Complete'
        PRESENTATION_ANALYSIS_COMPLETE = 'PRESENTATION_ANALYSIS_COMPLETE', 'Presentation Analysis Complete'
        APPLICATION_STATUS = 'APPLICATION_STATUS', 'Application Status'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text="Recipient user of the notification"
    )
    title = models.CharField(max_length=200, help_text="Notification heading")
    message = models.TextField(help_text="Notification detailed body")
    link_url = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text="Frontend deep link to the results or dashboard"
    )
    notification_type = models.CharField(
        max_length=50,
        choices=NotificationType.choices,
        default=NotificationType.INFO,
        help_text="Category and severity of notification"
    )
    is_read = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether recipient has viewed/acknowledged the notification"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="Timestamp when notification was generated"
    )

    class Meta:
        db_table = 'careerflow_notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        read_flag = "Read" if self.is_read else "Unread"
        return f"[{self.notification_type}] {self.user.email} - {self.title} ({read_flag})"


class AIConsentLog(models.Model):
    """
    US-48-T2: AI Biometric & Evaluation Consent Notice Gatekeeper.
    Records explicit user agreements to AI biometric and telemetric analysis
    (audio tone/speech metrics, facial telemetry, posture analysis) in compliance
    with GDPR Article 9 & EU AI Act ethical disclosure requirements.
    """
    class ConsentType(models.TextChoices):
        BIOMETRIC_EVALUATION = 'BIOMETRIC_EVALUATION', 'AI Presentation Biometric & Telemetry Evaluation'
        GENERAL_AI_PROCESSING = 'GENERAL_AI_PROCESSING', 'General AI Processing'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ai_consent_logs',
        help_text="User who granted consent (null if unauthenticated public candidate)"
    )
    email = models.EmailField(
        max_length=255,
        blank=True,
        default='',
        help_text="Candidate email recorded at time of consent"
    )
    consent_type = models.CharField(
        max_length=50,
        choices=ConsentType.choices,
        default=ConsentType.BIOMETRIC_EVALUATION,
        help_text="Type of AI analysis covered by consent"
    )
    policy_version = models.CharField(
        max_length=20,
        default='v1.0',
        help_text="Version identifier of the ethical AI disclosure agreed to"
    )
    agreed = models.BooleanField(
        default=True,
        help_text="Whether explicit consent was granted (True) or refused (False)"
    )
    consent_token = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        default=generate_consent_token,
        help_text="Cryptographically secure verification token issued upon consent"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="Client IP address recorded at time of consent submission"
    )
    user_agent = models.TextField(
        blank=True,
        default='',
        help_text="Browser user agent string for audit logging"
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="UTC timestamp when consent action was recorded"
    )

    class Meta:
        db_table = 'careerflow_ai_consent_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'agreed']),
            models.Index(fields=['consent_token']),
            models.Index(fields=['email', 'agreed']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        user_repr = self.user.email if self.user else (self.email or "Anonymous")
        status_repr = "Agreed" if self.agreed else "Refused"
        return f"[{self.timestamp}] {user_repr} - {self.consent_type} {self.policy_version} ({status_repr})"
