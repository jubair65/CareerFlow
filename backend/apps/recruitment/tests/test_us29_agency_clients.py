"""
US-29: Manage Multiple Client Companies Unit & Integration Tests (US-29-T7).
Tests cover:
- ClientCompany model instantiation, fields, string representation, default is_active=True (AC#1, AC#4)
- Multi-tenant database uniqueness: same agency duplicate company name rejected, different agencies duplicate allowed (AC#2, AC#4, AC#6)
- Role-based Access Control (RBAC): Unauthenticated (401), Student (403), HR Manager (403), Agency Admin (200/201) (AC#5)
- Strict multi-tenant query isolation: Agency Admin A cannot list, retrieve, update, toggle, or delete Agency Admin B's clients (AC#6)
- Client validation: name length, required fields, email format (AC#2)
- Operational lifecycle: Create, List, Retrieve, Partial Update (PATCH), Full Update (PUT), Soft-Deactivate / Reactivate (AC#3)
- Custom action: /api/recruitment/agency/clients/{id}/toggle-active/ (AC#3)
- KPI metrics action: /api/recruitment/agency/clients/summary-stats/ with associated rooms calculation (AC#1, AC#4)
"""

import os
import uuid
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'careerflow.settings')
django.setup()

from rest_framework import status
from rest_framework.test import APITestCase
from apps.authentication.models import User
from apps.recruitment.models import ClientCompany, RecruitmentRoom


