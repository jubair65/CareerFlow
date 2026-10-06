import secrets
from django.conf import settings
from django.db import models


class RecruitmentRoom(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        PAUSED = 'PAUSED', 'Paused'
        CLOSED = 'CLOSED', 'Closed'

    title = models.CharField(max_length=200, help_text="Job title for the recruitment opening")
    company_name = models.CharField(max_length=200, help_text="Hiring company or department organization")
    department = models.CharField(max_length=150, blank=True, default="", help_text="Optional department or team")
    description = models.TextField(blank=True, default="", help_text="Detailed job description and responsibilities")
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        help_text="Current operational status of the room"
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recruitment_rooms',
        help_text="HR Manager who created and owns this room"
    )

    # US-19: Job Role & Skills Foundation
    requirements_text = models.TextField(
        blank=True,
        default="",
        help_text="Detailed job requirements text criteria"
    )
    skills_required = models.JSONField(
        default=list,
        blank=True,
        help_text="List of required skills and proficiency requirements"
    )

    # US-20: Evaluation Weighting Foundation
    cv_weight = models.PositiveSmallIntegerField(
        default=50,
        help_text="Percentage weight allocated to CV match score (0-100)"
    )
    video_weight = models.PositiveSmallIntegerField(
        default=50,
        help_text="Percentage weight allocated to Video presentation score (0-100)"
    )

    # US-21: Shareable Application Link Foundation
    share_token = models.CharField(
        max_length=64,
        unique=True,
        null=True,
        blank=True,
        help_text="Cryptographically secure unique token for the public application link"
    )
    link_is_active = models.BooleanField(
        default=True,
        help_text="Whether candidates can access the application page via share_token"
    )
    link_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Optional expiration timestamp for the shareable link"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'careerflow_recruitment_rooms'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} @ {self.company_name} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        # Auto-generate a secure non-guessable share token if not set
        if not self.share_token:
            self.share_token = secrets.token_urlsafe(16)
        super().save(*args, **kwargs)
