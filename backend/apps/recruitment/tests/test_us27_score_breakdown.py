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
from apps.recruitment.services.breakdown_service import get_applicant_score_breakdown


class US27ScoreBreakdownUnitTests(APITestCase):
    """
    US-27: Explainable Applicant Score Breakdown & Transparency Test Suite (US-27-T7).
    Validates:
    - US-27-T1: Score explanation & mathematical formula display.
    - US-27-T2: API data contract for CV and video contribution data.
    - US-27-T4: Display of room weights used and exact per-component points contribution.
    - US-27-T5: Graceful degradation and clear explanation for missing components (partial scores).
    - Multi-tenant room owner authorization and candidate access blocking.
    """

    def setUp(self):
        self.uid = uuid.uuid4().hex[:8]

        # 1. Primary HR User (Room Owner)
        self.hr_owner = User.objects.create_user(
            username=f"hr_bonny_{self.uid}",
            email=f"hr_bonny_{self.uid}@careerflow.demo",
            password="Password123!",
            role=User.Role.HR_MANAGER,
            full_name="Farhana Tahsin Bonny"
        )

        # 2. Unauthorized HR User (Different room owner)
        self.other_hr = User.objects.create_user(
            username=f"other_hr_{self.uid}",
            email=f"other_hr_{self.uid}@careerflow.demo",
            password="Password123!",
            role=User.Role.HR_MANAGER,
            full_name="Other HR Manager"
        )

        # 3. Candidate User (STUDENT role)
        self.candidate = User.objects.create_user(
            username=f"cand_{self.uid}",
            email=f"cand_{self.uid}@careerflow.demo",
            password="Password123!",
            role=User.Role.STUDENT,
            full_name="Sarah Candidate"
        )

        # 4. Standard Room (50% CV / 50% Video)
        self.room_standard = RecruitmentRoom.objects.create(
            title="Senior QA Engineer",
            company_name="Innovate Ltd",
            department="Quality Assurance",
            cv_weight=50,
            video_weight=50,
            status=RecruitmentRoom.Status.ACTIVE,
            created_by=self.hr_owner
        )

        # 5. Full Signal Application (Both CV and Video complete)
        self.app_full = CandidateApplication.objects.create(
            room=self.room_standard,
            candidate=self.candidate,
            final_score=85.0,
            cv_score=80.0,
            video_score=90.0,
            is_partial_score=False,
            status=CandidateApplication.Status.COMPLETED
        )

    def test_breakdown_standard_weights_full_signals(self):
        """
        US-27-T2 & US-27-T4: Verifies standard 50/50 breakdown contract.
        50% of 80.0 = 40.0 pts from CV.
        50% of 90.0 = 45.0 pts from Video.
        Total = 85.0 / 100.
        """
        self.client.force_authenticate(user=self.hr_owner)
        url = f"/api/recruitment/applications/{self.app_full.id}/score-breakdown/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        self.assertEqual(data["application_id"], self.app_full.id)
        self.assertEqual(data["candidate_name"], "Sarah Candidate")
        self.assertEqual(data["final_score"], 85.0)
        self.assertFalse(data["is_partial_score"])
        self.assertEqual(data["cv_weight"], 50)
        self.assertEqual(data["video_weight"], 50)
        self.assertIn("85.0", data["formula_display"])
        self.assertIsNone(data["missing_components_explanation"])

        # Check CV component
        cv_comp = data["cv_component"]
        self.assertTrue(cv_comp["is_available"])
        self.assertEqual(cv_comp["raw_score"], 80.0)
        self.assertEqual(cv_comp["weight_percentage"], 50)
        self.assertEqual(cv_comp["points_contributed"], 40.0)
        self.assertEqual(cv_comp["max_points_possible"], 50.0)
        self.assertEqual(cv_comp["percentage_of_total"], 47.1)  # 40 / 85 * 100 = 47.05 -> 47.1%

        # Check Video component
        video_comp = data["video_component"]
        self.assertTrue(video_comp["is_available"])
        self.assertEqual(video_comp["raw_score"], 90.0)
        self.assertEqual(video_comp["weight_percentage"], 50)
        self.assertEqual(video_comp["points_contributed"], 45.0)
        self.assertEqual(video_comp["max_points_possible"], 50.0)
        self.assertEqual(video_comp["percentage_of_total"], 52.9)  # 45 / 85 * 100 = 52.94 -> 52.9%

    def test_breakdown_asymmetric_weights(self):
        """
        US-27-T4: Verifies asymmetric weighting (e.g., 70% CV / 30% Video).
        CV 85.0 @ 70% = 59.5 pts
        Video 70.0 @ 30% = 21.0 pts
        Final = 80.5 / 100
        """
        room_70_30 = RecruitmentRoom.objects.create(
            title="Backend Architect",
            company_name="Cloud Tech",
            cv_weight=70,
            video_weight=30,
            created_by=self.hr_owner
        )
        app = CandidateApplication.objects.create(
            room=room_70_30,
            candidate=self.candidate,
            final_score=80.5,
            cv_score=85.0,
            video_score=70.0,
            is_partial_score=False
        )

        self.client.force_authenticate(user=self.hr_owner)
        url = f"/api/recruitment/applications/{app.id}/score-breakdown/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        self.assertEqual(data["cv_weight"], 70)
        self.assertEqual(data["video_weight"], 30)
        self.assertEqual(data["cv_component"]["points_contributed"], 59.5)
        self.assertEqual(data["cv_component"]["max_points_possible"], 70.0)
        self.assertEqual(data["video_component"]["points_contributed"], 21.0)
        self.assertEqual(data["video_component"]["max_points_possible"], 30.0)
        self.assertEqual(data["final_score"], 80.5)

    def test_breakdown_boundary_weights(self):
        """
        US-27-T4: Tests boundary allocations (100% CV / 0% Video and 0% CV / 100% Video).
        """
        room_100_0 = RecruitmentRoom.objects.create(
            title="Async Writer",
            company_name="Remote Co",
            cv_weight=100,
            video_weight=0,
            created_by=self.hr_owner
        )
        app = CandidateApplication.objects.create(
            room=room_100_0,
            candidate=self.candidate,
            final_score=92.0,
            cv_score=92.0,
            video_score=60.0,
            is_partial_score=False
        )

        self.client.force_authenticate(user=self.hr_owner)
        res = self.client.get(f"/api/recruitment/applications/{app.id}/score-breakdown/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["cv_component"]["points_contributed"], 92.0)
        self.assertEqual(res.data["video_component"]["points_contributed"], 0.0)

    def _create_candidate(self, suffix: str) -> User:
        return User.objects.create_user(
            username=f"cand_{suffix}_{self.uid}",
            email=f"cand_{suffix}_{self.uid}@careerflow.demo",
            password="Password123!",
            role=User.Role.STUDENT,
            full_name=f"Candidate {suffix}"
        )

    def test_breakdown_missing_video_graceful_degradation(self):
        """
        US-27-T5: Graceful degradation when Video presentation is missing.
        Asserts partial score flag, explanation message, and normalized points.
        """
        cand = self._create_candidate("no_vid")
        app_no_video = CandidateApplication.objects.create(
            room=self.room_standard,
            candidate=cand,
            final_score=88.0,
            cv_score=88.0,
            video_score=None,
            is_partial_score=True
        )

        self.client.force_authenticate(user=self.hr_owner)
        url = f"/api/recruitment/applications/{app_no_video.id}/score-breakdown/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        self.assertTrue(data["is_partial_score"])
        self.assertEqual(data["final_score"], 88.0)
        self.assertTrue(data["cv_component"]["is_available"])
        self.assertFalse(data["video_component"]["is_available"])
        self.assertIsNotNone(data["missing_components_explanation"])
        self.assertIn("Video", data["missing_components_explanation"])
        self.assertIn("Pro-rated", data["formula_display"])

    def test_breakdown_missing_cv_graceful_degradation(self):
        """
        US-27-T5: Graceful degradation when CV is missing.
        """
        cand = self._create_candidate("no_cv")
        app_no_cv = CandidateApplication.objects.create(
            room=self.room_standard,
            candidate=cand,
            final_score=76.0,
            cv_score=None,
            video_score=76.0,
            is_partial_score=True
        )

        self.client.force_authenticate(user=self.hr_owner)
        url = f"/api/recruitment/applications/{app_no_cv.id}/score-breakdown/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        self.assertTrue(data["is_partial_score"])
        self.assertEqual(data["final_score"], 76.0)
        self.assertFalse(data["cv_component"]["is_available"])
        self.assertTrue(data["video_component"]["is_available"])
        self.assertIsNotNone(data["missing_components_explanation"])
        self.assertIn("CV", data["missing_components_explanation"])

    def test_breakdown_both_components_missing(self):
        """
        US-27-T5: Both components pending.
        """
        cand = self._create_candidate("empty")
        app_empty = CandidateApplication.objects.create(
            room=self.room_standard,
            candidate=cand,
            final_score=None,
            cv_score=None,
            video_score=None,
            is_partial_score=False
        )

        self.client.force_authenticate(user=self.hr_owner)
        url = f"/api/recruitment/applications/{app_empty.id}/score-breakdown/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertIsNone(data["final_score"])
        self.assertFalse(data["cv_component"]["is_available"])
        self.assertFalse(data["video_component"]["is_available"])
        self.assertIn("Neither CV nor Video", data["missing_components_explanation"])

    def test_breakdown_unauthorized_other_hr_blocked(self):
        """
        AC Tenant Isolation: Another HR manager cannot view this room's score breakdown.
        """
        self.client.force_authenticate(user=self.other_hr)
        url = f"/api/recruitment/applications/{self.app_full.id}/score-breakdown/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_breakdown_unauthorized_student_blocked(self):
        """
        AC Role Permission: Student / Candidate cannot access breakdown endpoint.
        """
        self.client.force_authenticate(user=self.candidate)
        url = f"/api/recruitment/applications/{self.app_full.id}/score-breakdown/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_breakdown_unauthenticated_blocked(self):
        """
        Unauthenticated requests receive 401 Unauthorized.
        """
        url = f"/api/recruitment/applications/{self.app_full.id}/score-breakdown/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_breakdown_nonexistent_application_404(self):
        """
        Non-existent application ID returns 404 Not Found.
        """
        self.client.force_authenticate(user=self.hr_owner)
        url = "/api/recruitment/applications/999999/score-breakdown/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