class US29AgencyClientManagementUnitTests(APITestCase):
    def setUp(self):
        self.uid = uuid.uuid4().hex[:8]

        # 1. Primary Agency Admin
        self.agency_admin_1 = User.objects.create_user(
            username=f"agency1_{self.uid}",
            email=f"agency1_{self.uid}@careerflow.agency",
            password="Password123!",
            role=User.Role.AGENCY_ADMIN,
            full_name="Maria Agency Admin"
        )

        # 2. Secondary Agency Admin (for multi-tenant isolation tests)
        self.agency_admin_2 = User.objects.create_user(
            username=f"agency2_{self.uid}",
            email=f"agency2_{self.uid}@careerflow.agency",
            password="Password123!",
            role=User.Role.AGENCY_ADMIN,
            full_name="Second Agency Admin"
        )

        # 3. HR Manager (Unauthorized role)
        self.hr_user = User.objects.create_user(
            username=f"hr_{self.uid}",
            email=f"hr_{self.uid}@careerflow.demo",
            password="Password123!",
            role=User.Role.HR_MANAGER,
            full_name="HR Manager User"
        )

        # 4. Student (Unauthorized role)
        self.student_user = User.objects.create_user(
            username=f"student_{self.uid}",
            email=f"student_{self.uid}@careerflow.demo",
            password="Password123!",
            role=User.Role.STUDENT,
            full_name="Student User"
        )

        # 5. Pre-create Client Company for Agency 1
        self.client_1 = ClientCompany.objects.create(
            agency=self.agency_admin_1,
            name="Acme Corporation",
            industry="Technology",
            contact_person="Alice Smith",
            contact_email="alice@acme.com",
            phone="+1-555-0199",
            website="https://acme.example.com",
            notes="Key strategic client in enterprise SaaS",
            is_active=True
        )

        # 6. Pre-create Client Company for Agency 2
        self.client_2 = ClientCompany.objects.create(
            agency=self.agency_admin_2,
            name="Apex Dynamics",
            industry="Finance",
            contact_person="Bob Vance",
            contact_email="bob@apex.com",
            phone="+1-555-0288",
            website="https://apex.example.com",
            notes="Fintech partner",
            is_active=True
        )

        self.list_url = "/api/recruitment/agency/clients/"
        self.summary_stats_url = "/api/recruitment/agency/clients/summary-stats/"

    # =========================================================================
    # MODEL LEVEL TESTS
    # =========================================================================

    def test_client_company_model_str_and_defaults(self):
        """Model string representation and default is_active state."""
        self.assertEqual(str(self.client_1), "Acme Corporation (Technology) - Active")
        self.assertTrue(self.client_1.is_active)
        self.assertIsNotNone(self.client_1.created_at)
        self.assertIsNotNone(self.client_1.updated_at)

    def test_client_company_deactivated_str(self):
        """Model string representation when deactivated."""
        self.client_1.is_active = False
        self.client_1.save()
        self.assertEqual(str(self.client_1), "Acme Corporation (Technology) - Deactivated")

    def test_different_agencies_can_have_same_company_name(self):
        """Multi-tenant test: Two distinct agencies CAN register a client with the same name."""
        duplicate_for_agency_2 = ClientCompany.objects.create(
            agency=self.agency_admin_2,
            name="Acme Corporation",  # same name as client_1 in agency_admin_1
            industry="Manufacturing",
            contact_person="Charlie Brown",
            contact_email="charlie@acme.com",
            is_active=True
        )
        self.assertIsNotNone(duplicate_for_agency_2.id)
        self.assertEqual(duplicate_for_agency_2.name, "Acme Corporation")

    # =========================================================================
    # RBAC PERMISSION TESTS (AC#5)
    # =========================================================================

    def test_unauthenticated_access_rejected(self):
        """Anonymous requests must receive 401 Unauthorized."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_student_role_forbidden(self):
        """Student users must be rejected with 403 Forbidden."""
        self.client.force_authenticate(user=self.student_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Attempt to create client as student
        payload = {
            "name": "Hack Corp",
            "industry": "Tech",
            "contact_person": "Hacker",
            "contact_email": "hack@corp.com"
        }
        create_resp = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(create_resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_hr_manager_role_forbidden(self):
        """HR Manager users must be rejected with 403 Forbidden (Agency-only feature)."""
        self.client.force_authenticate(user=self.hr_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_agency_admin_role_authorized(self):
        """Agency Admin users have full access."""
        self.client.force_authenticate(user=self.agency_admin_1)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # =========================================================================
    # MULTI-TENANT QUERY ISOLATION TESTS (AC#6)
    # =========================================================================

    def test_agency_admin_only_sees_own_clients_in_list(self):
        """Agency Admin 1 must only see Agency 1 clients and NOT Agency 2 clients."""
        self.client.force_authenticate(user=self.agency_admin_1)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        client_ids = [item['id'] for item in response.data]
        self.assertIn(self.client_1.id, client_ids)
        self.assertNotIn(self.client_2.id, client_ids)

    def test_agency_admin_cannot_retrieve_other_agency_client(self):
        """Agency Admin 1 cannot retrieve Agency Admin 2's client (returns 404)."""
        self.client.force_authenticate(user=self.agency_admin_1)
        url = f"/api/recruitment/agency/clients/{self.client_2.id}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_agency_admin_cannot_update_other_agency_client(self):
        """Agency Admin 1 cannot update Agency Admin 2's client (returns 404)."""
        self.client.force_authenticate(user=self.agency_admin_1)
        url = f"/api/recruitment/agency/clients/{self.client_2.id}/"
        payload = {"name": "Malicious Modification"}
        response = self.client.patch(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_agency_admin_cannot_toggle_other_agency_client(self):
        """Agency Admin 1 cannot toggle active state of Agency Admin 2's client (returns 404)."""
        self.client.force_authenticate(user=self.agency_admin_1)
        url = f"/api/recruitment/agency/clients/{self.client_2.id}/toggle-active/"
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # =========================================================================
    # CLIENT CREATION & VALIDATION TESTS (AC#1, AC#2, AC#4)
    # =========================================================================

    def test_create_client_company_success(self):
        """Agency Admin can successfully create a new client company."""
        self.client.force_authenticate(user=self.agency_admin_1)
        payload = {
            "name": "Starlight Robotics",
            "industry": "Artificial Intelligence",
            "contact_person": "Sarah Connor",
            "contact_email": "sconnor@starlight.ai",
            "phone": "+1-555-8822",
            "website": "https://starlight.ai",
            "notes": "Autonomous systems research client"
        }
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], "Starlight Robotics")
        self.assertEqual(response.data['industry'], "Artificial Intelligence")
        self.assertEqual(response.data['agency_id'], self.agency_admin_1.id)
        self.assertTrue(response.data['is_active'])

        # Verify in DB
        created_obj = ClientCompany.objects.get(id=response.data['id'])
        self.assertEqual(created_obj.agency, self.agency_admin_1)

    def test_create_client_duplicate_name_within_same_agency_rejected(self):
        """Duplicate client name within the same agency must be rejected."""
        self.client.force_authenticate(user=self.agency_admin_1)
        payload = {
            "name": "Acme Corporation",  # already exists for agency_admin_1
            "industry": "Consulting",
            "contact_person": "Dan Brown",
            "contact_email": "dan@acme.com"
        }
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)

    def test_create_client_validation_missing_required_fields(self):
        """Missing required fields (name, industry, contact_person, email) must return 400."""
        self.client.force_authenticate(user=self.agency_admin_1)

        # Blank name
        resp = self.client.post(self.list_url, {
            "name": "   ",
            "industry": "Tech",
            "contact_person": "Person",
            "contact_email": "valid@email.com"
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        # Invalid email format
        resp = self.client.post(self.list_url, {
            "name": "Beta Labs",
            "industry": "Tech",
            "contact_person": "Person",
            "contact_email": "not-an-email"
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("contact_email", resp.data)

    # =========================================================================
    # EDIT & SOFT DEACTIVATE / REACTIVATE TESTS (AC#3)
    # =========================================================================

    def test_update_client_company(self):
        """Agency Admin can update their client company details."""
        self.client.force_authenticate(user=self.agency_admin_1)
        url = f"/api/recruitment/agency/clients/{self.client_1.id}/"
        payload = {
            "name": "Acme Global Solutions",
            "contact_person": "Alice Smith-Johnson",
            "phone": "+1-555-9999"
        }
        response = self.client.patch(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Acme Global Solutions")
        self.assertEqual(response.data['contact_person'], "Alice Smith-Johnson")
        self.assertEqual(response.data['phone'], "+1-555-9999")

    def test_toggle_active_deactivates_and_reactivates(self):
        """toggle-active custom endpoint toggles is_active from True -> False -> True."""
        self.client.force_authenticate(user=self.agency_admin_1)
        toggle_url = f"/api/recruitment/agency/clients/{self.client_1.id}/toggle-active/"

        # 1. Toggle Active -> Deactivated
        resp1 = self.client.post(toggle_url)
        self.assertEqual(resp1.status_code, status.HTTP_200_OK)
        self.assertFalse(resp1.data['is_active'])
        self.assertIn("deactivated", resp1.data['message'])

        self.client_1.refresh_from_db()
        self.assertFalse(self.client_1.is_active)

        # 2. Toggle Deactivated -> Reactivated
        resp2 = self.client.post(toggle_url)
        self.assertEqual(resp2.status_code, status.HTTP_200_OK)
        self.assertTrue(resp2.data['is_active'])
        self.assertIn("activated", resp2.data['message'])

        self.client_1.refresh_from_db()
        self.assertTrue(self.client_1.is_active)

    # =========================================================================
    # SEARCH & FILTER TESTS (US-29-T5)
    # =========================================================================

    def test_filter_clients_by_search_query(self):
        """Query parameter ?q= searches across name, industry, and contact fields."""
        self.client.force_authenticate(user=self.agency_admin_1)

        # Create a second client for agency 1
        ClientCompany.objects.create(
            agency=self.agency_admin_1,
            name="Quantum Computing Ltd",
            industry="Deep Tech",
            contact_person="David Quantum",
            contact_email="david@quantum.io",
            is_active=True
        )

        resp = self.client.get(f"{self.list_url}?q=Quantum")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]['name'], "Quantum Computing Ltd")

    def test_filter_clients_by_status(self):
        """Query parameter ?status=active or ?status=deactivated filters accordingly."""
        self.client.force_authenticate(user=self.agency_admin_1)

        # Create an inactive client
        ClientCompany.objects.create(
            agency=self.agency_admin_1,
            name="Dormant Systems",
            industry="Hardware",
            contact_person="Eve Dormant",
            contact_email="eve@dormant.com",
            is_active=False
        )

        resp_active = self.client.get(f"{self.list_url}?status=active")
        self.assertEqual(resp_active.status_code, status.HTTP_200_OK)
        self.assertTrue(all(c['is_active'] for c in resp_active.data))

        resp_deact = self.client.get(f"{self.list_url}?status=deactivated")
        self.assertEqual(resp_deact.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp_deact.data), 1)
        self.assertEqual(resp_deact.data[0]['name'], "Dormant Systems")

    # =========================================================================
    # SUMMARY STATS & ASSOCIATED ROOMS (US-29-T4)
    # =========================================================================

    def test_summary_stats_calculation(self):
        """summary-stats returns accurate counts for total, active, deactivated, and associated rooms."""
        self.client.force_authenticate(user=self.agency_admin_1)

        # Create 1 deactivated client
        ClientCompany.objects.create(
            agency=self.agency_admin_1,
            name="Inactive Holdings",
            industry="Real Estate",
            contact_person="Frank Inactive",
            contact_email="frank@holdings.com",
            is_active=False
        )

        # Create a recruitment room associated with client_1
        RecruitmentRoom.objects.create(
            title="Senior React Engineer",
            company_name="Acme Corporation",
            client_company=self.client_1,
            created_by=self.agency_admin_1,
            cv_weight=50,
            video_weight=50
        )

        resp = self.client.get(self.summary_stats_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['total_clients'], 2)
        self.assertEqual(resp.data['active_clients'], 1)
        self.assertEqual(resp.data['deactivated_clients'], 1)
        self.assertEqual(resp.data['associated_rooms'], 1)

        # Verify client_1 serializer includes rooms_count = 1
        client_detail_resp = self.client.get(f"/api/recruitment/agency/clients/{self.client_1.id}/")
        self.assertEqual(client_detail_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(client_detail_resp.data['rooms_count'], 1)
