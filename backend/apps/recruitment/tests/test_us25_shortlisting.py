import os
import uuid
from datetime import timedelta
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'careerflow.settings')
django.setup()

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from apps.authentication.models import User
from apps.recruitment.models import RecruitmentRoom, CandidateApplication
from apps.recruitment.services.shortlisting_service import (
    evaluate_room_shortlist,
    validate_shortlisting_criteria,
)
from apps.recruitment.services.scoring_service import calculate_room_applicant_scores


class US25AutomaticShortlistingTests(APITestCase):
    """
    US-25: Automatic Candidate Shortlisting Test Suite (US-25-T7).
    Validates:
    - AC#1: HR can configure shortlisting by minimum score or required candidate count (Top N or Combined).
    - AC#2: Candidates are shortlisted automatically according to the configured criteria.
    - AC#3: Shortlisting criteria are validated with clear error messages.
    - AC#4: Shortlist status is stored for each applicant (in database).
    - AC#5: Shortlist updates correctly when criteria or scores change.
    - AC#6: Shortlisted candidates are clearly shown to HR (with role-based access control).
    """

    def setUp(self):
        self.uid = uuid.uuid4().hex[:8]

        # 1. Primary HR User (Room Owner)
        self.hr_owner = User.objects.create_user(
            username=f"hr_shortlist_{self.uid}",
            email=f"hr_shortlist_{self.uid}@careerflow.demo",
            password="Password123!",
            role=User.Role.HR_MANAGER,
            full_name="Mona HR"
        )

        # 2. Unauthorized HR User (Non-Owner)
        self.other_hr = User.objects.create_user(
            username=f"other_hr_{self.uid}",
            email=f"other_hr_{self.uid}@careerflow.demo",
            password="Password123!",
            role=User.Role.HR_MANAGER,
            full_name="Other HR"
        )

        # 3. Recruitment Room
        self.room = RecruitmentRoom.objects.create(
            title="Senior AI Engineer",
            company_name="DeepMind Tech",
            department="Machine Learning",
            cv_weight=50,
            video_weight=50,
            shortlist_strategy=RecruitmentRoom.ShortlistStrategy.NONE,
            status=RecruitmentRoom.Status.ACTIVE,
            created_by=self.hr_owner
        )

        now = timezone.now()

        # 4. Candidates with distinct scores
        # Cand 1: Final 90.0 (CV: 92.0, Vid: 88.0)
        self.u1 = User.objects.create_user(
            username=f"cand1_{self.uid}", email=f"cand1_{self.uid}@demo.com",
            password="Password123!", role=User.Role.STUDENT, full_name="Alice Wang"
        )
        self.app1 = CandidateApplication.objects.create(
            room=self.room, candidate=self.u1, final_score=90.0,
            cv_score=92.0, video_score=88.0, status=CandidateApplication.Status.COMPLETED
        )
        CandidateApplication.objects.filter(id=self.app1.id).update(applied_at=now - timedelta(days=5))

        # Cand 2: Final 82.0 (CV: 84.0, Vid: 80.0)
        self.u2 = User.objects.create_user(
            username=f"cand2_{self.uid}", email=f"cand2_{self.uid}@demo.com",
            password="Password123!", role=User.Role.STUDENT, full_name="Bob Smith"
        )
        self.app2 = CandidateApplication.objects.create(
            room=self.room, candidate=self.u2, final_score=82.0,
            cv_score=84.0, video_score=80.0, status=CandidateApplication.Status.COMPLETED
        )
        CandidateApplication.objects.filter(id=self.app2.id).update(applied_at=now - timedelta(days=4))

        # Cand 3: Final 74.0 (CV: 76.0, Vid: 72.0)
        self.u3 = User.objects.create_user(
            username=f"cand3_{self.uid}", email=f"cand3_{self.uid}@demo.com",
            password="Password123!", role=User.Role.STUDENT, full_name="Charlie Brown"
        )
        self.app3 = CandidateApplication.objects.create(
            room=self.room, candidate=self.u3, final_score=74.0,
            cv_score=76.0, video_score=72.0, status=CandidateApplication.Status.COMPLETED
        )
        CandidateApplication.objects.filter(id=self.app3.id).update(applied_at=now - timedelta(days=3))

        # Cand 4: Incomplete / Unranked (final_score is None)
        self.u4 = User.objects.create_user(
            username=f"cand4_{self.uid}", email=f"cand4_{self.uid}@demo.com",
            password="Password123!", role=User.Role.STUDENT, full_name="Diana Prince"
        )
        self.app4 = CandidateApplication.objects.create(
            room=self.room, candidate=self.u4, final_score=None,
            cv_score=None, video_score=None, status=CandidateApplication.Status.PENDING
        )
        CandidateApplication.objects.filter(id=self.app4.id).update(applied_at=now - timedelta(days=2))

    # ==========================================
    # AC#1: Criteria Configuration via API
    # ==========================================
    def test_configure_shortlist_criteria_min_score(self):
        """HR can configure shortlisting by minimum score threshold."""
        self.client.force_authenticate(user=self.hr_owner)
        url = f"/api/recruitment/rooms/{self.room.id}/shortlist-criteria/"
        payload = {
            "shortlist_strategy": "MIN_SCORE",
            "shortlist_min_score": 80.0,
        }
        res = self.client.patch(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["criteria"]["shortlist_strategy"], "MIN_SCORE")
        self.assertEqual(res.data["criteria"]["shortlist_min_score"], 80.0)

        # Database verification (US-25-T5)
        self.room.refresh_from_db()
        self.assertEqual(self.room.shortlist_strategy, "MIN_SCORE")
        self.assertEqual(self.room.shortlist_min_score, 80.0)

    def test_configure_shortlist_criteria_top_n(self):
        """HR can configure shortlisting by required candidate count (Top N)."""
        self.client.force_authenticate(user=self.hr_owner)
        url = f"/api/recruitment/rooms/{self.room.id}/shortlist-criteria/"
        payload = {
            "shortlist_strategy": "TOP_N",
            "shortlist_top_n": 2,
        }
        res = self.client.patch(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["criteria"]["shortlist_strategy"], "TOP_N")
        self.assertEqual(res.data["criteria"]["shortlist_top_n"], 2)

        self.room.refresh_from_db()
        self.assertEqual(self.room.shortlist_strategy, "TOP_N")
        self.assertEqual(self.room.shortlist_top_n, 2)

    def test_configure_shortlist_criteria_combined(self):
        """HR can configure shortlisting with combined criteria (Top N + Min Score)."""
        self.client.force_authenticate(user=self.hr_owner)
        url = f"/api/recruitment/rooms/{self.room.id}/shortlist-criteria/"
        payload = {
            "shortlist_strategy": "COMBINED",
            "shortlist_min_score": 75.0,
            "shortlist_top_n": 3,
        }
        res = self.client.patch(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["criteria"]["shortlist_strategy"], "COMBINED")
        self.assertEqual(res.data["criteria"]["shortlist_min_score"], 75.0)
        self.assertEqual(res.data["criteria"]["shortlist_top_n"], 3)

    # ==========================================
    # AC#3: Validation with Clear Error Messages
    # ==========================================
    def test_validation_invalid_strategy(self):
        """Invalid shortlisting strategy is rejected with clear error."""
        self.client.force_authenticate(user=self.hr_owner)
        url = f"/api/recruitment/rooms/{self.room.id}/shortlist-criteria/"
        res = self.client.patch(url, {"shortlist_strategy": "MAGIC_AI"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("shortlist_strategy", str(res.data))

    def test_validation_min_score_out_of_range(self):
        """Min score below 0 or above 100 is rejected with clear error."""
        self.client.force_authenticate(user=self.hr_owner)
        url = f"/api/recruitment/rooms/{self.room.id}/shortlist-criteria/"

        res_neg = self.client.patch(url, {"shortlist_strategy": "MIN_SCORE", "shortlist_min_score": -5.0}, format="json")
        self.assertEqual(res_neg.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("shortlist_min_score", str(res_neg.data))

        res_over = self.client.patch(url, {"shortlist_strategy": "MIN_SCORE", "shortlist_min_score": 105.0}, format="json")
        self.assertEqual(res_over.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("shortlist_min_score", str(res_over.data))

    def test_validation_top_n_invalid(self):
        """Top N count of zero or negative is rejected with clear error."""
        self.client.force_authenticate(user=self.hr_owner)
        url = f"/api/recruitment/rooms/{self.room.id}/shortlist-criteria/"

        res_zero = self.client.patch(url, {"shortlist_strategy": "TOP_N", "shortlist_top_n": 0}, format="json")
        self.assertEqual(res_zero.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("shortlist_top_n", str(res_zero.data))

    def test_validation_missing_required_fields(self):
        """Strategy requires corresponding fields, else clear error message."""
        self.client.force_authenticate(user=self.hr_owner)
        url = f"/api/recruitment/rooms/{self.room.id}/shortlist-criteria/"

        # MIN_SCORE without min_score
        res = self.client.patch(url, {"shortlist_strategy": "MIN_SCORE"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("shortlist_min_score", str(res.data))

        # TOP_N without top_n
        res = self.client.patch(url, {"shortlist_strategy": "TOP_N"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("shortlist_top_n", str(res.data))

    # ==========================================
    # AC#2 & AC#4: Automatic Shortlisting Logic & DB Persistence
    # ==========================================
    def test_automatic_shortlisting_min_score_logic(self):
        """Candidates with score >= min_score are shortlisted and stored in DB."""
        self.room.shortlist_strategy = RecruitmentRoom.ShortlistStrategy.MIN_SCORE
        self.room.shortlist_min_score = 80.0
        self.room.save(update_fields=['shortlist_strategy', 'shortlist_min_score'])

        result = evaluate_room_shortlist(self.room, persist=True)

        self.assertEqual(result["shortlisted_count"], 2)  # app1 (90.0) and app2 (82.0)
        self.assertEqual(result["total_applicants"], 4)

        # Check DB persistence (AC#4)
        self.app1.refresh_from_db()
        self.app2.refresh_from_db()
        self.app3.refresh_from_db()
        self.app4.refresh_from_db()

        self.assertTrue(self.app1.is_shortlisted)
        self.assertIn("80.0", self.app1.shortlist_reason)
        self.assertIsNotNone(self.app1.shortlisted_at)

        self.assertTrue(self.app2.is_shortlisted)
        self.assertIn("80.0", self.app2.shortlist_reason)
        self.assertIsNotNone(self.app2.shortlisted_at)

        self.assertFalse(self.app3.is_shortlisted)  # 74.0 < 80.0
        self.assertIn("Below minimum", self.app3.shortlist_reason)
        self.assertIsNone(self.app3.shortlisted_at)

        self.assertFalse(self.app4.is_shortlisted)  # Incomplete / Unranked
        self.assertIn("Pending", self.app4.shortlist_reason)
        self.assertIsNone(self.app4.shortlisted_at)

    def test_automatic_shortlisting_top_n_logic(self):
        """Top N ranked candidates are shortlisted based on score ranking."""
        self.room.shortlist_strategy = RecruitmentRoom.ShortlistStrategy.TOP_N
        self.room.shortlist_top_n = 2
        self.room.save(update_fields=['shortlist_strategy', 'shortlist_top_n'])

        result = evaluate_room_shortlist(self.room, persist=True)
        self.assertEqual(result["shortlisted_count"], 2)

        self.app1.refresh_from_db()
        self.app2.refresh_from_db()
        self.app3.refresh_from_db()

        self.assertTrue(self.app1.is_shortlisted)
        self.assertIn("Ranked #1", self.app1.shortlist_reason)

        self.assertTrue(self.app2.is_shortlisted)
        self.assertIn("Ranked #2", self.app2.shortlist_reason)

        self.assertFalse(self.app3.is_shortlisted)
        self.assertIn("outside required top 2", self.app3.shortlist_reason)

    def test_automatic_shortlisting_combined_logic(self):
        """Combined criteria: shortlisted candidates must satisfy score threshold within Top N quota."""
        self.room.shortlist_strategy = RecruitmentRoom.ShortlistStrategy.COMBINED
        self.room.shortlist_min_score = 80.0
        self.room.shortlist_top_n = 1  # only top 1 meeting 80.0
        self.room.save(update_fields=['shortlist_strategy', 'shortlist_min_score', 'shortlist_top_n'])

        result = evaluate_room_shortlist(self.room, persist=True)
        self.assertEqual(result["shortlisted_count"], 1)

        self.app1.refresh_from_db()
        self.app2.refresh_from_db()
        self.app3.refresh_from_db()

        self.assertTrue(self.app1.is_shortlisted)  # 90.0 >= 80 and top 1
        self.assertFalse(self.app2.is_shortlisted)  # 82.0 >= 80 but rank 2 exceeds top 1
        self.assertIn("exceeds top 1 quota", self.app2.shortlist_reason)
        self.assertFalse(self.app3.is_shortlisted)  # 74.0 < 80

    def test_disabled_strategy_resets_shortlist(self):
        """Setting strategy to NONE clears shortlisted status."""
        # First shortlist candidates
        self.room.shortlist_strategy = RecruitmentRoom.ShortlistStrategy.MIN_SCORE
        self.room.shortlist_min_score = 80.0
        self.room.save(update_fields=['shortlist_strategy', 'shortlist_min_score'])
        evaluate_room_shortlist(self.room, persist=True)

        self.app1.refresh_from_db()
        self.assertTrue(self.app1.is_shortlisted)

        # Now disable shortlisting
        self.room.shortlist_strategy = RecruitmentRoom.ShortlistStrategy.NONE
        self.room.save(update_fields=['shortlist_strategy'])
        evaluate_room_shortlist(self.room, persist=True)

        self.app1.refresh_from_db()
        self.assertFalse(self.app1.is_shortlisted)
        self.assertIn("disabled", self.app1.shortlist_reason)

    # ==========================================
    # AC#5: Shortlist Updates when Criteria or Scores Change
    # ==========================================
    def test_shortlist_updates_on_criteria_patch(self):
        """Updating criteria via API triggers automatic recalculation."""
        self.client.force_authenticate(user=self.hr_owner)
        url = f"/api/recruitment/rooms/{self.room.id}/shortlist-criteria/"

        # Set threshold to 85.0 -> only app1 (90.0) should be shortlisted
        res = self.client.patch(url, {"shortlist_strategy": "MIN_SCORE", "shortlist_min_score": 85.0}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["shortlist_summary"]["shortlisted_count"], 1)

        self.app1.refresh_from_db()
        self.app2.refresh_from_db()
        self.assertTrue(self.app1.is_shortlisted)
        self.assertFalse(self.app2.is_shortlisted)

        # Lower threshold to 70.0 -> app1, app2, app3 should all be shortlisted
        res2 = self.client.patch(url, {"shortlist_strategy": "MIN_SCORE", "shortlist_min_score": 70.0}, format="json")
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertEqual(res2.data["shortlist_summary"]["shortlisted_count"], 3)

        self.app1.refresh_from_db()
        self.app2.refresh_from_db()
        self.app3.refresh_from_db()
        self.assertTrue(self.app1.is_shortlisted)
        self.assertTrue(self.app2.is_shortlisted)
        self.assertTrue(self.app3.is_shortlisted)

    def test_shortlist_updates_on_score_calculation(self):
        """When room scores are recalculated, active shortlist is refreshed."""
        self.room.shortlist_strategy = RecruitmentRoom.ShortlistStrategy.MIN_SCORE
        self.room.shortlist_min_score = 80.0
        self.room.save(update_fields=['shortlist_strategy', 'shortlist_min_score'])

        # Update candidate 3 scores so final score changes from 74.0 to 86.0
        self.app3.cv_score = 86.0
        self.app3.video_score = 86.0
        self.app3.save(update_fields=['cv_score', 'video_score'])

        calculate_room_applicant_scores(self.room)

        self.app3.refresh_from_db()
        self.assertEqual(self.app3.final_score, 86.0)
        self.assertTrue(self.app3.is_shortlisted)  # Now shortlisted!

    # ==========================================
    # AC#6: Shortlisted Candidates Shown to HR & Access Control
    # ==========================================
    def test_get_shortlisted_applicants_endpoint(self):
        """HR Room Owner can retrieve shortlisted candidates via API."""
        self.room.shortlist_strategy = RecruitmentRoom.ShortlistStrategy.TOP_N
        self.room.shortlist_top_n = 2
        self.room.save()
        evaluate_room_shortlist(self.room, persist=True)

        self.client.force_authenticate(user=self.hr_owner)
        url = f"/api/recruitment/rooms/{self.room.id}/shortlisted-applicants/"
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["shortlisted_count"], 2)
        self.assertEqual(len(res.data["shortlisted_applicants"]), 2)
        self.assertEqual(res.data["shortlisted_applicants"][0]["candidate_name"], "Alice Wang")
        self.assertTrue(res.data["shortlisted_applicants"][0]["is_shortlisted"])

    def test_shortlisted_applicants_access_control(self):
        """Unauthorized HR manager cannot view another HR manager's room shortlist."""
        self.client.force_authenticate(user=self.other_hr)
        url = f"/api/recruitment/rooms/{self.room.id}/shortlisted-applicants/"
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
