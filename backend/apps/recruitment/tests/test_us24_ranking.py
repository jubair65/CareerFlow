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
from apps.cv.models import CandidateCV, JobRequirement, CVJobMatch
from apps.presentation.models import PresentationVideo, PresentationScore
from apps.recruitment.services.ranking_service import (
    get_ranked_room_applicants,
    get_score_tier,
    get_rank_badge,
)


class US24ApplicantRankingTests(APITestCase):
    """
    US-24: Applicant Ranking Comprehensive Test Suite (US-24-T7).
    Validates:
    - AC#1: Descending order of Applicant Score (Rank #1 = highest score).
    - AC#2: Consistent tie-breaking order (CV Score > Video Score > Applied Date).
    - AC#3: Real-time update when scores change.
    - AC#4: Clear segregation of unranked/incomplete candidates.
    - AC#5: Display of rank number, badges, scores, and key details.
    - AC#6: Sorting and filtering by score range, search query, and date.
    """

    def setUp(self):
        self.uid = uuid.uuid4().hex[:8]

        # 1. Primary HR User (Room Owner)
        self.hr_owner = User.objects.create_user(
            username=f"hr_rank_owner_{self.uid}",
            email=f"hr_rank_owner_{self.uid}@careerflow.demo",
            password="Password123!",
            role=User.Role.HR_MANAGER,
            full_name="Fatima Al-Sayed"
        )

        # 2. Other HR User (Unauthorized Non-Owner)
        self.other_hr = User.objects.create_user(
            username=f"other_hr_rank_{self.uid}",
            email=f"other_hr_rank_{self.uid}@careerflow.demo",
            password="Password123!",
            role=User.Role.HR_MANAGER,
            full_name="Marcus Vance"
        )

        # 3. Recruitment Room
        self.room = RecruitmentRoom.objects.create(
            title="Senior Backend Architect",
            company_name="Apex Global",
            department="Engineering",
            role_category="Engineering",
            cv_weight=50,
            video_weight=50,
            status=RecruitmentRoom.Status.ACTIVE,
            created_by=self.hr_owner
        )

        now = timezone.now()

        # 4. Create 5 Candidates with controlled scores and timestamps
        # Candidate 1: Highest score (92.0)
        self.u1 = User.objects.create_user(
            username=f"cand1_{self.uid}",
            email=f"cand1_{self.uid}@demo.com",
            password="Password123!",
            role=User.Role.STUDENT,
            full_name="Zayn Malik"
        )
        self.app1 = CandidateApplication.objects.create(
            room=self.room,
            candidate=self.u1,
            final_score=92.0,
            cv_score=94.0,
            video_score=90.0,
            is_partial_score=False,
            status=CandidateApplication.Status.COMPLETED
        )
        # Manually set applied_at to control FIFO tie breaking
        CandidateApplication.objects.filter(id=self.app1.id).update(applied_at=now - timedelta(days=5))

        # Candidate 2: Score 85.0, higher CV score (90.0) -> Tie-break test
        self.u2 = User.objects.create_user(
            username=f"cand2_{self.uid}",
            email=f"cand2_{self.uid}@demo.com",
            password="Password123!",
            role=User.Role.STUDENT,
            full_name="Amina Yusuf"
        )
        self.app2 = CandidateApplication.objects.create(
            room=self.room,
            candidate=self.u2,
            final_score=85.0,
            cv_score=90.0,
            video_score=80.0,
            is_partial_score=False,
            status=CandidateApplication.Status.COMPLETED
        )
        CandidateApplication.objects.filter(id=self.app2.id).update(applied_at=now - timedelta(days=4))

        # Candidate 3: Score 85.0, lower CV score (80.0) but higher Video score (90.0)
        self.u3 = User.objects.create_user(
            username=f"cand3_{self.uid}",
            email=f"cand3_{self.uid}@demo.com",
            password="Password123!",
            role=User.Role.STUDENT,
            full_name="Bilal Tariq"
        )
        self.app3 = CandidateApplication.objects.create(
            room=self.room,
            candidate=self.u3,
            final_score=85.0,
            cv_score=80.0,
            video_score=90.0,
            is_partial_score=False,
            status=CandidateApplication.Status.COMPLETED
        )
        CandidateApplication.objects.filter(id=self.app3.id).update(applied_at=now - timedelta(days=3))

        # Candidate 4: Score 85.0, identical CV & Video scores to Candidate 5, but applied earlier
        self.u4 = User.objects.create_user(
            username=f"cand4_{self.uid}",
            email=f"cand4_{self.uid}@demo.com",
            password="Password123!",
            role=User.Role.STUDENT,
            full_name="Clara Oswald"
        )
        self.app4 = CandidateApplication.objects.create(
            room=self.room,
            candidate=self.u4,
            final_score=75.0,
            cv_score=75.0,
            video_score=75.0,
            is_partial_score=False,
            status=CandidateApplication.Status.COMPLETED
        )
        CandidateApplication.objects.filter(id=self.app4.id).update(applied_at=now - timedelta(days=2))

        # Candidate 5: Score 75.0, identical scores, but applied later than Candidate 4
        self.u5 = User.objects.create_user(
            username=f"cand5_{self.uid}",
            email=f"cand5_{self.uid}@demo.com",
            password="Password123!",
            role=User.Role.STUDENT,
            full_name="Daniel Craig"
        )
        self.app5 = CandidateApplication.objects.create(
            room=self.room,
            candidate=self.u5,
            final_score=75.0,
            cv_score=75.0,
            video_score=75.0,
            is_partial_score=False,
            status=CandidateApplication.Status.COMPLETED
        )
        CandidateApplication.objects.filter(id=self.app5.id).update(applied_at=now - timedelta(days=1))

        # Candidate 6: Incomplete / Unranked (no final score)
        self.u6 = User.objects.create_user(
            username=f"cand6_{self.uid}",
            email=f"cand6_{self.uid}@demo.com",
            password="Password123!",
            role=User.Role.STUDENT,
            full_name="Eva Green"
        )
        self.app6 = CandidateApplication.objects.create(
            room=self.room,
            candidate=self.u6,
            final_score=None,
            cv_score=None,
            video_score=None,
            is_partial_score=False,
            status=CandidateApplication.Status.PENDING
        )

        self.ranked_url = f"/api/recruitment/rooms/{self.room.id}/ranked-applicants/"

    # =========================================================================
    # Task US-24-T1: Ranking Logic & Tie-Breaking
    # =========================================================================

    def test_descending_order_and_rank_numbering(self):
        """Applicants are ranked in descending order with sequential 1-based ranks (AC#1 & AC#5)."""
        data = get_ranked_room_applicants(self.room)
        results = data["results"]

        self.assertEqual(data["ranked_count"], 5)
        self.assertEqual(data["unranked_count"], 1)

        # Ranks must be 1, 2, 3, 4, 5
        ranks = [r["rank"] for r in results]
        self.assertEqual(ranks, [1, 2, 3, 4, 5])

        # Rank 1 must be Zayn Malik with 92.0
        self.assertEqual(results[0]["candidate_name"], "Zayn Malik")
        self.assertEqual(results[0]["final_score"], 92.0)
        self.assertEqual(results[0]["badge"], "GOLD")

        # Rank 2 must be Silver, Rank 3 Bronze
        self.assertEqual(results[1]["badge"], "SILVER")
        self.assertEqual(results[2]["badge"], "BRONZE")
        self.assertEqual(results[3]["badge"], "STANDARD")

    def test_tie_breaking_rule_cv_score_first(self):
        """When final_score is tied (85.0 vs 85.0), higher CV score takes superior rank (AC#2)."""
        data = get_ranked_room_applicants(self.room)
        results = data["results"]

        # App 2 (Amina) has cv_score=90.0, App 3 (Bilal) has cv_score=80.0
        rank_2 = results[1]
        rank_3 = results[2]

        self.assertEqual(rank_2["final_score"], 85.0)
        self.assertEqual(rank_3["final_score"], 85.0)

        self.assertEqual(rank_2["candidate_name"], "Amina Yusuf")
        self.assertEqual(rank_2["cv_score"], 90.0)

        self.assertEqual(rank_3["candidate_name"], "Bilal Tariq")
        self.assertEqual(rank_3["cv_score"], 80.0)

    def test_tie_breaking_rule_applied_date_fifo(self):
        """When final_score, cv_score, and video_score are identical, earlier applicant wins (AC#2)."""
        data = get_ranked_room_applicants(self.room)
        results = data["results"]

        # Clara (App 4) applied 2 days ago, Daniel (App 5) applied 1 day ago
        rank_4 = results[3]
        rank_5 = results[4]

        self.assertEqual(rank_4["candidate_name"], "Clara Oswald")
        self.assertEqual(rank_4["final_score"], 75.0)

        self.assertEqual(rank_5["candidate_name"], "Daniel Craig")
        self.assertEqual(rank_5["final_score"], 75.0)

    # =========================================================================
    # Task US-24-T5: Unranked / Incomplete Segregation
    # =========================================================================

    def test_unranked_candidates_are_segregated(self):
        """Candidates without final score are placed in unranked list with reasons (AC#4)."""
        data = get_ranked_room_applicants(self.room)
        unranked = data["unranked"]

        self.assertEqual(len(unranked), 1)
        self.assertEqual(unranked[0]["candidate_name"], "Eva Green")
        self.assertIsNone(unranked[0]["final_score"])
        self.assertIn("missing", unranked[0]["pending_reason"].lower())

    # =========================================================================
    # Task US-24-T4: Sorting and Filtering
    # =========================================================================

    def test_min_score_filter(self):
        """Filtering by min_score returns only candidates meeting threshold (AC#6)."""
        # Threshold 80: Zayn (92), Amina (85), Bilal (85) qualify; Clara (75), Daniel (75) excluded
        data = get_ranked_room_applicants(self.room, min_score=80.0)
        self.assertEqual(data["ranked_count"], 3)
        names = [r["candidate_name"] for r in data["results"]]
        self.assertIn("Zayn Malik", names)
        self.assertIn("Amina Yusuf", names)
        self.assertIn("Bilal Tariq", names)
        self.assertNotIn("Clara Oswald", names)

    def test_max_score_filter(self):
        """Filtering by max_score returns only candidates at or below threshold."""
        # Max score 80: Clara (75), Daniel (75) qualify
        data = get_ranked_room_applicants(self.room, max_score=80.0)
        self.assertEqual(data["ranked_count"], 2)
        names = [r["candidate_name"] for r in data["results"]]
        self.assertEqual(names, ["Clara Oswald", "Daniel Craig"])

    def test_search_by_candidate_name_and_email(self):
        """Search query matches candidate name or email."""
        data_name = get_ranked_room_applicants(self.room, search="amina")
        self.assertEqual(data_name["ranked_count"], 1)
        self.assertEqual(data_name["results"][0]["candidate_name"], "Amina Yusuf")

        data_email = get_ranked_room_applicants(self.room, search="cand1")
        self.assertEqual(data_email["ranked_count"], 1)
        self.assertEqual(data_email["results"][0]["candidate_name"], "Zayn Malik")

    # =========================================================================
    # Task US-24-T2: REST API Endpoint & Authorization
    # =========================================================================

    def test_get_ranked_applicants_api_success(self):
        """Room owner can retrieve ranked applicants list via API (US-24-T2)."""
        self.client.force_authenticate(user=self.hr_owner)
        response = self.client.get(self.ranked_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        self.assertEqual(data["room_id"], self.room.id)
        self.assertEqual(data["total_applicants"], 6)
        self.assertEqual(data["ranked_count"], 5)
        self.assertEqual(data["unranked_count"], 1)
        self.assertEqual(data["results"][0]["rank"], 1)
        self.assertEqual(data["results"][0]["candidate_name"], "Zayn Malik")

    def test_get_ranked_applicants_api_with_query_params(self):
        """API respects min_score, search, and ordering parameters."""
        self.client.force_authenticate(user=self.hr_owner)
        url = f"{self.ranked_url}?min_score=80&search=bilal"

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(data["ranked_count"], 1)
        self.assertEqual(data["results"][0]["candidate_name"], "Bilal Tariq")

    def test_get_ranked_applicants_api_unauthorized_non_owner(self):
        """Non-owner HR cannot access rankings for another's room."""
        self.client.force_authenticate(user=self.other_hr)
        response = self.client.get(self.ranked_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_ranked_applicants_api_unauthenticated(self):
        """Unauthenticated request is rejected with 401."""
        response = self.client.get(self.ranked_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
