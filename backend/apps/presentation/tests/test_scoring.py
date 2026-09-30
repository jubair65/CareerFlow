import os
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.authentication.models import User
from apps.presentation.models import PresentationVideo, SpeechAnalysis, BehavioralAnalysis, PresentationScore
from apps.presentation.services.scorer import PresentationScorer, calculate_presentation_score


class PresentationScoringLogicUnitTests(APITestCase):
    """
    US-14-T6: Unit tests for presentation scoring algorithm, subscore equations,
    and clamping boundaries according to the formal specification.
    """

    def test_wpm_optimal_range(self):
        """Within 130-160 WPM should yield a perfect 100 pace score."""
        self.assertEqual(PresentationScorer.calculate_pace_score(130), 100)
        self.assertEqual(PresentationScorer.calculate_pace_score(145), 100)
        self.assertEqual(PresentationScorer.calculate_pace_score(160), 100)

    def test_wpm_slow_deductions(self):
        """Below 130 WPM should deduct 1 point per WPM deviation."""
        self.assertEqual(PresentationScorer.calculate_pace_score(120), 90)
        self.assertEqual(PresentationScorer.calculate_pace_score(100), 70)
        self.assertEqual(PresentationScorer.calculate_pace_score(30), 0)
        self.assertEqual(PresentationScorer.calculate_pace_score(0), 0)
        self.assertEqual(PresentationScorer.calculate_pace_score(-10), 0)

    def test_wpm_fast_deductions(self):
        """Above 160 WPM should deduct 1 point per WPM deviation."""
        self.assertEqual(PresentationScorer.calculate_pace_score(170), 90)
        self.assertEqual(PresentationScorer.calculate_pace_score(195), 65)
        self.assertEqual(PresentationScorer.calculate_pace_score(280), 0)

    def test_filler_word_score_penalties(self):
        """Each filler word deducts 5 points from 100, clamped at 0."""
        self.assertEqual(PresentationScorer.calculate_filler_score(0), 100)
        self.assertEqual(PresentationScorer.calculate_filler_score(2), 90)
        self.assertEqual(PresentationScorer.calculate_filler_score(6), 70)
        self.assertEqual(PresentationScorer.calculate_filler_score(20), 0)
        self.assertEqual(PresentationScorer.calculate_filler_score(50), 0)

    def test_speech_composite_score(self):
        """Speech score is 50% pace and 50% filler words."""
        # 140 WPM (100) and 2 fillers (90) -> (100*0.5 + 90*0.5) = 95
        pace, filler, speech = PresentationScorer.calculate_speech_score(wpm=140, filler_count=2)
        self.assertEqual(pace, 100)
        self.assertEqual(filler, 90)
        self.assertEqual(speech, 95)

    def test_behavioral_score_weightings(self):
        """Behavioral score is 40% eye contact + 30% posture + 30% engagement."""
        # eye: 90, posture: 80, engagement: 70
        # 90*0.4 (36) + 80*0.3 (24) + 70*0.3 (21) = 81
        eye, post, eng, composite = PresentationScorer.calculate_behavioral_score(
            eye_contact=90,
            posture=80,
            engagement=70
        )
        self.assertEqual(eye, 90)
        self.assertEqual(post, 80)
        self.assertEqual(eng, 70)
        self.assertEqual(composite, 81)

    def test_composite_overall_score(self):
        """Overall score combines 50% speech and 50% behavioral."""
        # Speech: pace 145 (100), fillers 0 (100) -> speech 100
        # Behavioral: eye 80 (32) + post 80 (24) + eng 80 (24) = 80
        # Overall: 100 * 0.5 + 80 * 0.5 = 90
        dummy_speech = type('Speech', (), {
            'words_per_minute': 145.0,
            'filler_word_count': 0
        })()
        dummy_behavior = type('Behavior', (), {
            'eye_contact_score': 80,
            'posture_score': 80,
            'engagement_score': 80
        })()

        res = PresentationScorer.evaluate(dummy_speech, dummy_behavior)
        self.assertEqual(res['overall_score'], 90)
        self.assertEqual(res['speech_score'], 100)
        self.assertEqual(res['behavioral_score'], 80)
        self.assertTrue(res['has_behavioral_data'])

    def test_graceful_degradation_missing_behavioral_data(self):
        """When behavioral data is None, overall score is 100% speech score."""
        dummy_speech = type('Speech', (), {
            'words_per_minute': 150.0,
            'filler_word_count': 4  # 80 filler score -> 90 speech score
        })()

        res = PresentationScorer.evaluate(dummy_speech, behavioral=None)
        self.assertEqual(res['overall_score'], 90)
        self.assertEqual(res['speech_score'], 90)
        self.assertEqual(res['behavioral_score'], 0)
        self.assertFalse(res['has_behavioral_data'])
        self.assertIn("insufficient", res['notes'])

    def test_clamping_extremes(self):
        """All subscores and overall score must remain within [0, 100]."""
        self.assertEqual(PresentationScorer.clamp_score(-25), 0)
        self.assertEqual(PresentationScorer.clamp_score(150), 100)
        self.assertEqual(PresentationScorer.clamp_score(78.6), 79)


