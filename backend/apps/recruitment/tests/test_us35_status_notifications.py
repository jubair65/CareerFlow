"""
US-35: Applicant Application Status Notification Test Suite (US-35-T7).
Validates:
- AC#1: Applicant receives a notification when their application status changes (shortlisted or rejected).
- AC#2: Notification is sent by email and displayed in applicant's application portal status page.
- AC#3: Status shown matches the HR Manager's confirmed decision.
- AC#4: Applicants can only see their own application status (strict candidate isolation).
- AC#5: Failed email delivery is logged and handled gracefully without rolling back decision.
- AC#6: Sent notifications are stored in audit logs (StatusNotificationLog) for later reference.
"""

import os
import uuid
from unittest.mock import patch
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'careerflow.settings')
django.setup()

from django.core import mail
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from apps.authentication.models import User
from apps.core.models import Notification
from apps.recruitment.models import (
    RecruitmentRoom,
    CandidateApplication,
    StatusNotificationLog,
)
from apps.recruitment.services.review_service import record_candidate_review_decision
from apps.recruitment.services.status_notification_service import dispatch_status_notification


class US35StatusNotificationTests(APITestCase):
    def setUp(self):
        self.uid = uuid.uuid4().hex[:8]

        # 1. HR Manager (Room Owner)
        self.hr_user = User.objects.create_user(
            username=f"hr_{self.uid}",
            email=f"hr_{self.uid}@careerflow.demo",
            password="Password123!",
            role=User.Role.HR_MANAGER,
            full_name="Hiring Manager Mona"
        )

        # 2. Candidate Student A
        self.candidate_a = User.objects.create_user(
            username=f"candidate_a_{self.uid}",
            email=f"candidate_a_{self.uid}@careerflow.demo",
            password="Password123!",
            role=User.Role.STUDENT,
            full_name="Alice Candidate"
        )

        # 3. Candidate Student B (Different user)
        self.candidate_b = User.objects.create_user(
            username=f"candidate_b_{self.uid}",
            email=f"candidate_b_{self.uid}@careerflow.demo",
            password="Password123!",
            role=User.Role.STUDENT,
            full_name="Bob Candidate"
        )

        # 4. Recruitment Room
        self.room = RecruitmentRoom.objects.create(
            title="Senior AI Full Stack Engineer",
            company_name="InnovateTech Global",
            department="Product Engineering",
            role_category="ENGINEERING",
            created_by=self.hr_user,
            cv_weight=50.0,
            video_weight=50.0
        )

        # 5. Candidate Application for Alice
        self.app_a = CandidateApplication.objects.create(
            room=self.room,
            candidate=self.candidate_a,
            status=CandidateApplication.Status.COMPLETED,
            cv_score=88.0,
            video_score=92.0,
            final_score=90.0,
            is_shortlisted=False,
            hr_decision=CandidateApplication.HrDecision.UNDECIDED
        )

        # Clear outbox
        mail.outbox = []

    def test_shortlist_transition_creates_in_app_notification_and_audit_log(self):
        """
        AC#1 & AC#6: When candidate is shortlisted, an in-app notification and
        StatusNotificationLog audit record are created.
        """
        initial_notif_count = Notification.objects.filter(user=self.candidate_a).count()
        initial_log_count = StatusNotificationLog.objects.filter(application=self.app_a).count()

        # Update candidate to shortlisted
        self.app_a.is_shortlisted = True
        self.app_a.shortlist_reason = "Top 10 percentile in multi-modal scoring"
        self.app_a.save()

        # Check in-app notification
        notifications = Notification.objects.filter(
            user=self.candidate_a,
            notification_type=Notification.NotificationType.APPLICATION_STATUS
        )
        self.assertGreater(notifications.count(), initial_notif_count)
        latest_notif = notifications.first()
        self.assertIn("Shortlisted", latest_notif.title)
        self.assertEqual(latest_notif.link_url, "/applications/my-status")

        # Check audit log in StatusNotificationLog
        logs = StatusNotificationLog.objects.filter(application=self.app_a)
        self.assertGreater(logs.count(), initial_log_count)
        latest_log = logs.first()
        self.assertEqual(latest_log.recipient_email, self.candidate_a.email)
        self.assertEqual(latest_log.status_type, StatusNotificationLog.StatusType.SHORTLISTED)
        self.assertTrue(latest_log.email_sent)
        self.assertEqual(latest_log.error_message, "")

    def test_hr_decision_confirmed_dispatches_shortlist_notification(self):
        """
        AC#1 & AC#3: When HR confirms shortlist, application status notification is generated.
        """
        record_candidate_review_decision(
            application=self.app_a,
            decision=CandidateApplication.HrDecision.CONFIRMED,
            notes="Outstanding technical performance and culture alignment",
            request_user=self.hr_user
        )

        self.app_a.refresh_from_db()
        self.assertTrue(self.app_a.is_shortlisted)
        self.assertEqual(self.app_a.hr_decision, CandidateApplication.HrDecision.CONFIRMED)

        # Audit log verification
        log = StatusNotificationLog.objects.filter(
            application=self.app_a,
            status_type=StatusNotificationLog.StatusType.CONFIRMED
        ).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.recipient_email, self.candidate_a.email)
        self.assertTrue(log.email_sent)

        # Email dispatch check
        self.assertGreater(len(mail.outbox), 0)
        sent_email = mail.outbox[-1]
        self.assertIn("Shortlisted", sent_email.subject)
        self.assertIn(self.candidate_a.email, sent_email.to)

    def test_hr_decision_rejected_dispatches_rejection_notification(self):
        """
        AC#1 & AC#3: When HR records REJECTED decision, polite notice email and in-app alert are created.
        """
        record_candidate_review_decision(
            application=self.app_a,
            decision=CandidateApplication.HrDecision.REJECTED,
            notes="Position filled by candidates with deeper distributed systems expertise",
            request_user=self.hr_user
        )

        self.app_a.refresh_from_db()
        self.assertFalse(self.app_a.is_shortlisted)
        self.assertEqual(self.app_a.hr_decision, CandidateApplication.HrDecision.REJECTED)

        # Audit log verification
        log = StatusNotificationLog.objects.filter(
            application=self.app_a,
            status_type=StatusNotificationLog.StatusType.REJECTED
        ).first()
        self.assertIsNotNone(log)
        self.assertTrue(log.email_sent)

        # Email dispatch check
        self.assertGreater(len(mail.outbox), 0)
        sent_email = mail.outbox[-1]
        self.assertIn("Application Update", sent_email.subject)
        self.assertIn(self.candidate_a.email, sent_email.to)

    def test_failed_email_delivery_handled_gracefully_without_rollback(self):
        """
        AC#5: If transactional email delivery encounters an exception, it is logged
        in StatusNotificationLog and does NOT fail or rollback the HR review decision.
        """
        with patch('apps.core.services.notification_service.NotificationService.send_notification_email') as mock_email:
            mock_email.side_effect = Exception("SMTP Connection Timeout: port 587 blocked")

            result = record_candidate_review_decision(
                application=self.app_a,
                decision=CandidateApplication.HrDecision.CONFIRMED,
                notes="Confirmed despite email gateway downtime",
                request_user=self.hr_user
            )

            # Decision should succeed and persist
            self.assertEqual(result["hr_decision"], CandidateApplication.HrDecision.CONFIRMED)
            self.app_a.refresh_from_db()
            self.assertEqual(self.app_a.hr_decision, CandidateApplication.HrDecision.CONFIRMED)
            self.assertTrue(self.app_a.is_shortlisted)

            # StatusNotificationLog should capture the error
            log = StatusNotificationLog.objects.filter(
                application=self.app_a,
                status_type=StatusNotificationLog.StatusType.CONFIRMED
            ).first()
            self.assertIsNotNone(log)
            self.assertFalse(log.email_sent)
            self.assertIn("SMTP Connection Timeout", log.error_message)

    def test_applicant_status_list_endpoint_and_milestones(self):
        """
        AC#2 & AC#3: Applicant can retrieve their application list with full multi-stage
        timeline milestones (Submitted -> AI Analysis -> HR Review -> Decision).
        """
        self.client.force_authenticate(user=self.candidate_a)
        response = self.client.get('/api/recruitment/applications/my-status/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(len(data), 1)

        app_item = data[0]
        self.assertEqual(app_item["id"], self.app_a.id)
        self.assertEqual(app_item["room_title"], "Senior AI Full Stack Engineer")
        self.assertEqual(app_item["final_score"], 90.0)
        self.assertIn("stages", app_item)
        self.assertEqual(len(app_item["stages"]), 4)

        stage_keys = [s["key"] for s in app_item["stages"]]
        self.assertEqual(stage_keys, ["SUBMITTED", "AI_ANALYSIS", "HR_REVIEW", "FINAL_DECISION"])

    def test_applicant_privacy_scoping_candidate_cannot_see_others_status(self):
        """
        AC#4: Strict candidate isolation.
        Candidate B cannot view Candidate A's application status endpoint.
        """
        # Candidate B requesting Alice's status
        self.client.force_authenticate(user=self.candidate_b)
        response = self.client.get(f'/api/recruitment/applications/{self.app_a.id}/status/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("Access forbidden", response.data["detail"])

        # Candidate B list endpoint should not include Alice's applications
        list_response = self.client.get('/api/recruitment/applications/my-status/')
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data), 0)

    def test_candidate_can_view_own_application_status_detail(self):
        """
        AC#4: Candidate can view their own application status detail.
        """
        self.client.force_authenticate(user=self.candidate_a)
        response = self.client.get(f'/api/recruitment/applications/{self.app_a.id}/status/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.app_a.id)
        self.assertEqual(response.data["room_title"], "Senior AI Full Stack Engineer")

    def test_unauthenticated_request_is_rejected(self):
        """
        Unauthenticated requests to status endpoints return 401 Unauthorized.
        """
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/recruitment/applications/my-status/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
