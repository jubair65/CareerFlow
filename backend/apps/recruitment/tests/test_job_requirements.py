import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'careerflow.settings')
django.setup()

from rest_framework import status
from rest_framework.test import APITestCase
from apps.authentication.models import User
from apps.recruitment.models import RecruitmentRoom
from apps.cv.models import JobRequirement
from apps.recruitment.services.matcher_bridge import (
    extract_room_skills,
    build_matcher_payload,
    sync_room_to_job_requirement,
)


class JobRequirementsAPITests(APITestCase):
    """
    US-19: Job Role & Required Skills Unit Tests (US-19-T7)
    Verifies role configuration, skill tag validation, duplicate checking,
    RBAC access control, and CV semantic matcher bridge synchronization.
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

        # Create room owned by hr_user
        self.room = RecruitmentRoom.objects.create(
            title="Senior Backend Engineer",
            company_name="Antigravity Labs",
            department="Engineering",
            role_category="Engineering",
            experience_level=RecruitmentRoom.ExperienceLevel.MID,
            description="Build scalable backend services for recruitment workflows.",
            skills_required=[{"name": "Python", "importance": "REQUIRED", "category": "Technical"}],
            created_by=self.hr_user
        )
        self.requirements_url = f"/api/recruitment/rooms/{self.room.id}/requirements/"

    def test_get_requirements_as_owner_success(self):
        """Owner HR can fetch requirements for their room."""
        self.client.force_authenticate(user=self.hr_user)
        response = self.client.get(self.requirements_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["room_id"], self.room.id)
        self.assertEqual(data["title"], "Senior Backend Engineer")
        self.assertEqual(data["company_name"], "Antigravity Labs")
        self.assertEqual(data["requirements"]["experience_level"], "MID")
        self.assertEqual(data["skill_names"], ["Python"])

    def test_get_requirements_unauthenticated_fails(self):
        """Unauthenticated requests are rejected with 401."""
        response = self.client.get(self.requirements_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_requirements_as_student_forbidden(self):
        """Candidate / Student role cannot view room requirements configuration (403)."""
        self.client.force_authenticate(user=self.student_user)
        response = self.client.get(self.requirements_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_requirements_as_other_hr_not_found(self):
        """Other HR cannot access rooms they do not own (404 isolation)."""
        self.client.force_authenticate(user=self.other_hr_user)
        response = self.client.get(self.requirements_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_requirements_success(self):
        """Owner HR can update role category, experience level, requirements text, and skill tags."""
        self.client.force_authenticate(user=self.hr_user)
        payload = {
            "experience_level": "SENIOR",
            "role_category": "Engineering",
            "requirements_text": "Must have 5+ years with Django, Celery, and distributed systems.",
            "skills_required": ["Python", "Django", "PostgreSQL", "Redis"]
        }
        response = self.client.patch(self.requirements_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["message"], "Job role and requirements updated successfully.")
        self.assertEqual(data["requirements"]["experience_level"], "SENIOR")
        self.assertEqual(len(data["requirements"]["skills_required"]), 4)

        # Verify DB updates on RecruitmentRoom
        self.room.refresh_from_db()
        self.assertEqual(self.room.experience_level, "SENIOR")
        self.assertEqual(self.room.requirements_text, payload["requirements_text"])
        self.assertEqual(self.room.get_skill_names(), ["Python", "Django", "PostgreSQL", "Redis"])

        # Verify synchronization with JobRequirement (US-19-T5)
        synced_req = JobRequirement.objects.filter(
            title=self.room.title,
            company=self.room.company_name,
            created_by=self.hr_user
        ).first()
        self.assertIsNotNone(synced_req)
        self.assertEqual(synced_req.required_skills, ["Python", "Django", "PostgreSQL", "Redis"])
        self.assertIn("Requirements:\nMust have 5+ years", synced_req.description)

    def test_put_requirements_structured_skills_success(self):
        """Owner HR can save skills with structured importance and categories."""
        self.client.force_authenticate(user=self.hr_user)
        payload = {
            "experience_level": "LEAD",
            "role_category": "Design",
            "requirements_text": "Lead UX research and design systems across multiple web products.",
            "skills_required": [
                {"name": "Figma", "importance": "REQUIRED", "category": "Design"},
                {"name": "User Research", "importance": "REQUIRED", "category": "Product"},
                {"name": "Design Systems", "importance": "PREFERRED", "category": "Design"}
            ]
        }
        response = self.client.put(self.requirements_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["requirements"]["experience_level"], "LEAD")
        self.assertEqual(data["requirements"]["role_category"], "Design")
        self.assertEqual(len(data["requirements"]["skills_required"]), 3)

        self.room.refresh_from_db()
        self.assertEqual(self.room.get_skill_names(), ["Figma", "User Research", "Design Systems"])

    def test_update_requirements_empty_skills_fails(self):
        """Updating requirements with empty skills list raises validation error (400)."""
        self.client.force_authenticate(user=self.hr_user)
        payload = {
            "skills_required": []
        }
        response = self.client.patch(self.requirements_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertIn("skills_required", data)
        self.assertIn("At least one required skill must be defined.", str(data["skills_required"]))

    def test_update_requirements_duplicate_skills_fails(self):
        """Duplicate skill tags (case-insensitive) are rejected with validation error (400)."""
        self.client.force_authenticate(user=self.hr_user)
        payload = {
            "skills_required": ["TypeScript", "React", "typescript"]
        }
        response = self.client.patch(self.requirements_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertIn("skills_required", data)
        self.assertIn("Duplicate skill tag", str(data["skills_required"]))

    def test_update_requirements_blank_skill_name_fails(self):
        """Blank or whitespace skill name is rejected with 400."""
        self.client.force_authenticate(user=self.hr_user)
        payload = {
            "skills_required": ["  "]
        }
        response = self.client.patch(self.requirements_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertIn("skills_required", data)

    def test_update_requirements_skill_too_short_fails(self):
        """Skill names shorter than 2 characters are rejected with 400."""
        self.client.force_authenticate(user=self.hr_user)
        payload = {
            "skills_required": ["C"]
        }
        response = self.client.patch(self.requirements_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertIn("skills_required", data)
        self.assertIn("too short", str(data["skills_required"]))

    def test_update_requirements_invalid_experience_level_fails(self):
        """Invalid experience level choice is rejected with 400."""
        self.client.force_authenticate(user=self.hr_user)
        payload = {
            "experience_level": "EXECUTIVE_VP"
        }
        response = self.client.patch(self.requirements_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertIn("experience_level", data)

    def test_update_requirements_as_other_hr_not_found(self):
        """Other HR cannot update rooms they do not own (404)."""
        self.client.force_authenticate(user=self.other_hr_user)
        payload = {
            "skills_required": ["Python", "Django"]
        }
        response = self.client.patch(self.requirements_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_requirements_as_student_forbidden(self):
        """Students cannot update requirements (403)."""
        self.client.force_authenticate(user=self.student_user)
        payload = {
            "skills_required": ["Python", "Django"]
        }
        response = self.client.patch(self.requirements_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_matcher_bridge_service_functions(self):
        """Direct unit test of matcher_bridge helper methods (US-19-T5)."""
        # Test extract_room_skills
        self.room.skills_required = [
            {"name": "Docker", "importance": "REQUIRED"},
            "Kubernetes",
            {"name": "docker", "importance": "PREFERRED"},  # Duplicate
        ]
        extracted = extract_room_skills(self.room)
        self.assertEqual(extracted, ["Docker", "Kubernetes"])

        # Test build_matcher_payload
        self.room.description = "Core cloud platform engineering."
        self.room.requirements_text = "Experience with container orchestration."
        self.room.save()

        payload = build_matcher_payload(self.room)
        self.assertEqual(payload["room_id"], self.room.id)
        self.assertEqual(payload["job_title"], self.room.title)
        self.assertEqual(payload["required_skills"], ["Docker", "Kubernetes"])
        self.assertIn("Core cloud platform engineering.", payload["job_description"])
        self.assertIn("Experience with container orchestration.", payload["job_description"])

        # Test sync_room_to_job_requirement
        job_req = sync_room_to_job_requirement(self.room)
        self.assertEqual(job_req.title, self.room.title)
        self.assertEqual(job_req.required_skills, ["Docker", "Kubernetes"])
        self.assertEqual(job_req.created_by, self.hr_user)
