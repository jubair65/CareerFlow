import uuid
from unittest.mock import patch
from django.core import mail
from rest_framework import status
from rest_framework.test import APITestCase
from apps.authentication.models import User
from apps.core.models import Notification
from apps.core.services.notification_service import NotificationService


class US34NotificationModelAndServiceUnitTests(APITestCase):
    """
    US-34-T7: Unit tests for Notification model creation and NotificationService.
    Covers Acceptance Criteria 1, 3, 5, 6.
    """

    def setUp(self):
        self.uid = uuid.uuid4().hex[:8]
        self.student = User.objects.create_user(
            username=f"student_{self.uid}",
            email=f"mona_{self.uid}@careerflow.test",
            password="StrongPassword123!",
            first_name="Mona",
            last_name="Naeem",
            role=User.Role.STUDENT,
        )
        self.other_student = User.objects.create_user(
            username=f"other_{self.uid}",
            email=f"other_{self.uid}@careerflow.test",
            password="StrongPassword123!",
            first_name="Other",
            last_name="Candidate",
            role=User.Role.STUDENT,
        )
        mail.outbox.clear()

    def test_notification_model_creation_and_defaults(self):
        """Verify model attributes, default values, and string representation."""
        notif = Notification.objects.create(
            user=self.student,
            title="Analysis Complete",
            message="Your presentation analysis results are available.",
            link_url="/presentation/history/14",
        )

        self.assertIsNotNone(notif.id)
        self.assertEqual(notif.user, self.student)
        self.assertEqual(notif.title, "Analysis Complete")
        self.assertEqual(notif.message, "Your presentation analysis results are available.")
        self.assertEqual(notif.link_url, "/presentation/history/14")
        self.assertEqual(notif.notification_type, Notification.NotificationType.INFO)
        self.assertFalse(notif.is_read)
        self.assertIsNotNone(notif.created_at)
        self.assertIn("Unread", str(notif))
        self.assertIn(self.student.email, str(notif))

    def test_notification_type_choices(self):
        """Verify specialized notification categories."""
        cv_notif = Notification.objects.create(
            user=self.student,
            title="CV Parsed",
            message="Extracted 8 skills from your CV.",
            notification_type=Notification.NotificationType.CV_ANALYSIS_COMPLETE,
        )
        self.assertEqual(cv_notif.notification_type, 'CV_ANALYSIS_COMPLETE')

        pres_notif = Notification.objects.create(
            user=self.student,
            title="Video Evaluated",
            message="Score: 88/100",
            notification_type=Notification.NotificationType.PRESENTATION_ANALYSIS_COMPLETE,
        )
        self.assertEqual(pres_notif.notification_type, 'PRESENTATION_ANALYSIS_COMPLETE')

    def test_create_notification_persists_and_sends_email(self):
        """US-34-T4 & AC#3: Verify notification persistence and transactional email delivery."""
        notif = NotificationService.create_notification(
            user=self.student,
            title="CV Analysis Ready",
            message="Your CV parsing is complete with recommendations.",
            link_url="/dashboard",
            notification_type=Notification.NotificationType.CV_ANALYSIS_COMPLETE,
            send_email=True,
        )

        self.assertIsNotNone(notif)
        self.assertFalse(notif.is_read)
        self.assertTrue(Notification.objects.filter(id=notif.id).exists())

        # Verify email was dispatched to outbox
        self.assertEqual(len(mail.outbox), 1)
        sent = mail.outbox[0]
        self.assertIn("CV Analysis Ready", sent.subject)
        self.assertIn(self.student.email, sent.to)
        self.assertIn("CV parsing is complete", sent.body)

    def test_create_notification_null_user_handled_safely(self):
        """Ensure no exception is thrown when user is None."""
        result = NotificationService.create_notification(
            user=None,
            title="Orphan Notification",
            message="No user recipient",
        )
        self.assertIsNone(result)

    def test_email_failure_does_not_break_notification_creation(self):
        """US-34 AC#5: Email failure never interrupts pipeline."""
        with patch('django.core.mail.EmailMultiAlternatives.send', side_effect=Exception("SMTP Connection Timeout")):
            notif = NotificationService.create_notification(
                user=self.student,
                title="Fault-Tolerant Alert",
                message="Testing SMTP outage resilience.",
                send_email=True,
            )

        self.assertIsNotNone(notif)
        self.assertEqual(notif.title, "Fault-Tolerant Alert")
        self.assertTrue(Notification.objects.filter(id=notif.id).exists())

    def test_notify_cv_analysis_complete_helper(self):
        """Verify CV analysis notification helper creates record and triggers email."""
        notif = NotificationService.notify_cv_analysis_complete(
            user=self.student,
            skills_count=12,
            feedback_summary="Strong Python & Django experience",
        )

        self.assertIsNotNone(notif)
        self.assertEqual(notif.notification_type, Notification.NotificationType.CV_ANALYSIS_COMPLETE)
        self.assertIn("12 skill(s)", notif.message)
        self.assertEqual(len(mail.outbox), 1)

    def test_notify_presentation_analysis_complete_helper(self):
        """Verify Presentation analysis notification helper creates record with score."""
        class MockVideo:
            id = 42

        notif = NotificationService.notify_presentation_analysis_complete(
            user=self.student,
            video=MockVideo(),
            overall_score=85.0,
        )

        self.assertIsNotNone(notif)
        self.assertEqual(notif.notification_type, Notification.NotificationType.PRESENTATION_ANALYSIS_COMPLETE)
        self.assertIn("85/100", notif.message)
        self.assertEqual(notif.link_url, "/presentation/history/42")
        self.assertEqual(len(mail.outbox), 1)


