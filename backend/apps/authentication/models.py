from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = 'STUDENT', 'Student / Applicant'
        HR_MANAGER = 'HR_MANAGER', 'HR Manager'
        AGENCY_ADMIN = 'AGENCY_ADMIN', 'Agency Admin'

    email = models.EmailField(unique=True, verbose_name="Email Address")
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
        help_text="Role determining user permissions in CareerFlow"
    )
    full_name = models.CharField(max_length=150, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'careerflow_users'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"


class PasswordResetToken(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='password_reset_tokens',
        help_text="User requesting the password reset"
    )
    code = models.CharField(
        max_length=10,
        blank=True,
        default="",
        db_index=True,
        help_text="4-digit random verification code"
    )
    token_hash = models.CharField(
        max_length=64,
        db_index=True,
        help_text="SHA-256 hash of the raw reset token"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when reset was requested"
    )
    expires_at = models.DateTimeField(
        help_text="Expiry timestamp (15 minutes from creation)"
    )
    is_used = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether this reset token has already been consumed"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of the requester for security audit"
    )

    class Meta:
        db_table = 'careerflow_password_reset_tokens'
        ordering = ['-created_at']

    def __str__(self):
        status_label = "Used" if self.is_used else ("Active" if self.is_active else "Expired")
        return f"ResetToken({self.user.email} - Code:{self.code} - {status_label})"

    @property
    def is_active(self) -> bool:
        from django.utils import timezone
        return not self.is_used and self.expires_at >= timezone.now()

    @classmethod
    def create_token_for_user(cls, user, ip_address=None, lifetime_minutes=15) -> str:
        """
        Generates a 4-digit verification code and a 32-byte random token,
        stores its SHA-256 hash with an expiration timestamp,
        and returns the raw token string for transmission via email.
        """
        import hashlib
        import secrets
        from datetime import timedelta
        from django.utils import timezone

        code = f"{secrets.randbelow(9000) + 1000}"  # 4 digits (1000-9999)
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode('utf-8')).hexdigest()
        expires_at = timezone.now() + timedelta(minutes=lifetime_minutes)

        cls.objects.create(
            user=user,
            code=code,
            token_hash=token_hash,
            expires_at=expires_at,
            ip_address=ip_address
        )
        return raw_token

    @classmethod
    def verify_code(cls, user, code: str) -> bool:
        """Checks if the 4-digit code is valid and active for the user without consuming it."""
        from django.utils import timezone
        if not user or not code:
            return False
        clean_code = str(code).strip()
        return cls.objects.filter(
            user=user,
            code=clean_code,
            is_used=False,
            expires_at__gte=timezone.now()
        ).exists()

    @classmethod
    def validate_and_consume_code(cls, user, code: str) -> bool:
        """Validates and atomically consumes the 4-digit verification code."""
        from django.utils import timezone
        if not user or not code:
            return False
        clean_code = str(code).strip()
        now = timezone.now()

        token_obj = cls.objects.filter(
            user=user,
            code=clean_code,
            is_used=False,
            expires_at__gte=now
        ).first()

        if not token_obj:
            return False

        token_obj.is_used = True
        token_obj.save(update_fields=['is_used'])
        cls.objects.filter(user=user, is_used=False).update(is_used=True)
        return True

    @classmethod
    def validate_and_consume_token(cls, user, raw_token: str) -> bool:
        """
        Validates raw token OR 4-digit code against unexpired tokens.
        If valid, unexpired, and unused, atomically marks it as used,
        revokes all other active tokens for that user, and returns True.
        """
        import hashlib
        from django.utils import timezone

        if not user or not raw_token:
            return False

        clean_token = str(raw_token).strip()
        now = timezone.now()

        # Check by 4-digit code first if length matches
        if len(clean_token) == 4 and clean_token.isdigit():
            if cls.validate_and_consume_code(user, clean_token):
                return True

        token_hash = hashlib.sha256(clean_token.encode('utf-8')).hexdigest()

        token_obj = cls.objects.filter(
            user=user,
            token_hash=token_hash,
            is_used=False,
            expires_at__gte=now
        ).first()

        if not token_obj:
            return False

        # Mark this token as used and revoke any lingering active tokens for this user
        token_obj.is_used = True
        token_obj.save(update_fields=['is_used'])
        cls.objects.filter(user=user, is_used=False).update(is_used=True)

        return True


class CandidateProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='candidate_profile',
        help_text="User owning this candidate profile"
    )
    phone_number = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        help_text="Contact phone number (international format e.g. +1234567890)"
    )
    linkedin_url = models.URLField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Public LinkedIn profile URL"
    )
    github_url = models.URLField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Public GitHub profile URL"
    )
    target_role = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        help_text="Target job title or specialization (e.g. Senior Frontend Engineer)"
    )
    bio = models.TextField(
        blank=True,
        null=True,
        help_text="Short career objective / professional bio"
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        help_text="Profile picture / avatar"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'careerflow_candidate_profiles'
        ordering = ['-updated_at']

    def __str__(self):
        return f"CandidateProfile({self.user.email} - {self.target_role or 'No Role'})"
