import secrets
from django.conf import settings
from django.db import models



class ClientCompany(models.Model):
    """
    US-29-T1: Client company profile managed by a Recruitment Agency Administrator.
    Supports multi-tenant company isolation, contact records, and soft deactivation states.
    """
    agency = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='client_companies',
        help_text="Recruitment Agency Administrator who manages this client company"
    )
    name = models.CharField(
        max_length=200,
        help_text="Client company name"
    )
    industry = models.CharField(
        max_length=100,
        help_text="Industry sector (e.g., Technology, Finance, Healthcare, Retail)"
    )
    contact_person = models.CharField(
        max_length=150,
        help_text="Primary representative or contact person at client company"
    )
    contact_email = models.EmailField(
        help_text="Primary contact email address for candidate forwarding and notifications"
    )
    phone = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="Contact phone number"
    )
    website = models.URLField(
        blank=True,
        default="",
        help_text="Company official website URL"
    )
    notes = models.TextField(
        blank=True,
        default="",
        help_text="Internal agency notes or remarks regarding the client"
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Operational status: Active (True) or Deactivated (False)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'careerflow_client_companies'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['agency', 'name'],
                name='unique_agency_client_company_name'
            )
        ]

    def __str__(self):
        status_label = "Active" if self.is_active else "Deactivated"
        return f"{self.name} ({self.industry}) - {status_label}"


class RecruitmentRoom(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        PAUSED = 'PAUSED', 'Paused'
        CLOSED = 'CLOSED', 'Closed'

    title = models.CharField(max_length=200, help_text="Job title for the recruitment opening")
    company_name = models.CharField(max_length=200, help_text="Hiring company or department organization")
    department = models.CharField(max_length=150, blank=True, default="", help_text="Optional department or team")
    description = models.TextField(blank=True, default="", help_text="Detailed job description and responsibilities")
    
    # US-29 / US-30: Associated Client Company for Agency Rooms
    client_company = models.ForeignKey(
        'ClientCompany',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rooms',
        help_text="Associated client company for agency-managed recruitment rooms"
    )

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

    class ExperienceLevel(models.TextChoices):
        ENTRY = 'ENTRY', 'Entry Level (0-2 years)'
        MID = 'MID', 'Mid Level (2-5 years)'
        SENIOR = 'SENIOR', 'Senior Level (5-8 years)'
        LEAD = 'LEAD', 'Lead / Principal (8+ years)'

    # US-19: Job Role & Skills Foundation
    role_category = models.CharField(
        max_length=100,
        blank=True,
        default="Engineering",
        help_text="Job role category (e.g. Engineering, Design, Product, Data)"
    )
    experience_level = models.CharField(
        max_length=20,
        choices=ExperienceLevel.choices,
        default=ExperienceLevel.MID,
        help_text="Target seniority or experience level required for the position"
    )
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

    # US-25: Automatic Candidate Shortlisting Foundation
    class ShortlistStrategy(models.TextChoices):
        NONE = 'NONE', 'None (Disabled)'
        MIN_SCORE = 'MIN_SCORE', 'Minimum Score Threshold'
        TOP_N = 'TOP_N', 'Top Candidates (Top N)'
        COMBINED = 'COMBINED', 'Top N meeting Minimum Score'

    shortlist_strategy = models.CharField(
        max_length=20,
        choices=ShortlistStrategy.choices,
        default=ShortlistStrategy.NONE,
        help_text="Configured automatic shortlisting strategy"
    )
    shortlist_min_score = models.FloatField(
        null=True,
        blank=True,
        help_text="Minimum final score required for shortlisting (0.0 - 100.0)"
    )
    shortlist_top_n = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Required candidate count / top N applicants to shortlist"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'careerflow_recruitment_rooms'
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(cv_weight__gte=0, cv_weight__lte=100) & models.Q(video_weight__gte=0, video_weight__lte=100),
                name='check_recruitment_room_weights_range'
            )
        ]

    def __str__(self):
        return f"{self.title} @ {self.company_name} ({self.get_status_display()})"

    def clean(self):
        super().clean()
        from django.core.exceptions import ValidationError
        if self.cv_weight is None:
            self.cv_weight = 50
        if self.video_weight is None:
            self.video_weight = 50
        if self.cv_weight < 0 or self.cv_weight > 100:
            raise ValidationError({'cv_weight': 'CV weight must be between 0 and 100.'})
        if self.video_weight < 0 or self.video_weight > 100:
            raise ValidationError({'video_weight': 'Video weight must be between 0 and 100.'})
        if self.cv_weight + self.video_weight != 100:
            raise ValidationError({'weights': f'Weights must sum to 100% (currently {self.cv_weight}% + {self.video_weight}% = {self.cv_weight + self.video_weight}%).'})

    def save(self, *args, **kwargs):
        # Auto-generate a secure non-guessable share token if not set
        if not self.share_token:
            self.share_token = secrets.token_urlsafe(32)
        self.clean()
        super().save(*args, **kwargs)

    def get_skill_names(self):
        """Returns clean list of string skill names from skills_required JSON."""
        if not self.skills_required or not isinstance(self.skills_required, list):
            return []
        names = []
        for item in self.skills_required:
            if isinstance(item, str):
                s = item.strip()
                if s:
                    names.append(s)
            elif isinstance(item, dict) and 'name' in item:
                s = str(item['name']).strip()
                if s:
                    names.append(s)
        return names


