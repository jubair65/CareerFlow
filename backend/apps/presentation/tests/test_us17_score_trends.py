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


class PresentationScoreTrendsTests(APITestCase):
    """
    US-17: Score Trends Across Attempts
    Covers all Acceptance Criteria:
    - AC 1: Dashboard displays the overall score trend across attempts.
    - AC 2: Category scores (speech and behavioral) are shown as separate comparative trends.
    - AC 3: Trends are built from stored previous analysis results.
    - AC 4: Dashboard handles students with one attempt or no attempts with informative feedback.
    - AC 5: Students only see their own trends (tenant isolation).
    - AC 6: Dashboard updates dynamically after each new attempt completes.
    """

    def setUp(self):
        self.student = User.objects.create_user(
            email='student_trends@careerflow.test',
            username='student_trends',
            password='Password123!',
            role=User.Role.STUDENT,
            full_name='Presentation Trends Student'
        )
        self.other_student = User.objects.create_user(
            email='other_candidate@careerflow.test',
            username='other_candidate',
            password='Password123!',
            role=User.Role.STUDENT,
            full_name='Other Candidate'
        )

        self.trends_url = reverse('presentation:score_trends')

        self.dummy_video_file = SimpleUploadedFile(
            "dummy_take.mp4",
            b"fake_mp4_binary_content_for_testing",
            content_type="video/mp4"
        )

    def tearDown(self):
        for user_id in [self.student.id, self.other_student.id]:
            user_dir = os.path.join(settings.MEDIA_ROOT, f"students/{user_id}")
            if os.path.exists(user_dir):
                try:
                    shutil.rmtree(user_dir)
                except OSError:
                    pass

    def test_tc17_01_no_attempts_returns_informative_empty_state_200_ok(self):
        """AC 4: Student with 0 completed attempts receives 200 OK with empty trend_points and guidance message."""
        self.client.force_authenticate(user=self.student)
        response = self.client.get(self.trends_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_attempts'], 0)
        self.assertEqual(response.data['trend_points'], [])
        self.assertEqual(response.data['summary']['progress_status'], 'NO_DATA')
        self.assertIn("first video", response.data['message'].lower())

    def test_tc17_02_single_attempt_returns_baseline_trend_data(self):
        """AC 4: Student with 1 completed attempt receives baseline metrics and prompt for second attempt."""
        self.client.force_authenticate(user=self.student)

        video = PresentationVideo.objects.create(
            user=self.student,
            file=self.dummy_video_file,
            original_filename="take_1.mp4",
            raw_file_size=1024 * 1024,
            duration_seconds=90,
            status='COMPLETED'
        )
        PresentationScore.objects.create(
            video=video,
            overall_score=75,
            speech_score=72,
            behavioral_score=78,
            pace_score=80,
            filler_score=70,
            eye_contact_score=75,
            posture_score=80,
            engagement_score=76
        )

        response = self.client.get(self.trends_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_attempts'], 1)
        self.assertEqual(len(response.data['trend_points']), 1)

        point = response.data['trend_points'][0]
        self.assertEqual(point['attempt'], 1)
        self.assertEqual(point['overall'], 75)
        self.assertEqual(point['speech'], 72)
        self.assertEqual(point['behavioral'], 78)
        self.assertEqual(response.data['summary']['progress_status'], 'BASELINE')
        self.assertIn("second attempt", response.data['message'].lower())

    def test_tc17_03_multiple_attempts_chronological_ordering_and_deltas(self):
        """AC 1, AC 2, AC 3: Multiple attempts aggregated chronologically with positive deltas."""
        self.client.force_authenticate(user=self.student)
        now = timezone.now()

        # Attempt 1 (10 days ago)
        v1 = PresentationVideo.objects.create(
            user=self.student,
            file=self.dummy_video_file,
            original_filename="round1.mp4",
            raw_file_size=1024 * 1024,
            duration_seconds=80,
            status='COMPLETED'
        )
        PresentationVideo.objects.filter(pk=v1.pk).update(uploaded_at=now - timedelta(days=10))
        PresentationScore.objects.create(
            video=v1,
            overall_score=70,
            speech_score=68,
            behavioral_score=72,
            pace_score=75,
            filler_score=65,
            eye_contact_score=70,
            posture_score=72,
            engagement_score=74
        )

        # Attempt 2 (5 days ago)
        v2 = PresentationVideo.objects.create(
            user=self.student,
            file=self.dummy_video_file,
            original_filename="round2.mp4",
            raw_file_size=1024 * 1024,
            duration_seconds=95,
            status='COMPLETED'
        )
        PresentationVideo.objects.filter(pk=v2.pk).update(uploaded_at=now - timedelta(days=5))
        PresentationScore.objects.create(
            video=v2,
            overall_score=78,
            speech_score=76,
            behavioral_score=80,
            pace_score=82,
            filler_score=74,
            eye_contact_score=78,
            posture_score=80,
            engagement_score=81
        )

        # Attempt 3 (today)
        v3 = PresentationVideo.objects.create(
            user=self.student,
            file=self.dummy_video_file,
            original_filename="round3.mp4",
            raw_file_size=1024 * 1024,
            duration_seconds=110,
            status='COMPLETED'
        )
        PresentationVideo.objects.filter(pk=v3.pk).update(uploaded_at=now)
        PresentationScore.objects.create(
            video=v3,
            overall_score=86,
            speech_score=84,
            behavioral_score=88,
            pace_score=88,
            filler_score=82,
            eye_contact_score=86,
            posture_score=90,
            engagement_score=88
        )

        response = self.client.get(self.trends_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_attempts'], 3)
        self.assertEqual(len(response.data['trend_points']), 3)

        # Verify chronological order (Attempt 1 -> 2 -> 3)
        attempts = [pt['attempt'] for pt in response.data['trend_points']]
        self.assertEqual(attempts, [1, 2, 3])

        overalls = [pt['overall'] for pt in response.data['trend_points']]
        self.assertEqual(overalls, [70, 78, 86])

        # Verify improvement deltas
        self.assertEqual(response.data['improvements']['overall_delta'], "+16%")
        self.assertEqual(response.data['improvements']['speech_delta'], "+16%")
        self.assertEqual(response.data['improvements']['behavioral_delta'], "+16%")
        self.assertEqual(response.data['improvements']['eye_contact_delta'], "+16%")

        # Verify summary statistics
        summary = response.data['summary']
        self.assertEqual(summary['first_score'], 70)
        self.assertEqual(summary['latest_score'], 86)
        self.assertEqual(summary['highest_score'], 86)
        self.assertEqual(summary['lowest_score'], 70)
        self.assertEqual(summary['average_score'], 78.0)
        self.assertEqual(summary['progress_status'], 'IMPROVED')

        # Verify highlights generated
        self.assertTrue(len(response.data['highlights']) >= 1)
        self.assertTrue(any("improved" in h.lower() for h in response.data['highlights']))

    def test_tc17_04_tenant_isolation_students_only_see_own_trends(self):
        """AC 5: Student A only receives their own scores in the trends aggregation, never Student B's."""
        self.client.force_authenticate(user=self.student)

        # My video
        my_v = PresentationVideo.objects.create(
            user=self.student,
            file=self.dummy_video_file,
            original_filename="my_take.mp4",
            raw_file_size=1024 * 1024,
            duration_seconds=60,
            status='COMPLETED'
        )
        PresentationScore.objects.create(
            video=my_v,
            overall_score=92,
            speech_score=90,
            behavioral_score=94
        )

        # Other student's video
        other_v = PresentationVideo.objects.create(
            user=self.other_student,
            file=self.dummy_video_file,
            original_filename="other_secret_take.mp4",
            raw_file_size=1024 * 1024,
            duration_seconds=70,
            status='COMPLETED'
        )
        PresentationScore.objects.create(
            video=other_v,
            overall_score=45,
            speech_score=40,
            behavioral_score=50
        )

        response = self.client.get(self.trends_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_attempts'], 1)
        self.assertEqual(response.data['trend_points'][0]['video_id'], my_v.id)
        self.assertEqual(response.data['trend_points'][0]['overall'], 92)

        # Verify other student's low score is not factored into average or points
        self.assertNotIn(other_v.id, [p['video_id'] for p in response.data['trend_points']])
        self.assertEqual(response.data['summary']['average_score'], 92.0)

    def test_tc17_05_incomplete_videos_excluded_from_trends(self):
        """AC 3: Videos still processing or failing (without presentation_score) are excluded from trends."""
        self.client.force_authenticate(user=self.student)

        # Completed take with score
        v_done = PresentationVideo.objects.create(
            user=self.student,
            file=self.dummy_video_file,
            original_filename="done.mp4",
            raw_file_size=1024 * 1024,
            duration_seconds=60,
            status='COMPLETED'
        )
        PresentationScore.objects.create(
            video=v_done,
            overall_score=80,
            speech_score=78,
            behavioral_score=82
        )

        # Incomplete takes
        PresentationVideo.objects.create(
            user=self.student,
            file=self.dummy_video_file,
            original_filename="processing.mp4",
            raw_file_size=1024 * 1024,
            duration_seconds=60,
            status='PROCESSING_SPEECH'
        )
        PresentationVideo.objects.create(
            user=self.student,
            file=self.dummy_video_file,
            original_filename="failed.mp4",
            raw_file_size=1024 * 1024,
            duration_seconds=60,
            status='FAILED'
        )

        response = self.client.get(self.trends_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Only the 1 scored video is included
        self.assertEqual(response.data['total_attempts'], 1)
        self.assertEqual(len(response.data['trend_points']), 1)
        self.assertEqual(response.data['trend_points'][0]['video_id'], v_done.id)

    def test_tc17_06_unauthenticated_requests_rejected_401(self):
        """Unauthenticated requests are rejected with 401 Unauthorized."""
        response = self.client.get(self.trends_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_tc17_07_category_subscores_included_in_trend_points(self):
        """AC 2: Speech subscores (pace, filler) and behavioral subscores (eye contact, posture, engagement) are included."""
        self.client.force_authenticate(user=self.student)

        v = PresentationVideo.objects.create(
            user=self.student,
            file=self.dummy_video_file,
            original_filename="detailed_subscores.mp4",
            raw_file_size=1024 * 1024,
            duration_seconds=75,
            status='COMPLETED'
        )
        PresentationScore.objects.create(
            video=v,
            overall_score=85,
            speech_score=84,
            behavioral_score=86,
            pace_score=88,
            filler_score=80,
            eye_contact_score=85,
            posture_score=90,
            engagement_score=82
        )
        SpeechAnalysis.objects.create(
            video=v,
            transcript="Testing speech breakdown in trend",
            words_per_minute=148.0,
            filler_word_count=1,
            clarity_score=90
        )
        BehavioralAnalysis.objects.create(
            video=v,
            eye_contact_score=85,
            posture_score=90,
            engagement_score=82
        )

        response = self.client.get(self.trends_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        point = response.data['trend_points'][0]

        self.assertEqual(point['pace_score'], 88)
        self.assertEqual(point['filler_score'], 80)
        self.assertEqual(point['eye_contact_score'], 85)
        self.assertEqual(point['posture_score'], 90)
        self.assertEqual(point['engagement_score'], 82)
        self.assertEqual(point['words_per_minute'], 148.0)
        self.assertEqual(point['filler_word_count'], 1)
        self.assertEqual(point['clarity_score'], 90)

    def test_tc17_08_dynamic_update_when_new_attempt_completed(self):
        """AC 6: Aggregation dynamically updates when an additional attempt completes."""
        self.client.force_authenticate(user=self.student)
        now = timezone.now()

        # Initial attempt
        v1 = PresentationVideo.objects.create(
            user=self.student,
            file=self.dummy_video_file,
            original_filename="attempt_one.mp4",
            raw_file_size=1024 * 1024,
            duration_seconds=60,
            status='COMPLETED'
        )
        PresentationVideo.objects.filter(pk=v1.pk).update(uploaded_at=now - timedelta(hours=2))
        PresentationScore.objects.create(
            video=v1,
            overall_score=68,
            speech_score=65,
            behavioral_score=70
        )

        res1 = self.client.get(self.trends_url)
        self.assertEqual(res1.data['total_attempts'], 1)
        self.assertEqual(res1.data['summary']['latest_score'], 68)

        # Student completes attempt 2
        v2 = PresentationVideo.objects.create(
            user=self.student,
            file=self.dummy_video_file,
            original_filename="attempt_two.mp4",
            raw_file_size=1024 * 1024,
            duration_seconds=65,
            status='COMPLETED'
        )
        PresentationVideo.objects.filter(pk=v2.pk).update(uploaded_at=now)
        PresentationScore.objects.create(
            video=v2,
            overall_score=82,
            speech_score=80,
            behavioral_score=84
        )

        res2 = self.client.get(self.trends_url)
        self.assertEqual(res2.data['total_attempts'], 2)
        self.assertEqual(res2.data['summary']['latest_score'], 82)
        self.assertEqual(res2.data['improvements']['overall_delta'], "+14%")
        self.assertEqual(res2.data['summary']['progress_status'], 'IMPROVED')
