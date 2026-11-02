import os
import sys
import time
import logging
from datetime import datetime, timezone as dt_timezone, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from apps.core.models import DataAccessLog
from apps.presentation.models import PresentationVideo

logger = logging.getLogger(__name__)


def safe_remove_file(file_path: str) -> tuple[bool, int, str]:
    """
    US-49-T3: Safe physical file deletion utility with exception and lock handling.
    Wraps os.remove in exception handling to handle missing files, file lock
    exceptions, or OS permissions without crashing.

    Returns:
        tuple[bool, int, str]: (success, freed_bytes, error_message)
    """
    if not file_path:
        return False, 0, "No file path provided"

    if not os.path.exists(file_path):
        return True, 0, "File does not exist on disk"

    try:
        file_size = os.path.getsize(file_path)
        os.remove(file_path)
        return True, file_size, ""
    except FileNotFoundError:
        return True, 0, "File not found"
    except PermissionError as e:
        logger.warning(f"File locked or permission denied while purging {file_path}: {e}")
        return False, 0, f"PermissionError: {e}"
    except OSError as e:
        logger.warning(f"OS error occurred while purging {file_path}: {e}")
        return False, 0, f"OSError: {e}"


def format_bytes(bytes_count: int) -> str:
    """Format bytes count to human-readable string (B, KB, MB, GB)."""
    if bytes_count < 1024:
        return f"{bytes_count} B"
    elif bytes_count < 1024 * 1024:
        return f"{bytes_count / 1024:.2f} KB"
    elif bytes_count < 1024 * 1024 * 1024:
        return f"{bytes_count / (1024 * 1024):.2f} MB"
    else:
        return f"{bytes_count / (1024 * 1024 * 1024):.2f} GB"


