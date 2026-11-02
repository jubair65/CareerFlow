import os
import shutil
import tempfile
from datetime import datetime, timezone as dt_timezone, timedelta
from unittest.mock import patch
from io import StringIO

from django.test import TestCase, override_settings
from django.utils import timezone
from django.core.management import call_command
from django.contrib.auth import get_user_model

from apps.core.models import DataAccessLog
from apps.presentation.models import (
    PresentationVideo,
    PresentationScore,
    SpeechAnalysis,
    BehavioralAnalysis
)
from apps.recruitment.models import (
    RecruitmentRoom,
    CandidateApplication,
    CandidateNote
)

User = get_user_model()


class MediaPurgeCommandTests(TestCase):
    """
    US-49-T7: Automated unit tests for media storage purge and retention command (purge_expired_media).
    Covers AC-1 through AC-6.
    """

    def setUp(self):
        # Create an isolated temporary directory for media during tests
        self.temp_media_root = tempfile.mkdtemp(prefix="test_cf_media_")
        self.settings_override = override_settings(MEDIA_ROOT=self.temp_media_root)
        self.settings_override.enable()

        self.user = User.objects.create_user(
            email="candidate.mobin@careerflow.test",
            password="TestPassword123!",
            username="candidate_mobin"
        )
        self.recruiter = User.objects.create_user(
            email="recruiter.mobin@careerflow.test",
            password="TestPassword123!",
            username="recruiter_mobin"
        )

        self.temp_uploads_dir = os.path.join(self.temp_media_root, 'temp_uploads')
        os.makedirs(self.temp_uploads_dir, exist_ok=True)

    def tearDown(self):
        self.settings_override.disable()
        shutil.rmtree(self.temp_media_root, ignore_errors=True)

    def _create_temp_upload(self, filename: str, age_hours: int, content_bytes: bytes = b"RAW_CHUNK_DATA") -> str:
        """Helper to create a temporary file in temp_uploads/ with an artificial modified time."""
        filepath = os.path.join(self.temp_uploads_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(content_bytes)

        # Artificial mtime in the past
        past_time = timezone.now() - timedelta(hours=age_hours)
        past_ts = past_time.timestamp()
        os.utime(filepath, (past_ts, past_ts))
        return filepath

    def _create_presentation_video(self, filename: str, age_days: int, content_bytes: bytes = b"VIDEO_MP4_CONTENT") -> PresentationVideo:
        """Helper to create a PresentationVideo with an artificial upload date and physical file."""
        video_dir = os.path.join(self.temp_media_root, 'students', str(self.user.id), 'videos')
        os.makedirs(video_dir, exist_ok=True)
        file_path = os.path.join(video_dir, filename)
        with open(file_path, 'wb') as f:
            f.write(content_bytes)

        rel_path = f"students/{self.user.id}/videos/{filename}"

        video = PresentationVideo.objects.create(
            user=self.user,
            file=rel_path,
            original_filename=filename,
            raw_file_size=len(content_bytes) * 2,
            compressed_file_size=len(content_bytes),
            file_type='mp4',
            status='COMPLETED'
        )

        # Set uploaded_at to the past
        past_time = timezone.now() - timedelta(days=age_days)
        PresentationVideo.objects.filter(id=video.id).update(uploaded_at=past_time)
        video.refresh_from_db()
        return video

    def test_dry_run_mode_does_not_delete_files_or_alter_database(self):
        """
        AC-5: Dry-run mode allows previewing files to be deleted without
        actually removing any physical files or altering DB records.
        """
        # Create expired temp upload (72 hours old > 48h threshold)
        old_temp_path = self._create_temp_upload("abandoned_upload_1.mp4", age_hours=72)

        # Create expired presentation video (45 days old > 30d threshold)
        old_video = self._create_presentation_video("stale_practice.mp4", age_days=45)
        old_video_path = old_video.file.path

        # Attach presentation score and feedback
        score = PresentationScore.objects.create(
            video=old_video,
            overall_score=85,
            speech_score=80,
            behavioral_score=90
        )

        out = StringIO()
        call_command('purge_expired_media', '--dry-run', stdout=out)
        output = out.getvalue()

        # Check stdout reflects dry-run preview
        self.assertIn("DRY-RUN PREVIEW", output)
        self.assertIn("Would delete temp upload: abandoned_upload_1.mp4", output)
        self.assertIn("Would purge video", output)
        self.assertIn(f"ID {old_video.id}", output)

        # Verify physical files STILL exist on disk
        self.assertTrue(os.path.exists(old_temp_path))
        self.assertTrue(os.path.exists(old_video_path))

        # Verify video model file field is NOT cleared
        old_video.refresh_from_db()
        self.assertTrue(bool(old_video.file))

        # Verify score is intact
        score.refresh_from_db()
        self.assertEqual(score.overall_score, 85)

        # Verify no batch audit log in live execution was created
        self.assertFalse(DataAccessLog.objects.filter(resource_path="system:purge_expired_media").exists())

    def test_live_purge_removes_expired_temp_uploads_only(self):
        """
        AC-1: System identifies temporary/abandoned uploads older than 48 hours and purges them.
        Fresh temporary files (<48 hours) must be safely preserved.
        """
        old_temp = self._create_temp_upload("old_staging.webm", age_hours=50, content_bytes=b"OLD_CONTENT")
        recent_temp = self._create_temp_upload("recent_staging.webm", age_hours=5, content_bytes=b"RECENT_CONTENT")

        out = StringIO()
        call_command('purge_expired_media', stdout=out)

        # Expired temp file must be deleted from disk
        self.assertFalse(os.path.exists(old_temp))

        # Fresh temp file must still exist
        self.assertTrue(os.path.exists(recent_temp))

        # Check individual audit log for purged temp file
        audit_log = DataAccessLog.objects.filter(resource_path="temp_uploads/old_staging.webm").first()
        self.assertIsNotNone(audit_log)
        self.assertEqual(audit_log.action, DataAccessLog.Action.DELETE)
        self.assertEqual(audit_log.status, DataAccessLog.Status.GRANTED)

    def test_live_purge_stale_videos_preserves_database_scores_and_metrics(self):
        """
        AC-2 & AC-3 & AC-4: Purge unlinks physical media older than 30 days while
        preserving PresentationVideo record, PresentationScore, SpeechAnalysis, BehavioralAnalysis.
        """
        # Expired video: 35 days old
        expired_video = self._create_presentation_video("practice_old.mp4", age_days=35, content_bytes=b"EXPIRED_BYTES_1234")
        expired_file_path = expired_video.file.path

        # Fresh video: 5 days old
        fresh_video = self._create_presentation_video("practice_fresh.mp4", age_days=5, content_bytes=b"FRESH_BYTES_5678")
        fresh_file_path = fresh_video.file.path

        # Create scores and analyses on the expired video
        score = PresentationScore.objects.create(
            video=expired_video,
            overall_score=92,
            speech_score=88,
            behavioral_score=95,
            notes="Outstanding confidence and eye contact."
        )
        speech = SpeechAnalysis.objects.create(
            video=expired_video,
            transcript="Welcome to my presentation on scalable software architecture.",
            words_per_minute=142.5,
            clarity_score=90
        )
        behavioral = BehavioralAnalysis.objects.create(
            video=expired_video,
            eye_contact_score=85,
            posture_score=90,
            engagement_score=88
        )

        out = StringIO()
        call_command('purge_expired_media', stdout=out)

        # 1. Physical file of expired video is deleted
        self.assertFalse(os.path.exists(expired_file_path))

        # 2. Physical file of fresh video is preserved
        self.assertTrue(os.path.exists(fresh_file_path))

        # 3. Expired video record is preserved, but file field is empty
        expired_video.refresh_from_db()
        self.assertEqual(expired_video.file, "")

        # 4. Fresh video record retains its file
        fresh_video.refresh_from_db()
        self.assertTrue(bool(fresh_video.file))

        # 5. Scores and analyses of expired video are completely intact
        score.refresh_from_db()
        self.assertEqual(score.overall_score, 92)
        self.assertEqual(score.notes, "Outstanding confidence and eye contact.")

        speech.refresh_from_db()
        self.assertEqual(speech.words_per_minute, 142.5)
        self.assertIn("scalable software architecture", speech.transcript)

        behavioral.refresh_from_db()
        self.assertEqual(behavioral.eye_contact_score, 85)

        # 6. Batch audit log created with freed bytes and files count (AC-4)
        batch_log = DataAccessLog.objects.filter(resource_path="system:purge_expired_media").first()
        self.assertIsNotNone(batch_log)
        self.assertEqual(batch_log.action, DataAccessLog.Action.DELETE)
        self.assertIn("freed_bytes=", batch_log.user_agent)
        self.assertIn("files_count=", batch_log.user_agent)

    def test_recruitment_application_data_remains_intact_after_purge(self):
        """
        Verify that candidate applications, room associations, notes, and stages
        remain completely accessible after physical media is unlinked.
        """
        room = RecruitmentRoom.objects.create(
            created_by=self.recruiter,
            title="Senior Backend Engineer Room",
            status=RecruitmentRoom.Status.OPEN
        )

        expired_video = self._create_presentation_video("candidate_video.mp4", age_days=40)
        app = CandidateApplication.objects.create(
            room=room,
            candidate=self.user,
            video=expired_video,
            final_score=87.5,
            stage=CandidateApplication.Stage.INTERVIEW_ROUND_1
        )
        note = CandidateNote.objects.create(
            application=app,
            author=self.recruiter,
            content="Strong candidate with good system design intuition."
        )

        out = StringIO()
        call_command('purge_expired_media', stdout=out)

        # Application record intact
        app.refresh_from_db()
        self.assertEqual(app.final_score, 87.5)
        self.assertEqual(app.stage, CandidateApplication.Stage.INTERVIEW_ROUND_1)
        self.assertEqual(app.video.id, expired_video.id)

        # Note intact
        note.refresh_from_db()
        self.assertEqual(note.content, "Strong candidate with good system design intuition.")

    def test_missing_physical_file_handled_gracefully(self):
        """
        AC-6: Command handles missing files on disk without crashing.
        """
        # Create video record pointing to non-existent file path
        ghost_video = PresentationVideo.objects.create(
            user=self.user,
            file="students/999/videos/non_existent_file.mp4",
            original_filename="ghost.mp4",
            raw_file_size=1000,
            status='COMPLETED'
        )
        past_time = timezone.now() - timedelta(days=60)
        PresentationVideo.objects.filter(id=ghost_video.id).update(uploaded_at=past_time)

        out = StringIO()
        # Should execute successfully without throwing FileNotFoundError
        call_command('purge_expired_media', stdout=out)

        ghost_video.refresh_from_db()
        self.assertEqual(ghost_video.file, "")

    @patch('apps.core.management.commands.purge_expired_media.safe_remove_file')
    def test_file_lock_or_permission_error_handled_without_crashing(self, mock_safe_remove):
        """
        AC-6: Purge command handles file lock exceptions or OS permission errors gracefully.
        """
        self._create_temp_upload("locked_file.mp4", age_hours=72)
        mock_safe_remove.return_value = (False, 0, "PermissionError: [WinError 32] The process cannot access the file")

        out = StringIO()
        call_command('purge_expired_media', stdout=out)
        output = out.getvalue()

        # Did not raise unhandled exception, reported failure in output
        self.assertIn("[FAILED] Could not delete locked_file.mp4", output)
        self.assertIn("Errors / Locked Files     : 1", output)

    def test_custom_days_and_temp_hours_arguments(self):
        """
        Tests configurable retention flags (--days and --temp-hours).
        """
        # 15 days old practice video (kept under default 30d, but purged with --days 10)
        mid_video = self._create_presentation_video("mid_age_video.mp4", age_days=15)
        # 20 hours old temp upload (kept under default 48h, but purged with --temp-hours 12)
        mid_temp = self._create_temp_upload("mid_age_temp.mp4", age_hours=20)

        out = StringIO()
        call_command('purge_expired_media', '--days', '10', '--temp-hours', '12', stdout=out)

        # Both should be purged because of stricter custom thresholds
        self.assertFalse(os.path.exists(mid_temp))
        mid_video.refresh_from_db()
        self.assertEqual(mid_video.file, "")
