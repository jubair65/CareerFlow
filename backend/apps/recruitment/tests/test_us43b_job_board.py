from datetime import timedelta
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from apps.authentication.models import User
from apps.recruitment.models import (
    RecruitmentRoom,
    CandidateApplication,
)
from apps.cv.models import CandidateCV
from apps.presentation.models import PresentationVideo


class JobBoardPublicRoomsTests(APITestCase):
    """
    US-43B-T8: Unit tests for public rooms API endpoint, tenant isolation, and annotation.
    Target endpoint: /api/recruitment/rooms/public/
    """

    def setUp(self):
        # 1. HR Manager (Room Owner)
        self.hr_user = User.objects.create_user(
            username="hr_mona_43b",
            email="hr_mona_43b@careerflow.test",
            password="Password123!",
            full_name="Jannatun Naeem Mona",
            role=User.Role.HR_MANAGER
        )

        # 2. Candidate Alpha (Applied to Room 1)
        self.candidate_alpha = User.objects.create_user(
            username="candidate_alpha_43b",
            email="alpha43b@careerflow.test",
            password="Password123!",
            full_name="Candidate Alpha",
            role=User.Role.STUDENT
        )

        # 3. Candidate Beta (Not applied to Room 1)
        self.candidate_beta = User.objects.create_user(
            username="candidate_beta_43b",
            email="beta43b@careerflow.test",
            password="Password123!",
            full_name="Candidate Beta",
            role=User.Role.STUDENT
        )

        now = timezone.now()

        # 4. Open Active Room 1 (Senior Full Stack, Acme Corp)
        self.room_open_1 = RecruitmentRoom.objects.create(
            title="Senior Full Stack Engineer",
            company_name="Acme Corp",
            department="Core Platform",
            role_category="Engineering",
            experience_level=RecruitmentRoom.ExperienceLevel.SENIOR,
            description="Build modern distributed microservices with React and Python.",
            requirements_text="5+ years Python, TypeScript, Docker.",
            skills_required=["Python", "TypeScript", "React", "Docker"],
            cv_weight=50,
            video_weight=50,
            status=RecruitmentRoom.Status.ACTIVE,
            link_is_active=True,
            link_expires_at=now + timedelta(days=14),
            share_token="acme-senior-dev-token-43b",
            created_by=self.hr_user
        )

        # 5. Open Active Room 2 (Junior Frontend Engineer, BetaTech)
        self.room_open_2 = RecruitmentRoom.objects.create(
            title="Junior Frontend Engineer",
            company_name="BetaTech Labs",
            department="Web Experience",
            role_category="Frontend",
            experience_level=RecruitmentRoom.ExperienceLevel.ENTRY,
            description="Help build user-facing interactive interfaces with Tailwind and Vue.",
            requirements_text="HTML, CSS, JavaScript, Vue or React.",
            skills_required=["JavaScript", "Tailwind CSS", "React"],
            cv_weight=60,
            video_weight=40,
            status=RecruitmentRoom.Status.ACTIVE,
            link_is_active=True,
            link_expires_at=now + timedelta(days=30),
            share_token="betatech-junior-fe-token-43b",
            created_by=self.hr_user
        )

        # 6. Closed Room (Should be hidden from listing, AC-3)
        self.room_closed = RecruitmentRoom.objects.create(
            title="Closed Data Analyst Role",
            company_name="Acme Corp",
            department="Analytics",
            role_category="Data",
            experience_level=RecruitmentRoom.ExperienceLevel.MID,
            status=RecruitmentRoom.Status.CLOSED,
            link_is_active=True,
            share_token="closed-room-token-43b",
            created_by=self.hr_user
        )

        # 7. Paused Room (Should be hidden from listing, AC-3)
        self.room_paused = RecruitmentRoom.objects.create(
            title="Paused DevOps Specialist",
            company_name="BetaTech Labs",
            department="Infrastructure",
            role_category="DevOps",
            experience_level=RecruitmentRoom.ExperienceLevel.MID,
            status=RecruitmentRoom.Status.PAUSED,
            link_is_active=True,
            share_token="paused-room-token-43b",
            created_by=self.hr_user
        )

        # 8. Expired Room (Past deadline, should be hidden from listing, AC-3)
        self.room_expired = RecruitmentRoom.objects.create(
            title="Expired Mobile Developer",
            company_name="MobileApp Studio",
            department="Mobile Team",
            role_category="Mobile",
            experience_level=RecruitmentRoom.ExperienceLevel.MID,
            status=RecruitmentRoom.Status.ACTIVE,
            link_is_active=True,
            link_expires_at=now - timedelta(days=2),  # Past deadline
            share_token="expired-room-token-43b",
            created_by=self.hr_user
        )

        # 9. Inactive Link Room (Link disabled, should be hidden from listing, AC-3)
        self.room_inactive_link = RecruitmentRoom.objects.create(
            title="Inactive Link QA Engineer",
            company_name="Acme Corp",
            department="Quality Assurance",
            role_category="QA",
            experience_level=RecruitmentRoom.ExperienceLevel.MID,
            status=RecruitmentRoom.Status.ACTIVE,
            link_is_active=False,  # Link disabled
            share_token="inactive-link-token-43b",
            created_by=self.hr_user
        )

        # 10. Candidate Alpha submits application for Room 1
        self.cv_alpha = CandidateCV.objects.create(
            user=self.candidate_alpha,
            file="students/alpha/resume.pdf",
            original_filename="Alpha_Resume.pdf",
            file_size=102400,
            file_type="pdf"
        )
        self.video_alpha = PresentationVideo.objects.create(
            user=self.candidate_alpha,
            file="students/alpha/pitch.mp4",
            original_filename="Alpha_Pitch.mp4",
            raw_file_size=2048000,
            file_type="mp4",
            duration_seconds=90,
            status="COMPLETED"
        )
        self.app_alpha_room1 = CandidateApplication.objects.create(
            room=self.room_open_1,
            candidate=self.candidate_alpha,
            cv=self.cv_alpha,
            video=self.video_alpha,
            status=CandidateApplication.Status.COMPLETED,
            final_score=88.0
        )

        self.list_url = "/api/recruitment/rooms/public/"

    def test_tc43b_01_list_open_rooms_unauthenticated(self):
        """AC-1: Anyone or unauthenticated user can list open active rooms."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only return the 2 active, unexpired rooms
        returned_ids = [r["id"] for r in response.data]
        self.assertIn(self.room_open_1.id, returned_ids)
        self.assertIn(self.room_open_2.id, returned_ids)
        self.assertEqual(len(response.data), 2)

    def test_tc43b_02_hidden_rooms_closed_and_paused(self):
        """AC-3: Closed and paused rooms are excluded from the job board."""
        response = self.client.get(self.list_url)
        returned_ids = [r["id"] for r in response.data]
        self.assertNotIn(self.room_closed.id, returned_ids)
        self.assertNotIn(self.room_paused.id, returned_ids)

    def test_tc43b_03_hidden_rooms_past_deadline(self):
        """AC-3: Rooms whose link_expires_at is in the past are excluded."""
        response = self.client.get(self.list_url)
        returned_ids = [r["id"] for r in response.data]
        self.assertNotIn(self.room_expired.id, returned_ids)

    def test_tc43b_04_hidden_rooms_inactive_link(self):
        """AC-3: Rooms with link_is_active=False are excluded."""
        response = self.client.get(self.list_url)
        returned_ids = [r["id"] for r in response.data]
        self.assertNotIn(self.room_inactive_link.id, returned_ids)

    def test_tc43b_05_annotation_is_applied_candidate(self):
        """AC-5: Candidate Alpha sees has_applied=True on Room 1 and has_applied=False on Room 2."""
        self.client.force_authenticate(user=self.candidate_alpha)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        room_1_data = next((r for r in response.data if r["id"] == self.room_open_1.id), None)
        room_2_data = next((r for r in response.data if r["id"] == self.room_open_2.id), None)

        self.assertIsNotNone(room_1_data)
        self.assertIsNotNone(room_2_data)

        self.assertTrue(room_1_data["has_applied"])
        self.assertTrue(room_1_data["is_applied"])
        self.assertEqual(room_1_data["application_id"], self.app_alpha_room1.id)

        self.assertFalse(room_2_data["has_applied"])
        self.assertFalse(room_2_data["is_applied"])
        self.assertIsNone(room_2_data["application_id"])

    def test_tc43b_06_annotation_candidate_isolation(self):
        """AC-8: Candidate Beta has NOT applied to Room 1; never sees Candidate Alpha's applied state."""
        self.client.force_authenticate(user=self.candidate_beta)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        room_1_data = next((r for r in response.data if r["id"] == self.room_open_1.id), None)
        self.assertIsNotNone(room_1_data)
        self.assertFalse(room_1_data["has_applied"])
        self.assertFalse(room_1_data["is_applied"])
        self.assertIsNone(room_1_data["application_id"])

    def test_tc43b_07_search_filter_by_title_or_company(self):
        """AC-6: Candidate can filter rooms by job title or company name."""
        # Search by company 'BetaTech'
        resp_company = self.client.get(f"{self.list_url}?search=BetaTech")
        self.assertEqual(resp_company.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp_company.data), 1)
        self.assertEqual(resp_company.data[0]["id"], self.room_open_2.id)

        # Search by title 'Senior'
        resp_title = self.client.get(f"{self.list_url}?search=Senior")
        self.assertEqual(resp_title.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp_title.data), 1)
        self.assertEqual(resp_title.data[0]["id"], self.room_open_1.id)

    def test_tc43b_08_filter_by_experience_level(self):
        """AC-6: Candidate can filter by experience level (e.g. ENTRY vs SENIOR)."""
        resp_entry = self.client.get(f"{self.list_url}?experience_level=ENTRY")
        self.assertEqual(resp_entry.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp_entry.data), 1)
        self.assertEqual(resp_entry.data[0]["id"], self.room_open_2.id)

        resp_senior = self.client.get(f"{self.list_url}?experience_level=SENIOR")
        self.assertEqual(resp_senior.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp_senior.data), 1)
        self.assertEqual(resp_senior.data[0]["id"], self.room_open_1.id)

    def test_tc43b_09_retrieve_single_public_room_detail(self):
        """Candidate can fetch full details of a specific open room."""
        detail_url = f"/api/recruitment/rooms/public/{self.room_open_1.id}/"
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.room_open_1.id)
        self.assertEqual(response.data["title"], "Senior Full Stack Engineer")
        self.assertEqual(response.data["company_name"], "Acme Corp")
        self.assertEqual(response.data["cv_weight"], 50)
        self.assertEqual(response.data["video_weight"], 50)
        self.assertIn("share_url", response.data)

    def test_tc43b_10_empty_state_when_no_active_rooms(self):
        """AC-7: Empty list returned when all active rooms are closed or none match filter."""
        resp = self.client.get(f"{self.list_url}?search=NonExistentRoleXYZ123")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 0)

    def test_tc43b_11_pagination_support(self):
        """AC-1: Supports pagination parameter returning count, total_pages, and results."""
        resp = self.client.get(f"{self.list_url}?page=1&page_size=1")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("results", resp.data)
        self.assertEqual(resp.data["count"], 2)
        self.assertEqual(resp.data["total_pages"], 2)
        self.assertEqual(len(resp.data["results"]), 1)

