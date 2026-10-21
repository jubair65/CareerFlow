import os
import uuid
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'careerflow.settings')
django.setup()

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from apps.authentication.models import User
from apps.recruitment.models import RecruitmentRoom, CandidateApplication
from apps.recruitment.services.review_service import (
    get_candidate_review_data,
    record_candidate_review_decision,
    AI_ADVISORY_DISCLAIMER,
)


class US26CandidateReviewDecisionTests(APITestCase):
    """
    US-26: HR Review of AI Results & Decision Audit Trail Test Suite (US-26-T7).
    Validates:
    - AC#1: HR can review scores and candidate information before making a final decision.
    - AC#2: CV, video and final scores are shown together for each candidate.
    - AC#3: HR can confirm or override the AI shortlist recommendation (override strictly requires note).
    - AC#4: Final HR decisions are stored in database with audit trail (decided_by, decided_at, notes).
    - AC#5: AI results are clearly marked as recommendations, not final decisions.
    - AC#6: Only authorized HR users owning the room can review details and record decisions.
    """

    def setUp(self):
        self.uid = uuid.uuid4().hex[:8]

        # 1. Primary HR User (Room Owner)
        self.hr_owner = User.objects.create_user(
            username=f"hr_mobin_{self.uid}",
            email=f"hr_mobin_{self.uid}@careerflow.demo",
            password="Password123!",
            role=User.Role.HR_MANAGER,
            full_name="Hasanul Mobin HR"
        )

        # 2. Unauthorized HR User (Different room owner)
        self.other_hr = User.objects.create_user(
            username=f"other_hr_{self.uid}",
            email=f"other_hr_{self.uid}@careerflow.demo",
            password="Password123!",
            role=User.Role.HR_MANAGER,
            full_name="Other HR Manager"
        )

        # 3. Candidate / Student User (Non-HR)
        self.candidate_user = User.objects.create_user(
            username=f"cand_{self.uid}",
            email=f"cand_{self.uid}@careerflow.demo",
            password="Password123!",
            role=User.Role.STUDENT,
            full_name="Jane Doe"
        )

        # 4. Recruitment Room owned by hr_owner
        self.room = RecruitmentRoom.objects.create(
            title="Senior Fullstack Developer",
            company_name="Innovate Ltd",
            department="Engineering",
            cv_weight=50,
            video_weight=50,
            status=RecruitmentRoom.Status.ACTIVE,
            created_by=self.hr_owner
        )

        # 5. Candidate Application with AI scores
        self.app_shortlisted = CandidateApplication.objects.create(
            room=self.room,
            candidate=self.candidate_user,
            final_score=88.5,
            cv_score=92.0,
            video_score=85.0,
            is_partial_score=False,
            is_shortlisted=True,
            shortlist_reason="Scored above 80.0 minimum threshold",
            shortlisted_at=timezone.now(),
            status=CandidateApplication.Status.COMPLETED
        )

        # 6. Candidate 2 (Not shortlisted by AI)
        self.cand_user2 = User.objects.create_user(
            username=f"cand2_{self.uid}",
            email=f"cand2_{self.uid}@careerflow.demo",
            password="Password123!",
            role=User.Role.STUDENT,
            full_name="John Smith"
        )
        self.app_non_shortlisted = CandidateApplication.objects.create(
            room=self.room,
            candidate=self.cand_user2,
            final_score=68.0,
            cv_score=70.0,
            video_score=66.0,
            is_partial_score=False,
            is_shortlisted=False,
            shortlist_reason="Score 68.0 below threshold 80.0",
            status=CandidateApplication.Status.COMPLETED
        )

    def test_review_details_success_and_ai_disclaimer(self):
        """
        US-26 AC#1, AC#2, AC#5: Verify HR owner can fetch review details.
        Scores are bundled together, AI recommendation is labeled, and disclaimer is present.
        """
        self.client.force_authenticate(user=self.hr_owner)
        url = f"/api/recruitment/applications/{self.app_shortlisted.id}/review/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(data["application_id"], self.app_shortlisted.id)
        self.assertEqual(data["candidate_name"], "Jane Doe")
        self.assertEqual(data["final_score"], 88.5)
        self.assertEqual(data["cv_score"], 92.0)
        self.assertEqual(data["video_score"], 85.0)
        self.assertTrue(data["is_shortlisted"])
        self.assertEqual(data["ai_recommendation"], "RECOMMENDED_SHORTLIST")
        self.assertEqual(data["ai_disclaimer"], AI_ADVISORY_DISCLAIMER)
        self.assertEqual(data["hr_decision"], CandidateApplication.HrDecision.UNDECIDED)

    def test_review_details_unauthorized_non_owner(self):
        """
        US-26 AC#6: Verify that another HR manager who does NOT own the room cannot view review details.
        """
        self.client.force_authenticate(user=self.other_hr)
        url = f"/api/recruitment/applications/{self.app_shortlisted.id}/review/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_review_details_unauthorized_student(self):
        """
        US-26 AC#6: Candidate cannot access review endpoints.
        """
        self.client.force_authenticate(user=self.candidate_user)
        url = f"/api/recruitment/applications/{self.app_shortlisted.id}/review/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_confirm_shortlist_decision(self):
        """
        US-26 AC#3 & AC#4: Confirming the AI shortlist recommendation.
        Persists decision, timestamps, and reviewer audit info.
        """
        self.client.force_authenticate(user=self.hr_owner)
        url = f"/api/recruitment/applications/{self.app_shortlisted.id}/decision/"
        payload = {
            "decision": "CONFIRMED",
            "notes": "Strong candidate matching all technical requirements and communication standards."
        }
        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["hr_decision"], "CONFIRMED")
        self.assertEqual(response.data["hr_decided_by"], self.hr_owner.email)
        self.assertTrue(response.data["is_shortlisted"])

        # DB persistence check
        self.app_shortlisted.refresh_from_db()
        self.assertEqual(self.app_shortlisted.hr_decision, CandidateApplication.HrDecision.CONFIRMED)
        self.assertEqual(self.app_shortlisted.hr_decided_by, self.hr_owner)
        self.assertIsNotNone(self.app_shortlisted.hr_decided_at)
        self.assertIn("Strong candidate", self.app_shortlisted.hr_decision_notes)
        self.assertTrue(self.app_shortlisted.is_shortlisted)

    def test_reject_candidate_decision(self):
        """
        US-26 AC#3 & AC#4: HR rejects a candidate who was previously AI-shortlisted.
        Shortlist flag is set to False and audit reason is stored.
        """
        self.client.force_authenticate(user=self.hr_owner)
        url = f"/api/recruitment/applications/{self.app_shortlisted.id}/decision/"
        payload = {
            "decision": "REJECTED",
            "notes": "Candidate salary expectations exceed room budget."
        }
        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["hr_decision"], "REJECTED")
        self.assertFalse(response.data["is_shortlisted"])

        self.app_shortlisted.refresh_from_db()
        self.assertEqual(self.app_shortlisted.hr_decision, CandidateApplication.HrDecision.REJECTED)
        self.assertFalse(self.app_shortlisted.is_shortlisted)

    def test_override_decision_requires_note_validation(self):
        """
        US-26 AC#3 & US-26-T7: Overriding an AI recommendation strictly requires an explanatory note.
        Missing or empty notes must be rejected with 400 Bad Request.
        """
        self.client.force_authenticate(user=self.hr_owner)
        url = f"/api/recruitment/applications/{self.app_non_shortlisted.id}/decision/"

        # 1. Without note
        response = self.client.post(url, {"decision": "OVERRIDDEN"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("notes", response.data)

        # 2. With blank whitespace note
        response = self.client.post(url, {"decision": "OVERRIDDEN", "notes": "   "}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("notes", response.data)

        # 3. With note too short (<5 chars)
        response = self.client.post(url, {"decision": "OVERRIDDEN", "notes": "ok"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("notes", response.data)

    def test_override_decision_successful_shortlist(self):
        """
        US-26 AC#3: HR overrides non-shortlisted candidate into shortlisted with justification.
        """
        self.client.force_authenticate(user=self.hr_owner)
        url = f"/api/recruitment/applications/{self.app_non_shortlisted.id}/decision/"
        payload = {
            "decision": "OVERRIDDEN",
            "notes": "Impressive open-source portfolio balances out slightly lower automated CV score."
        }
        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["hr_decision"], "OVERRIDDEN")
        self.assertTrue(response.data["is_shortlisted"])

        self.app_non_shortlisted.refresh_from_db()
        self.assertEqual(self.app_non_shortlisted.hr_decision, CandidateApplication.HrDecision.OVERRIDDEN)
        self.assertTrue(self.app_non_shortlisted.is_shortlisted)
        self.assertIn("Impressive open-source", self.app_non_shortlisted.hr_decision_notes)

    def test_hold_decision_successful(self):
        """
        US-26: Placing application on hold preserves state and logs decision.
        """
        self.client.force_authenticate(user=self.hr_owner)
        url = f"/api/recruitment/applications/{self.app_shortlisted.id}/decision/"
        payload = {
            "decision": "ON_HOLD",
            "notes": "Awaiting second round of reference checks."
        }
        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["hr_decision"], "ON_HOLD")

        self.app_shortlisted.refresh_from_db()
        self.assertEqual(self.app_shortlisted.hr_decision, CandidateApplication.HrDecision.ON_HOLD)

    def test_decision_unauthorized_room_owner(self):
        """
        US-26 AC#6: Non-owner HR cannot record a decision on this room's application.
        """
        self.client.force_authenticate(user=self.other_hr)
        url = f"/api/recruitment/applications/{self.app_shortlisted.id}/decision/"
        payload = {
            "decision": "CONFIRMED",
            "notes": "Trying to confirm someone else's room applicant."
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
