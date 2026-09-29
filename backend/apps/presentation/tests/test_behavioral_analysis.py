import os
import shutil
import tempfile
from unittest.mock import patch, MagicMock
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.authentication.models import User
from apps.presentation.models import PresentationVideo, BehavioralAnalysis
from apps.presentation.services.behavioral_metrics import (
    compute_eye_aspect_ratio,
    compute_iris_horizontal_ratio,
    is_eye_contact_frame,
    calculate_eye_contact_score,
    calculate_shoulder_tilt_angle,
    check_is_slouched,
    calculate_posture_score,
    calculate_facial_engagement,
    calculate_engagement_score,
    euclidean_distance,
)
from apps.presentation.services.vision_pipeline import VisionPipeline
from apps.presentation.services.behavioral_analyzer import (
    BehavioralAnalyzer,
    analyze_behavior,
)


class MockVisionPipeline:
    """
    Mock vision pipeline for deterministic, fast unit tests without requiring live camera/GPU inference.
    """
    def __init__(
        self,
        eye_contact_score=85,
        posture_score=90,
        engagement_score=88,
        total_frames=100,
        face_frames=95,
        contact_frames=85
    ):
        self.eye_contact_score = eye_contact_score
        self.posture_score = posture_score
        self.engagement_score = engagement_score
        self.total_frames = total_frames
        self.face_frames = face_frames
        self.contact_frames = contact_frames

    def analyze_video(self, video_path: str):
        return {
            "eye_contact_score": self.eye_contact_score,
            "posture_score": self.posture_score,
            "engagement_score": self.engagement_score,
            "frame_metrics": {
                "total_video_frames": self.total_frames,
                "sampled_frames_count": self.total_frames,
                "face_detected_frames": self.face_frames,
                "contact_frames": self.contact_frames,
                "duration_seconds": 30.0,
                "sampling_fps": 3.0,
                "eye_contact": {
                    "score": self.eye_contact_score,
                    "contact_percentage": round((self.contact_frames / self.face_frames * 100.0), 1),
                },
                "posture": {
                    "shoulder_tilt_avg_deg": 1.5,
                    "slouch_percentage": 2.0,
                    "posture_status": "Upright & Confident"
                },
                "engagement": {
                    "attentiveness_avg": 85.0,
                    "smile_percentage": 25.0,
                    "expression_summary": "Engaging & Warm"
                },
                "timeline_sample": [
                    {"timestamp_sec": 1.0, "eye_contact": True, "is_slouched": False, "engagement_score": 85.0},
                    {"timestamp_sec": 2.0, "eye_contact": True, "is_slouched": False, "engagement_score": 88.0}
                ]
            }
        }


