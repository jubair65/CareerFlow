import os
import shutil
import tempfile
from unittest.mock import patch, MagicMock
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.authentication.models import User
from apps.presentation.models import PresentationVideo, SpeechAnalysis
from apps.presentation.services.audio_extractor import extract_audio, cleanup_audio_file
from apps.presentation.services.transcription_service import (
    BaseTranscriptionService,
    FasterWhisperTranscriptionService
)
from apps.presentation.services.speech_metrics import (
    calculate_wpm,
    detect_filler_words,
    calculate_clarity_score,
    count_words
)
from apps.presentation.services.speech_analyzer import SpeechAnalyzer


class MockTranscriptionService(BaseTranscriptionService):
    """
    Mock transcription service for deterministic, fast unit tests without loading neural models.
    """
    def __init__(self, sample_text="Um hello everyone, I like wanted to talk about my project, basically.", duration=30.0):
        self.sample_text = sample_text
        self.duration = duration

    def transcribe(self, audio_path: str) -> dict:
        return {
            "text": self.sample_text,
            "language": "en",
            "duration": self.duration,
            "segments": [
                {"id": 1, "start": 0.0, "end": 15.0, "text": "Um hello everyone, I like"},
                {"id": 2, "start": 15.0, "end": 30.0, "text": "wanted to talk about my project, basically."}
            ]
        }


class SpeechMetricsUnitTests(APITestCase):
    """
    Unit tests for WPM calculation, filler word taxonomy detection, and clarity score (US-12-T4, US-12-T5).
    """

    def test_count_words(self):
        self.assertEqual(count_words(""), 0)
        self.assertEqual(count_words("   "), 0)
        self.assertEqual(count_words("Hello world"), 2)
        self.assertEqual(count_words("  One   two   three  four  "), 4)

    def test_calculate_wpm_optimal(self):
        # 150 words in 60 seconds = 150.0 WPM
        wpm = calculate_wpm(total_words=150, duration_seconds=60.0)
        self.assertEqual(wpm, 150.0)

    def test_calculate_wpm_fractional_duration(self):
        # 75 words in 30 seconds = 150.0 WPM
        wpm = calculate_wpm(total_words=75, duration_seconds=30.0)
        self.assertEqual(wpm, 150.0)

    def test_calculate_wpm_edge_cases(self):
        self.assertEqual(calculate_wpm(0, 60.0), 0.0)
        self.assertEqual(calculate_wpm(100, 0.0), 0.0)
        self.assertEqual(calculate_wpm(100, -5.0), 0.0)
        self.assertEqual(calculate_wpm(-10, 60.0), 0.0)

    def test_detect_filler_words_clean_speech(self):
        text = "Good morning everyone. Today I will present our architectural blueprint."
        result = detect_filler_words(text)
        self.assertEqual(result["filler_word_count"], 0)
        self.assertEqual(result["filler_words_breakdown"], {})

    def test_detect_filler_words_multiple_and_casing(self):
        text = "Um, hello. I uh think, you know, this is like basically the right way, actually."
        result = detect_filler_words(text)
        self.assertGreater(result["filler_word_count"], 0)
        breakdown = result["filler_words_breakdown"]
        self.assertEqual(breakdown.get("um"), 1)
        self.assertEqual(breakdown.get("uh"), 1)
        self.assertEqual(breakdown.get("you know"), 1)
        self.assertEqual(breakdown.get("like"), 1)
        self.assertEqual(breakdown.get("basically"), 1)
        self.assertEqual(breakdown.get("actually"), 1)
        self.assertEqual(result["filler_word_count"], 6)

    def test_detect_filler_words_word_boundaries(self):
        # Ensure 'alike' does not match 'like', and 'summary' does not match 'um'
        text = "The summary looks alike to the previous outcome."
        result = detect_filler_words(text)
        self.assertEqual(result["filler_word_count"], 0)
        self.assertEqual(result["filler_words_breakdown"], {})

    def test_calculate_clarity_score_optimal_speech(self):
        score = calculate_clarity_score(
            wpm=145.0,
            filler_count=0,
            total_words=145,
            duration_seconds=60.0
        )
        self.assertEqual(score, 100)

    def test_calculate_clarity_score_penalized_for_deviations(self):
        # Very fast speech (200 WPM) + high filler count
        score = calculate_clarity_score(
            wpm=200.0,
            filler_count=15,
            total_words=200,
            duration_seconds=60.0
        )
        self.assertLess(score, 80)
        self.assertGreaterEqual(score, 0)

    def test_calculate_clarity_score_zero_words(self):
        score = calculate_clarity_score(
            wpm=0.0,
            filler_count=0,
            total_words=0,
            duration_seconds=30.0
        )
        self.assertEqual(score, 0)


class AudioExtractorUnitTests(APITestCase):
    """
    Unit tests for audio extraction service (US-12-T2).
    """

    def test_extract_audio_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            extract_audio("/non/existent/path/video.mp4")

    @patch('apps.presentation.services.audio_extractor.subprocess.run')
    @patch('apps.presentation.services.audio_extractor.get_ffmpeg_binary')
    def test_extract_audio_invokes_ffmpeg(self, mock_get_bin, mock_subproc):
        mock_get_bin.return_value = 'ffmpeg'
        mock_subproc.return_value = MagicMock(returncode=0)

        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_video:
            temp_video.write(b'fake video content')
            temp_video_path = temp_video.name

        target_wav = temp_video_path.replace('.mp4', '.wav')
        try:
            output_path = extract_audio(temp_video_path, target_wav)
            self.assertEqual(output_path, target_wav)
            self.assertTrue(mock_subproc.called)
            cmd_args = mock_subproc.call_args[0][0]
            self.assertIn("-ar", cmd_args)
            self.assertIn("16000", cmd_args)
            self.assertIn("-ac", cmd_args)
            self.assertIn("1", cmd_args)
        finally:
            if os.path.exists(temp_video_path):
                os.remove(temp_video_path)

    def test_cleanup_audio_file_removes_file(self):
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
            temp_wav.write(b'wav content')
            wav_path = temp_wav.name

        self.assertTrue(os.path.exists(wav_path))
        cleanup_audio_file(wav_path)
        self.assertFalse(os.path.exists(wav_path))


