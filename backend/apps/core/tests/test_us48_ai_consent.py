import uuid
from io import BytesIO
from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status
from apps.authentication.models import User
from apps.core.models import AIConsentLog
from apps.core.views import verify_ai_consent
from apps.recruitment.models import RecruitmentRoom


class AIConsentGatekeeperTests(TestCase):
    """
    US-48-T7: Unit tests for AI Biometric & Evaluation Consent Notice Gatekeeper.
    Tests consent recording, audit logging (IP, user agent, token), status endpoint,
    policy endpoint, and gatekeeper blocking on video upload and room application.
    """

    def setUp(self):
        self.client = APIClient()
        self.uid = uuid.uuid4().hex[:6]
        self.student_email = f"student_{self.uid}@careerflow.test"
        self.student = User.objects.create_user(
            username=f"student_{self.uid}",
            email=self.student_email,
            password="ValidPass2026!",
            role=User.Role.STUDENT,
            full_name="Alex Rivera",
        )
        self.hr_user = User.objects.create_user(
            username=f"hr_{self.uid}",
            email=f"hr_{self.uid}@careerflow.test",
            password="ValidPass2026!",
            role=User.Role.HR_MANAGER,
            full_name="HR Director",
        )
        self.room = RecruitmentRoom.objects.create(
            created_by=self.hr_user,
            title="Senior Cloud Architect",
            company_name="Cloud Corp",
            status=RecruitmentRoom.Status.OPEN,
            link_is_active=True,
        )

    def test_record_consent_agreement_authenticated(self):
        """
        AC-1, AC-3, AC-5: Authenticated candidate records agreement to AI Biometric Consent.
        Check AIConsentLog is persisted with user, IP, token, policy version.
        """
        self.client.force_authenticate(user=self.student)
        url = reverse('core:ai_consent_record')
        payload = {
            'agreed': True,
            'policy_version': 'v1.0',
        }
        response = self.client.post(url, payload, format='json', REMOTE_ADDR='192.168.1.42', HTTP_USER_AGENT='Mozilla/5.0')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'recorded')
        self.assertTrue(response.data['agreed'])
        self.assertTrue(response.data['consent_token'])

        log = AIConsentLog.objects.filter(user=self.student).first()
        self.assertIsNotNone(log)
        self.assertTrue(log.agreed)
        self.assertEqual(log.policy_version, 'v1.0')
        self.assertEqual(log.ip_address, '192.168.1.42')
        self.assertEqual(log.user_agent, 'Mozilla/5.0')
        self.assertEqual(str(log.consent_token), str(response.data['consent_token']))

    def test_record_consent_refusal_authenticated(self):
        """
        AC-4: Candidate explicitly refuses AI Biometric Consent.
        Recorded with agreed=False, returns refusal status without error.
        """
        self.client.force_authenticate(user=self.student)
        url = reverse('core:ai_consent_record')
        payload = {
            'agreed': False,
            'policy_version': 'v1.0',
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'refused')
        self.assertFalse(response.data['agreed'])

        log = AIConsentLog.objects.filter(user=self.student).first()
        self.assertIsNotNone(log)
        self.assertFalse(log.agreed)

    def test_record_consent_public_candidate_by_email(self):
        """
        AC-5: Public unauthenticated applicant records consent with candidate email.
        """
        url = reverse('core:ai_consent_record')
        candidate_email = f"public_{self.uid}@careerflow.test"
        payload = {
            'agreed': True,
            'email': candidate_email,
            'policy_version': 'v1.0',
        }
        response = self.client.post(url, payload, format='json', REMOTE_ADDR='10.0.0.99')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'recorded')

        log = AIConsentLog.objects.filter(email=candidate_email).first()
        self.assertIsNotNone(log)
        self.assertIsNone(log.user)
        self.assertEqual(log.ip_address, '10.0.0.99')
        self.assertTrue(log.agreed)

    def test_consent_status_unconsented(self):
        """
        AC-1: GET /api/core/ai-consent/status/ returns has_consented=False when no agreement exists.
        """
        self.client.force_authenticate(user=self.student)
        url = reverse('core:ai_consent_status')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['has_consented'])

    def test_consent_status_consented(self):
        """
        AC-3: GET /api/core/ai-consent/status/ returns has_consented=True when agreement is logged.
        """
        AIConsentLog.objects.create(
            user=self.student,
            email=self.student.email,
            agreed=True,
            policy_version='v1.0',
        )
        self.client.force_authenticate(user=self.student)
        url = reverse('core:ai_consent_status')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['has_consented'])
        self.assertEqual(response.data['policy_version'], 'v1.0')

    def test_consent_policy_endpoint(self):
        """
        AC-2, AC-6: GET /api/core/ai-consent/policy/ returns structured privacy notice.
        Verifies sections cover audio telemetry, facial/posture tracking, retention, and rights.
        """
        url = reverse('core:ai_consent_policy')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(data['version'], 'v1.0')
        self.assertTrue(len(data['sections']) >= 4)
        section_ids = [s['id'] for s in data['sections']]
        self.assertIn('audio_analysis', section_ids)
        self.assertIn('facial_posture_telemetry', section_ids)
        self.assertIn('human_oversight', section_ids)
        self.assertIn('retention_storage', section_ids)

    def test_consent_token_header_verification(self):
        """
        US-48-T5: Verify token in X-AI-Consent-Token header is validated by verify_ai_consent.
        """
        log = AIConsentLog.objects.create(
            email="token_test@careerflow.test",
            agreed=True,
            policy_version='v1.0',
        )
        url = reverse('core:ai_consent_status')
        # With valid token header
        response = self.client.get(url, HTTP_X_AI_CONSENT_TOKEN=log.consent_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['has_consented'])

        # With invalid/random token header
        response_invalid = self.client.get(url, HTTP_X_AI_CONSENT_TOKEN='invalid-token-12345')
        self.assertEqual(response_invalid.status_code, status.HTTP_200_OK)
        self.assertFalse(response_invalid.data['has_consented'])

    def test_video_upload_blocked_without_consent(self):
        """
        US-48-T5: Video upload to /api/presentation/upload/ without prior consent
        must be blocked with HTTP 403 Forbidden and AI_CONSENT_REQUIRED error code.
        """
        self.client.force_authenticate(user=self.student)
        fake_video = SimpleUploadedFile("take1.mp4", b"fake-video-bytes", content_type="video/mp4")
        url = reverse('presentation:video_upload')
        response = self.client.post(url, {'file': fake_video}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data.get('code'), 'AI_CONSENT_REQUIRED')

    def test_video_upload_allowed_with_consent(self):
        """
        US-48-T5: Video upload with valid consent passes the consent gatekeeper.
        """
        AIConsentLog.objects.create(
            user=self.student,
            email=self.student.email,
            agreed=True,
            policy_version='v1.0',
        )
        self.client.force_authenticate(user=self.student)
        fake_video = SimpleUploadedFile("take1.mp4", b"fake-video-bytes", content_type="video/mp4")
        url = reverse('presentation:video_upload')
        response = self.client.post(url, {'file': fake_video}, format='multipart')
        # Even if video validation fails (e.g. invalid format/bytes), it must NOT be 403 AI_CONSENT_REQUIRED
        self.assertNotEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_public_application_blocked_without_consent(self):
        """
        US-48-T5: Candidate application submission with video to /api/recruitment/apply/{token}/submit/
        without consent returns HTTP 403 Forbidden with AI_CONSENT_REQUIRED.
        """
        cv_file = SimpleUploadedFile("resume.pdf", b"%PDF-1.4 mock cv", content_type="application/pdf")
        vid_file = SimpleUploadedFile("intro.mp4", b"mock video content", content_type="video/mp4")
        url = reverse('recruitment:public-apply-submit', kwargs={'token': self.room.share_token})
        payload = {
            'full_name': 'New Candidate',
            'email': f'unconsented_{self.uid}@careerflow.test',
            'cv_file': cv_file,
            'video_file': vid_file,
            'consent_token': '',
        }
        response = self.client.post(url, payload, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data.get('code'), 'AI_CONSENT_REQUIRED')

    def test_public_application_allowed_with_consent(self):
        """
        US-48-T5: Candidate application with video and valid consent passes the consent gatekeeper.
        """
        cand_email = f'consented_{self.uid}@careerflow.test'
        consent_log = AIConsentLog.objects.create(
            email=cand_email,
            agreed=True,
            policy_version='v1.0',
        )
        cv_file = SimpleUploadedFile("resume.pdf", b"%PDF-1.4 mock cv", content_type="application/pdf")
        vid_file = SimpleUploadedFile("intro.mp4", b"mock video content", content_type="video/mp4")
        url = reverse('recruitment:public-apply-submit', kwargs={'token': self.room.share_token})
        payload = {
            'full_name': 'New Candidate',
            'email': cand_email,
            'cv_file': cv_file,
            'video_file': vid_file,
            'consent_token': consent_log.consent_token,
        }
        response = self.client.post(url, payload, format='multipart')
        # Does not fail with 403 AI_CONSENT_REQUIRED
        self.assertNotEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_consent_requires_agreed_boolean(self):
        """
        AC-3: Submitting consent without required 'agreed' field returns HTTP 400 Bad Request.
        """
        url = reverse('core:ai_consent_record')
        response = self.client.post(url, {'policy_version': 'v1.0'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('agreed', response.data)
