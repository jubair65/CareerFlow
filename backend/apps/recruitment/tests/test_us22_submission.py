import pytest
from django.urls import reverse
from rest_framework import status
from apps.recruitment.models import RecruitmentRoom, CandidateApplication
from apps.authentication.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
import uuid
from apps.recruitment.tokens import generate_secure_share_token
from unittest.mock import patch

@pytest.fixture
def hr_user(db):
    return User.objects.create_user(email='hr@careerflow.demo', password='password123', role='HR_MANAGER', username='hr')

@pytest.fixture
def active_room(db, hr_user):
    room = RecruitmentRoom.objects.create(
        title='Frontend Developer',
        company_name='Tech Innovators',
        created_by=hr_user,
        share_token=generate_secure_share_token(),
        link_is_active=True,
        status='ACTIVE'
    )
    return room

@pytest.fixture
def test_pdf():
    return SimpleUploadedFile("test_cv.pdf", b"file_content", content_type="application/pdf")

@pytest.fixture
def test_video():
    return SimpleUploadedFile("test_video.mp4", b"video_content", content_type="video/mp4")

@pytest.mark.django_db
@patch('apps.presentation.services.pipeline_manager.PipelineManager.run_pipeline')
@patch('apps.cv.services.pipeline.CVExtractionPipeline.process_candidate_cv')
def test_valid_submission(mock_cv_pipeline, mock_vid_pipeline, active_room, test_pdf, test_video, client):
    """
    Test positive scenario: valid form data submits successfully
    """
    # Mock pipeline success
    class MockCVResult:
        success = True
        raw_text = "test text"
        skills = []
        education = []
        experience = []
    
    mock_cv_pipeline.return_value = MockCVResult()

    url = reverse('recruitment:public-apply-submit', kwargs={'token': active_room.share_token})
    data = {
        'full_name': 'Test Candidate',
        'email': 'candidate@test.com',
        'cv_file': test_pdf,
        'video_file': test_video
    }
    
    response = client.post(url, data, format='multipart')
    assert response.status_code == status.HTTP_201_CREATED
    assert "application_id" in response.data

    # Verify models
    candidate = User.objects.get(email='candidate@test.com')
    assert candidate.role == 'STUDENT'
    
    app = CandidateApplication.objects.get(room=active_room, candidate=candidate)
    assert app.cv is not None
    assert app.video is not None
    assert app.status == 'COMPLETED'
    
    # Verify pipelines were triggered
    mock_cv_pipeline.assert_called_once()
    mock_vid_pipeline.assert_called_once()

@pytest.mark.django_db
def test_missing_fields(active_room, client):
    """
    Test negative scenario: missing file fields
    """
    url = reverse('recruitment:public-apply-submit', kwargs={'token': active_room.share_token})
    data = {
        'full_name': 'Test Candidate',
        'email': 'candidate@test.com',
        # Missing files
    }
    
    response = client.post(url, data, format='multipart')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "error" in response.data

@pytest.mark.django_db
def test_inactive_link_submission(active_room, client, test_pdf, test_video):
    """
    Test negative scenario: submission on inactive link
    """
    active_room.link_is_active = False
    active_room.save()

    url = reverse('recruitment:public-apply-submit', kwargs={'token': active_room.share_token})
    data = {
        'full_name': 'Test Candidate',
        'email': 'candidate@test.com',
        'cv_file': test_pdf,
        'video_file': test_video
    }
    
    response = client.post(url, data, format='multipart')
    assert response.status_code == status.HTTP_410_GONE

@pytest.mark.django_db
@patch('apps.presentation.services.pipeline_manager.PipelineManager.run_pipeline')
@patch('apps.cv.services.pipeline.CVExtractionPipeline.process_candidate_cv')
def test_duplicate_submission(mock_cv, mock_vid, active_room, test_pdf, test_video, client):
    """
    Test negative scenario: duplicate application for the same room
    """
    class MockCVResult:
        success = False
        error_message = ""
    mock_cv.return_value = MockCVResult()

    url = reverse('recruitment:public-apply-submit', kwargs={'token': active_room.share_token})
    
    # First submit
    data1 = {
        'full_name': 'Test Candidate',
        'email': 'candidate@test.com',
        'cv_file': SimpleUploadedFile("cv1.pdf", b"file", content_type="application/pdf"),
        'video_file': SimpleUploadedFile("vid1.mp4", b"vid", content_type="video/mp4")
    }
    response1 = client.post(url, data1, format='multipart')
    assert response1.status_code == status.HTTP_201_CREATED

    # Second submit (duplicate)
    data2 = {
        'full_name': 'Test Candidate',
        'email': 'candidate@test.com',
        'cv_file': SimpleUploadedFile("cv2.pdf", b"file2", content_type="application/pdf"),
        'video_file': SimpleUploadedFile("vid2.mp4", b"vid2", content_type="video/mp4")
    }
    response2 = client.post(url, data2, format='multipart')
    assert response2.status_code == status.HTTP_400_BAD_REQUEST
    assert "already submitted" in response2.data["error"].lower()
