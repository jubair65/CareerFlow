import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'careerflow.settings')
django.setup()

from rest_framework import status
from rest_framework.test import APITestCase
from apps.authentication.models import User
from apps.recruitment.models import RecruitmentRoom


class RecruitmentRoomManagementAPITests(APITestCase):
    """
    US-18: Create Recruitment Room Unit Tests (US-18-T7)
    Verifies Room data model, HR RBAC isolation, validation, and full CRUD.
    """

    def setUp(self):
        self.hr_user = User.objects.create_user(
            username="hr_lead@careerflow.demo",
            email="hr_lead@careerflow.demo",
            password="Password123!",
            role=User.Role.HR_MANAGER,
            full_name="Sarah Jenkins"
        )
        self.other_hr_user = User.objects.create_user(
            username="hr_other@careerflow.demo",
            email="hr_other@careerflow.demo",
            password="Password123!",
            role=User.Role.HR_MANAGER,
            full_name="David Miller"
        )
        self.student_user = User.objects.create_user(
            username="candidate@careerflow.demo",
            email="candidate@careerflow.demo",
            password="Password123!",
            role=User.Role.STUDENT,
            full_name="Alex Rahman"
        )
        self.agency_user = User.objects.create_user(
            username="agency@careerflow.demo",
            email="agency@careerflow.demo",
            password="Password123!",
            role=User.Role.AGENCY_ADMIN,
            full_name="Talent Agency Admin"
        )
        self.rooms_url = "/api/recruitment/rooms/"

    def test_create_room_as_hr_success(self):
        """HR Manager can create a Room successfully (US-18-T2)."""
        self.client.force_authenticate(user=self.hr_user)
        payload = {
            "title": "Senior AI Systems Engineer",
            "company_name": "Antigravity Labs",
            "department": "Engineering",
            "description": "Lead the development of next-gen agentic workflows."
        }
        response = self.client.post(self.rooms_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertEqual(data["message"], "Recruitment room created successfully.")
        
        room = data["room"]
        self.assertEqual(room["title"], payload["title"])
        self.assertEqual(room["company_name"], payload["company_name"])
        self.assertEqual(room["department"], payload["department"])
        self.assertEqual(room["created_by"], self.hr_user.id)
        self.assertEqual(room["created_by_name"], self.hr_user.full_name)
        self.assertEqual(room["status"], "ACTIVE")
        self.assertTrue(bool(room["share_token"]))
        self.assertIn(f"/apply/{room['share_token']}", room["share_url"])

        # Verify DB record
        db_room = RecruitmentRoom.objects.get(id=room["id"])
        self.assertEqual(db_room.created_by, self.hr_user)
        self.assertEqual(db_room.title, payload["title"])

    def test_create_room_as_student_forbidden(self):
        """Candidates/Students cannot create Rooms (US-18-T3 RBAC)."""
        self.client.force_authenticate(user=self.student_user)
        payload = {
            "title": "Junior Developer",
            "company_name": "Tech Corp"
        }
        response = self.client.post(self.rooms_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_room_as_agency_forbidden(self):
        """Agency Admins without HR role cannot access HR room endpoints."""
        self.client.force_authenticate(user=self.agency_user)
        payload = {
            "title": "Recruiter Role",
            "company_name": "Agency Partners"
        }
        response = self.client.post(self.rooms_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_room_unauthenticated_fails(self):
        """Unauthenticated requests are rejected with 401."""
        payload = {
            "title": "Public Attempt",
            "company_name": "Acme Inc"
        }
        response = self.client.post(self.rooms_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_room_validation_blank_title(self):
        """Room creation fails if title is blank."""
        self.client.force_authenticate(user=self.hr_user)
        payload = {
            "title": "   ",
            "company_name": "Tech Corp"
        }
        response = self.client.post(self.rooms_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("title", response.json())

    def test_create_room_validation_short_title(self):
        """Room creation fails if title is less than 3 characters."""
        self.client.force_authenticate(user=self.hr_user)
        payload = {
            "title": "AI",
            "company_name": "Tech Corp"
        }
        response = self.client.post(self.rooms_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("title", response.json())

    def test_create_room_validation_blank_company(self):
        """Room creation fails if company name is blank."""
        self.client.force_authenticate(user=self.hr_user)
        payload = {
            "title": "DevOps Engineer",
            "company_name": "   "
        }
        response = self.client.post(self.rooms_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("company_name", response.json())

    def test_list_rooms_only_returns_own_rooms(self):
        """HR Manager can only list their own rooms (US-18-T5 isolation)."""
        RecruitmentRoom.objects.create(title="HR1 Room Alpha", company_name="Corp A", created_by=self.hr_user)
        RecruitmentRoom.objects.create(title="HR1 Room Beta", company_name="Corp A", created_by=self.hr_user)
        RecruitmentRoom.objects.create(title="HR2 Room Gamma", company_name="Corp B", created_by=self.other_hr_user)

        self.client.force_authenticate(user=self.hr_user)
        response = self.client.get(self.rooms_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data), 2)
        for room in data:
            self.assertEqual(room["created_by"], self.hr_user.id)

    def test_retrieve_and_update_room_as_owner(self):
        """HR can retrieve and edit their own room."""
        room = RecruitmentRoom.objects.create(
            title="Frontend Specialist",
            company_name="Design Solutions",
            created_by=self.hr_user
        )
        self.client.force_authenticate(user=self.hr_user)
        
        # GET Detail
        get_res = self.client.get(f"{self.rooms_url}{room.id}/")
        self.assertEqual(get_res.status_code, status.HTTP_200_OK)
        self.assertEqual(get_res.json()["title"], "Frontend Specialist")

        # PATCH Update
        patch_res = self.client.patch(
            f"{self.rooms_url}{room.id}/",
            {"description": "Updated job description.", "status": "PAUSED"},
            format="json"
        )
        self.assertEqual(patch_res.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_res.json()["room"]["status"], "PAUSED")
        
        room.refresh_from_db()
        self.assertEqual(room.description, "Updated job description.")
        self.assertEqual(room.status, "PAUSED")

    def test_unauthorized_hr_cannot_access_other_hrs_room(self):
        """HR Manager cannot view or modify another HR's room."""
        other_room = RecruitmentRoom.objects.create(
            title="Secret Executive Role",
            company_name="Private Equity",
            created_by=self.other_hr_user
        )
        self.client.force_authenticate(user=self.hr_user)
        
        # Attempt GET
        res = self.client.get(f"{self.rooms_url}{other_room.id}/")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

        # Attempt PATCH
        patch_res = self.client.patch(
            f"{self.rooms_url}{other_room.id}/",
            {"title": "Hacked Title"},
            format="json"
        )
        self.assertEqual(patch_res.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_room_as_owner(self):
        """HR Manager can delete their own room."""
        room = RecruitmentRoom.objects.create(
            title="Old Archive Role",
            company_name="Legacy Corp",
            created_by=self.hr_user
        )
        self.client.force_authenticate(user=self.hr_user)
        del_res = self.client.delete(f"{self.rooms_url}{room.id}/")
        self.assertEqual(del_res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(RecruitmentRoom.objects.filter(id=room.id).exists())
