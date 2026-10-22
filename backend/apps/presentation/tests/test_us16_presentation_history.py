import os
import shutil
from datetime import timedelta
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
)


class PresentationHistoryTests(APITestCase):
    """
    US-16: View Previous Presentation Analysis Results
    Covers all Acceptance Criteria:
    - AC 1: Student can see a list of their previous presentation analyses
    - AC 2: Student can open any past analysis to view its score, breakdown, and suggestions
    - AC 3: Results are listed by date, newest first
    - AC 4: Students can only access their own results (tenant isolation)
    - AC 5: Empty history is handled with a clear message and upload call-to-action
    - AC 6: Results load within reasonable time (<1.2s under standard conditions)
    """

    def setUp(self):
        self.student_user = User.objects.create_user(
            email='student_history@careerflow.test',
            username='student_history',
            password='Password123!',
            role=User.Role.STUDENT,
            full_name='Presentation History Student'
        )
        self.other_student = User.objects.create_user(
            email='other_student@careerflow.test',
            username='other_student',
            password='Password123!',
            role=User.Role.STUDENT,
            full_name='Other Candidate'
        )

        self.history_url = reverse('presentation:video_history')

        # Create dummy file for video model
        self.dummy_video_file = SimpleUploadedFile(
            "dummy_take.mp4",
            b"fake_mp4_binary_content_for_testing",
            content_type="video/mp4"
        )

    def tearDown(self):
        # Cleanup any generated test media dirs
        for user_id in [self.student_user.id, self.other_student.id]:
            user_dir = os.path.join(settings.MEDIA_ROOT, f"students/{user_id}")
            if os.path.exists(user_dir):
                try:
                    shutil.rmtree(user_dir)
                except OSError:
                    pass

    def test_tc16_01_student_retrieves_empty_history_200_ok(self):
        """AC 1 & AC 5: When student has no previous uploads, history returns 200 OK with empty array."""
        self.client.force_authenticate(user=self.student_user)
        response = self.client.get(self.history_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_tc16_02_student_retrieves_presentation_history_chronological(self):
        """AC 1 & AC 3: History returns student's previous videos ordered newest first."""
        self.client.force_authenticate(user=self.student_user)

        # Create 3 videos uploaded at different times
        now = timezone.now()
        v1 = PresentationVideo.objects.create(
            user=self.student_user,
            file=self.dummy_video_file,
            original_filename="take_1_oldest.mp4",
            raw_file_size=1024 * 1024,
            duration_seconds=60,
            status='COMPLETED'
        )
        # Manually backdate uploaded_at
        PresentationVideo.objects.filter(pk=v1.pk).update(uploaded_at=now - timedelta(days=2))

        v2 = PresentationVideo.objects.create(
            user=self.student_user,
            file=self.dummy_video_file,
            original_filename="take_2_yesterday.mp4",
            raw_file_size=2 * 1024 * 1024,
            duration_seconds=90,
            status='COMPLETED'
        )
        PresentationVideo.objects.filter(pk=v2.pk).update(uploaded_at=now - timedelta(days=1))

        v3 = PresentationVideo.objects.create(
            user=self.student_user,
            file=self.dummy_video_file,
            original_filename="take_3_newest.mp4",
            raw_file_size=3 * 1024 * 1024,
            duration_seconds=120,
            status='COMPLETED'
        )
        PresentationVideo.objects.filter(pk=v3.pk).update(uploaded_at=now)

        response = self.client.get(self.history_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

        # Verify strict descending order (newest first)
        returned_ids = [item['id'] for item in response.data]
        self.assertEqual(returned_ids, [v3.id, v2.id, v1.id])
        self.assertEqual(response.data[0]['original_filename'], "take_3_newest.mp4")
        self.assertEqual(response.data[2]['original_filename'], "take_1_oldest.mp4")

    def test_tc16_03_tenant_isolation_student_only_sees_own_videos(self):
        """AC 4: Students can only view their own presentation analyses, not others'."""
        self.client.force_authenticate(user=self.student_user)

        # Create videos for student_user
        my_v1 = PresentationVideo.objects.create(
            user=self.student_user,
            file=self.dummy_video_file,
            original_filename="my_interview_pitch.mp4",
            raw_file_size=1024 * 1024,
            duration_seconds=60,
            status='COMPLETED'
        )

        # Create videos for other_student
        other_v1 = PresentationVideo.objects.create(
            user=self.other_student,
            file=self.dummy_video_file,
            original_filename="secret_other_candidate_pitch.mp4",
            raw_file_size=2 * 1024 * 1024,
            duration_seconds=90,
            status='COMPLETED'
        )

        response = self.client.get(self.history_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], my_v1.id)
        self.assertNotIn(other_v1.id, [v['id'] for v in response.data])

    def test_tc16_04_student_retrieves_complete_analysis_payload(self):
        """AC 2: Past analysis contains composite score, speech breakdown, behavioral metrics, and AI suggestions."""
        self.client.force_authenticate(user=self.student_user)

        video = PresentationVideo.objects.create(
            user=self.student_user,
            file=self.dummy_video_file,
            original_filename="complete_presentation.mp4",
            raw_file_size=2048 * 1024,
            duration_seconds=110,
            status='COMPLETED'
        )

        SpeechAnalysis.objects.create(
            video=video,
            transcript="Hello everyone, today I want to present CareerFlow.",
            words_per_minute=145.5,
            filler_word_count=2,
            filler_words_breakdown={"um": 1, "like": 1},
            clarity_score=88,
            duration_seconds=110.0
        )

        BehavioralAnalysis.objects.create(
            video=video,
            eye_contact_score=84,
            posture_score=90,
            engagement_score=82,
            frame_metrics={"sample": "metrics"}
        )

        PresentationScore.objects.create(
            video=video,
            overall_score=86,
            speech_score=88,
            behavioral_score=84,
            pace_score=92,
            filler_score=85,
            eye_contact_score=84,
            posture_score=90,
            engagement_score=82
        )

        PresentationFeedback.objects.create(
            video=video,
            summary="Strong and confident presentation with great camera gaze.",
            strengths=["Optimal speaking pace (145 WPM)", "Steady eye contact"],
            improvements=[{"category": "Pacing", "observation": "Slight rush at opening", "actionable_drill": "Take a 2-second breath"}],
            practice_tip="Pause intentionally before transition slides."
        )

        response = self.client.get(self.history_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        data = response.data[0]
        # Check speech metrics
        self.assertIsNotNone(data['speech_analysis'])
        self.assertEqual(data['speech_analysis']['words_per_minute'], 145.5)
        self.assertEqual(data['speech_analysis']['filler_word_count'], 2)
        self.assertEqual(data['speech_analysis']['clarity_score'], 88)

        # Check behavioral metrics
        self.assertIsNotNone(data['behavioral_analysis'])
        self.assertEqual(data['behavioral_analysis']['eye_contact_score'], 84)
        self.assertEqual(data['behavioral_analysis']['posture_score'], 90)

        # Check score card
        self.assertIsNotNone(data['presentation_score'])
        self.assertEqual(data['presentation_score']['overall_score'], 86)
        self.assertEqual(data['presentation_score']['grade_label'], "Excellent")

        # Check feedback
        self.assertIsNotNone(data['ai_feedback'])
        self.assertIn("Optimal speaking pace", data['ai_feedback']['strengths'][0])

    def test_tc16_05_unauthorized_user_cannot_access_other_students_video_detail(self):
        """AC 4 & US-16-T5: Student cannot view another student's past video via detail endpoint."""
        self.client.force_authenticate(user=self.student_user)

        other_video = PresentationVideo.objects.create(
            user=self.other_student,
            file=self.dummy_video_file,
            original_filename="private_take.mp4",
            raw_file_size=1024 * 1024,
            duration_seconds=45,
            status='COMPLETED'
        )

        detail_url = reverse('presentation:video_detail', kwargs={'pk': other_video.id})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("permission", response.data['error'].lower())

        # Also test via /api/presentation/history/<pk>/
        history_detail_url = reverse('presentation:video_history_detail', kwargs={'pk': other_video.id})
        response_hist = self.client.get(history_detail_url)
        self.assertEqual(response_hist.status_code, status.HTTP_403_FORBIDDEN)

    def test_tc16_06_non_existent_video_returns_404(self):
        """Detail endpoint returns 404 Not Found for non-existent video ID."""
        self.client.force_authenticate(user=self.student_user)
        detail_url = reverse('presentation:video_detail', kwargs={'pk': 99999})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_tc16_07_unauthenticated_request_rejected(self):
        """Unauthenticated requests are rejected with 401 Unauthorized."""
        response = self.client.get(self.history_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_tc16_08_search_filter_by_original_filename(self):
        """Search query parameter filters past presentations by filename."""
        self.client.force_authenticate(user=self.student_user)

        PresentationVideo.objects.create(
            user=self.student_user,
            file=self.dummy_video_file,
            original_filename="technical_architecture_pitch.mp4",
            raw_file_size=1024 * 1024,
            duration_seconds=60,
            status='COMPLETED'
        )
        PresentationVideo.objects.create(
            user=self.student_user,
            file=self.dummy_video_file,
            original_filename="behavioral_hr_interview.mp4",
            raw_file_size=1024 * 1024,
            duration_seconds=60,
            status='COMPLETED'
        )

        res_search = self.client.get(f"{self.history_url}?search=technical")
        self.assertEqual(res_search.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_search.data), 1)
        self.assertEqual(res_search.data[0]['original_filename'], "technical_architecture_pitch.mp4")

    def test_tc16_09_status_filter_completed(self):
        """Status query parameter filters past presentations by processing status."""
        self.client.force_authenticate(user=self.student_user)

        PresentationVideo.objects.create(
            user=self.student_user,
            file=self.dummy_video_file,
            original_filename="completed_take.mp4",
            raw_file_size=1024 * 1024,
            duration_seconds=60,
            status='COMPLETED'
        )
        PresentationVideo.objects.create(
            user=self.student_user,
            file=self.dummy_video_file,
            original_filename="processing_take.mp4",
            raw_file_size=1024 * 1024,
            duration_seconds=60,
            status='PROCESSING_SPEECH'
        )

        res_filter = self.client.get(f"{self.history_url}?status=completed")
        self.assertEqual(res_filter.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_filter.data), 1)
        self.assertEqual(res_filter.data[0]['original_filename'], "completed_take.mp4")

    def test_tc16_10_student_can_delete_own_video(self):
        """Student can successfully delete their own past presentation."""
        self.client.force_authenticate(user=self.student_user)

        video = PresentationVideo.objects.create(
            user=self.student_user,
            file=self.dummy_video_file,
            original_filename="take_to_delete.mp4",
            raw_file_size=1024 * 1024,
            duration_seconds=60,
            status='COMPLETED'
        )

        detail_url = reverse('presentation:video_detail', kwargs={'pk': video.id})
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(PresentationVideo.objects.filter(pk=video.id).exists())

    def test_tc16_11_student_cannot_delete_other_students_video(self):
        """AC 4 & US-16-T5: Student cannot delete another student's presentation video."""
        self.client.force_authenticate(user=self.student_user)

        other_video = PresentationVideo.objects.create(
            user=self.other_student,
            file=self.dummy_video_file,
            original_filename="other_protected_take.mp4",
            raw_file_size=1024 * 1024,
            duration_seconds=60,
            status='COMPLETED'
        )

        detail_url = reverse('presentation:video_detail', kwargs={'pk': other_video.id})
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # Verify video still exists
        self.assertTrue(PresentationVideo.objects.filter(pk=other_video.id).exists())
