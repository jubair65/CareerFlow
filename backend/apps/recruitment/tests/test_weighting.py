import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'careerflow.settings')
django.setup()

from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.test import APITestCase
from apps.authentication.models import User
from apps.recruitment.models import RecruitmentRoom


class RecruitmentWeightingAPITests(APITestCase):
    """
    US-20: CV-to-Video Weighting Configuration Unit Tests (US-20-T7)
    Verifies:
      - Default 50/50 weighting logic (US-20-T4)
      - Weight configuration API endpoints GET / PATCH / PUT (US-20-T2)
      - Strict validation: sum == 100%, 0-100 bounds, integer type (US-20-T4)
      - Data persistence & room exposure (US-20-T5)
      - Role-based access control & ownership isolation (IsHRManager, IsRoomOwner)
    """

    def setUp(self):
        self.hr_owner = User.objects.create_user(
            username="hr_mobin@careerflow.demo",
            email="hr_mobin@careerflow.demo",
            password="Password123!",
            role=User.Role.HR_MANAGER,
            full_name="Hasanul Mobin"
        )
        self.other_hr = User.objects.create_user(
            username="hr_other@careerflow.demo",
            email="hr_other@careerflow.demo",
            password="Password123!",
            role=User.Role.HR_MANAGER,
            full_name="Sarah Jenkins"
        )
        self.student_user = User.objects.create_user(
            username="student@careerflow.demo",
            email="student@careerflow.demo",
            password="Password123!",
            role=User.Role.STUDENT,
            full_name="Candidate Student"
        )

        self.room = RecruitmentRoom.objects.create(
            title="Senior Full-Stack Engineer",
            company_name="CareerFlow Inc",
            department="Product Engineering",
            description="Leading fullstack architecture and development.",
            created_by=self.hr_owner,
            cv_weight=50,
            video_weight=50
        )
        self.weighting_url = f"/api/recruitment/rooms/{self.room.id}/weighting/"

    # --- US-20-T4: Default Weighting Tests ---
    def test_default_weights_applied_on_room_creation(self):
        """Verify new rooms default to 50% CV and 50% Video weighting."""
        new_room = RecruitmentRoom.objects.create(
            title="Junior DevOps Engineer",
            company_name="Cloud Solutions",
            created_by=self.hr_owner
        )
        self.assertEqual(new_room.cv_weight, 50)
        self.assertEqual(new_room.video_weight, 50)
        self.assertEqual(new_room.cv_weight + new_room.video_weight, 100)

    # --- US-20-T2 & US-20-T5: GET Weighting Endpoint ---
    def test_get_weighting_as_owner_success(self):
        """HR owner can retrieve weighting configuration for their room."""
        self.client.force_authenticate(user=self.hr_owner)
        response = self.client.get(self.weighting_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["room_id"], self.room.id)
        self.assertEqual(data["cv_weight"], 50)
        self.assertEqual(data["video_weight"], 50)
        self.assertIn("weighting", data)
        self.assertEqual(data["weighting"]["cv_weight"], 50)
        self.assertEqual(data["weighting"]["video_weight"], 50)

    # --- US-20-T2: PATCH / PUT Weight Configuration ---
    def test_patch_weighting_success(self):
        """HR owner can update weights with a valid 70/30 split."""
        self.client.force_authenticate(user=self.hr_owner)
        payload = {
            "cv_weight": 70,
            "video_weight": 30
        }
        response = self.client.patch(self.weighting_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["message"], "Evaluation weighting updated successfully.")
        self.assertEqual(data["weighting"]["cv_weight"], 70)
        self.assertEqual(data["weighting"]["video_weight"], 30)

        # Verify DB persistence (US-20-T5)
        self.room.refresh_from_db()
        self.assertEqual(self.room.cv_weight, 70)
        self.assertEqual(self.room.video_weight, 30)

    def test_put_weighting_success(self):
        """HR owner can update weights via PUT request."""
        self.client.force_authenticate(user=self.hr_owner)
        payload = {
            "cv_weight": 40,
            "video_weight": 60
        }
        response = self.client.put(self.weighting_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.room.refresh_from_db()
        self.assertEqual(self.room.cv_weight, 40)
        self.assertEqual(self.room.video_weight, 60)

    def test_patch_weighting_extreme_splits(self):
        """HR can set 100% CV / 0% Video or 0% CV / 100% Video."""
        self.client.force_authenticate(user=self.hr_owner)

        # 100% CV
        res1 = self.client.patch(self.weighting_url, {"cv_weight": 100, "video_weight": 0}, format="json")
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        self.room.refresh_from_db()
        self.assertEqual(self.room.cv_weight, 100)
        self.assertEqual(self.room.video_weight, 0)

        # 100% Video
        res2 = self.client.patch(self.weighting_url, {"cv_weight": 0, "video_weight": 100}, format="json")
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.room.refresh_from_db()
        self.assertEqual(self.room.cv_weight, 0)
        self.assertEqual(self.room.video_weight, 100)

    # --- US-20-T4: Validation Error Tests ---
    def test_weights_not_summing_to_100_rejected(self):
        """Weights sum != 100% must be rejected with 400 Bad Request."""
        self.client.force_authenticate(user=self.hr_owner)
        payload = {
            "cv_weight": 60,
            "video_weight": 50  # Total 110%
        }
        response = self.client.patch(self.weighting_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertIn("weights", data)
        self.assertIn("must total exactly 100%", str(data["weights"]))

    def test_weights_sum_less_than_100_rejected(self):
        """Weights sum < 100% must be rejected with 400 Bad Request."""
        self.client.force_authenticate(user=self.hr_owner)
        payload = {
            "cv_weight": 30,
            "video_weight": 30  # Total 60%
        }
        response = self.client.patch(self.weighting_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertIn("weights", data)

    def test_negative_weight_rejected(self):
        """Negative weight values must be rejected."""
        self.client.force_authenticate(user=self.hr_owner)
        payload = {
            "cv_weight": -10,
            "video_weight": 110
        }
        response = self.client.patch(self.weighting_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertTrue("cv_weight" in data or "weights" in data)

    def test_weight_exceeding_100_rejected(self):
        """Weight values > 100 must be rejected."""
        self.client.force_authenticate(user=self.hr_owner)
        payload = {
            "cv_weight": 150,
            "video_weight": -50
        }
        response = self.client.patch(self.weighting_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_integer_weight_rejected(self):
        """Non-integer weight values must be rejected."""
        self.client.force_authenticate(user=self.hr_owner)
        payload = {
            "cv_weight": "invalid_string",
            "video_weight": 50
        }
        response = self.client.patch(self.weighting_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # --- US-20 RBAC & Security Isolation Tests ---
    def test_unauthenticated_access_fails(self):
        """Unauthenticated requests to weighting endpoint return 401."""
        response = self.client.get(self.weighting_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        patch_res = self.client.patch(self.weighting_url, {"cv_weight": 60, "video_weight": 40})
        self.assertEqual(patch_res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_student_user_forbidden(self):
        """Student users cannot access HR weighting endpoints (403)."""
        self.client.force_authenticate(user=self.student_user)
        response = self.client.get(self.weighting_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_other_hr_cannot_access_or_modify_weights(self):
        """Other HR managers cannot view or modify another HR's room weights (404 isolation)."""
        self.client.force_authenticate(user=self.other_hr)
        get_res = self.client.get(self.weighting_url)
        self.assertEqual(get_res.status_code, status.HTTP_404_NOT_FOUND)

        patch_res = self.client.patch(
            self.weighting_url,
            {"cv_weight": 80, "video_weight": 20},
            format="json"
        )
        self.assertEqual(patch_res.status_code, status.HTTP_404_NOT_FOUND)

    # --- Model Level Clean & Validation Tests ---
    def test_model_clean_validation(self):
        """Direct model clean() method enforces sum == 100 and bounds."""
        invalid_room = RecruitmentRoom(
            title="Test Role",
            company_name="Test Inc",
            created_by=self.hr_owner,
            cv_weight=80,
            video_weight=50
        )
        with self.assertRaises(ValidationError):
            invalid_room.clean()
