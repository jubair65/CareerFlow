import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'careerflow.settings')
django.setup()

from rest_framework import status
from rest_framework.test import APITestCase
from apps.authentication.models import User
from apps.recruitment.models import RecruitmentRoom, CandidateApplication
from apps.cv.models import CandidateCV, ParsedCV, JobRequirement, CVJobMatch


class US10ApplicantCVScoresAPITests(APITestCase):
    """
    US-10: View Applicant CV Match Scores Unit Tests (US-10-T7)
    Verifies that HR Managers can view applicants' CV match scores,
    inspect matched and missing skill breakdowns, access is restricted
    to room owners only, and missing CVs are handled gracefully.
    """

    def setUp(self):
        # 1. Primary HR User (Room Owner)
        self.hr_owner = User.objects.create_user(
            username="hr_owner_us10@careerflow.demo",
            email="hr_owner_us10@careerflow.demo",
            password="Password123!",
            role=User.Role.HR_MANAGER,
            full_name="Fatima Al-Sayed"
        )

        # 2. Other HR User (Non-owner)
        self.other_hr = User.objects.create_user(
            username="other_hr_us10@careerflow.demo",
            email="other_hr_us10@careerflow.demo",
            password="Password123!",
            role=User.Role.HR_MANAGER,
            full_name="Marcus Vance"
        )

        # 3. Candidate / Student Users
        self.candidate_alice = User.objects.create_user(
            username="alice_candidate@careerflow.demo",
            email="alice_candidate@careerflow.demo",
            password="Password123!",
            role=User.Role.STUDENT,
            full_name="Alice Candidate"
        )
        self.candidate_bob = User.objects.create_user(
            username="bob_candidate@careerflow.demo",
            email="bob_candidate@careerflow.demo",
            password="Password123!",
            role=User.Role.STUDENT,
            full_name="Bob Candidate"
        )
        self.candidate_charlie = User.objects.create_user(
            username="charlie_candidate@careerflow.demo",
            email="charlie_candidate@careerflow.demo",
            password="Password123!",
            role=User.Role.STUDENT,
            full_name="Charlie NoCV"
        )

        # 4. Recruitment Room owned by hr_owner
        self.room = RecruitmentRoom.objects.create(
            title="Senior React Architect",
            company_name="Apex Cloud Systems",
            department="Frontend Engineering",
            description="Leading architecture for scalable web clients.",
            status=RecruitmentRoom.Status.ACTIVE,
            requirements_text="Must have deep mastery of React, TypeScript, and Redux. Experience with Docker is required.",
            skills_required=["React", "TypeScript", "Redux", "Docker"],
            cv_weight=60,
            video_weight=40,
            created_by=self.hr_owner
        )

        # 5. Alice's CV and match record
        self.alice_cv = CandidateCV.objects.create(
            user=self.candidate_alice,
            file="students/alice/test_resume.pdf",
            original_filename="Alice_Resume_React_Expert.pdf",
            file_size=204800,
            file_type="pdf",
            is_active=True
        )
        self.alice_parsed = ParsedCV.objects.create(
            cv=self.alice_cv,
            raw_text="Senior React and TypeScript developer with 6 years experience. Expert in Redux architecture.",
            skills=["React", "TypeScript", "Redux"],
            education=[{"degree": "B.Sc. CSE", "institution": "BUET", "year": "2020"}],
            experience=[{"title": "Senior Engineer", "company": "Tech", "duration_years": 4}]
        )
        self.alice_match = CVJobMatch.objects.create(
            cv=self.alice_cv,
            job_title=self.room.title,
            company=self.room.company_name,
            job_description=self.room.description,
            match_score=88,
            keyword_coverage=75,
            category_scores={"domain_craft": 90, "collaboration": 85, "leadership": 80, "accessibility": 70},
            skills_matched=["React", "TypeScript", "Redux"],
            skills_missing=["Docker"],
            strengths=["Strong overlap in core technical skills: React, TypeScript, Redux"],
            gaps=["Missing required skill: Docker"],
            recommendations=["Highlight containerization and Docker deployment experience"]
        )

        # 6. Bob's CV and match record
        self.bob_cv = CandidateCV.objects.create(
            user=self.candidate_bob,
            file="students/bob/bob_cv.pdf",
            original_filename="Bob_Junior_Frontend.pdf",
            file_size=150000,
            file_type="pdf",
            is_active=True
        )
        self.bob_match = CVJobMatch.objects.create(
            cv=self.bob_cv,
            job_title=self.room.title,
            company=self.room.company_name,
            job_description=self.room.description,
            match_score=55,
            keyword_coverage=25,
            category_scores={"domain_craft": 60, "collaboration": 65, "leadership": 50, "accessibility": 50},
            skills_matched=["React"],
            skills_missing=["TypeScript", "Redux", "Docker"],
            strengths=["Familiar with basic React workflows"],
            gaps=["Missing TypeScript, Redux, Docker"],
            recommendations=["Gain production TypeScript and state management experience"]
        )

        # 7. Candidate Applications for the Room
        self.app_alice = CandidateApplication.objects.create(
            room=self.room,
            candidate=self.candidate_alice,
            cv=self.alice_cv,
            status=CandidateApplication.Status.COMPLETED
        )
        self.app_bob = CandidateApplication.objects.create(
            room=self.room,
            candidate=self.candidate_bob,
            cv=self.bob_cv,
            status=CandidateApplication.Status.COMPLETED
        )
        # Charlie applies without a CV document
        self.app_charlie = CandidateApplication.objects.create(
            room=self.room,
            candidate=self.candidate_charlie,
            cv=None,
            status=CandidateApplication.Status.PENDING
        )

        self.cv_scores_url = f"/api/recruitment/rooms/{self.room.id}/cv-scores/"
        self.applicant_cv_scores_alias_url = f"/api/recruitment/rooms/{self.room.id}/applicant-cv-scores/"

    def test_get_cv_scores_as_room_owner_success(self):
        """HR Manager who owns the Room can view applicants' CV match scores (US-10-T2 & AC#1, AC#4)."""
        self.client.force_authenticate(user=self.hr_owner)
        response = self.client.get(self.cv_scores_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        self.assertEqual(data["room_id"], self.room.id)
        self.assertEqual(data["room_title"], self.room.title)
        self.assertEqual(data["company_name"], self.room.company_name)
        self.assertEqual(data["total_applicants"], 3)
        self.assertEqual(data["scored_applicants"], 2)
        self.assertAlmostEqual(data["average_cv_score"], 71.5, places=1)
        self.assertEqual(data["highest_cv_score"], 88)
        self.assertEqual(data["lowest_cv_score"], 55)

        # Verify results list contains all applicants
        self.assertEqual(len(data["results"]), 3)

        # Locate Alice's result
        alice_result = next((r for r in data["results"] if r["candidate_id"] == self.candidate_alice.id), None)
        self.assertIsNotNone(alice_result)
        self.assertEqual(alice_result["match_score"], 88)
        self.assertEqual(alice_result["keyword_coverage"], 75)
        self.assertTrue(alice_result["has_cv"])
        self.assertTrue(alice_result["has_score"])
        self.assertEqual(alice_result["skills_matched"], ["React", "TypeScript", "Redux"])
        self.assertEqual(alice_result["skills_missing"], ["Docker"])
        self.assertEqual(alice_result["category_scores"]["domain_craft"], 90)

    def test_alias_endpoint_applicant_cv_scores(self):
        """Alias endpoint /applicant-cv-scores/ returns identical score payload."""
        self.client.force_authenticate(user=self.hr_owner)
        response = self.client.get(self.applicant_cv_scores_alias_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["room_id"], self.room.id)
        self.assertEqual(response.data["total_applicants"], 3)

    def test_applicant_without_cv_handled_gracefully(self):
        """Applicants without a CV score are handled gracefully without errors (AC#5)."""
        self.client.force_authenticate(user=self.hr_owner)
        response = self.client.get(self.cv_scores_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        charlie_result = next((r for r in data["results"] if r["candidate_id"] == self.candidate_charlie.id), None)
        self.assertIsNotNone(charlie_result)
        self.assertFalse(charlie_result["has_cv"])
        self.assertFalse(charlie_result["has_score"])
        self.assertIsNone(charlie_result["match_score"])
        self.assertEqual(charlie_result["keyword_coverage"], 0)
        self.assertEqual(charlie_result["skills_matched"], [])
        self.assertIn("No CV document uploaded", charlie_result["gaps"][0])

    def test_single_applicant_cv_score_detail(self):
        """HR can view detailed CV score and skill breakdown for a single candidate (US-10-T4 & AC#2)."""
        self.client.force_authenticate(user=self.hr_owner)
        detail_url = f"/api/recruitment/rooms/{self.room.id}/cv-scores/{self.app_alice.id}/"
        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(data["application_id"], self.app_alice.id)
        self.assertEqual(data["candidate_name"], "Alice Candidate")
        self.assertEqual(data["match_score"], 88)
        self.assertEqual(data["skills_matched"], ["React", "TypeScript", "Redux"])
        self.assertEqual(data["skills_missing"], ["Docker"])
        self.assertIn("domain_craft", data["category_scores"])

    def test_single_applicant_cv_score_not_found(self):
        """Non-existent application in room returns 404."""
        self.client.force_authenticate(user=self.hr_owner)
        detail_url = f"/api/recruitment/rooms/{self.room.id}/cv-scores/99999/"
        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_user_cannot_view_scores(self):
        """Unauthenticated requests are rejected (AC#3 & US-10-T5)."""
        response = self.client.get(self.cv_scores_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_student_user_cannot_view_scores(self):
        """Student candidates cannot view applicant CV scores (US-10-T5)."""
        self.client.force_authenticate(user=self.candidate_alice)
        response = self.client.get(self.cv_scores_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_other_hr_cannot_view_scores_of_another_room(self):
        """Only the HR Manager who owns the Room can view its scores (AC#3 & US-10-T5)."""
        self.client.force_authenticate(user=self.other_hr)
        response = self.client.get(self.cv_scores_url)
        # Returns 404 since get_queryset filters by created_by=request.user
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_search_filter_by_candidate_name_or_skill(self):
        """HR can filter applicants by candidate name or matching skill."""
        self.client.force_authenticate(user=self.hr_owner)

        # Search by candidate name
        res_name = self.client.get(f"{self.cv_scores_url}?search=alice")
        self.assertEqual(res_name.status_code, status.HTTP_200_OK)
        self.assertEqual(res_name.data["total_applicants"], 1)
        self.assertEqual(res_name.data["results"][0]["candidate_name"], "Alice Candidate")

        # Search by skill (Redux is matched by Alice, not Bob or Charlie)
        res_skill = self.client.get(f"{self.cv_scores_url}?search=redux")
        self.assertEqual(res_skill.status_code, status.HTTP_200_OK)
        self.assertEqual(res_skill.data["total_applicants"], 1)
        self.assertEqual(res_skill.data["results"][0]["candidate_name"], "Alice Candidate")

    def test_min_score_filter(self):
        """HR can filter applicants by minimum CV match score."""
        self.client.force_authenticate(user=self.hr_owner)

        # min_score = 80: Alice has 88, Bob has 55, Charlie has None
        res_score = self.client.get(f"{self.cv_scores_url}?min_score=80")
        self.assertEqual(res_score.status_code, status.HTTP_200_OK)
        self.assertEqual(res_score.data["total_applicants"], 1)
        self.assertEqual(res_score.data["results"][0]["match_score"], 88)
