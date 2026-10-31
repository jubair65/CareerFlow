import os
import django
import uuid
from datetime import timedelta
from unittest.mock import patch

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'careerflow.settings')
django.setup()

from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase

from apps.authentication.models import User
from apps.recruitment.models import RecruitmentRoom, CandidateApplication
from apps.recruitment.tokens import generate_secure_share_token


class US45RoomLifecycleUnitTests(APITestCase):
    """
    US-45-T7: Unit tests for Recruitment Room Lifecycle & Expiration Management.
    Covers:
      - AC-1: HR Manager can set and update an application deadline date and time for a Room.
      - AC-2: Room supports four lifecycle states: Draft, Open, Paused, and Closed.
      - AC-3: Submissions through the application link are blocked when room is Paused or Closed.
      - AC-4: Room automatically transitions to Closed or rejects applications past deadline.
      - AC-5: HR Manager can manually reopen a closed or paused room.
      - AC-6: HR dashboard clearly filters and organizes rooms by lifecycle state.
    """

    def setUp(self):
        uid = uuid.uuid4().hex[:8]
        self.hr_user = User.objects.create_user(
            email=f'hr_{uid}@careerflow.com',
            password='Password123!',
            role='HR_MANAGER',
            username=f'hr_{uid}',
            full_name='HR Maria'
        )
        self.other_hr = User.objects.create_user(
            email=f'other_hr_{uid}@careerflow.com',
            password='Password123!',
            role='HR_MANAGER',
            username=f'other_hr_{uid}',
            full_name='Other Recruiter'
        )

        self.room = RecruitmentRoom.objects.create(
            title='Senior Backend Engineer',
            company_name='Apex Corp',
            department='Platform Engineering',
            created_by=self.hr_user,
            status=RecruitmentRoom.Status.OPEN,
            share_token=generate_secure_share_token(),
            link_is_active=True,
            application_deadline=timezone.now() + timedelta(days=7)
        )

        self.client.force_authenticate(user=self.hr_user)

        self.mock_cv = SimpleUploadedFile("cv.pdf", b"pdf_data", content_type="application/pdf")
        self.mock_video = SimpleUploadedFile("pres.mp4", b"video_data", content_type="video/mp4")

    # =========================================================================
    # 1. Room Status State Machine & Reopening (AC-2 & AC-5)
    # =========================================================================

    def test_get_room_status(self):
        """Verify GET /api/recruitment/rooms/<id>/status/ returns status and display."""
        url = reverse('recruitment:room-status', kwargs={'pk': self.room.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'OPEN')
        self.assertEqual(response.data['status_display'], 'Open')

    def test_update_status_to_paused_and_closed(self):
        """Verify transitioning room from OPEN to PAUSED, then CLOSED."""
        url = reverse('recruitment:room-status', kwargs={'pk': self.room.id})

        # Transition to PAUSED
        res_pause = self.client.patch(url, {'status': 'PAUSED'}, format='json')
        self.assertEqual(res_pause.status_code, status.HTTP_200_OK)
        self.assertEqual(res_pause.data['status'], 'PAUSED')
        self.room.refresh_from_db()
        self.assertEqual(self.room.status, 'PAUSED')

        # Transition to CLOSED
        res_close = self.client.patch(url, {'status': 'CLOSED'}, format='json')
        self.assertEqual(res_close.status_code, status.HTTP_200_OK)
        self.assertEqual(res_close.data['status'], 'CLOSED')
        self.room.refresh_from_db()
        self.assertEqual(self.room.status, 'CLOSED')

    def test_update_status_to_draft(self):
        """Verify transitioning room to DRAFT state."""
        url = reverse('recruitment:room-status', kwargs={'pk': self.room.id})
        response = self.client.patch(url, {'status': 'DRAFT'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'DRAFT')
        self.room.refresh_from_db()
        self.assertEqual(self.room.status, 'DRAFT')

    def test_reopen_paused_room(self):
        """AC-5: HR Manager can manually reopen a paused room."""
        self.room.status = RecruitmentRoom.Status.PAUSED
        self.room.save(update_fields=['status'])

        url = reverse('recruitment:room-status', kwargs={'pk': self.room.id})
        response = self.client.patch(url, {'status': 'OPEN'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'OPEN')
        self.room.refresh_from_db()
        self.assertEqual(self.room.status, 'OPEN')
        self.assertTrue(self.room.is_open)

    def test_reopen_closed_room(self):
        """AC-5: HR Manager can manually reopen a closed room."""
        self.room.status = RecruitmentRoom.Status.CLOSED
        self.room.save(update_fields=['status'])

        url = reverse('recruitment:room-status', kwargs={'pk': self.room.id})
        response = self.client.patch(url, {'status': 'OPEN'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'OPEN')
        self.room.refresh_from_db()
        self.assertEqual(self.room.status, 'OPEN')
        self.assertTrue(self.room.is_open)

    def test_invalid_status_rejection(self):
        """Invalid status values are rejected with HTTP 400."""
        url = reverse('recruitment:room-status', kwargs={'pk': self.room.id})
        response = self.client.patch(url, {'status': 'ARCHIVED_INVALID'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # =========================================================================
    # 2. Application Deadline Management & Auto-Expiration (AC-1 & AC-4)
    # =========================================================================

    def test_get_room_deadline(self):
        """Verify GET /api/recruitment/rooms/<id>/deadline/ returns current deadline."""
        url = reverse('recruitment:room-deadline', kwargs={'pk': self.room.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data['application_deadline'])
        self.assertFalse(response.data['is_past_deadline'])

    def test_set_and_update_deadline(self):
        """AC-1: HR Manager can set and update an application deadline date and time."""
        url = reverse('recruitment:room-deadline', kwargs={'pk': self.room.id})
        new_deadline = (timezone.now() + timedelta(days=14)).isoformat()

        response = self.client.patch(url, {'application_deadline': new_deadline}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_past_deadline'])

        self.room.refresh_from_db()
        self.assertIsNotNone(self.room.application_deadline)
        self.assertEqual(self.room.link_expires_at, self.room.application_deadline)

    def test_clear_deadline(self):
        """HR Manager can clear the application deadline by setting it to null."""
        url = reverse('recruitment:room-deadline', kwargs={'pk': self.room.id})
        response = self.client.patch(url, {'application_deadline': None}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data['application_deadline'])
        self.assertFalse(response.data['is_past_deadline'])

        self.room.refresh_from_db()
        self.assertIsNone(self.room.application_deadline)

    def test_setting_past_deadline_auto_transitions_to_closed(self):
        """AC-4: Setting a deadline in the past auto-transitions room to CLOSED."""
        url = reverse('recruitment:room-deadline', kwargs={'pk': self.room.id})
        past_deadline = (timezone.now() - timedelta(hours=2)).isoformat()

        response = self.client.patch(url, {'application_deadline': past_deadline}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_past_deadline'])

        self.room.refresh_from_db()
        self.assertEqual(self.room.status, RecruitmentRoom.Status.CLOSED)

    # =========================================================================
    # 3. Submission Gatekeeper & Blockage (AC-3 & AC-4)
    # =========================================================================

    def test_candidate_link_blocked_when_paused(self):
        """AC-3: Public application view is blocked when room is PAUSED."""
        self.room.status = RecruitmentRoom.Status.PAUSED
        self.room.save(update_fields=['status'])

        self.client.logout()
        url = reverse('recruitment:public-apply', kwargs={'token': self.room.share_token})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_410_GONE)
        self.assertEqual(response.data['code'], 'ROOM_PAUSED')
        self.assertIn('paused', response.data['error'].lower())

    def test_candidate_link_blocked_when_closed(self):
        """AC-3: Public application view is blocked when room is CLOSED."""
        self.room.status = RecruitmentRoom.Status.CLOSED
        self.room.save(update_fields=['status'])

        self.client.logout()
        url = reverse('recruitment:public-apply', kwargs={'token': self.room.share_token})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_410_GONE)
        self.assertEqual(response.data['code'], 'ROOM_CLOSED')
        self.assertIn('closed', response.data['error'].lower())

    def test_candidate_link_blocked_when_draft(self):
        """Public application view is blocked when room is DRAFT."""
        self.room.status = RecruitmentRoom.Status.DRAFT
        self.room.save(update_fields=['status'])

        self.client.logout()
        url = reverse('recruitment:public-apply', kwargs={'token': self.room.share_token})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_410_GONE)
        self.assertEqual(response.data['code'], 'ROOM_DRAFT')

    def test_candidate_submission_blocked_when_paused(self):
        """AC-3: Submissions are blocked when room is PAUSED."""
        self.room.status = RecruitmentRoom.Status.PAUSED
        self.room.save(update_fields=['status'])

        self.client.logout()
        url = reverse('recruitment:public-apply-submit', kwargs={'token': self.room.share_token})
        data = {
            'full_name': 'John Doe',
            'email': 'john@example.com',
            'cv_file': self.mock_cv,
            'video_file': self.mock_video,
        }
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_410_GONE)
        self.assertEqual(response.data['code'], 'ROOM_PAUSED')

    def test_candidate_submission_blocked_when_closed(self):
        """AC-3: Submissions are blocked when room is CLOSED."""
        self.room.status = RecruitmentRoom.Status.CLOSED
        self.room.save(update_fields=['status'])

        self.client.logout()
        url = reverse('recruitment:public-apply-submit', kwargs={'token': self.room.share_token})
        data = {
            'full_name': 'Jane Doe',
            'email': 'jane@example.com',
            'cv_file': self.mock_cv,
            'video_file': self.mock_video,
        }
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_410_GONE)
        self.assertEqual(response.data['code'], 'ROOM_CLOSED')

    def test_candidate_submission_blocked_when_deadline_passed(self):
        """AC-4: Submissions are blocked when application deadline has passed."""
        self.room.application_deadline = timezone.now() - timedelta(minutes=15)
        self.room.save(update_fields=['application_deadline'])

        self.client.logout()
        url = reverse('recruitment:public-apply-submit', kwargs={'token': self.room.share_token})
        data = {
            'full_name': 'Alice Smith',
            'email': 'alice@example.com',
            'cv_file': self.mock_cv,
            'video_file': self.mock_video,
        }
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_410_GONE)
        self.assertEqual(response.data['code'], 'DEADLINE_PASSED')
        self.assertIn('deadline', response.data['error'].lower())

    @patch('apps.presentation.services.pipeline_manager.PipelineManager.run_pipeline')
    @patch('apps.cv.services.pipeline.CVExtractionPipeline.process_candidate_cv')
    def test_successful_submission_when_open_and_within_deadline(self, mock_cv, mock_vid):
        """Candidate can successfully submit when room is OPEN and deadline is in future."""
        class MockCVResult:
            success = True
            raw_text = "test cv text"
            skills = []
            education = []
            experience = []
        mock_cv.return_value = MockCVResult()

        self.room.status = RecruitmentRoom.Status.OPEN
        self.room.application_deadline = timezone.now() + timedelta(days=5)
        self.room.save(update_fields=['status', 'application_deadline'])

        self.client.logout()
        url = reverse('recruitment:public-apply-submit', kwargs={'token': self.room.share_token})
        data = {
            'full_name': 'Bob Tester',
            'email': 'bob@example.com',
            'cv_file': self.mock_cv,
            'video_file': self.mock_video,
        }
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('application_id', response.data)

    def test_direct_gatekeeper_endpoint_blocks_paused_and_expired(self):
        """US-45-T3: POST /api/recruitment/applications/submit/ blocks paused/expired room."""
        self.room.status = RecruitmentRoom.Status.PAUSED
        self.room.save(update_fields=['status'])

        self.client.logout()
        gatekeeper_url = reverse('recruitment:application-submit-gatekeeper')

        # Test with token
        res_token = self.client.post(gatekeeper_url, {
            'token': self.room.share_token,
            'full_name': 'Test User',
            'email': 'test@example.com',
        }, format='multipart')
        self.assertEqual(res_token.status_code, status.HTTP_410_GONE)

        # Test with room_id
        res_room = self.client.post(gatekeeper_url, {
            'room_id': self.room.id,
            'full_name': 'Test User',
            'email': 'test@example.com',
        }, format='multipart')
        self.assertEqual(res_room.status_code, status.HTTP_410_GONE)

    # =========================================================================
    # 4. HR Dashboard Filtering (AC-6)
    # =========================================================================

    def test_hr_dashboard_filter_by_status(self):
        """AC-6: HR dashboard clearly filters and organizes rooms by lifecycle state."""
        # Create rooms in various lifecycle states
        room_paused = RecruitmentRoom.objects.create(
            title='Paused Room',
            company_name='Apex Corp',
            created_by=self.hr_user,
            status=RecruitmentRoom.Status.PAUSED,
        )
        room_closed = RecruitmentRoom.objects.create(
            title='Closed Room',
            company_name='Apex Corp',
            created_by=self.hr_user,
            status=RecruitmentRoom.Status.CLOSED,
        )
        room_draft = RecruitmentRoom.objects.create(
            title='Draft Room',
            company_name='Apex Corp',
            created_by=self.hr_user,
            status=RecruitmentRoom.Status.DRAFT,
        )

        list_url = reverse('recruitment:room-list')

        # Filter: OPEN
        res_open = self.client.get(f"{list_url}?status=OPEN")
        self.assertEqual(res_open.status_code, status.HTTP_200_OK)
        open_ids = [r['id'] for r in res_open.data]
        self.assertIn(self.room.id, open_ids)
        self.assertNotIn(room_paused.id, open_ids)
        self.assertNotIn(room_closed.id, open_ids)

        # Filter: PAUSED
        res_paused = self.client.get(f"{list_url}?status=PAUSED")
        self.assertEqual(res_paused.status_code, status.HTTP_200_OK)
        paused_ids = [r['id'] for r in res_paused.data]
        self.assertIn(room_paused.id, paused_ids)
        self.assertNotIn(self.room.id, paused_ids)

        # Filter: CLOSED
        res_closed = self.client.get(f"{list_url}?status=CLOSED")
        self.assertEqual(res_closed.status_code, status.HTTP_200_OK)
        closed_ids = [r['id'] for r in res_closed.data]
        self.assertIn(room_closed.id, closed_ids)

        # Filter: DRAFT
        res_draft = self.client.get(f"{list_url}?status=DRAFT")
        self.assertEqual(res_draft.status_code, status.HTTP_200_OK)
        draft_ids = [r['id'] for r in res_draft.data]
        self.assertIn(room_draft.id, draft_ids)

        # Filter: ALL
        res_all = self.client.get(f"{list_url}?status=ALL")
        self.assertEqual(res_all.status_code, status.HTTP_200_OK)
        all_ids = [r['id'] for r in res_all.data]
        self.assertIn(self.room.id, all_ids)
        self.assertIn(room_paused.id, all_ids)
        self.assertIn(room_closed.id, all_ids)
        self.assertIn(room_draft.id, all_ids)

    # =========================================================================
    # 5. Permission & Security Isolation
    # =========================================================================

    def test_other_hr_cannot_modify_room_lifecycle(self):
        """Unauthorized HR managers cannot change status or deadline of another user's room."""
        self.client.force_authenticate(user=self.other_hr)

        status_url = reverse('recruitment:room-status', kwargs={'pk': self.room.id})
        res_status = self.client.patch(status_url, {'status': 'PAUSED'}, format='json')
        self.assertIn(res_status.status_code, [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN])

        deadline_url = reverse('recruitment:room-deadline', kwargs={'pk': self.room.id})
        res_deadline = self.client.patch(deadline_url, {'application_deadline': timezone.now().isoformat()}, format='json')
        self.assertIn(res_deadline.status_code, [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN])