class Command(BaseCommand):
    """
    US-49-T2: Django Management Command `purge_expired_media`
    Identifies and purges:
      1. Abandoned/temporary video uploads older than configured hours (default: 48h) in media/temp_uploads/
      2. Practice session presentation media files older than configured retention period (default: 30 days)

    Preserves all database records, scores, feedback, analyses, and audit logs while unlinking physical media.
    Supports dry-run mode for previewing deletions without modifying disk or DB.
    Logs audit records to DataAccessLog with freed bytes, files count, and execution duration.
    """
    help = "Purge expired media files and abandoned uploads according to retention policies (US-49)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview files and records eligible for deletion without deleting them (AC-5).'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Retention window in days for practice session presentation media (default: 30 days).'
        )
        parser.add_argument(
            '--temp-hours',
            type=int,
            default=48,
            help='Retention window in hours for abandoned temporary uploads in temp_uploads/ (default: 48 hours).'
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        days = options.get('days', 30)
        temp_hours = options.get('temp_hours', 48)

        start_time = timezone.now()
        mode_label = "DRY-RUN PREVIEW" if dry_run else "LIVE PURGE EXECUTION"

        self.stdout.write(self.style.MIGRATE_HEADING(f"=== CareerFlow Media Retention Purge [{mode_label}] ==="))
        self.stdout.write(f"Practice video retention threshold: {days} days")
        self.stdout.write(f"Temporary uploads retention threshold: {temp_hours} hours")

        video_cutoff = start_time - timedelta(days=days)
        temp_cutoff = start_time - timedelta(hours=temp_hours)

        self.stdout.write(f"Video Cutoff Timestamp: {video_cutoff.isoformat()}")
        self.stdout.write(f"Temp Uploads Cutoff Timestamp: {temp_cutoff.isoformat()}\n")

        # Metrics tracking
        temp_scanned = 0
        temp_purged = 0
        temp_freed_bytes = 0
        temp_errors = 0

        video_scanned = 0
        video_purged = 0
        video_freed_bytes = 0
        video_errors = 0

        # =========================================================================
        # PART 1: Scan and Purge Abandoned Staging Uploads (media/temp_uploads/)
        # =========================================================================
        self.stdout.write(self.style.HTTP_INFO("[Phase 1] Scanning temporary uploads directory..."))
        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_uploads')

        if os.path.exists(temp_dir) and os.path.isdir(temp_dir):
            for entry in os.scandir(temp_dir):
                if entry.is_file():
                    temp_scanned += 1
                    try:
                        mtime_dt = datetime.fromtimestamp(entry.stat().st_mtime, tz=dt_timezone.utc)
                    except Exception:
                        mtime_dt = timezone.now()

                    if mtime_dt < temp_cutoff:
                        file_path = entry.path
                        try:
                            file_size = entry.stat().st_size
                        except OSError:
                            file_size = 0

                        if dry_run:
                            temp_purged += 1
                            temp_freed_bytes += file_size
                            self.stdout.write(
                                f"  [DRY-RUN] Would delete temp upload: {entry.name} "
                                f"({format_bytes(file_size)}, modified: {mtime_dt.strftime('%Y-%m-%d %H:%M')})"
                            )
                        else:
                            success, freed, err = safe_remove_file(file_path)
                            if success:
                                temp_purged += 1
                                temp_freed_bytes += freed
                                self.stdout.write(
                                    self.style.SUCCESS(
                                        f"  [PURGED] Temp upload: {entry.name} ({format_bytes(freed)})"
                                    )
                                )
                                # US-49-T5: Log audit trail for temp file deletion
                                DataAccessLog.objects.create(
                                    user=None,
                                    resource_path=f"temp_uploads/{entry.name}",
                                    action=DataAccessLog.Action.DELETE,
                                    status=DataAccessLog.Status.GRANTED,
                                    ip_address='127.0.0.1',
                                    user_agent=(
                                        f"System Management Command: purge_expired_media "
                                        f"(freed_bytes={freed})"
                                    )
                                )
                            else:
                                temp_errors += 1
                                self.stdout.write(
                                    self.style.ERROR(
                                        f"  [FAILED] Could not delete {entry.name}: {err}"
                                    )
                                )
        else:
            self.stdout.write("  Directory 'temp_uploads' does not exist or is empty.")

        # =========================================================================
        # PART 2: Scan and Purge Expired Presentation Videos
        # =========================================================================
        self.stdout.write(self.style.HTTP_INFO("\n[Phase 2] Scanning expired presentation videos in database..."))

        # Find videos uploaded before the cutoff date
        expired_videos = PresentationVideo.objects.filter(
            uploaded_at__lt=video_cutoff
        ).exclude(
            file=''
        ).exclude(
            file__isnull=True
        ).select_related(
            'presentation_score',
            'speech_analysis',
            'behavioral_analysis'
        )

        for video in expired_videos:
            video_scanned += 1
            file_abs_path = ""
            file_size = 0
            file_exists = False

            if video.file:
                try:
                    file_abs_path = video.file.path
                    if os.path.exists(file_abs_path):
                        file_exists = True
                        file_size = os.path.getsize(file_abs_path)
                    else:
                        file_size = video.compressed_file_size or video.raw_file_size or 0
                except Exception:
                    file_size = video.compressed_file_size or 0

            if dry_run:
                video_purged += 1
                video_freed_bytes += file_size
                status_note = "exists on disk" if file_exists else "already missing from disk"
                self.stdout.write(
                    f"  [DRY-RUN] Would purge video: ID {video.id} ({video.original_filename}) "
                    f"[{format_bytes(file_size)}, uploaded: {video.uploaded_at.strftime('%Y-%m-%d')}, {status_note}]"
                )
            else:
                # AC-3: Safely purge physical file while preserving database scores and logs
                success = True
                freed = 0
                if file_exists and file_abs_path:
                    success, freed, err = safe_remove_file(file_abs_path)
                    if not success:
                        video_errors += 1
                        self.stdout.write(
                            self.style.ERROR(f"  [FAILED] Could not unlink {file_abs_path}: {err}")
                        )

                if success:
                    video_purged += 1
                    video_freed_bytes += freed
                    # Preserve database model and scores; unlink media field reference
                    old_path = str(video.file)
                    video.file = ''
                    video.save(update_fields=['file'])

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  [PURGED] Video record ID {video.id} ({video.original_filename}) "
                            f"- freed {format_bytes(freed)}, scores preserved"
                        )
                    )

                    # US-49-T5: Log audit trail for video media purge
                    DataAccessLog.objects.create(
                        user=video.user,
                        resource_path=old_path or f"presentation_videos/{video.id}",
                        action=DataAccessLog.Action.DELETE,
                        status=DataAccessLog.Status.GRANTED,
                        ip_address='127.0.0.1',
                        user_agent=(
                            f"System Management Command: purge_expired_media "
                            f"(video_id={video.id}, freed_bytes={freed})"
                        )
                    )

        # =========================================================================
        # PART 3: Summary Reporting and Batch Audit Log
        # =========================================================================
        end_time = timezone.now()
        duration_sec = (end_time - start_time).total_seconds()
        total_scanned = temp_scanned + video_scanned
        total_purged = temp_purged + video_purged
        total_freed_bytes = temp_freed_bytes + video_freed_bytes
        total_errors = temp_errors + video_errors

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.MIGRATE_HEADING(f"SUMMARY REPORT - {mode_label}"))
        self.stdout.write("=" * 60)
        self.stdout.write(f"Execution Duration        : {duration_sec:.2f} seconds")
        self.stdout.write(f"Temporary Files Scanned   : {temp_scanned}")
        self.stdout.write(f"Temporary Files Purged    : {temp_purged}")
        self.stdout.write(f"Temporary Space Freed     : {format_bytes(temp_freed_bytes)}")
        self.stdout.write(f"Videos Scanned            : {video_scanned}")
        self.stdout.write(f"Videos Purged             : {video_purged}")
        self.stdout.write(f"Video Space Freed         : {format_bytes(video_freed_bytes)}")
        self.stdout.write("-" * 60)
        self.stdout.write(f"Total Objects Purged      : {total_purged} of {total_scanned} scanned")
        self.stdout.write(f"Total Storage Freed       : {format_bytes(total_freed_bytes)} ({total_freed_bytes} bytes)")
        self.stdout.write(f"Errors / Locked Files     : {total_errors}")
        self.stdout.write("=" * 60)

        # US-49-T5: In live purge execution, record batch audit log in DataAccessLog
        if not dry_run:
            DataAccessLog.objects.create(
                user=None,
                resource_path="system:purge_expired_media",
                action=DataAccessLog.Action.DELETE,
                status=DataAccessLog.Status.GRANTED,
                ip_address='127.0.0.1',
                user_agent=(
                    f"CareerFlow Management Command: purge_expired_media "
                    f"(freed_bytes={total_freed_bytes}, files_count={total_purged}, "
                    f"execution_duration={duration_sec:.2f}s)"
                )
            )
            self.stdout.write(self.style.SUCCESS("[Audit] Batch audit log successfully saved to DataAccessLog."))
        else:
            self.stdout.write(self.style.WARNING("[Notice] Dry-run complete. No files were removed and no DB records altered."))
