import os
import shutil
import tempfile
from django.utils import timezone
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase

from apps.authentication.models import User
from apps.presentation.models import (
    PresentationVideo,
    SpeechAnalysis,
    BehavioralAnalysis,
    PresentationScore,
    PresentationFeedback,
    PipelineExecutionLog,
)


class PracticeSessionManagementTests(APITestCase):
    """
    US-44: Student Practice Session Management & Deletion
    Covers Acceptance Criteria:
    - AC-1: Student can rename any previous practice session with custom title or tag (max 100 chars).
    - AC-2: Student can delete an unwanted practice recording and its associated analysis data.
    - AC-3: Confirmation modal & endpoint authorization protection.
    - AC-4: Deleting a practice session safely removes the video file from media storage.
    - AC-5: Score trend graphs and history list automatically update after rename or deletion.
    - AC-6: Students cannot rename or delete practice sessions belonging to other users.
    """

    def setUp(self):
        self.student_a = User.objects.create_user(
            email='student_a@careerflow.test',
            username='student_a',
            password='Password123!',
            role=User.Role.STUDENT,
            full_name='Alice Student'
        )
        self.student_b = User.objects.create_user(
            email='student_b@careerflow.test',
            username='student_b',
            password='Password123!',
            role=User.Role.STUDENT,
            full_name='Bob Candidate'
        )

        # Temporary media folder for testing file deletions
        self.test_media_dir = tempfile.mkdtemp()
        self._original_media_root = settings.MEDIA_ROOT
        settings.MEDIA_ROOT = self.test_media_dir

        # Create dummy video file
        self.dummy_video_file = SimpleUploadedFile(
            "practice_take_1.mp4",
            b"fake_mp4_binary_stream_data_for_us44_tests",
            content_type="video/mp4"
        )

        # Create sample video for Student A
        self.video_a = PresentationVideo.objects.create(
            user=self.student_a,
            file=self.dummy_video_file,
            original_filename="practice_take_1.mp4",
            raw_file_size=1024 * 1024,
            compressed_file_size=512 * 1024,
            file_type="mp4",
            duration_seconds=90,
            status="COMPLETED",
            is_active=True
        )

        # Attach analyses and score
        self.speech_a = SpeechAnalysis.objects.create(
            video=self.video_a,
            transcript="Hello world, this is a practice take.",
            words_per_minute=140.0,
            filler_word_count=2,
            clarity_score=85
        )
        self.behavioral_a = BehavioralAnalysis.objects.create(
            video=self.video_a,
            eye_contact_score=88,
            posture_score=84,
            engagement_score=80
        )
        self.score_a = PresentationScore.objects.create(
            video=self.video_a,
            overall_score=85,
            speech_score=85,
            behavioral_score=84
        )
        self.feedback_a = PresentationFeedback.objects.create(
            video=self.video_a,
            summary="Strong opening with good clarity.",
            strengths=["Consistent eye contact", "Natural pacing"],
            improvements=[{"category": "Posture", "actionable_drill": "Keep shoulders squared"}]
        )
        self.log_a = PipelineExecutionLog.objects.create(
            video=self.video_a,
            stage=PipelineExecutionLog.Stage.PIPELINE,
            status=PipelineExecutionLog.Status.SUCCESS,
            execution_time_ms=1200
        )

        # Create sample video for Student B
        dummy_b_file = SimpleUploadedFile(
            "student_b_take.mp4",
            b"fake_mp4_binary_stream_data_for_student_b",
            content_type="video/mp4"
        )
        self.video_b = PresentationVideo.objects.create(
            user=self.student_b,
            file=dummy_b_file,
            original_filename="student_b_take.mp4",
            raw_file_size=1024 * 1024,
            compressed_file_size=512 * 1024,
            file_type="mp4",
            duration_seconds=60,
            status="COMPLETED",
            is_active=True
        )

    def tearDown(self):
        settings.MEDIA_ROOT = self._original_media_root
        if os.path.exists(self.test_media_dir):
            shutil.rmtree(self.test_media_dir, ignore_errors=True)

    # =========================================================================
    # RENAME TESTS (US-44-T2, AC-1, AC-6)
    # =========================================================================

    def test_rename_practice_session_success(self):
        """AC-1: Student can rename any previous practice session with custom title."""
        self.client.force_authenticate(user=self.student_a)
        url = reverse('presentation:video_rename', kwargs={'pk': self.video_a.id})
        response = self.client.patch(url, {'title': 'Elevator Pitch - Final Polish'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Practice session renamed successfully.')
        self.assertEqual(response.data['video']['title'], 'Elevator Pitch - Final Polish')
        self.assertEqual(response.data['video']['display_title'], 'Elevator Pitch - Final Polish')

        self.video_a.refresh_from_db()
        self.assertEqual(self.video_a.title, 'Elevator Pitch - Final Polish')
        self.assertEqual(self.video_a.display_title, 'Elevator Pitch - Final Polish')

    def test_rename_via_practice_url(self):
        """AC-1: Rename via dedicated /api/practice/<id>/rename/ endpoint."""
        self.client.force_authenticate(user=self.student_a)
        url = reverse('practice:practice_rename', kwargs={'pk': self.video_a.id})
        response = self.client.patch(url, {'title': 'Practice Direct Route'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.video_a.refresh_from_db()
        self.assertEqual(self.video_a.title, 'Practice Direct Route')

    def test_rename_trims_whitespace(self):
        """AC-1: Title with surrounding whitespace is cleanly stripped."""
        self.client.force_authenticate(user=self.student_a)
        url = reverse('presentation:video_rename', kwargs={'pk': self.video_a.id})
        response = self.client.patch(url, {'title': '   Technical Intro Take 2   '}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.video_a.refresh_from_db()
        self.assertEqual(self.video_a.title, 'Technical Intro Take 2')

    def test_rename_empty_title_fails(self):
        """AC-1: Empty title string returns 400 Bad Request."""
        self.client.force_authenticate(user=self.student_a)
        url = reverse('presentation:video_rename', kwargs={'pk': self.video_a.id})
        response = self.client.patch(url, {'title': ''}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('title', response.data)

    def test_rename_whitespace_only_title_fails(self):
        """AC-1: Whitespace-only title returns 400 Bad Request."""
        self.client.force_authenticate(user=self.student_a)
        url = reverse('presentation:video_rename', kwargs={'pk': self.video_a.id})
        response = self.client.patch(url, {'title': '     '}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('title', response.data)

    def test_rename_exceeding_max_length_fails(self):
        """AC-1: Title longer than 100 characters returns 400 Bad Request."""
        self.client.force_authenticate(user=self.student_a)
        url = reverse('presentation:video_rename', kwargs={'pk': self.video_a.id})
        long_title = 'A' * 101
        response = self.client.patch(url, {'title': long_title}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('title', response.data)

    def test_rename_unauthorized_user_forbidden(self):
        """AC-6: Student cannot rename another student's practice session (tenant isolation)."""
        self.client.force_authenticate(user=self.student_a)
        url = reverse('presentation:video_rename', kwargs={'pk': self.video_b.id})
        response = self.client.patch(url, {'title': 'Hacked Title'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.video_b.refresh_from_db()
        self.assertNotEqual(self.video_b.title, 'Hacked Title')

    def test_rename_nonexistent_session_not_found(self):
        """Rename non-existent session returns 404 Not Found."""
        self.client.force_authenticate(user=self.student_a)
        url = reverse('presentation:video_rename', kwargs={'pk': 999999})
        response = self.client.patch(url, {'title': 'Does Not Exist'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_rename_unauthenticated_returns_401(self):
        """Unauthenticated request cannot rename session."""
        url = reverse('presentation:video_rename', kwargs={'pk': self.video_a.id})
        response = self.client.patch(url, {'title': 'Unauthorized'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # =========================================================================
    # DELETION & STORAGE CLEANUP TESTS (US-44-T3, AC-2, AC-4, AC-6)
    # =========================================================================

    def test_delete_practice_session_success(self):
        """AC-2 & AC-4: Student can delete practice session and removes record from DB."""
        self.client.force_authenticate(user=self.student_a)
        url = reverse('presentation:video_detail', kwargs={'pk': self.video_a.id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(PresentationVideo.objects.filter(id=self.video_a.id).exists())

    def test_delete_via_practice_url(self):
        """AC-2: Delete via dedicated /api/practice/<id>/ route."""
        self.client.force_authenticate(user=self.student_a)
        url = reverse('practice:practice_detail', kwargs={'pk': self.video_a.id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(PresentationVideo.objects.filter(id=self.video_a.id).exists())

    def test_delete_physical_media_file_cleanup(self):
        """AC-4: Deleting a practice session safely removes the video file from media storage."""
        self.client.force_authenticate(user=self.student_a)
        video_file_path = self.video_a.file.path
        self.assertTrue(os.path.exists(video_file_path))

        url = reverse('presentation:video_detail', kwargs={'pk': self.video_a.id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify physical file is gone from filesystem
        self.assertFalse(os.path.exists(video_file_path))

    def test_delete_cascades_associated_telemetry(self):
        """AC-2: Deleting video cascades to speech, behavioral, score, feedback, and logs."""
        video_id = self.video_a.id
        self.client.force_authenticate(user=self.student_a)
        url = reverse('presentation:video_detail', kwargs={'pk': video_id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(SpeechAnalysis.objects.filter(video_id=video_id).exists())
        self.assertFalse(BehavioralAnalysis.objects.filter(video_id=video_id).exists())
        self.assertFalse(PresentationScore.objects.filter(video_id=video_id).exists())
        self.assertFalse(PresentationFeedback.objects.filter(video_id=video_id).exists())
        self.assertFalse(PipelineExecutionLog.objects.filter(video_id=video_id).exists())

    def test_delete_handles_missing_file_gracefully(self):
        """AC-4: Deleting when physical file was already missing does not raise 500 error."""
        self.client.force_authenticate(user=self.student_a)
        video_file_path = self.video_a.file.path
        if os.path.exists(video_file_path):
            os.remove(video_file_path)

        url = reverse('presentation:video_detail', kwargs={'pk': self.video_a.id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(PresentationVideo.objects.filter(id=self.video_a.id).exists())

    def test_delete_unauthorized_user_forbidden(self):
        """AC-6: Student cannot delete another student's practice session."""
        self.client.force_authenticate(user=self.student_a)
        url = reverse('presentation:video_detail', kwargs={'pk': self.video_b.id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # Verify student B's video still exists
        self.assertTrue(PresentationVideo.objects.filter(id=self.video_b.id).exists())

    def test_delete_nonexistent_session_not_found(self):
        """Deleting non-existent session returns 404 Not Found."""
        self.client.force_authenticate(user=self.student_a)
        url = reverse('presentation:video_detail', kwargs={'pk': 999999})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_unauthenticated_returns_401(self):
        """Unauthenticated request cannot delete session."""
        url = reverse('presentation:video_detail', kwargs={'pk': self.video_a.id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # =========================================================================
    # SCORE TRENDS RECALCULATION POST-DELETION (AC-5)
    # =========================================================================

    def test_score_trends_recalculate_after_session_deleted(self):
        """AC-5: Score trend metrics and attempt count update after session deletion."""
        # Add second video for student A with score 95
        dummy_file_2 = SimpleUploadedFile(
            "take_2.mp4",
            b"fake_mp4_binary_content_take_2",
            content_type="video/mp4"
        )
        video_2 = PresentationVideo.objects.create(
            user=self.student_a,
            file=dummy_file_2,
            original_filename="take_2.mp4",
            raw_file_size=1024 * 1024,
            file_type="mp4",
            duration_seconds=120,
            status="COMPLETED",
            is_active=False
        )
        PresentationScore.objects.create(
            video=video_2,
            overall_score=95,
            speech_score=95,
            behavioral_score=95
        )

        self.client.force_authenticate(user=self.student_a)
        trends_url = reverse('presentation:score_trends')

        # Check initial trends with 2 attempts (avg = (85 + 95)/2 = 90.0)
        res1 = self.client.get(trends_url)
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        self.assertEqual(res1.data['summary']['total_attempts'], 2)
        self.assertEqual(res1.data['summary']['average_score'], 90.0)

        # Delete first video (score 85)
        del_url = reverse('presentation:video_detail', kwargs={'pk': self.video_a.id})
        del_res = self.client.delete(del_url)
        self.assertEqual(del_res.status_code, status.HTTP_200_OK)

        # Fetch trends again -> now 1 attempt with score 95
        res2 = self.client.get(trends_url)
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertEqual(res2.data['summary']['total_attempts'], 1)
        self.assertEqual(res2.data['summary']['average_score'], 95.0)
        self.assertEqual(res2.data['summary']['highest_score'], 95)
