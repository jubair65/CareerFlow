import os
import shutil
from unittest.mock import patch, MagicMock
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.conf import settings
from rest_framework import status
from rest_framework.test import APITestCase

from apps.authentication.models import User
from apps.presentation.models import PresentationVideo
from apps.presentation.validators import (
    validate_video_file,
    MAX_UPLOAD_SIZE,
    MAX_DURATION_SECONDS
)
from apps.presentation.services.video_compressor import compress_video, cleanup_staging_file
from apps.core.models import DataAccessLog


class PresentationVideoUploadTests(APITestCase):
    def setUp(self):
        self.student_user = User.objects.create_user(
            email='student_pres_test@careerflow.demo',
            username='student_pres_test',
            password='Password123!',
            role=User.Role.STUDENT,
            full_name='Presentation Candidate'
        )
        self.other_user = User.objects.create_user(
            email='other_candidate@careerflow.demo',
            username='other_candidate',
            password='Password123!',
            role=User.Role.STUDENT,
            full_name='Other Candidate'
        )
        self.upload_url = reverse('presentation:video_upload')
        self.active_url = reverse('presentation:video_active')
        self.history_url = reverse('presentation:video_history')

    def tearDown(self):
        # Clean up any created test media
        test_student_dir = os.path.join(settings.MEDIA_ROOT, f"students/{self.student_user.id}/videos")
        if os.path.exists(test_student_dir):
            try:
                shutil.rmtree(test_student_dir)
            except OSError:
                pass
        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_uploads')
        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except OSError:
                pass

    def create_dummy_video(self, filename='pitch.mp4', size=1024 * 50, content_type='video/mp4'):
        # Small binary payload simulating video container bytes
        content = b'\x00\x00\x00\x20ftypisom' + (b'\x00' * (size - 12 if size > 12 else 0))
        return SimpleUploadedFile(
            filename,
            content,
            content_type=content_type
        )

    def test_unauthenticated_upload_rejected(self):
        """Unauthenticated requests must be rejected with 401 Unauthorized."""
        video = self.create_dummy_video('pitch.mp4')
        response = self.client.post(self.upload_url, {'file': video}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch('apps.presentation.views.probe_video_duration', return_value=65)
    def test_valid_mp4_upload_success(self, mock_probe):
        """US-11: Candidate can upload a valid MP4 presentation video."""
        self.client.force_authenticate(user=self.student_user)
        video_file = self.create_dummy_video('pitch.mp4', size=1024 * 500)

        response = self.client.post(self.upload_url, {'file': video_file}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('video', response.data)
        video_data = response.data['video']
        self.assertEqual(video_data['original_filename'], 'pitch.mp4')
        self.assertEqual(video_data['file_type'], 'mp4')
        self.assertEqual(video_data['duration_seconds'], 65)
        self.assertTrue(video_data['is_active'])
        self.assertEqual(video_data['status'], 'READY_FOR_ANALYSIS')

        # Database record check
        record = PresentationVideo.objects.get(id=video_data['id'])
        self.assertEqual(record.user, self.student_user)
        self.assertTrue(record.is_active)
        self.assertEqual(record.duration_seconds, 65)
        self.assertTrue(record.file.name.startswith(f"students/{self.student_user.id}/videos/"))

    @patch('apps.presentation.views.probe_video_duration', return_value=45)
    def test_valid_webm_upload_success(self, mock_probe):
        """US-11: Candidate can upload/record a WebM video stream."""
        self.client.force_authenticate(user=self.student_user)
        video_file = self.create_dummy_video('webcam_recording.webm', size=1024 * 300, content_type='video/webm')

        response = self.client.post(self.upload_url, {'file': video_file}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['video']['original_filename'], 'webcam_recording.webm')
        self.assertTrue(response.data['video']['is_active'])

    @patch('apps.presentation.views.probe_video_duration', return_value=50)
    def test_valid_mov_upload_success(self, mock_probe):
        """US-11: Candidate can upload a .mov format video."""
        self.client.force_authenticate(user=self.student_user)
        video_file = self.create_dummy_video('iphone_clip.mov', size=1024 * 400, content_type='video/quicktime')

        response = self.client.post(self.upload_url, {'file': video_file}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['video']['original_filename'], 'iphone_clip.mov')

    def test_file_size_exceeding_250mb_rejected(self):
        """US-11: Video larger than 250MB is rejected with 400 Bad Request."""
        self.client.force_authenticate(user=self.student_user)

        # 1. Direct validator test with mock oversized file object
        mock_oversized = MagicMock()
        mock_oversized.size = MAX_UPLOAD_SIZE + 1024
        mock_oversized.name = "huge_presentation.mp4"
        with self.assertRaises(Exception) as ctx:
            validate_video_file(mock_oversized)
        self.assertIn("exceeds maximum allowed limit of 250MB", str(ctx.exception))

        # 2. Endpoint rejection test simulating validator rejection
        with patch('apps.presentation.views.validate_video_file') as mock_val:
            from django.core.exceptions import ValidationError
            mock_val.side_effect = ValidationError("File size exceeds maximum allowed limit of 250MB. Uploaded video is 260.0MB.")
            dummy = self.create_dummy_video('oversized.mp4')
            response = self.client.post(self.upload_url, {'file': dummy}, format='multipart')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn('exceeds maximum allowed limit of 250MB', response.data['error'])

    def test_unsupported_file_format_rejected(self):
        """US-11: Unsupported extensions (e.g. .pdf, .exe, .zip) are rejected."""
        self.client.force_authenticate(user=self.student_user)
        bad_file = SimpleUploadedFile('malicious.exe', b'MZ\x90\x00', content_type='application/x-msdownload')

        response = self.client.post(self.upload_url, {'file': bad_file}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Unsupported video format', response.data['error'])

    @patch('apps.presentation.views.probe_video_duration', return_value=195)
    def test_duration_exceeding_180s_rejected(self, mock_probe):
        """US-11: Video longer than 180s (3 minutes) is rejected."""
        self.client.force_authenticate(user=self.student_user)
        video_file = self.create_dummy_video('long_video.mp4', size=1024 * 100)

        response = self.client.post(self.upload_url, {'file': video_file}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('exceeds the maximum allowed length of 180s', response.data['error'])
        # Verify no video record is created
        self.assertEqual(PresentationVideo.objects.filter(user=self.student_user).count(), 0)

    @patch('apps.presentation.views.probe_video_duration', return_value=60)
    def test_video_replacement_deactivates_prior_active_video(self, mock_probe):
        """US-11: Uploading a new presentation deactivates previous active video."""
        self.client.force_authenticate(user=self.student_user)

        # Upload first video
        v1 = self.create_dummy_video('take_1.mp4', size=1024 * 50)
        res1 = self.client.post(self.upload_url, {'file': v1}, format='multipart')
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)
        video1_id = res1.data['video']['id']

        # Upload second video
        v2 = self.create_dummy_video('take_2.mp4', size=1024 * 50)
        res2 = self.client.post(self.upload_url, {'file': v2}, format='multipart')
        self.assertEqual(res2.status_code, status.HTTP_201_CREATED)
        video2_id = res2.data['video']['id']

        # Check DB statuses
        video1 = PresentationVideo.objects.get(id=video1_id)
        video2 = PresentationVideo.objects.get(id=video2_id)

        self.assertFalse(video1.is_active)
        self.assertTrue(video2.is_active)

    @patch('apps.presentation.views.probe_video_duration', return_value=70)
    def test_get_active_video_endpoint(self, mock_probe):
        """US-11: GET /api/presentation/active/ returns current active video."""
        self.client.force_authenticate(user=self.student_user)

        # Initially no video
        res_empty = self.client.get(self.active_url)
        self.assertEqual(res_empty.status_code, status.HTTP_404_NOT_FOUND)

        # Upload video
        v = self.create_dummy_video('current_speech.mp4', size=1024 * 60)
        self.client.post(self.upload_url, {'file': v}, format='multipart')

        # Now active video is returned
        res_active = self.client.get(self.active_url)
        self.assertEqual(res_active.status_code, status.HTTP_200_OK)
        self.assertEqual(res_active.data['original_filename'], 'current_speech.mp4')
        self.assertTrue(res_active.data['is_active'])

    @patch('apps.presentation.views.probe_video_duration', return_value=70)
    def test_video_history_and_isolation(self, mock_probe):
        """US-11: GET /api/presentation/history/ only returns videos for requesting user."""
        self.client.force_authenticate(user=self.student_user)
        v = self.create_dummy_video('student1_clip.mp4')
        self.client.post(self.upload_url, {'file': v}, format='multipart')

        # Other candidate uploads a video
        self.client.force_authenticate(user=self.other_user)
        v_other = self.create_dummy_video('other_clip.mp4')
        self.client.post(self.upload_url, {'file': v_other}, format='multipart')

        # History for other user should only have 1 video
        res_other = self.client.get(self.history_url)
        self.assertEqual(res_other.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_other.data), 1)
        self.assertEqual(res_other.data[0]['original_filename'], 'other_clip.mp4')


class CompressionServiceTests(APITestCase):
    def test_staging_cleanup_helper(self):
        """Test staging file removal."""
        temp_file = os.path.join(settings.MEDIA_ROOT, 'temp_test_staging.tmp')
        with open(temp_file, 'w') as f:
            f.write("temporary data")
        self.assertTrue(os.path.exists(temp_file))

        cleanup_staging_file(temp_file)
        self.assertFalse(os.path.exists(temp_file))

    @patch('shutil.which', return_value=None)
    def test_compress_video_fallback_without_ffmpeg(self, mock_which):
        """If FFmpeg is not installed, service gracefully copies file with fallback."""
        src = os.path.join(settings.MEDIA_ROOT, 'test_src.mp4')
        dst = os.path.join(settings.MEDIA_ROOT, 'test_dst.mp4')

        try:
            with open(src, 'wb') as f:
                f.write(b'\x00' * 512)

            result = compress_video(src, dst)
            self.assertTrue(result['success'])
            self.assertFalse(result['ffmpeg_used'])
            self.assertTrue(os.path.exists(dst))
        finally:
            if os.path.exists(src):
                os.remove(src)
            if os.path.exists(dst):
                os.remove(dst)
