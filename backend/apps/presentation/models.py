import os
from django.db import models
from django.conf import settings
from django.utils import timezone


def video_upload_to(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    return f"students/{instance.user_id}/videos/{timestamp}_presentation{ext}"


class PresentationVideo(models.Model):
    STATUS_CHOICES = [
        ('UPLOADED', 'Uploaded (Staged)'),
        ('COMPRESSING', 'Compressing Video'),
        ('READY_FOR_ANALYSIS', 'Ready for Analysis'),
        ('PROCESSING_SPEECH', 'Processing Speech Analysis'),
        ('PROCESSING_VISION', 'Processing Behavioral Analysis'),
        ('SCORING', 'Calculating Scores'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='presentation_videos'
    )
    file = models.FileField(
        upload_to=video_upload_to,
        help_text="Path to compressed, normalized video"
    )
    original_filename = models.CharField(max_length=255)
    raw_file_size = models.PositiveIntegerField(
        help_text="Original uploaded size in bytes (up to 250MB)"
    )
    compressed_file_size = models.PositiveIntegerField(
        default=0,
        help_text="Compressed size in bytes (<50MB)"
    )
    file_type = models.CharField(max_length=10)  # mp4, webm, mov
    duration_seconds = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='UPLOADED'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Presentation Video'
        verbose_name_plural = 'Presentation Videos'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.user.username} - {self.original_filename} ({self.status})"

    @property
    def formatted_raw_size(self) -> str:
        mb = self.raw_file_size / (1024 * 1024)
        return f"{mb:.1f} MB"

    @property
    def formatted_compressed_size(self) -> str:
        if not self.compressed_file_size:
            return "Pending"
        mb = self.compressed_file_size / (1024 * 1024)
        return f"{mb:.1f} MB"

    @property
    def compression_savings_percent(self) -> float:
        if self.raw_file_size > 0 and self.compressed_file_size > 0:
            savings = (1 - (self.compressed_file_size / self.raw_file_size)) * 100
            return max(0.0, round(savings, 1))
        return 0.0


class SpeechAnalysis(models.Model):
    video = models.OneToOneField(
        PresentationVideo,
        on_delete=models.CASCADE,
        related_name='speech_analysis'
    )
    transcript = models.TextField(blank=True, default='')
    words_per_minute = models.FloatField(default=0.0)
    filler_word_count = models.PositiveIntegerField(default=0)
    filler_words_breakdown = models.JSONField(default=dict, blank=True)
    clarity_score = models.PositiveIntegerField(default=80)  # 0-100
    duration_seconds = models.FloatField(default=0.0)
    processed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Speech Analysis'
        verbose_name_plural = 'Speech Analyses'
        ordering = ['-processed_at']

    def __str__(self):
        return f"SpeechAnalysis ({self.video.original_filename}) - {self.words_per_minute} WPM"