class US34NotificationAPIIntegrationTests(APITestCase):
    """
    US-34-T5: REST API endpoints integration tests for in-app notifications.
    Covers Acceptance Criteria 2, 4, 6.
    """

    def setUp(self):
        self.uid = uuid.uuid4().hex[:8]
        self.student = User.objects.create_user(
            username=f"student_{self.uid}",
            email=f"mona_{self.uid}@careerflow.test",
            password="StrongPassword123!",
            first_name="Mona",
            last_name="Naeem",
            role=User.Role.STUDENT,
        )
        self.other_student = User.objects.create_user(
            username=f"other_{self.uid}",
            email=f"other_{self.uid}@careerflow.test",
            password="StrongPassword123!",
            first_name="Other",
            last_name="Candidate",
            role=User.Role.STUDENT,
        )

    def test_unauthenticated_request_rejected(self):
        """Ensure endpoints require authentication."""
        response = self.client.get('/api/notifications/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_notifications_list_and_unread_count(self):
        """Verify GET /api/notifications/ returns unread_count and notification array."""
        Notification.objects.create(user=self.student, title="Unread 1", message="Body 1", is_read=False)
        Notification.objects.create(user=self.student, title="Unread 2", message="Body 2", is_read=False)
        Notification.objects.create(user=self.student, title="Read 1", message="Body 3", is_read=True)

        self.client.force_authenticate(user=self.student)
        response = self.client.get('/api/notifications/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['unread_count'], 2)
        self.assertEqual(len(data['notifications']), 3)

    def test_notifications_multi_tenant_user_isolation(self):
        """Verify User A can never see User B's notifications."""
        Notification.objects.create(user=self.student, title="Mona's Private Alert", message="Confidential")
        Notification.objects.create(user=self.other_student, title="Other's Alert", message="Other")

        self.client.force_authenticate(user=self.other_student)
        response = self.client.get('/api/notifications/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['unread_count'], 1)
        self.assertEqual(len(data['notifications']), 1)
        self.assertEqual(data['notifications'][0]['title'], "Other's Alert")

    def test_mark_single_notification_read(self):
        """Verify POST /api/notifications/<id>/read/ updates is_read flag."""
        notif = Notification.objects.create(user=self.student, title="Alert", message="Unread text", is_read=False)

        # Other user cannot mark Mona's notification as read (returns 404)
        self.client.force_authenticate(user=self.other_student)
        forbidden_resp = self.client.post(f'/api/notifications/{notif.id}/read/')
        self.assertEqual(forbidden_resp.status_code, status.HTTP_404_NOT_FOUND)

        # Owner can mark as read
        self.client.force_authenticate(user=self.student)
        response = self.client.post(f'/api/notifications/{notif.id}/read/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        notif.refresh_from_db()
        self.assertTrue(notif.is_read)

    def test_mark_all_notifications_read(self):
        """Verify POST /api/notifications/mark-all-read/ marks all user notifications as read."""
        Notification.objects.create(user=self.student, title="N1", message="M1", is_read=False)
        Notification.objects.create(user=self.student, title="N2", message="M2", is_read=False)
        Notification.objects.create(user=self.student, title="N3", message="M3", is_read=False)

        self.client.force_authenticate(user=self.student)
        response = self.client.post('/api/notifications/mark-all-read/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['updated_count'], 3)

        # Verify unread count is now 0
        get_resp = self.client.get('/api/notifications/')
        self.assertEqual(get_resp.json()['unread_count'], 0)

    def test_delete_notification(self):
        """Verify DELETE /api/notifications/<id>/ deletes the notification."""
        notif = Notification.objects.create(user=self.student, title="To Delete", message="Temporary")

        self.client.force_authenticate(user=self.student)
        response = self.client.delete(f'/api/notifications/{notif.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Notification.objects.filter(id=notif.id).exists())

    def test_delete_other_user_notification_rejected(self):
        """Verify user cannot delete another user's notification."""
        notif = Notification.objects.create(user=self.student, title="Mona's Notification", message="Keep")

        self.client.force_authenticate(user=self.other_student)
        response = self.client.delete(f'/api/notifications/{notif.id}/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Notification.objects.filter(id=notif.id).exists())