class PresentationScoreAPITests(APITestCase):
    """
    US-14-T4 & US-14-T6: API endpoint tests for GET and POST score calculations,
    permissions, cross-user isolation, and status updates.
    """

    def setUp(self):
        self.user1 = User.objects.create_user(
            email="mona_student@careerflow.test",
            username="mona_candidate",
            password="SecurePass2026!",
            role=User.Role.STUDENT,
            full_name="Mona Candidate"
        )
        self.user2 = User.objects.create_user(
            email="other_student@careerflow.test",
            username="other_candidate",
            password="SecurePass2026!",
            role=User.Role.STUDENT,
            full_name="Other Candidate"
        )

        dummy_file = SimpleUploadedFile("presentation.mp4", b"fake_mp4_bytes", content_type="video/mp4")
        self.video = PresentationVideo.objects.create(
            user=self.user1,
            file=dummy_file,
            original_filename="interview_take1.mp4",
            raw_file_size=1024 * 1024 * 15,
            compressed_file_size=1024 * 1024 * 5,
            file_type="mp4",
            duration_seconds=60,
            status="READY_FOR_ANALYSIS",
            is_active=True
        )

        self.speech = SpeechAnalysis.objects.create(
            video=self.video,
            transcript="Hello, I am presenting my SWE project for the interview.",
            words_per_minute=140.0,
            filler_word_count=2,
            filler_words_breakdown={"um": 2},
            clarity_score=85,
            duration_seconds=60.0
        )

        self.behavioral = BehavioralAnalysis.objects.create(
            video=self.video,
            eye_contact_score=85,
            posture_score=90,
            engagement_score=80
        )

    def test_calculate_presentation_score_creates_record(self):
        """calculate_presentation_score service creates PresentationScore and marks video COMPLETED."""
        score = calculate_presentation_score(self.video)
        self.assertIsInstance(score, PresentationScore)
        self.video.refresh_from_db()
        self.assertEqual(self.video.status, "COMPLETED")
        self.assertGreaterEqual(score.overall_score, 0)
        self.assertLessEqual(score.overall_score, 100)
        self.assertEqual(score.grade_label, "Excellent")

    def test_api_get_score_auto_calculates(self):
        """GET /api/presentation/<id>/score/ auto-calculates if speech analysis exists."""
        self.client.force_authenticate(user=self.user1)
        url = reverse('presentation:presentation_score', kwargs={'video_id': self.video.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertIn('overall_score', data)
        self.assertIn('speech_score', data)
        self.assertIn('behavioral_score', data)
        self.assertIn('grade_label', data)
        self.assertIn('grade_color', data)
        self.assertEqual(data['grade_label'], 'Excellent')
        self.assertEqual(data['has_behavioral_data'], True)

    def test_api_post_score_recalculate(self):
        """POST /api/presentation/<id>/score/ explicitly calculates/updates score."""
        self.client.force_authenticate(user=self.user1)
        url = reverse('presentation:presentation_score', kwargs={'video_id': self.video.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Presentation score calculated successfully.')
        self.assertIn('presentation_score', response.data)
        self.assertEqual(response.data['presentation_score']['video'], self.video.id)

    def test_api_score_requires_authentication(self):
        """Unauthenticated requests must be rejected with 401."""
        url = reverse('presentation:presentation_score', kwargs={'video_id': self.video.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_api_score_cross_user_isolation(self):
        """Candidate B cannot view or trigger candidate A's presentation score."""
        self.client.force_authenticate(user=self.user2)
        url = reverse('presentation:presentation_score', kwargs={'video_id': self.video.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
