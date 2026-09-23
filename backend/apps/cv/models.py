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


class CVFeedback(models.Model):
    """
    Automated CV feedback, rubric scoring, and actionable recommendations (US-08).
    Evaluates formatting, clarity, keyword strength, experience, and education completeness.
    """
    cv = models.OneToOneField(
        CandidateCV,
        on_delete=models.CASCADE,
        related_name='feedback',
        help_text="Candidate CV document associated with this feedback"
    )
    overall_score = models.PositiveIntegerField(help_text="Calculated score 0-100")
    formatting_score = models.PositiveIntegerField(
        default=80,
        help_text="Formatting and completeness score (0-100)"
    )
    clarity_score = models.PositiveIntegerField(
        default=80,
        help_text="Clarity and impact score (0-100)"
    )
    keyword_strength_score = models.PositiveIntegerField(
        default=80,
        help_text="Keyword and action verb strength score (0-100)"
    )
    experience_score = models.PositiveIntegerField(
        default=80,
        help_text="Experience fit and details score (0-100)"
    )
    education_score = models.PositiveIntegerField(
        default=80,
        help_text="Education fit score (0-100)"
    )
    suggestions = models.JSONField(
        default=list,
        help_text="3 actionable edits e.g. ['Quantify checkout result', ...]"
    )
    signal_breakdown = models.JSONField(
        default=dict,
        help_text="Granular score breakdown and extracted signal metrics"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'careerflow_cv_feedback'
        ordering = ['-updated_at']

    def __str__(self):
        return f"CVFeedback for {self.cv.original_filename} (Score: {self.overall_score}/100)"


class JobRequirement(models.Model):
    """
    Target Job Description & Role Requirements (US-09).
    """
    title = models.CharField(max_length=255, help_text="Job role title e.g. Senior Frontend Engineer")
    company = models.CharField(max_length=255, default='CareerFlow Client', help_text="Target hiring company")
    role_type = models.CharField(max_length=255, blank=True, default='', help_text="Role category/seniority")
    description = models.TextField(help_text="Detailed job description and responsibilities")
    required_skills = models.JSONField(default=list, help_text="List of mandatory/preferred skills e.g. ['React', 'Python']")
    threshold_score = models.PositiveIntegerField(default=75, help_text="Minimum score threshold for shortlisting (0-100)")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_jobs',
        help_text="HR manager who posted or created this job brief"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'careerflow_job_requirements'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.company})"


class CVJobMatch(models.Model):
    """
    Semantic similarity scoring and skill gap evaluation between a CV and job requirements (US-09).
    """
    cv = models.ForeignKey(
        CandidateCV,
        on_delete=models.CASCADE,
        related_name='job_matches',
        help_text="Candidate CV evaluated"
    )
    job = models.ForeignKey(
        JobRequirement,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='matches',
        help_text="Associated job requirement brief if matching against a predefined job"
    )
    job_title = models.CharField(max_length=255, help_text="Job title evaluated against")
    company = models.CharField(max_length=255, default='CareerFlow Client', help_text="Company name")
    job_description = models.TextField(blank=True, default='', help_text="Job description text evaluated")
    match_score = models.PositiveIntegerField(help_text="Overall semantic similarity score (0-100)")
    keyword_coverage = models.PositiveIntegerField(default=0, help_text="Percentage of required skills & keywords covered (0-100)")
    category_scores = models.JSONField(
        default=dict,
        help_text="Sub-signal category breakdown e.g. {'domain_craft': 91, 'collaboration': 86, 'leadership': 74, 'accessibility': 62}"
    )
    skills_matched = models.JSONField(default=list, help_text="List of skills present in both CV and Job")
    skills_missing = models.JSONField(default=list, help_text="List of required job skills missing from CV")
    strengths = models.JSONField(default=list, help_text="Key matching strengths identified")
    gaps = models.JSONField(default=list, help_text="Areas needing enhancement for this role")
    recommendations = models.JSONField(default=list, help_text="Actionable suggestions to improve role match score")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'careerflow_cv_job_matches'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['cv', '-updated_at']),
            models.Index(fields=['match_score']),
        ]

    def __str__(self):
        return f"Match: {self.cv.original_filename} vs {self.job_title} ({self.match_score}/100)"



