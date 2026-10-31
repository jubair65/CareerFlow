from rest_framework import status
from rest_framework.test import APITestCase
from apps.authentication.models import User
from apps.recruitment.models import RecruitmentRoom, CandidateApplication
from apps.cv.models import CandidateCV
from apps.presentation.models import PresentationVideo


class CandidateMyApplicationsTests(APITestCase):
    """
    US-43: Candidate "My Applications" Tracking Dashboard
    Tests covering all 6 Acceptance Criteria:
    ✓ AC 1: Candidate can view a list of all their submitted room applications
    ✓ AC 2: Each application displays room title, company/client name, applied date, and current status
    ✓ AC 3: Candidate can click into an application to view submission details and available feedback
    ✓ AC 4: Real-time status changes (Shortlisted, Rejected, Under Review) are displayed accurately
    ✓ AC 5: Empty state is displayed when candidate has not applied to any room
    ✓ AC 6: Access is strictly restricted to candidate's own submitted applications
    """

    def setUp(self):
        self.list_url = "/api/recruitment/applications/my/"
        
        # 1. HR User & Room
        self.hr_user = User.objects.create_user(
            username="hr_recruiter_43",
            email="hr43@company.test",
            password="Password123!",
            role=User.Role.HR_MANAGER
        )
        self.room_1 = RecruitmentRoom.objects.create(
            title="Senior Backend Engineer",
            company_name="Acme Tech",
            department="Engineering",
            role_category="Engineering",
            experience_level="MID",
            description="Build scalable Python microservices.",
            requirements_text="3+ years Django, MySQL, REST APIs.",
            created_by=self.hr_user,
            cv_weight=50,
            video_weight=50
        )
        self.room_2 = RecruitmentRoom.objects.create(
            title="Frontend Specialist",
            company_name="DesignPro Studio",
            department="Product",
            created_by=self.hr_user,
            cv_weight=40,
            video_weight=60
        )

        # 2. Candidate A (Owner)
        self.candidate_a = User.objects.create_user(
            username="candidate_alpha_43",
            email="alpha43@careerflow.test",
            password="Password123!",
            full_name="Candidate Alpha",
            role=User.Role.STUDENT
        )

        # 3. Candidate B (Cross-Tenant User)
        self.candidate_b = User.objects.create_user(
            username="candidate_beta_43",
            email="beta43@careerflow.test",
            password="Password123!",
            full_name="Candidate Beta",
            role=User.Role.STUDENT
        )

        # 4. Applications for Candidate A
        self.cv_a = CandidateCV.objects.create(
            user=self.candidate_a,
            file="students/alpha/resume.pdf",
            original_filename="Alpha_Resume.pdf",
            file_size=204800,
            file_type="pdf"
        )
        self.video_a = PresentationVideo.objects.create(
            user=self.candidate_a,
            file="students/alpha/video.mp4",
            original_filename="Alpha_Pitch.mp4",
            raw_file_size=2048000,
            file_type="mp4",
            duration_seconds=90,
            status="COMPLETED"
        )
        self.app_a1 = CandidateApplication.objects.create(
            room=self.room_1,
            candidate=self.candidate_a,
            cv=self.cv_a,
            video=self.video_a,
            status=CandidateApplication.Status.COMPLETED,
            cv_score=85.0,
            video_score=90.0,
            final_score=87.5,
            is_shortlisted=True,
            shortlist_reason="Top 5% candidate with high score",
            hr_decision=CandidateApplication.HrDecision.CONFIRMED,
            hr_decision_notes="Strong performance in behavioral pitch."
        )

        self.app_a2 = CandidateApplication.objects.create(
            room=self.room_2,
            candidate=self.candidate_a,
            status=CandidateApplication.Status.ANALYZING,
            is_shortlisted=False,
            hr_decision=CandidateApplication.HrDecision.UNDECIDED
        )

        # 5. Application for Candidate B
        self.app_b = CandidateApplication.objects.create(
            room=self.room_1,
            candidate=self.candidate_b,
            status=CandidateApplication.Status.COMPLETED,
            final_score=55.0,
            is_shortlisted=False,
            hr_decision=CandidateApplication.HrDecision.REJECTED
        )

    def test_tc43_01_unauthenticated_access_denied(self):
        """AC 6: Unauthenticated request to /api/recruitment/applications/my/ returns 401."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_tc43_02_empty_state_when_no_applications(self):
        """AC 5: Candidate with no applications receives empty list []."""
        new_candidate = User.objects.create_user(
            username="newbie_candidate",
            email="newbie@careerflow.test",
            password="Password123!",
            role=User.Role.STUDENT
        )
        self.client.force_authenticate(user=new_candidate)
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_tc43_03_list_my_applications_with_metadata(self):
        """AC 1, 2, 4: Candidate A retrieves their applications with room info, status, and badges."""
        self.client.force_authenticate(user=self.candidate_a)
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        app_1_data = next((a for a in response.data if a["id"] == self.app_a1.id), None)
        self.assertIsNotNone(app_1_data)
        self.assertEqual(app_1_data["room_title"], "Senior Backend Engineer")
        self.assertEqual(app_1_data["company_name"], "Acme Tech")
        self.assertEqual(app_1_data["badge"]["label"], "Shortlisted")
        self.assertEqual(app_1_data["badge"]["tone"], "emerald")
        self.assertEqual(app_1_data["final_score"], 87.5)
        self.assertEqual(app_1_data["cv_details"]["original_filename"], "Alpha_Resume.pdf")
        self.assertEqual(app_1_data["video_details"]["duration_seconds"], 90)

    def test_tc43_04_data_isolation_cannot_see_other_candidate(self):
        """AC 6: Candidate A never receives Candidate B's application in list."""
        self.client.force_authenticate(user=self.candidate_a)
        response = self.client.get(self.list_url)

        returned_ids = [a["id"] for a in response.data]
        self.assertIn(self.app_a1.id, returned_ids)
        self.assertIn(self.app_a2.id, returned_ids)
        self.assertNotIn(self.app_b.id, returned_ids)

    def test_tc43_05_application_detail_owner_success(self):
        """AC 3: Candidate can retrieve single application details with full timeline and artifacts."""
        self.client.force_authenticate(user=self.candidate_a)
        detail_url = f"/api/recruitment/applications/my/{self.app_a1.id}/"
        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.app_a1.id)
        self.assertEqual(response.data["room_title"], "Senior Backend Engineer")
        self.assertEqual(response.data["hr_decision"], "CONFIRMED")
        self.assertEqual(response.data["hr_decision_notes"], "Strong performance in behavioral pitch.")
        self.assertIn("stages", response.data)
        self.assertEqual(len(response.data["stages"]), 4)

    def test_tc43_06_application_detail_forbidden_for_other_candidate(self):
        """AC 6: Candidate B receives 403 Forbidden when attempting to view Candidate A's application."""
        self.client.force_authenticate(user=self.candidate_b)
        detail_url = f"/api/recruitment/applications/my/{self.app_a1.id}/"
        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("Access forbidden", response.data.get("detail", ""))

    def test_tc43_07_filter_applications_by_status(self):
        """AC 4: Candidate can filter applications by shortlisted vs review."""
        self.client.force_authenticate(user=self.candidate_a)
        
        # Filter: shortlisted
        response_shortlisted = self.client.get(f"{self.list_url}?status=shortlisted")
        self.assertEqual(response_shortlisted.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_shortlisted.data), 1)
        self.assertEqual(response_shortlisted.data[0]["id"], self.app_a1.id)

        # Filter: review
        response_review = self.client.get(f"{self.list_url}?status=review")
        self.assertEqual(response_review.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_review.data), 1)
        self.assertEqual(response_review.data[0]["id"], self.app_a2.id)

    def test_tc43_08_search_filter_by_keyword(self):
        """Candidate can search applications by room title or company name."""
        self.client.force_authenticate(user=self.candidate_a)
        response = self.client.get(f"{self.list_url}?search=Backend")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.app_a1.id)