class SpeechAnalysisIntegrationTests(APITestCase):
    """
    Integration tests for SpeechAnalyzer orchestration, DB persistence, and REST endpoints (US-12-T6, US-12-T7).
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email='hasanul_mobin_test@careerflow.demo',
            username='mobin_candidate',
            password='Password123!',
            role=User.Role.STUDENT,
            full_name='Hasanul Mobin'
        )
        self.other_user = User.objects.create_user(
            email='other_student_test@careerflow.demo',
            username='other_student',
            password='Password123!',
            role=User.Role.STUDENT,
            full_name='Other Candidate'
        )
        self.client.force_authenticate(user=self.user)

        # Create dummy physical video file for testing inside media
        from django.conf import settings
        test_video_dir = os.path.join(settings.MEDIA_ROOT, f"students/{self.user.id}/videos")
        os.makedirs(test_video_dir, exist_ok=True)
        self.video_rel_path = f"students/{self.user.id}/videos/test_pres.mp4"
        self.video_abs_path = os.path.join(settings.MEDIA_ROOT, self.video_rel_path)
        with open(self.video_abs_path, 'wb') as f:
            f.write(b'\x00\x00\x00\x20ftypisom' + (b'\x00' * 1024))

        self.video = PresentationVideo.objects.create(
            user=self.user,
            file=self.video_rel_path,
            original_filename='presentation_speech_test.mp4',
            raw_file_size=1024,
            compressed_file_size=512,
            file_type='mp4',
            duration_seconds=30,
            status='READY_FOR_ANALYSIS',
            is_active=True
        )

    def tearDown(self):
        if hasattr(self, 'video_abs_path') and os.path.exists(self.video_abs_path):
            try:
                os.remove(self.video_abs_path)
            except OSError:
                pass

    @patch('apps.presentation.services.speech_analyzer.extract_audio')
    def test_speech_analyzer_orchestration(self, mock_extract_audio):
        fake_wav = self.video_abs_path.replace('.mp4', '.wav')
        mock_extract_audio.return_value = fake_wav

        mock_transcription = MockTranscriptionService(
            sample_text="Hello world, I like think this basically works, um yeah.",
            duration=30.0
        )
        analyzer = SpeechAnalyzer(transcription_service=mock_transcription)
        speech_record = analyzer.analyze_presentation_video(self.video)

        self.assertIsNotNone(speech_record)
        self.assertEqual(speech_record.video, self.video)
        self.assertIn("Hello world", speech_record.transcript)
        self.assertGreater(speech_record.words_per_minute, 0)
        self.assertGreaterEqual(speech_record.filler_word_count, 2)
        self.assertIn("like", speech_record.filler_words_breakdown)
        self.assertEqual(speech_record.duration_seconds, 30.0)

        # Check DB persistence
        db_record = SpeechAnalysis.objects.get(video=self.video)
        self.assertEqual(db_record.transcript, speech_record.transcript)

    def test_get_speech_analysis_endpoint_not_found_initially(self):
        url = reverse('presentation:speech_analysis', kwargs={'video_id': self.video.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('Speech analysis has not been performed', response.data.get('detail', ''))

    @patch('apps.presentation.services.speech_analyzer.extract_audio')
    @patch('apps.presentation.services.speech_analyzer.FasterWhisperTranscriptionService')
    def test_post_trigger_and_get_speech_analysis_endpoint(self, mock_whisper_cls, mock_extract_audio):
        fake_wav = self.video_abs_path.replace('.mp4', '.wav')
        mock_extract_audio.return_value = fake_wav

        mock_instance = MagicMock()
        mock_instance.transcribe.return_value = {
            "text": "Good afternoon, I am presenting my technical project today. Thank you.",
            "language": "en",
            "duration": 20.0,
            "segments": []
        }
        mock_whisper_cls.return_value = mock_instance

        url = reverse('presentation:speech_analysis', kwargs={'video_id': self.video.id})
        # Trigger via POST
        post_response = self.client.post(url)
        self.assertEqual(post_response.status_code, status.HTTP_200_OK)
        self.assertIn('speech_analysis', post_response.data)
        self.assertIn('Good afternoon', post_response.data['speech_analysis']['transcript'])

        # Now GET should return 200 OK
        get_response = self.client.get(url)
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            get_response.data['transcript'],
            post_response.data['speech_analysis']['transcript']
        )

    def test_speech_analysis_endpoint_unauthorized(self):
        self.client.force_authenticate(user=None)
        url = reverse('presentation:speech_analysis', kwargs={'video_id': self.video.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_speech_analysis_endpoint_forbidden_other_user(self):
        self.client.force_authenticate(user=self.other_user)
        url = reverse('presentation:speech_analysis', kwargs={'video_id': self.video.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
