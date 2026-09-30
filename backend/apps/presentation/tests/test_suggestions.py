"""
Unit and Integration Tests for AI Improvement Suggestions (US-15-T7).
Deterministic test suite with mocked Google Gemini API client.
"""

import json
from unittest.mock import MagicMock, patch
from django.core.files.uploadedfile import SimpleUploadedFile
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
)
from apps.presentation.services.llm_coach_service import GeminiPresentationCoachService


class GeminiPresentationCoachServiceUnitTests(APITestCase):
    """
    US-15-T7: Unit tests for GeminiPresentationCoachService with mocked LLM API client.
    Ensures offline determinism and zero API quota consumption.
    """

    @patch('google.genai.Client')
    def test_gemini_coach_service_mocked_success(self, mock_client_class):
        # Arrange mock response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "summary": "Great clarity and steady pacing throughout your response.",
            "strengths": [
                "Controlled speaking pace within optimal bounds",
                "Natural and engaging smile"
            ],
            "critical_improvements": [
                {
                    "category": "Filler Words",
                    "observation": "Used 'like' 7 times across 2 minutes",
                    "actionable_drill": "Practice pausing silently whenever tempted to vocalize 'like'."
                }
            ],
            "practice_script_tip": "Pause... breathe... then deliver your core point."
        })
        mock_client.models.generate_content.return_value = mock_response
        mock_client_class.return_value = mock_client

        # Act
        service = GeminiPresentationCoachService(api_key="test-api-key")
        result = service.generate_feedback({
            "wpm": 140,
            "filler_count": 7,
            "filler_breakdown": "like: 7",
            "eye_contact": 80,
            "posture_score": 85,
            "engagement_score": 80,
            "overall_score": 82
        })

        # Assert
        self.assertIn("summary", result)
        self.assertEqual(len(result["strengths"]), 2)
        self.assertEqual(len(result["critical_improvements"]), 1)
        self.assertEqual(result["critical_improvements"][0]["category"], "Filler Words")
        self.assertEqual(result["practice_script_tip"], "Pause... breathe... then deliver your core point.")

    @patch('google.genai.Client')
    def test_gemini_coach_service_handles_markdown_code_fence(self, mock_client_class):
        """Should strip markdown ```json ... ``` code fence cleanly."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = (
            "```json\n"
            "{\n"
            '  "summary": "Solid posture and direct camera engagement.",\n'
            '  "strengths": ["Clear articulation", "Consistent eye level"],\n'
            '  "critical_improvements": [\n'
            '    {\n'
            '      "category": "Pacing",\n'
            '      "observation": "Spoke at 115 WPM which felt slightly hesitant",\n'
            '      "actionable_drill": "Practice with 140 WPM metronome cadence"\n'
            '    }\n'
            '  ],\n'
            '  "practice_script_tip": "Deliver operative verbs with punch."\n'
            "}\n"
            "```"
        )
        mock_client.models.generate_content.return_value = mock_response
        mock_client_class.return_value = mock_client

        service = GeminiPresentationCoachService(api_key="test-api-key")
        result = service.generate_feedback({
            "wpm": 115,
            "filler_count": 1,
            "filler_breakdown": "um: 1",
            "eye_contact": 88,
            "posture_score": 85,
            "engagement_score": 80,
            "overall_score": 79
        })

        self.assertEqual(result["summary"], "Solid posture and direct camera engagement.")
        self.assertEqual(result["critical_improvements"][0]["category"], "Pacing")

    @patch('google.genai.Client')
    def test_gemini_coach_service_fallback_on_api_exception(self, mock_client_class):
        """Should gracefully fall back to rule-based coaching if Gemini API throws exception."""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = RuntimeError("API quota exceeded or network down")
        mock_client_class.return_value = mock_client

        service = GeminiPresentationCoachService(api_key="test-api-key")
        result = service.generate_feedback({
            "wpm": 175,
            "filler_count": 8,
            "filler_breakdown": "uh: 5, basically: 3",
            "eye_contact": 60,
            "posture_score": 70,
            "engagement_score": 65,
            "overall_score": 68
        })

        self.assertIn("summary", result)
        self.assertTrue(len(result["strengths"]) >= 1)
        self.assertTrue(len(result["critical_improvements"]) >= 1)
        categories = [item["category"] for item in result["critical_improvements"]]
        self.assertIn("Pacing", categories)
        self.assertIn("Filler Words", categories)

    def test_rule_based_fallback_directly(self):
        """Rule engine produces well-formed response conforming strictly to schema."""
        service = GeminiPresentationCoachService(api_key=None)
        result = service.generate_rule_based_fallback({
            "wpm": 145,
            "filler_count": 0,
            "filler_breakdown": "none",
            "eye_contact": 90,
            "posture_score": 88,
            "engagement_score": 85,
            "overall_score": 92
        })

        self.assertIn("summary", result)
        self.assertTrue(len(result["strengths"]) >= 2)
        self.assertIn("practice_script_tip", result)


class PresentationSuggestionsAPITests(APITestCase):
    """
    US-15-T5: Integration tests for PresentationSuggestionsView endpoints.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='bonny_candidate',
            email='bonny@test.com',
            password='TestPassword123!',
            role=User.Role.STUDENT,
            full_name='Farhana Bonny'
        )
        self.client.force_authenticate(user=self.user)

        self.dummy_video = SimpleUploadedFile(
            "bonny_test_take.mp4",
            b"fake mp4 video binary content",
            content_type="video/mp4"
        )
        self.video = PresentationVideo.objects.create(
            user=self.user,
            file=self.dummy_video,
            original_filename="bonny_test_take.mp4",
            raw_file_size=1024 * 1024,
            compressed_file_size=512 * 1024,
            file_type="mp4",
            duration_seconds=90,
            status="COMPLETED"
        )
        self.speech = SpeechAnalysis.objects.create(
            video=self.video,
            transcript="Hello, I am excited to apply for the software engineer role.",
            words_per_minute=142.0,
            filler_word_count=2,
            filler_words_breakdown={"um": 2},
            clarity_score=88,
            duration_seconds=90.0
        )
        self.behavioral = BehavioralAnalysis.objects.create(
            video=self.video,
            eye_contact_score=82,
            posture_score=86,
            engagement_score=80
        )
        self.score = PresentationScore.objects.create(
            video=self.video,
            overall_score=85,
            speech_score=88,
            behavioral_score=82,
            pace_score=95,
            filler_score=90,
            eye_contact_score=82,
            posture_score=86,
            engagement_score=80
        )

    @patch('apps.presentation.services.llm_coach_service.GeminiPresentationCoachService.generate_feedback')
    def test_get_suggestions_generates_and_persists_feedback(self, mock_generate):
        mock_generate.return_value = {
            "summary": "Exceptional executive presence with crisp cadence.",
            "strengths": [
                "Optimal speaking pace at 142 WPM",
                "High camera engagement (82%)"
            ],
            "critical_improvements": [
                {
                    "category": "Filler Words",
                    "observation": "Detected 2 'um' fillers",
                    "actionable_drill": "Practice the Silent Pause Pivot."
                }
            ],
            "practice_script_tip": "Pause... then deliver your core achievement."
        }

        url = reverse('presentation:presentation_suggestions', kwargs={'video_id': self.video.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(data["summary"], "Exceptional executive presence with crisp cadence.")
        self.assertEqual(len(data["strengths"]), 2)
        self.assertEqual(data["improvements"][0]["category"], "Filler Words")

        # Verify persisted in database (US-15-T5)
        feedback_db = PresentationFeedback.objects.filter(video=self.video).first()
        self.assertIsNotNone(feedback_db)
        self.assertEqual(feedback_db.summary, "Exceptional executive presence with crisp cadence.")

    def test_unauthenticated_request_rejected(self):
        self.client.logout()
        url = reverse('presentation:presentation_suggestions', kwargs={'video_id': self.video.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_suggestions_not_found_for_invalid_video(self):
        url = reverse('presentation:presentation_suggestions', kwargs={'video_id': 999999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
