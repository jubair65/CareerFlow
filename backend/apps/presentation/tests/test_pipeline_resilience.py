import json
from unittest.mock import MagicMock, patch
from django.urls import reverse
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
from apps.presentation.services.pipeline_manager import (
    PipelineManager,
    retry_with_backoff,
)


class PipelineResilienceUnitTests(APITestCase):
    """
    US-40: Comprehensive Unit Test Suite for AI Pipeline Resilience,
    Retry Supervision, and Graceful Degradation.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='maria_candidate',
            email='maria_architect@careerflow.test',
            password='ArchitectPass2026!',
            role=User.Role.STUDENT,
            full_name='Nafisa Maria'
        )
        self.client.force_authenticate(user=self.user)

        self.video = PresentationVideo.objects.create(
            user=self.user,
            file='students/test_maria.mp4',
            original_filename='maria_presentation.mp4',
            raw_file_size=1024 * 1024 * 15,
            compressed_file_size=1024 * 1024 * 4,
            file_type='mp4',
            duration_seconds=75,
            status='READY_FOR_ANALYSIS',
            is_active=True
        )

    def test_retry_with_backoff_transient_recovery(self):
        """TC-US40-01: Verifies transient failures retry with backoff and succeed."""
        attempts = 0

        @retry_with_backoff(
            stage=PipelineExecutionLog.Stage.SPEECH_ANALYSIS,
            max_attempts=3,
            base_delay=0.01,
            max_delay=0.05,
            jitter=False
        )
        def transient_work(video):
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise ConnectionResetError("Transient network jitter")
            return "SUCCESS_RESULT"

        result = transient_work(self.video)
        self.assertEqual(result, "SUCCESS_RESULT")
        self.assertEqual(attempts, 3)

        logs = PipelineExecutionLog.objects.filter(video=self.video, stage=PipelineExecutionLog.Stage.SPEECH_ANALYSIS)
        self.assertEqual(logs.count(), 3)
        self.assertEqual(logs.filter(status=PipelineExecutionLog.Status.RETRY).count(), 2)
        self.assertEqual(logs.filter(status=PipelineExecutionLog.Status.SUCCESS).count(), 1)

    def test_retry_with_backoff_fatal_exception_fails_fast(self):
        """TC-US40-02: Fatal exceptions fail on first attempt without wasteful retries."""
        attempts = 0

        @retry_with_backoff(
            stage=PipelineExecutionLog.Stage.AUDIO_EXTRACTION,
            max_attempts=3,
            base_delay=0.01,
            jitter=False
        )
        def fatal_work(video):
            nonlocal attempts
            attempts += 1
            raise FileNotFoundError("Audio file not found on disk")

        with self.assertRaises(FileNotFoundError):
            fatal_work(self.video)

        # Should only execute once
        self.assertEqual(attempts, 1)
        logs = PipelineExecutionLog.objects.filter(video=self.video, stage=PipelineExecutionLog.Stage.AUDIO_EXTRACTION)
        self.assertEqual(logs.count(), 1)
        self.assertEqual(logs.first().status, PipelineExecutionLog.Status.FAILED)
        self.assertTrue(logs.first().details.get('fatal'))

    @patch('apps.presentation.services.pipeline_manager.analyze_speech')
    def test_pipeline_manager_speech_fatal_failure_marks_video_failed(self, mock_speech):
        """TC-US40-03: Fatal speech analysis failure sets video status to FAILED."""
        mock_speech.side_effect = RuntimeError("Whisper CTranslate2 memory fault")

        results = PipelineManager.run_pipeline(self.video, force_refresh=True)

        self.assertFalse(results['success'])
        self.assertEqual(results['status'], 'FAILED')

        self.video.refresh_from_db()
        self.assertEqual(self.video.status, 'FAILED')

        pipeline_log = PipelineExecutionLog.objects.filter(
            video=self.video,
            stage=PipelineExecutionLog.Stage.PIPELINE,
            status=PipelineExecutionLog.Status.FAILED
        ).first()
        self.assertIsNotNone(pipeline_log)

    @patch('apps.presentation.services.pipeline_manager.GeminiPresentationCoachService')
    @patch('apps.presentation.services.pipeline_manager.analyze_behavior')
    @patch('apps.presentation.services.pipeline_manager.analyze_speech')
    def test_pipeline_manager_vision_failure_triggers_graceful_degradation(
        self, mock_speech, mock_behavior, mock_gemini_cls
    ):
        """TC-US40-04: Vision failure gracefully degrades to 100% speech scoring."""
        # 1. Speech succeeds with 140 WPM, 0 fillers -> Speech Score: 100
        speech_record = SpeechAnalysis.objects.create(
            video=self.video,
            transcript="I am presenting our architecture design.",
            words_per_minute=140.0,
            filler_word_count=0,
            filler_words_breakdown={},
            clarity_score=95,
            duration_seconds=75.0
        )
        mock_speech.return_value = speech_record

        # 2. Vision analysis fails (low lighting / no face detected)
        mock_behavior.side_effect = ValueError("MediaPipe: No facial landmarks detected in sampled video frames")

        # 3. Gemini suggestions mock
        mock_coach = MagicMock()
        mock_coach.generate_feedback.return_value = {
            'summary': 'Clear vocal pitch.',
            'strengths': ['Steady pace'],
            'critical_improvements': [{'category': 'Camera Setup', 'observation': 'Dark lighting', 'actionable_drill': 'Adjust desk lamp'}],
            'practice_script_tip': 'Deliver with confidence.'
        }
        mock_gemini_cls.return_value = mock_coach

        # Run pipeline
        results = PipelineManager.run_pipeline(self.video, force_refresh=True)

        self.assertTrue(results['success'])
        self.assertTrue(results['degraded'])
        self.assertEqual(results['status'], 'PARTIALLY_COMPLETED')

        self.video.refresh_from_db()
        self.assertEqual(self.video.status, 'PARTIALLY_COMPLETED')

        score = self.video.presentation_score
        self.assertIsNotNone(score)
        self.assertFalse(score.has_behavioral_data)
        # Score evaluated 100% on speech score (100)
        self.assertEqual(score.overall_score, score.speech_score)
        self.assertIn("insufficient", score.notes.lower())

        degraded_log = PipelineExecutionLog.objects.filter(
            video=self.video,
            stage=PipelineExecutionLog.Stage.VISION_ANALYSIS,
            status=PipelineExecutionLog.Status.DEGRADED
        ).first()
        self.assertIsNotNone(degraded_log)

    @patch('apps.presentation.services.pipeline_manager.PipelineManager.run_pipeline')
    def test_pipeline_retry_endpoint(self, mock_run):
        """TC-US40-05: Manual retry API endpoint triggers supervised pipeline re-run."""
        mock_run.return_value = {'success': True, 'status': 'COMPLETED'}
        self.video.status = 'FAILED'
        self.video.save()

        url = reverse('presentation:pipeline_retry', kwargs={'video_id': self.video.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['result']['success'])

        retry_log = PipelineExecutionLog.objects.filter(
            video=self.video,
            status=PipelineExecutionLog.Status.RETRY
        ).first()
        self.assertIsNotNone(retry_log)

    def test_pipeline_status_and_logs_endpoints(self):
        """TC-US40-06: Status and logs endpoints provide diagnostic observability."""
        PipelineExecutionLog.objects.create(
            video=self.video,
            stage=PipelineExecutionLog.Stage.SPEECH_ANALYSIS,
            status=PipelineExecutionLog.Status.SUCCESS,
            attempt=1,
            execution_time_ms=120
        )

        status_url = reverse('presentation:pipeline_status', kwargs={'video_id': self.video.id})
        status_res = self.client.get(status_url)
        self.assertEqual(status_res.status_code, status.HTTP_200_OK)
        self.assertEqual(status_res.data['video_id'], self.video.id)
        self.assertIn('logs', status_res.data)
        self.assertIn('is_degraded', status_res.data)

        logs_url = reverse('presentation:pipeline_logs', kwargs={'video_id': self.video.id})
        logs_res = self.client.get(logs_url)
        self.assertEqual(logs_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(logs_res.data), 1)
        self.assertEqual(logs_res.data[0]['stage'], PipelineExecutionLog.Stage.SPEECH_ANALYSIS)