class CandidateApplication(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending Analysis'
        ANALYZING = 'ANALYZING', 'Analyzing'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'

    room = models.ForeignKey(
        RecruitmentRoom,
        on_delete=models.CASCADE,
        related_name='applications',
        help_text="The recruitment room applied to"
    )
    candidate = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='applications',
        help_text="The candidate applying"
    )
    cv = models.OneToOneField(
        'cv.CandidateCV',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="The CV uploaded for this application"
    )
    video = models.OneToOneField(
        'presentation.PresentationVideo',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="The Video uploaded for this application"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        help_text="Current processing status"
    )
    # --- SPRINT 5 ENHANCEMENTS: US-23 Score Storage & Component Cache ---
    cv_score = models.FloatField(
        null=True,
        blank=True,
        help_text="Cached CV match score (0-100)"
    )
    video_score = models.FloatField(
        null=True,
        blank=True,
        help_text="Cached Video presentation score (0-100)"
    )
    final_score = models.FloatField(
        null=True, 
        blank=True,
        db_index=True,
        help_text="Calculated weighted score based on room criteria"
    )
    is_partial_score = models.BooleanField(
        default=False,
        help_text="True if calculated with missing CV or video"
    )
    score_calculated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when final score was last computed"
    )
    # --- SPRINT 5 ENHANCEMENTS: US-25 Automatic Candidate Shortlisting ---
    is_shortlisted = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether candidate is currently shortlisted"
    )
    shortlist_reason = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Reason or criteria match explanation for shortlist status"
    )
    shortlisted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when candidate was shortlisted"
    )
    # --- SPRINT 5 ENHANCEMENTS: US-26 HR Review of AI Results & Audit Trail ---
    class HrDecision(models.TextChoices):
        UNDECIDED = 'UNDECIDED', 'Pending HR Review'
        CONFIRMED = 'CONFIRMED', 'Shortlist Confirmed'
        OVERRIDDEN = 'OVERRIDDEN', 'AI Recommendation Overridden'
        REJECTED = 'REJECTED', 'Candidate Rejected'
        ON_HOLD = 'ON_HOLD', 'Application On Hold'

    hr_decision = models.CharField(
        max_length=25,
        choices=HrDecision.choices,
        default=HrDecision.UNDECIDED,
        db_index=True,
        help_text="Human HR Manager final decision"
    )
    hr_decision_notes = models.TextField(
        blank=True,
        default="",
        help_text="Reason or audit notes from HR reviewer"
    )
    hr_decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='hr_reviewed_applications',
        help_text="HR user who recorded the review decision"
    )
    hr_decided_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when HR review decision was recorded"
    )
    applied_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'careerflow_candidate_applications'
        ordering = ['-applied_at']
        unique_together = ('room', 'candidate')

    def __str__(self):
        return f"{self.candidate.email} -> {self.room.title} ({self.get_status_display()})"