class BehavioralMetricsUnitTests(APITestCase):
    """
    Unit tests for biometric and algorithmic functions (US-13-T2, US-13-T3, US-13-T4).
    """

    def test_euclidean_distance(self):
        d = euclidean_distance((0.0, 0.0), (3.0, 4.0))
        self.assertAlmostEqual(d, 5.0)

    def test_compute_eye_aspect_ratio(self):
        # Open eye: vertical span is reasonably high compared to width
        top = (0.5, 0.45)
        bottom = (0.5, 0.55)
        inner = (0.35, 0.50)
        outer = (0.65, 0.50)
        ear = compute_eye_aspect_ratio(top, bottom, inner, outer)
        self.assertGreater(ear, 0.25)

        # Closed eye: vertical span near zero
        top_closed = (0.5, 0.50)
        bottom_closed = (0.5, 0.51)
        ear_closed = compute_eye_aspect_ratio(top_closed, bottom_closed, inner, outer)
        self.assertLess(ear_closed, 0.10)

    def test_compute_iris_horizontal_ratio(self):
        # Centered iris
        inner = (0.2, 0.5)
        outer = (0.8, 0.5)
        iris_center = (0.5, 0.5)
        ratio = compute_iris_horizontal_ratio(inner, outer, iris_center)
        self.assertAlmostEqual(ratio, 0.5, places=2)

        # Looking left/right
        iris_left = (0.25, 0.5)
        ratio_left = compute_iris_horizontal_ratio(inner, outer, iris_left)
        self.assertLess(ratio_left, 0.30)

    def test_is_eye_contact_frame(self):
        # Good eye contact: centered gaze, open eyes, forward head pose
        self.assertTrue(
            is_eye_contact_frame(
                left_ratio=0.50,
                right_ratio=0.50,
                left_ear=0.28,
                right_ear=0.28,
                head_yaw_deg=2.0,
                head_pitch_deg=3.0
            )
        )

        # Closed eyes / blinking -> not eye contact
        self.assertFalse(
            is_eye_contact_frame(
                left_ratio=0.50,
                right_ratio=0.50,
                left_ear=0.12,
                right_ear=0.12
            )
        )

        # Looking away to side
        self.assertFalse(
            is_eye_contact_frame(
                left_ratio=0.15,
                right_ratio=0.18,
                left_ear=0.28,
                right_ear=0.28
            )
        )

        # Head turned away
        self.assertFalse(
            is_eye_contact_frame(
                left_ratio=0.50,
                right_ratio=0.50,
                left_ear=0.28,
                right_ear=0.28,
                head_yaw_deg=25.0
            )
        )

    def test_calculate_eye_contact_score(self):
        # 90 out of 100 frames looking at camera with 100% face presence
        score = calculate_eye_contact_score(total_frames=100, face_detected_frames=100, contact_frames=90)
        self.assertEqual(score, 90)

        # Missing face penalty (face present only 50% of the time)
        score_missing_face = calculate_eye_contact_score(total_frames=100, face_detected_frames=50, contact_frames=45)
        self.assertLess(score_missing_face, 90)

        # Edge cases: 0 frames
        self.assertEqual(calculate_eye_contact_score(0, 0, 0), 0)

    def test_calculate_shoulder_tilt_angle(self):
        # Level shoulders
        left = (0.2, 0.7)
        right = (0.8, 0.7)
        self.assertAlmostEqual(calculate_shoulder_tilt_angle(left, right), 0.0, places=1)

        # Uneven shoulders (e.g. sloped)
        right_high = (0.8, 0.6)
        tilt = calculate_shoulder_tilt_angle(left, right_high)
        self.assertGreater(tilt, 8.0)

    def test_check_is_slouched(self):
        # Upright presenter
        nose = (0.5, 0.3)
        left = (0.2, 0.7)
        right = (0.8, 0.7)
        is_slouch, ratio = check_is_slouched(nose, left, right)
        self.assertFalse(is_slouch)
        self.assertGreater(ratio, 0.50)

        # Slouched forward (nose compressed close to shoulder line)
        nose_slouch = (0.5, 0.58)
        is_slouch, ratio = check_is_slouched(nose_slouch, left, right)
        self.assertTrue(is_slouch)
        self.assertLess(ratio, 0.40)

    def test_calculate_posture_score(self):
        # Perfect level posture, no slouch
        tilts = [1.0, 1.2, 0.8, 1.5]
        slouches = [False, False, False, False]
        score, breakdown = calculate_posture_score(tilts, slouches, 4)
        self.assertGreaterEqual(score, 95)
        self.assertEqual(breakdown["posture_status"], "Upright & Confident")

        # Heavy tilt and persistent slouch
        bad_tilts = [15.0, 18.0, 16.0, 14.0]
        bad_slouches = [True, True, True, True]
        bad_score, bad_breakdown = calculate_posture_score(bad_tilts, bad_slouches, 4)
        self.assertLess(bad_score, 65)

    def test_calculate_facial_engagement(self):
        # Alert, pleasant expression
        frame_score, is_smiling = calculate_facial_engagement(
            mouth_left=(0.40, 0.60),
            mouth_right=(0.60, 0.60),
            upper_lip=(0.50, 0.62),
            lower_lip=(0.50, 0.68),
            left_ear=0.28,
            right_ear=0.28
        )
        self.assertGreaterEqual(frame_score, 75.0)

    def test_calculate_engagement_score(self):
        scores = [80.0, 85.0, 82.0, 88.0]
        score, breakdown = calculate_engagement_score(scores, smiling_frame_count=2, total_face_frames=4)
        self.assertGreaterEqual(score, 80)
        self.assertEqual(breakdown["expression_summary"], "Engaging & Warm")


