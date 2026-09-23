import os
import re
from django.db import models
from django.conf import settings
from django.utils import timezone


def cv_upload_to(instance, filename):
    """
    Store uploaded CVs in user-isolated storage under media/students/{student_id}/cv/
    with sanitized, timestamped filenames to avoid collisions and path traversal.
    """
    ext = os.path.splitext(filename)[1].lower()
    base_name = os.path.splitext(filename)[0]
    # Keep only alphanumeric, hyphens, and underscores
    sanitized_base = re.sub(r'[^a-zA-Z0-9_\-]', '_', base_name)[:50]
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    clean_filename = f"{timestamp}_{sanitized_base}{ext}"
    return f"students/{instance.user_id}/cv/{clean_filename}"


class CandidateCV(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cvs',
        help_text="Candidate who owns this CV"
    )
    file = models.FileField(
        upload_to=cv_upload_to,
        help_text="Path to stored CV document"
    )
    original_filename = models.CharField(
        max_length=255,
        help_text="Original filename as uploaded by candidate"
    )
    file_size = models.PositiveIntegerField(
        help_text="File size in bytes"
    )
    file_type = models.CharField(
        max_length=10,
        help_text="Document format extension (pdf or docx)"
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="True if this is the active CV version used for scoring and matching"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'careerflow_candidate_cvs'
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['uploaded_at']),
        ]

    def __str__(self):
        status = 'active' if self.is_active else 'archived'
        return f"{self.user.email} - {self.original_filename} ({status})"


class ParsedCV(models.Model):
    """
    Extracted structured data from candidate CV (US-07).
    Contains raw text, identified skills, education history, and experience records.
    """
    cv = models.OneToOneField(
        CandidateCV,
        on_delete=models.CASCADE,
        related_name='parsed_data',
        help_text="Candidate CV document associated with this parsed data"
    )
    raw_text = models.TextField(help_text="Extracted text from the CV document")
    skills = models.JSONField(default=list, help_text="List of extracted skills [React, Python, ...]")
    education = models.JSONField(default=list, help_text="[{degree, institution, year}]")
    experience = models.JSONField(default=list, help_text="[{title, company, duration_years}]")
    parsed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'careerflow_parsed_cvs'
        ordering = ['-parsed_at']

    def __str__(self):
        return f"ParsedCV for {self.cv.original_filename} ({len(self.skills)} skills)"

    @property
    def skills_count(self) -> int:
        return len(self.skills) if isinstance(self.skills, list) else 0

