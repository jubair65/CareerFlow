import io
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.authentication.models import User
from apps.cv.models import CandidateCV
from apps.core.models import DataAccessLog


class CVUploadTests(APITestCase):
    def setUp(self):
        self.student_user = User.objects.create_user(
            email='student_cv_test@careerflow.demo',
            username='student_cv_test',
            password='Password123!',
            role=User.Role.STUDENT,
            full_name='Test Candidate'
        )
        self.hr_user = User.objects.create_user(
            email='hr_cv_test@careerflow.demo',
            username='hr_cv_test',
            password='Password123!',
            role=User.Role.HR_MANAGER,
            full_name='Test HR'
        )
        self.upload_url = reverse('cv:cv_upload')
        self.current_url = reverse('cv:cv_current')
        self.history_url = reverse('cv:cv_history')

    def create_dummy_file(self, filename='resume.pdf', size=1024, content_type='application/pdf'):
        content = b'%PDF-1.4 dummy pdf content ' + (b'x' * (size - 25 if size > 25 else 0))
        return SimpleUploadedFile(
            filename,
            content,
            content_type=content_type
        )

    def test_valid_pdf_upload_success(self):
        """US-06: Student can upload a valid PDF CV file."""
        self.client.force_authenticate(user=self.student_user)
        pdf_file = self.create_dummy_file('my_resume.pdf', 5000, 'application/pdf')

        response = self.client.post(self.upload_url, {'file': pdf_file}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], 'CV uploaded successfully.')
        cv_data = response.data['cv']
        self.assertEqual(cv_data['original_filename'], 'my_resume.pdf')
        self.assertEqual(cv_data['file_type'], 'pdf')
        self.assertTrue(cv_data['is_active'])

        # Verify database record
        cv = CandidateCV.objects.get(id=cv_data['id'])
        self.assertEqual(cv.user, self.student_user)
        self.assertTrue(cv.is_active)
        self.assertTrue(cv.file.name.startswith(f"students/{self.student_user.id}/cv/"))

    def test_valid_docx_upload_success(self):
        """US-06: Student can upload a valid DOCX CV file."""
        self.client.force_authenticate(user=self.student_user)
        docx_file = SimpleUploadedFile(
            'my_cv.docx',
            b'PK\x03\x04 dummy docx content' + b'y' * 100,
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )

        response = self.client.post(self.upload_url, {'file': docx_file}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['cv']['file_type'], 'docx')
        self.assertTrue(response.data['cv']['is_active'])

    def test_invalid_extension_rejected(self):
        """US-06: Files with unsupported formats (png, txt, exe) are rejected with error."""
        self.client.force_authenticate(user=self.student_user)

        for filename, ctype in [('photo.png', 'image/png'), ('notes.txt', 'text/plain'), ('script.exe', 'application/octet-stream')]:
            dummy = SimpleUploadedFile(filename, b'some file content', content_type=ctype)
            response = self.client.post(self.upload_url, {'file': dummy}, format='multipart')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn('file', response.data)

    def test_file_size_exceeded_rejected(self):
        """US-06: Files exceeding 10 MB limit are rejected."""
        self.client.force_authenticate(user=self.student_user)
        # Create an actual 10.5 MB file buffer
        oversized_content = b'%PDF-1.4 ' + (b'0' * (10 * 1024 * 1024 + 1024))
        oversized_file = SimpleUploadedFile('large_cv.pdf', oversized_content, content_type='application/pdf')

        response = self.client.post(self.upload_url, {'file': oversized_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('file', response.data)
        self.assertTrue(any('exceeds 10 MB' in str(err) for err in response.data['file']))

    def test_reupload_deactivates_previous_cv(self):
        """US-06: Re-uploading marks the newly uploaded CV as active and prior ones as inactive."""
        self.client.force_authenticate(user=self.student_user)

        # Upload first CV
        file1 = self.create_dummy_file('cv_v1.pdf')
        resp1 = self.client.post(self.upload_url, {'file': file1}, format='multipart')
        self.assertEqual(resp1.status_code, status.HTTP_201_CREATED)
        id_1 = resp1.data['cv']['id']

        # Upload second CV
        file2 = self.create_dummy_file('cv_v2.docx', content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        resp2 = self.client.post(self.upload_url, {'file': file2}, format='multipart')
        self.assertEqual(resp2.status_code, status.HTTP_201_CREATED)
        id_2 = resp2.data['cv']['id']

        cv1 = CandidateCV.objects.get(id=id_1)
        cv2 = CandidateCV.objects.get(id=id_2)

        self.assertFalse(cv1.is_active, "Prior CV should be deactivated")
        self.assertTrue(cv2.is_active, "New CV should be active")

    def test_unauthenticated_upload_rejected(self):
        """Unauthenticated requests cannot upload CVs."""
        pdf_file = self.create_dummy_file('resume.pdf')
        response = self.client.post(self.upload_url, {'file': pdf_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_student_upload_rejected(self):
        """Only candidate/student role can upload CVs; HR/Agency are forbidden."""
        self.client.force_authenticate(user=self.hr_user)
        pdf_file = self.create_dummy_file('resume.pdf')
        response = self.client.post(self.upload_url, {'file': pdf_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_current_cv(self):
        """Current CV endpoint returns active CV or null when none uploaded."""
        self.client.force_authenticate(user=self.student_user)

        # Initially no CV
        resp = self.client.get(self.current_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIsNone(resp.data['cv'])

        # Upload a CV
        pdf_file = self.create_dummy_file('active_cv.pdf')
        self.client.post(self.upload_url, {'file': pdf_file}, format='multipart')

        # Current CV should now return the active CV
        resp2 = self.client.get(self.current_url)
        self.assertEqual(resp2.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(resp2.data['cv'])
        self.assertEqual(resp2.data['cv']['original_filename'], 'active_cv.pdf')
        self.assertTrue(resp2.data['cv']['is_active'])

    def test_audit_log_created_on_upload(self):
        """US-36: CV upload records an audit log entry in careerflow_data_access_logs."""
        self.client.force_authenticate(user=self.student_user)
        pdf_file = self.create_dummy_file('audit_cv.pdf')

        initial_count = DataAccessLog.objects.count()
        response = self.client.post(self.upload_url, {'file': pdf_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(DataAccessLog.objects.count(), initial_count + 1)
        latest_log = DataAccessLog.objects.first()
        self.assertEqual(latest_log.user, self.student_user)
        self.assertEqual(latest_log.action, DataAccessLog.Action.UPLOAD)
        self.assertEqual(latest_log.status, DataAccessLog.Status.GRANTED)
