from rest_framework import status
from rest_framework.test import APITestCase
from apps.authentication.models import User, CandidateProfile


class CandidateProfileTests(APITestCase):
    """
    US-42: Candidate Profile & Career Objective Management
    Tests covering all Acceptance Criteria:
    ✓ AC 1: User can view and update their profile details (phone, LinkedIn/GitHub URLs, target role, bio)
    ✓ AC 2: Profile data is validated (valid URLs, proper phone number formatting)
    ✓ AC 3: Updated profile information is stored securely in the database
    ✓ AC 4: Candidate profile information is automatically reflected / synced with user records
    ✓ AC 5: Users can only edit their own profile (strict user isolation)
    ✓ AC 6: Profile updates load and save with clear feedback
    """

    def setUp(self):
        self.profile_url = "/api/auth/profile/"
        self.user_a = User.objects.create_user(
            username="candidate_a",
            email="candidate_a@careerflow.test",
            password="Password123!",
            full_name="Candidate Alpha",
            role=User.Role.STUDENT
        )
        self.user_b = User.objects.create_user(
            username="candidate_b",
            email="candidate_b@careerflow.test",
            password="Password123!",
            full_name="Candidate Beta",
            role=User.Role.STUDENT
        )

    def test_tc42_01_unauthenticated_access_denied(self):
        """AC 5: Unauthenticated request to /api/auth/profile/ is blocked with 401."""
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.patch(self.profile_url, {"bio": "Hacker attempt"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_tc42_02_get_profile_auto_created(self):
        """AC 1 & 3: Authenticated candidate GET returns 200 OK and lazily initializes profile."""
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.user_a.email)
        self.assertEqual(response.data["full_name"], "Candidate Alpha")
        self.assertEqual(response.data["role"], "STUDENT")
        self.assertIn("phone_number", response.data)
        self.assertIn("linkedin_url", response.data)
        self.assertIn("github_url", response.data)
        self.assertIn("target_role", response.data)
        self.assertIn("bio", response.data)

        # Confirm DB entry created
        self.assertTrue(CandidateProfile.objects.filter(user=self.user_a).exists())

    def test_tc42_03_update_profile_success(self):
        """AC 1, 3, 6: Update candidate profile details with valid fields."""
        self.client.force_authenticate(user=self.user_a)
        payload = {
            "full_name": "Alpha Senior Dev",
            "phone_number": "+1 (555) 234-5678",
            "linkedin_url": "https://www.linkedin.com/in/candidate-alpha",
            "github_url": "https://github.com/candidate-alpha",
            "target_role": "Full Stack Software Engineer",
            "bio": "Passionate developer with 3 years of React & Django experience."
        }

        response = self.client.patch(self.profile_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Profile updated successfully.")

        profile_data = response.data["profile"]
        self.assertEqual(profile_data["full_name"], "Alpha Senior Dev")
        self.assertEqual(profile_data["phone_number"], "+1 (555) 234-5678")
        self.assertEqual(profile_data["linkedin_url"], "https://www.linkedin.com/in/candidate-alpha")
        self.assertEqual(profile_data["github_url"], "https://github.com/candidate-alpha")
        self.assertEqual(profile_data["target_role"], "Full Stack Software Engineer")
        self.assertEqual(profile_data["bio"], "Passionate developer with 3 years of React & Django experience.")

        # Verify DB persistence
        self.user_a.refresh_from_db()
        self.assertEqual(self.user_a.full_name, "Alpha Senior Dev")
        profile = CandidateProfile.objects.get(user=self.user_a)
        self.assertEqual(profile.target_role, "Full Stack Software Engineer")

    def test_tc42_04_user_isolation(self):
        """AC 5: Candidate A's updates do not modify Candidate B's profile."""
        self.client.force_authenticate(user=self.user_a)
        self.client.patch(self.profile_url, {"target_role": "Data Scientist"}, format="json")

        self.client.force_authenticate(user=self.user_b)
        response_b = self.client.get(self.profile_url)
        self.assertNotEqual(response_b.data["target_role"], "Data Scientist")
        self.assertEqual(response_b.data["email"], self.user_b.email)

    def test_tc42_05_invalid_phone_format(self):
        """AC 2: Rejects phone numbers with invalid characters or too few/many digits."""
        self.client.force_authenticate(user=self.user_a)
        response = self.client.patch(self.profile_url, {"phone_number": "123"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("phone_number", response.data.get("errors", {}))

        response = self.client.patch(self.profile_url, {"phone_number": "phone#with#bad#symbols"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_tc42_06_invalid_linkedin_url(self):
        """AC 2: Rejects non-LinkedIn domain URLs."""
        self.client.force_authenticate(user=self.user_a)
        response = self.client.patch(self.profile_url, {"linkedin_url": "https://www.facebook.com/fake"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("linkedin_url", response.data.get("errors", {}))

    def test_tc42_07_invalid_github_url(self):
        """AC 2: Rejects non-GitHub domain URLs."""
        self.client.force_authenticate(user=self.user_a)
        response = self.client.patch(self.profile_url, {"github_url": "https://www.gitlab.com/fake"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("github_url", response.data.get("errors", {}))

    def test_tc42_08_valid_links_auto_prefixed(self):
        """AC 2: Links provided without scheme (e.g. linkedin.com/in/xyz) are accepted and normalized."""
        self.client.force_authenticate(user=self.user_a)
        payload = {
            "linkedin_url": "linkedin.com/in/alex",
            "github_url": "github.com/alex"
        }
        response = self.client.patch(self.profile_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["profile"]["linkedin_url"], "https://linkedin.com/in/alex")
        self.assertEqual(response.data["profile"]["github_url"], "https://github.com/alex")

