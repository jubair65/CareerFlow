"""
US-30: Agency Room Creation for Client Companies Unit & Integration Tests (US-30-T7).
Tests cover:
- Room-to-client company association model and auto company name synchronization (US-30-T1, AC#1, AC#2)
- Multi-tenant security checks: Agency A cannot create room for Agency B's client (US-30-T5, AC#5)
- Inactive client validation: Cannot create room for deactivated client company
- Room creation via Agency API (US-30-T2, AC#1)
- Reuse of job requirements, evaluation weighting, and link generation for Agency Rooms (US-30-T3, AC#3, AC#4)
- Multi-tenant isolation: Agency A cannot list or retrieve Agency B's rooms (US-30-T5)
- Rooms grouped by client company endpoint (AC#6)
- Summary KPI stats for agency room dashboard
- RBAC permissions: Unauthenticated (401), Student (403), HR Manager (403), Agency Admin (200/201)
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


class US30AgencyRoomManagementUnitTests(APITestCase):
    def setUp(self):
        self.uid = uuid.uuid4().hex[:8]

        # 1. Primary Agency Admin (Bonny / Agency 1)
        self.agency_admin_1 = User.objects.create_user(
            username=f"bonny_agency_{self.uid}",
            email=f"bonny_{self.uid}@careerflow.agency",
            password="Password123!",
            role=User.Role.AGENCY_ADMIN,
            full_name="Bonny Agency Admin"
        )

        # 2. Secondary Agency Admin (Agency 2 - for multi-tenant isolation tests)
        self.agency_admin_2 = User.objects.create_user(
            username=f"other_agency_{self.uid}",
            email=f"other_{self.uid}@careerflow.agency",
            password="Password123!",
            role=User.Role.AGENCY_ADMIN,
            full_name="Other Agency Admin"
        )

        # 3. HR Manager (Unauthorized for Agency room endpoints)
        self.hr_user = User.objects.create_user(
            username=f"hr_{self.uid}",
            email=f"hr_{self.uid}@careerflow.demo",
            password="Password123!",
            role=User.Role.HR_MANAGER,
            full_name="HR Manager User"
        )

        # 4. Student (Unauthorized)
        self.student_user = User.objects.create_user(
            username=f"student_{self.uid}",
            email=f"student_{self.uid}@careerflow.demo",
            password="Password123!",
            role=User.Role.STUDENT,
            full_name="Student Candidate"
        )

        # 5. Active Client Companies for Agency 1
        self.client_1a = ClientCompany.objects.create(
            agency=self.agency_admin_1,
            name="Apex Dynamics",
            industry="Fintech",
            contact_person="Michael Scott",
            contact_email="mscott@apexdynamics.com",
            is_active=True
        )
        self.client_1b = ClientCompany.objects.create(
            agency=self.agency_admin_1,
            name="CloudScale Systems",
            industry="Cloud Computing",
            contact_person="Jim Halpert",
            contact_email="jhalpert@cloudscale.io",
            is_active=True
        )

        # 6. Deactivated Client Company for Agency 1
        self.client_1_inactive = ClientCompany.objects.create(
            agency=self.agency_admin_1,
            name="Legacy Tech Inc",
            industry="Manufacturing",
            contact_person="Dwight Schrute",
            contact_email="dwight@legacytech.com",
            is_active=False
        )

        # 7. Client Company for Agency 2 (Tenant boundary)
        self.client_2 = ClientCompany.objects.create(
            agency=self.agency_admin_2,
            name="CyberSec Global",
            industry="Security",
            contact_person="Pam Beesly",
            contact_email="pam@cybersec.com",
            is_active=True
        )

        self.rooms_url = "/api/recruitment/agency/rooms/"
        self.grouped_url = "/api/recruitment/agency/rooms/grouped-by-client/"
        self.stats_url = "/api/recruitment/agency/rooms/summary-stats/"

    # =========================================================================
    # MODEL LEVEL & INTEGRITY TESTS (US-30-T1)
    # =========================================================================

    def test_model_clean_syncs_company_name_from_client_company(self):
        """Room automatically synchronizes company_name if left empty."""
        room = RecruitmentRoom(
            title="Senior Backend Engineer",
            client_company=self.client_1a,
            created_by=self.agency_admin_1
        )
        room.save()
        self.assertEqual(room.company_name, "Apex Dynamics")
        self.assertEqual(room.client_company, self.client_1a)
        self.assertTrue(bool(room.share_token))

    def test_model_clean_rejects_cross_agency_association(self):
        """Model-level validation prevents assigning client company of another agency."""
        from django.core.exceptions import ValidationError
        room = RecruitmentRoom(
            title="DevOps Lead",
            client_company=self.client_2,  # Belongs to Agency 2
            created_by=self.agency_admin_1   # Agency 1
        )
        with self.assertRaises(ValidationError) as ctx:
            room.clean()
        self.assertIn('client_company', ctx.exception.message_dict)

    def test_model_clean_rejects_deactivated_client_for_new_room(self):
        """Model-level validation prevents creating new room for deactivated client."""
        from django.core.exceptions import ValidationError
        room = RecruitmentRoom(
            title="QA Engineer",
            client_company=self.client_1_inactive,
            created_by=self.agency_admin_1
        )
        with self.assertRaises(ValidationError) as ctx:
            room.clean()
        self.assertIn('client_company', ctx.exception.message_dict)

    # =========================================================================
    # ROOM CREATION API & CLIENT COMPANY ASSOCIATION (US-30-T2)
    # =========================================================================

    def test_agency_create_room_success(self):
        """Agency Admin can create a Room for a selected client company (AC#1, AC#2)."""
        self.client.force_authenticate(user=self.agency_admin_1)
        payload = {
            "title": "Lead AI Architect",
            "client_company": self.client_1a.id,
            "department": "Engineering",
            "description": "Architect autonomous AI evaluation agents."
        }
        response = self.client.post(self.rooms_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertEqual(data["message"], "Agency recruitment room created successfully.")

        room = data["room"]
        self.assertEqual(room["title"], "Lead AI Architect")
        self.assertEqual(room["client_company"], self.client_1a.id)
        self.assertEqual(room["client_company_name"], "Apex Dynamics")
        self.assertEqual(room["company_name"], "Apex Dynamics")
        self.assertEqual(room["created_by"], self.agency_admin_1.id)
        self.assertEqual(room["status"], "ACTIVE")
        self.assertTrue(bool(room["share_token"]))
        self.assertIn(f"/apply/{room['share_token']}", room["share_url"])

        # Check in Database
        db_room = RecruitmentRoom.objects.get(id=room["id"])
        self.assertEqual(db_room.client_company, self.client_1a)
        self.assertEqual(db_room.created_by, self.agency_admin_1)

    def test_agency_create_room_missing_client_company_fails(self):
        """Agency room creation requires a client company."""
        self.client.force_authenticate(user=self.agency_admin_1)
        payload = {
            "title": "General Recruiter",
            "department": "Talent"
        }
        response = self.client.post(self.rooms_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertIn("client_company", data)

    # =========================================================================
    # MULTI-TENANT OWNERSHIP CHECKS (US-30-T5)
    # =========================================================================

    def test_agency_cannot_create_room_for_another_agency_client(self):
        """Agency 1 cannot associate a Room with Agency 2's client company (AC#5)."""
        self.client.force_authenticate(user=self.agency_admin_1)
        payload = {
            "title": "Security Analyst",
            "client_company": self.client_2.id  # Belongs to Agency 2
        }
        response = self.client.post(self.rooms_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertIn("client_company", data)

    def test_agency_cannot_create_room_for_deactivated_client(self):
        """Agency cannot create a room for a deactivated client company."""
        self.client.force_authenticate(user=self.agency_admin_1)
        payload = {
            "title": "Legacy Maintenance Lead",
            "client_company": self.client_1_inactive.id
        }
        response = self.client.post(self.rooms_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertIn("client_company", data)

    def test_agency_multi_tenant_isolation_list(self):
        """Agency 1 can only see their own client rooms, not Agency 2's."""
        # Create room for Agency 1
        room_1 = RecruitmentRoom.objects.create(
            title="Agency 1 Room",
            client_company=self.client_1a,
            created_by=self.agency_admin_1
        )
        # Create room for Agency 2
        room_2 = RecruitmentRoom.objects.create(
            title="Agency 2 Room",
            client_company=self.client_2,
            created_by=self.agency_admin_2
        )

        self.client.force_authenticate(user=self.agency_admin_1)
        response = self.client.get(self.rooms_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [r["id"] for r in response.json()]
        self.assertIn(room_1.id, ids)
        self.assertNotIn(room_2.id, ids)

    def test_agency_multi_tenant_isolation_retrieve_and_edit(self):
        """Agency 1 cannot retrieve, edit, or delete Agency 2's room (404/403)."""
        room_2 = RecruitmentRoom.objects.create(
            title="Agency 2 Confidential Room",
            client_company=self.client_2,
            created_by=self.agency_admin_2
        )

        self.client.force_authenticate(user=self.agency_admin_1)
        detail_url = f"{self.rooms_url}{room_2.id}/"
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Attempt to patch
        patch_response = self.client.patch(detail_url, {"title": "Hacked Title"})
        self.assertEqual(patch_response.status_code, status.HTTP_404_NOT_FOUND)

    # =========================================================================
    # ROLE-BASED ACCESS CONTROL (RBAC) CHECKS
    # =========================================================================

    def test_hr_manager_cannot_access_agency_rooms_endpoint(self):
        """HR Manager cannot access agency room management endpoints."""
        self.client.force_authenticate(user=self.hr_user)
        response = self.client.get(self.rooms_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_cannot_access_agency_rooms_endpoint(self):
        """Student candidates cannot access agency room management endpoints."""
        self.client.force_authenticate(user=self.student_user)
        response = self.client.get(self.rooms_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_access_agency_rooms_endpoint(self):
        """Unauthenticated requests are rejected with 401."""
        response = self.client.get(self.rooms_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # =========================================================================
    # REUSE OF REQUIREMENTS, WEIGHTING & LINK ACTIONS (US-30-T3)
    # =========================================================================

    def test_agency_room_requirements_configuration(self):
        """Agency Admin can configure job requirements and skills for their room (AC#3)."""
        room = RecruitmentRoom.objects.create(
            title="Frontend Specialist",
            client_company=self.client_1a,
            created_by=self.agency_admin_1
        )
        self.client.force_authenticate(user=self.agency_admin_1)
        req_url = f"{self.rooms_url}{room.id}/requirements/"

        payload = {
            "role_category": "Design & UI",
            "experience_level": "SENIOR",
            "requirements_text": "Strong React and TailwindCSS experience.",
            "skills_required": [
                {"name": "React", "importance": "REQUIRED", "category": "Technical"},
                {"name": "TypeScript", "importance": "REQUIRED", "category": "Technical"}
            ]
        }
        response = self.client.patch(req_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["requirements"]["role_category"], "Design & UI")
        self.assertEqual(data["requirements"]["experience_level"], "SENIOR")

        # Verify DB
        room.refresh_from_db()
        self.assertEqual(room.role_category, "Design & UI")
        self.assertEqual(room.experience_level, "SENIOR")
        self.assertEqual(len(room.skills_required), 2)

    def test_agency_room_weighting_configuration(self):
        """Agency Admin can configure CV vs Video evaluation weighting (AC#3)."""
        room = RecruitmentRoom.objects.create(
            title="Sales Director",
            client_company=self.client_1a,
            created_by=self.agency_admin_1
        )
        self.client.force_authenticate(user=self.agency_admin_1)
        weighting_url = f"{self.rooms_url}{room.id}/weighting/"

        payload = {
            "cv_weight": 30,
            "video_weight": 70
        }
        response = self.client.patch(weighting_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        room.refresh_from_db()
        self.assertEqual(room.cv_weight, 30)
        self.assertEqual(room.video_weight, 70)

    def test_agency_room_link_retrieval_and_lifecycle(self):
        """Agency Admin can retrieve shareable application link and toggle active state (AC#4)."""
        room = RecruitmentRoom.objects.create(
            title="Product Designer",
            client_company=self.client_1a,
            created_by=self.agency_admin_1
        )
        self.client.force_authenticate(user=self.agency_admin_1)
        link_url = f"{self.rooms_url}{room.id}/link/"

        # 1. Retrieve link
        response = self.client.get(link_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        token = data["link"]["share_token"]
        self.assertTrue(bool(token))
        self.assertTrue(data["link"]["link_is_active"])

        # 2. Deactivate link
        deact_response = self.client.post(f"{self.rooms_url}{room.id}/link/deactivate/")
        self.assertEqual(deact_response.status_code, status.HTTP_200_OK)
        room.refresh_from_db()
        self.assertFalse(room.link_is_active)

        # 3. Reactivate link
        act_response = self.client.post(f"{self.rooms_url}{room.id}/link/activate/")
        self.assertEqual(act_response.status_code, status.HTTP_200_OK)
        room.refresh_from_db()
        self.assertTrue(room.link_is_active)

    # =========================================================================
    # GROUPED-BY-CLIENT & KPI SUMMARY (AC#6)
    # =========================================================================

    def test_grouped_by_client_endpoint(self):
        """Agency Admin can view rooms grouped by client company (AC#6)."""
        # Create 2 rooms for client 1a and 1 room for client 1b
        RecruitmentRoom.objects.create(
            title="Room A1",
            client_company=self.client_1a,
            created_by=self.agency_admin_1
        )
        RecruitmentRoom.objects.create(
            title="Room A2",
            client_company=self.client_1a,
            created_by=self.agency_admin_1
        )
        RecruitmentRoom.objects.create(
            title="Room B1",
            client_company=self.client_1b,
            created_by=self.agency_admin_1
        )

        self.client.force_authenticate(user=self.agency_admin_1)
        response = self.client.get(self.grouped_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIsInstance(data, list)
        
        client_map = {item["client_id"]: item for item in data}
        self.assertIn(self.client_1a.id, client_map)
        self.assertIn(self.client_1b.id, client_map)
        self.assertEqual(client_map[self.client_1a.id]["rooms_count"], 2)
        self.assertEqual(client_map[self.client_1b.id]["rooms_count"], 1)

    def test_agency_summary_stats_endpoint(self):
        """Summary stats endpoint accurately calculates totals."""
        RecruitmentRoom.objects.create(
            title="Room 1",
            client_company=self.client_1a,
            created_by=self.agency_admin_1,
            status=RecruitmentRoom.Status.ACTIVE
        )
        RecruitmentRoom.objects.create(
            title="Room 2",
            client_company=self.client_1b,
            created_by=self.agency_admin_1,
            status=RecruitmentRoom.Status.PAUSED
        )

        self.client.force_authenticate(user=self.agency_admin_1)
        response = self.client.get(self.stats_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        stats = response.json()
        self.assertEqual(stats["total_rooms"], 2)
        self.assertEqual(stats["active_rooms"], 1)
        self.assertEqual(stats["clients_with_rooms"], 2)