class BehavioralAnalyzerOrchestratorTests(APITestCase):
    """
    Tests for BehavioralAnalyzer service and database model persistence (US-13-T5).
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='test_presenter',
            email='presenter@example.com',
            password='testpassword123'
        )
        self.temp_dir = tempfile.mkdtemp()
        self.dummy_video_path = os.path.join(self.temp_dir, "test_video.mp4")
        with open(self.dummy_video_path, "wb") as f:
            f.write(b"\x00\x00\x00\x20ftypisom" + b"\x00" * 2000)

        self.video = PresentationVideo.objects.create(
            user=self.user,
            file=self.dummy_video_path,
            original_filename="sample_pitch.mp4",
            raw_file_size=2000,
            compressed_file_size=1500,
            file_type="mp4",
            duration_seconds=30,
            is_active=True,
            status="READY_FOR_ANALYSIS"
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_analyzer_persists_behavioral_analysis(self):
        mock_pipeline = MockVisionPipeline(
            eye_contact_score=88,
            posture_score=92,
            engagement_score=85
        )
        analyzer = BehavioralAnalyzer(vision_pipeline=mock_pipeline)

        behavioral_record = analyzer.analyze_presentation_video(self.video)

        self.assertIsNotNone(behavioral_record)
        self.assertEqual(behavioral_record.eye_contact_score, 88)
        self.assertEqual(behavioral_record.posture_score, 92)
        self.assertEqual(behavioral_record.engagement_score, 85)
        self.assertIn("timeline_sample", behavioral_record.frame_metrics)

        # Database verification
        persisted = BehavioralAnalysis.objects.get(video=self.video)
        self.assertEqual(persisted.eye_contact_score, 88)
        self.assertEqual(self.video.status, "READY_FOR_ANALYSIS")

    def test_analyzer_updates_existing_record(self):
        # Create initial record
        BehavioralAnalysis.objects.create(
            video=self.video,
            eye_contact_score=50,
            posture_score=50,
            engagement_score=50
        )

        mock_pipeline = MockVisionPipeline(eye_contact_score=95, posture_score=90, engagement_score=92)
        analyzer = BehavioralAnalyzer(vision_pipeline=mock_pipeline)
        analyzer.analyze_presentation_video(self.video)

        # Verify record updated rather than duplicated
        self.assertEqual(BehavioralAnalysis.objects.filter(video=self.video).count(), 1)
        updated = BehavioralAnalysis.objects.get(video=self.video)
        self.assertEqual(updated.eye_contact_score, 95)


class BehavioralAnalysisAPITests(APITestCase):
    """
    Tests for REST API endpoints:
      - GET /api/presentation/<video_id>/behavioral/
      - POST /api/presentation/<video_id>/behavioral/
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='api_presenter',
            email='presenter_api@example.com',
            password='testpassword123'
        )
        self.other_user = User.objects.create_user(
            username='other_presenter',
            email='other@example.com',
            password='testpassword123'
        )
        self.client.force_authenticate(user=self.user)

        self.temp_dir = tempfile.mkdtemp()
        self.dummy_video_path = os.path.join(self.temp_dir, "test_api_video.mp4")
        with open(self.dummy_video_path, "wb") as f:
            f.write(b"\x00\x00\x00\x20ftypisom" + b"\x00" * 1500)

        self.video = PresentationVideo.objects.create(
            user=self.user,
            file=self.dummy_video_path,
            original_filename="demo.mp4",
            raw_file_size=1500,
            compressed_file_size=1200,
            file_type="mp4",
            duration_seconds=25,
            is_active=True,
            status="READY_FOR_ANALYSIS"
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_get_behavioral_analysis_not_yet_performed(self):
        url = reverse('presentation:behavioral_analysis', kwargs={'video_id': self.video.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("detail", response.data)

    def test_get_behavioral_analysis_success(self):
        BehavioralAnalysis.objects.create(
            video=self.video,
            eye_contact_score=82,
            posture_score=88,
            engagement_score=79,
            frame_metrics={"test_metric": 123}
        )

        url = reverse('presentation:behavioral_analysis', kwargs={'video_id': self.video.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["eye_contact_score"], 82)
        self.assertEqual(response.data["posture_score"], 88)
        self.assertEqual(response.data["engagement_score"], 79)

    @patch('apps.presentation.views.analyze_behavior')
    def test_post_trigger_behavioral_analysis(self, mock_analyze):
        mock_record = BehavioralAnalysis(
            video=self.video,
            eye_contact_score=91,
            posture_score=89,
            engagement_score=86,
            frame_metrics={"sample": "data"}
        )
        mock_analyze.return_value = mock_record

        url = reverse('presentation:behavioral_analysis', kwargs={'video_id': self.video.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["behavioral_analysis"]["eye_contact_score"], 91)
        self.assertEqual(response.data["behavioral_analysis"]["posture_score"], 89)
        self.assertEqual(response.data["behavioral_analysis"]["engagement_score"], 86)

    def test_get_behavioral_analysis_unauthorized_user(self):
        # Create video for other user
        other_video = PresentationVideo.objects.create(
            user=self.other_user,
            file=self.dummy_video_path,
            original_filename="secret.mp4",
            raw_file_size=1000,
            compressed_file_size=800,
            file_type="mp4",
            duration_seconds=10,
            status="READY_FOR_ANALYSIS"
        )
        url = reverse('presentation:behavioral_analysis', kwargs={'video_id': other_video.id})
        response = self.client.get(url)
        # Should return 404 since video does not belong to self.user
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
