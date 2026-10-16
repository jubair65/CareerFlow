import os
import django
import uuid

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'careerflow.settings')
django.setup()

from unittest.mock import patch
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase
from apps.recruitment.models import RecruitmentRoom, CandidateApplication
from apps.authentication.models import User
from apps.recruitment.tokens import generate_secure_share_token


class US22SubmissionAPITests(APITestCase):
    def setUp(self):
        uid = uuid.uuid4().hex[:8]
        self.hr_user = User.objects.create_user(
            email=f'hr_{uid}@careerflow.demo',
            password='password123',
            role='HR_MANAGER',
            username=f'hr_{uid}'
        )
        self.active_room = RecruitmentRoom.objects.create(
            title='Frontend Developer',
            company_name='Tech Innovators',
            created_by=self.hr_user,
            share_token=generate_secure_share_token(),
            link_is_active=True,
            status='ACTIVE'
        )
        self.test_pdf = SimpleUploadedFile("test_cv.pdf", b"file_content", content_type="application/pdf")
        self.test_video = SimpleUploadedFile("test_video.mp4", b"video_content", content_type="video/mp4")
        self.candidate_email = f'candidate_{uid}@test.com'

    @patch('apps.presentation.services.pipeline_manager.PipelineManager.run_pipeline')
    @patch('apps.cv.services.pipeline.CVExtractionPipeline.process_candidate_cv')
    def test_valid_submission(self, mock_cv_pipeline, mock_vid_pipeline):
        """
        Test positive scenario: valid form data submits successfully
        """
        class MockCVResult:
            success = True
            raw_text = "test text"
            skills = []
            education = []
            experience = []
        
        mock_cv_pipeline.return_value = MockCVResult()

        url = reverse('recruitment:public-apply-submit', kwargs={'token': self.active_room.share_token})
        data = {
            'full_name': 'Test Candidate',
            'email': self.candidate_email,
            'cv_file': self.test_pdf,
            'video_file': self.test_video
        }
        
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("application_id", response.data)

        # Verify models
        candidate = User.objects.get(email=self.candidate_email)
        self.assertEqual(candidate.role, 'STUDENT')
        
        app = CandidateApplication.objects.get(room=self.active_room, candidate=candidate)
        self.assertIsNotNone(app.cv)
        self.assertIsNotNone(app.video)
        self.assertEqual(app.status, 'COMPLETED')
        
        # Verify pipelines were triggered
        mock_cv_pipeline.assert_called_once()
        mock_vid_pipeline.assert_called_once()

    def test_missing_fields(self):
        """
        Test negative scenario: missing file fields
        """
        url = reverse('recruitment:public-apply-submit', kwargs={'token': self.active_room.share_token})
        data = {
            'full_name': 'Test Candidate',
            'email': self.candidate_email,
        }
        
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_inactive_link_submission(self):
        """
        Test negative scenario: submission on inactive link
        """
        self.active_room.link_is_active = False
        self.active_room.save()

        url = reverse('recruitment:public-apply-submit', kwargs={'token': self.active_room.share_token})
        data = {
            'full_name': 'Test Candidate',
            'email': self.candidate_email,
            'cv_file': self.test_pdf,
            'video_file': self.test_video
        }
        
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_410_GONE)

    @patch('apps.presentation.services.pipeline_manager.PipelineManager.run_pipeline')
    @patch('apps.cv.services.pipeline.CVExtractionPipeline.process_candidate_cv')
    def test_duplicate_submission(self, mock_cv, mock_vid):
        """
        Test negative scenario: duplicate application for the same room
        """
        class MockCVResult:
            success = False
            error_message = ""
        mock_cv.return_value = MockCVResult()

        url = reverse('recruitment:public-apply-submit', kwargs={'token': self.active_room.share_token})
        
        # First submit
        data1 = {
            'full_name': 'Test Candidate',
            'email': self.candidate_email,
            'cv_file': SimpleUploadedFile("cv1.pdf", b"file", content_type="application/pdf"),
            'video_file': SimpleUploadedFile("vid1.mp4", b"vid", content_type="video/mp4")
        }
        response1 = self.client.post(url, data1, format='multipart')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        # Second submit (duplicate)
        data2 = {
            'full_name': 'Test Candidate',
            'email': self.candidate_email,
            'cv_file': SimpleUploadedFile("cv2.pdf", b"file2", content_type="application/pdf"),
            'video_file': SimpleUploadedFile("vid2.mp4", b"vid2", content_type="video/mp4")
        }
        response2 = self.client.post(url, data2, format='multipart')
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already submitted", response2.data["error"].lower())
