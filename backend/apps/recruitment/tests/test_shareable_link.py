import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'careerflow.settings')
django.setup()

from datetime import timedelta
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from apps.authentication.models import User
from apps.recruitment.models import RecruitmentRoom
from apps.recruitment.tokens import generate_secure_share_token, is_token_expired, validate_share_token


class RecruitmentShareableLinkTests(APITestCase):
    """
    US-21: Shareable Application Link Unit Tests (US-21-T7)
    Verifies:
      - Secure token generation strategy (US-21-T1)
      - Application link generation API endpoints (US-21-T2)
      - Public unauthenticated resolution & validation (US-21-T3)
      - Deactivation and regeneration workflows (US-21-T5)
      - Expiration and boundary condition handling
      - Role-based access control and tenant isolation
    """

    def setUp(self):
        self.hr_owner = User.objects.create_user(
            username="hr_mona@careerflow.demo",
            email="hr_mona@careerflow.demo",
            password="Password123!",
            role=User.Role.HR_MANAGER,
            full_name="Jannatun Naeem Mona"
        )
        self.other_hr = User.objects.create_user(
            username="hr_other_mona@careerflow.demo",
            email="hr_other_mona@careerflow.demo",
            password="Password123!",
            role=User.Role.HR_MANAGER,
            full_name="David Miller"
        )
        self.student_user = User.objects.create_user(
            username="applicant_student@careerflow.demo",
            email="applicant_student@careerflow.demo",
            password="Password123!",
            role=User.Role.STUDENT,
            full_name="Candidate Student"
        )

        self.room = RecruitmentRoom.objects.create(
            title="Lead DevOps Engineer",
            company_name="CloudEdge Solutions",
            department="Cloud Operations",
            description="Leading multi-cloud infrastructure and automated CI/CD pipelines.",
            created_by=self.hr_owner,
            cv_weight=60,
            video_weight=40,
            role_category="Engineering",
            experience_level="SENIOR",
            skills_required=["AWS", "Terraform", "Kubernetes", "Docker"],
            requirements_text="5+ years DevOps experience with container orchestration and Infrastructure-as-Code."
        )

        self.link_url = f"/api/recruitment/rooms/{self.room.id}/link/"
        self.deactivate_url = f"/api/recruitment/rooms/{self.room.id}/link/deactivate/"
        self.activate_url = f"/api/recruitment/rooms/{self.room.id}/link/activate/"
        self.regenerate_url = f"/api/recruitment/rooms/{self.room.id}/link/regenerate/"

    # --- US-21-T1: Token Strategy Tests ---
    def test_token_generation_format_and_security(self):
        """Verify tokens are non-guessable, URL-safe, and sufficiently long."""
        token1 = generate_secure_share_token()
        token2 = generate_secure_share_token()
        self.assertNotEqual(token1, token2)
        self.assertGreaterEqual(len(token1), 16)
        # Ensure token is URL safe (no / + =)
        self.assertTrue(token1.replace('-', '').replace('_', '').isalnum())

    def test_room_auto_generates_share_token(self):
        """Verify room created without token automatically obtains a valid token."""
        self.assertTrue(bool(self.room.share_token))
        self.assertTrue(self.room.link_is_active)
        self.assertIsNone(self.room.link_expires_at)

    # --- US-21-T2: Link Management Endpoints (HR Owner) ---
    def test_get_link_as_owner_success(self):
        """HR owner can retrieve shareable application link information."""
        self.client.force_authenticate(user=self.hr_owner)
        response = self.client.get(self.link_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("link", data)
        link_data = data["link"]
        self.assertEqual(link_data["id"], self.room.id)
        self.assertEqual(link_data["share_token"], self.room.share_token)
        self.assertIn(f"/apply/{self.room.share_token}", link_data["share_url"])
        self.assertTrue(link_data["link_is_active"])
        self.assertFalse(link_data["is_expired"])

    def test_post_link_as_owner_returns_or_creates_token(self):
        """POST /rooms/{id}/link/ returns existing or freshly initialized token."""
        self.client.force_authenticate(user=self.hr_owner)
        response = self.client.post(self.link_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["link"]["share_token"], self.room.share_token)

    # --- US-21-T3: Public Unauthenticated Resolution ---
    def test_public_resolution_unauthenticated_success(self):
        """Candidate can access public job opening via token without authentication."""
        public_url = f"/api/recruitment/apply/{self.room.share_token}/"
        response = self.client.get(public_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["title"], "Lead DevOps Engineer")
        self.assertEqual(data["company_name"], "CloudEdge Solutions")
        self.assertEqual(data["cv_weight"], 60)
        self.assertEqual(data["video_weight"], 40)
        self.assertEqual(data["experience_level"], "SENIOR")
        self.assertIn("AWS", data["skill_names"])
        self.assertTrue(data["link_is_active"])

    def test_public_resolution_invalid_token_returns_404(self):
        """Invalid or non-existent token returns HTTP 404 Not Found."""
        response = self.client.get("/api/recruitment/apply/non_existent_fake_token_123/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.json()
        self.assertEqual(data["code"], "LINK_NOT_FOUND")

    # --- US-21-T5: Deactivate and Reactivate Link ---
    def test_deactivate_link_as_owner(self):
        """HR owner can deactivate a link, immediately blocking public candidate access (410)."""
        self.client.force_authenticate(user=self.hr_owner)
        response = self.client.post(self.deactivate_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.json()["link"]["link_is_active"])

        self.room.refresh_from_db()
        self.assertFalse(self.room.link_is_active)

        # Public candidate access must now return 410 Gone
        public_url = f"/api/recruitment/apply/{self.room.share_token}/"
        candidate_res = self.client.get(public_url)
        self.assertEqual(candidate_res.status_code, status.HTTP_410_GONE)
        self.assertEqual(candidate_res.json()["code"], "LINK_DEACTIVATED")

    def test_activate_link_restores_public_access(self):
        """HR owner can reactivate a deactivated link."""
        self.room.link_is_active = False
        self.room.save(update_fields=['link_is_active'])

        self.client.force_authenticate(user=self.hr_owner)
        response = self.client.post(self.activate_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()["link"]["link_is_active"])

        public_url = f"/api/recruitment/apply/{self.room.share_token}/"
        candidate_res = self.client.get(public_url)
        self.assertEqual(candidate_res.status_code, status.HTTP_200_OK)

    # --- US-21-T5: Regenerate Link Token ---
    def test_regenerate_link_generates_new_token_and_invalidates_old(self):
        """Regenerating creates a new token and immediately causes old token to return 404."""
        old_token = self.room.share_token
        self.client.force_authenticate(user=self.hr_owner)
        response = self.client.post(self.regenerate_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_token = response.json()["link"]["share_token"]
        self.assertNotEqual(old_token, new_token)

        self.room.refresh_from_db()
        self.assertEqual(self.room.share_token, new_token)
        self.assertTrue(self.room.link_is_active)

        # Old token is now 404
        old_res = self.client.get(f"/api/recruitment/apply/{old_token}/")
        self.assertEqual(old_res.status_code, status.HTTP_404_NOT_FOUND)

        # New token resolves to 200 OK
        new_res = self.client.get(f"/api/recruitment/apply/{new_token}/")
        self.assertEqual(new_res.status_code, status.HTTP_200_OK)
        self.assertEqual(new_res.json()["title"], "Lead DevOps Engineer")

    # --- Expiration and Edge Conditions ---
    def test_expired_link_returns_410_gone(self):
        """Link past its expiration timestamp returns HTTP 410 Gone."""
        self.room.link_expires_at = timezone.now() - timedelta(days=1)
        self.room.save(update_fields=['link_expires_at'])

        public_url = f"/api/recruitment/apply/{self.room.share_token}/"
        response = self.client.get(public_url)
        self.assertEqual(response.status_code, status.HTTP_410_GONE)
        self.assertEqual(response.json()["code"], "LINK_EXPIRED")

    def test_closed_room_returns_410_gone(self):
        """Closed recruitment room returns HTTP 410 Gone to public candidates."""
        self.room.status = 'CLOSED'
        self.room.save(update_fields=['status'])

        public_url = f"/api/recruitment/apply/{self.room.share_token}/"
        response = self.client.get(public_url)
        self.assertEqual(response.status_code, status.HTTP_410_GONE)

    # --- RBAC & Tenant Isolation ---
    def test_unauthenticated_cannot_manage_link(self):
        """Unauthenticated requests to link management endpoints return 401."""
        response = self.client.get(self.link_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        deact_res = self.client.post(self.deactivate_url)
        self.assertEqual(deact_res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_student_cannot_manage_link(self):
        """Candidate/Student users cannot manage room links (403 Forbidden)."""
        self.client.force_authenticate(user=self.student_user)
        response = self.client.get(self.link_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        regen_res = self.client.post(self.regenerate_url)
        self.assertEqual(regen_res.status_code, status.HTTP_403_FORBIDDEN)

    def test_other_hr_cannot_manage_or_view_link(self):
        """Other HR managers cannot view or manage another HR's room link (404 isolation)."""
        self.client.force_authenticate(user=self.other_hr)
        response = self.client.get(self.link_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        deact_res = self.client.post(self.deactivate_url)
        self.assertEqual(deact_res.status_code, status.HTTP_404_NOT_FOUND)
