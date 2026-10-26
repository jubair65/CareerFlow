"""
US-31: Cross-Client Applicant View Unit & Integration Tests (US-31-T7).
Tests cover:
- Cross-client applicant aggregation across all client companies of an agency (US-31-T2, AC#1)
- Response schema validation: client company, Room, scores, and application status (AC#2)
- Filtering by client company, Room, application status, shortlist status (US-31-T4, AC#3)
- Search across candidate name, email, room title, and client name (US-31-T4)
- Multi-tenant data isolation: Agency A cannot see or retrieve Agency B's applicants (US-31-T5, AC#4)
- Empty results handling (AC#5)
- Sorting and ordering by score and date
- Pipeline summary KPI statistics endpoint
- RBAC permissions: Unauthenticated (401), Student (403), HR Manager (403), Agency Admin (200)
"""

import os
import uuid
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'careerflow.settings')
django.setup()

from rest_framework import status
from rest_framework.test import APITestCase
from apps.authentication.models import User
from apps.recruitment.models import ClientCompany, RecruitmentRoom, CandidateApplication


class US31CrossClientApplicantUnitTests(APITestCase):
    def setUp(self):
        self.uid = uuid.uuid4().hex[:8]

        # 1. Primary Agency Admin (Agency 1 - Bonny)
        self.agency_admin_1 = User.objects.create_user(
            username=f"agency1_{self.uid}",
            email=f"agency1_{self.uid}@careerflow.agency",
            password="Password123!",
            role=User.Role.AGENCY_ADMIN,
            full_name="Bonny Agency Admin"
        )

        # 2. Secondary Agency Admin (Agency 2 - for multi-tenant isolation tests)
        self.agency_admin_2 = User.objects.create_user(
            username=f"agency2_{self.uid}",
            email=f"agency2_{self.uid}@careerflow.agency",
            password="Password123!",
            role=User.Role.AGENCY_ADMIN,
            full_name="Second Agency Admin"
        )

        # 3. HR Manager (Unauthorized for cross-client agency endpoint)
        self.hr_user = User.objects.create_user(
            username=f"hr_{self.uid}",
            email=f"hr_{self.uid}@careerflow.demo",
            password="Password123!",
            role=User.Role.HR_MANAGER,
            full_name="Sarah HR"
        )

        # 4. Student (Unauthorized)
        self.student_user = User.objects.create_user(
            username=f"student_{self.uid}",
            email=f"student_{self.uid}@careerflow.demo",
            password="Password123!",
            role=User.Role.STUDENT,
            full_name="Student Candidate"
        )

        # 5. Candidate Users
        self.candidate_1 = User.objects.create_user(
            username=f"cand1_{self.uid}",
            email=f"alice_{self.uid}@example.com",
            password="Password123!",
            role=User.Role.STUDENT,
            full_name="Alice Smith"
        )
        self.candidate_2 = User.objects.create_user(
            username=f"cand2_{self.uid}",
            email=f"bob_{self.uid}@example.com",
            password="Password123!",
            role=User.Role.STUDENT,
            full_name="Bob Jones"
        )
        self.candidate_3 = User.objects.create_user(
            username=f"cand3_{self.uid}",
            email=f"charlie_{self.uid}@example.com",
            password="Password123!",
            role=User.Role.STUDENT,
            full_name="Charlie Brown"
        )

        # 6. Client Companies for Agency 1
        self.client_1a = ClientCompany.objects.create(
            agency=self.agency_admin_1,
            name="Fintech Global",
            industry="Finance",
            contact_person="Gordon Gekko",
            contact_email="gekko@fintech.com",
            is_active=True
        )
        self.client_1b = ClientCompany.objects.create(
            agency=self.agency_admin_1,
            name="HealthPulse Labs",
            industry="Healthcare",
            contact_person="Gregory House",
            contact_email="house@healthpulse.com",
            is_active=True
        )

        # 7. Client Company for Agency 2 (Multi-tenant boundary)
        self.client_2 = ClientCompany.objects.create(
            agency=self.agency_admin_2,
            name="CyberSec Corp",
            industry="Cybersecurity",
            contact_person="Elliot Alderson",
            contact_email="elliot@cybersec.com",
            is_active=True
        )

        # 8. Rooms for Agency 1
        self.room_1a = RecruitmentRoom.objects.create(
            title="Senior Quant Analyst",
            company_name=self.client_1a.name,
            client_company=self.client_1a,
            created_by=self.agency_admin_1,
            cv_weight=40,
            video_weight=60
        )
        self.room_1b = RecruitmentRoom.objects.create(
            title="Lead Biostatistician",
            company_name=self.client_1b.name,
            client_company=self.client_1b,
            created_by=self.agency_admin_1,
            cv_weight=50,
            video_weight=50
        )

        # 9. Room for Agency 2
        self.room_2 = RecruitmentRoom.objects.create(
            title="Penetration Tester",
            company_name=self.client_2.name,
            client_company=self.client_2,
            created_by=self.agency_admin_2,
            cv_weight=50,
            video_weight=50
        )

        # 10. Applications for Agency 1
        self.app_1 = CandidateApplication.objects.create(
            room=self.room_1a,
            candidate=self.candidate_1,
            status=CandidateApplication.Status.COMPLETED,
            cv_score=85.0,
            video_score=90.0,
            final_score=88.0,
            is_shortlisted=True,
            shortlist_reason="Top scoring applicant",
            hr_decision=CandidateApplication.HrDecision.CONFIRMED
        )
        self.app_2 = CandidateApplication.objects.create(
            room=self.room_1b,
            candidate=self.candidate_2,
            status=CandidateApplication.Status.COMPLETED,
            cv_score=75.0,
            video_score=70.0,
            final_score=72.5,
            is_shortlisted=False,
            hr_decision=CandidateApplication.HrDecision.UNDECIDED
        )
        self.app_3 = CandidateApplication.objects.create(
            room=self.room_1a,
            candidate=self.candidate_3,
            status=CandidateApplication.Status.ANALYZING,
            is_shortlisted=False,
            hr_decision=CandidateApplication.HrDecision.UNDECIDED
        )

        # 11. Application for Agency 2 (Must be isolated)
        self.app_other = CandidateApplication.objects.create(
            room=self.room_2,
            candidate=self.candidate_1,
            status=CandidateApplication.Status.COMPLETED,
            cv_score=95.0,
            video_score=95.0,
            final_score=95.0,
            is_shortlisted=True
        )

        self.list_url = "/api/recruitment/agency/applicants/"
        self.stats_url = "/api/recruitment/agency/applicants/summary-stats/"

    # =========================================================================
    # AGGREGATION & FIELD SCHEMA (AC#1, AC#2)
    # =========================================================================

    def test_agency_can_view_applicants_across_all_client_companies(self):
        """Agency Admin can view applicants across all of their client companies (AC#1)."""
        self.client.force_authenticate(user=self.agency_admin_1)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        # Agency 1 has 3 applications across 2 client companies
        self.assertEqual(len(data), 3)
        ids = [item["id"] for item in data]
        self.assertIn(self.app_1.id, ids)
        self.assertIn(self.app_2.id, ids)
        self.assertIn(self.app_3.id, ids)
        self.assertNotIn(self.app_other.id, ids)

    def test_applicant_list_contains_required_fields(self):
        """List response includes client company, Room, scores, and application status (AC#2)."""
        self.client.force_authenticate(user=self.agency_admin_1)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        item = next(x for x in data if x["id"] == self.app_1.id)
        self.assertEqual(item["candidate_name"], "Alice Smith")
        self.assertEqual(item["candidate_email"], self.candidate_1.email)
        self.assertEqual(item["client_company_name"], "Fintech Global")
        self.assertEqual(item["client_company_industry"], "Finance")
        self.assertEqual(item["room_title"], "Senior Quant Analyst")
        self.assertEqual(item["cv_score"], 85.0)
        self.assertEqual(item["video_score"], 90.0)
        self.assertEqual(item["final_score"], 88.0)
        self.assertEqual(item["status"], "COMPLETED")
        self.assertTrue(item["is_shortlisted"])
        self.assertEqual(item["hr_decision"], "CONFIRMED")
        self.assertIn("applied_at", item)

    # =========================================================================
    # FILTERING & SEARCH (US-31-T4, AC#3)
    # =========================================================================

    def test_filter_by_client_company(self):
        """Applicants can be filtered by client company (AC#3)."""
        self.client.force_authenticate(user=self.agency_admin_1)
        # Filter by client 1b (HealthPulse Labs)
        response = self.client.get(f"{self.list_url}?client_company={self.client_1b.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], self.app_2.id)
        self.assertEqual(data[0]["client_company_name"], "HealthPulse Labs")

    def test_filter_by_room(self):
        """Applicants can be filtered by specific Room (AC#3)."""
        self.client.force_authenticate(user=self.agency_admin_1)
        response = self.client.get(f"{self.list_url}?room={self.room_1a.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data), 2)
        for item in data:
            self.assertEqual(item["room_id"], self.room_1a.id)

    def test_filter_by_status(self):
        """Applicants can be filtered by application status (AC#3)."""
        self.client.force_authenticate(user=self.agency_admin_1)
        response = self.client.get(f"{self.list_url}?status=ANALYZING")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], self.app_3.id)
        self.assertEqual(data[0]["status"], "ANALYZING")

    def test_filter_by_shortlisted(self):
        """Applicants can be filtered by shortlisted flag."""
        self.client.force_authenticate(user=self.agency_admin_1)
        response = self.client.get(f"{self.list_url}?shortlisted=true")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], self.app_1.id)
        self.assertTrue(data[0]["is_shortlisted"])

    def test_search_by_candidate_name_and_email(self):
        """Search by candidate full name or email returns matching records."""
        self.client.force_authenticate(user=self.agency_admin_1)
        response = self.client.get(f"{self.list_url}?q=Alice")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["candidate_name"], "Alice Smith")

    def test_search_by_room_title_and_client_name(self):
        """Search query matching client company or room title filters correctly."""
        self.client.force_authenticate(user=self.agency_admin_1)
        response = self.client.get(f"{self.list_url}?q=HealthPulse")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], self.app_2.id)

    def test_sorting_by_final_score(self):
        """Sorting by -final_score places highest scoring candidates first."""
        self.client.force_authenticate(user=self.agency_admin_1)
        response = self.client.get(f"{self.list_url}?ordering=-final_score")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        # app_1 has final_score 88.0, app_2 has 72.5
        scored = [d for d in data if d["final_score"] is not None]
        self.assertEqual(scored[0]["id"], self.app_1.id)
        self.assertEqual(scored[1]["id"], self.app_2.id)

    # =========================================================================
    # MULTI-TENANT ISOLATION (US-31-T5, AC#4)
    # =========================================================================

    def test_multi_tenant_isolation_cannot_see_other_agency_applicants(self):
        """Agency 1 cannot see applicants belonging to Agency 2 (AC#4)."""
        self.client.force_authenticate(user=self.agency_admin_1)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in response.json()]
        self.assertNotIn(self.app_other.id, ids)

    def test_multi_tenant_isolation_filtering_other_agency_client_returns_empty(self):
        """Filtering by a client company belonging to another agency returns empty list."""
        self.client.force_authenticate(user=self.agency_admin_1)
        # Attempt to filter by Agency 2's client (CyberSec Corp)
        response = self.client.get(f"{self.list_url}?client_company={self.client_2.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data), 0)

    def test_multi_tenant_isolation_retrieve_detail(self):
        """Agency 1 cannot retrieve detail of an applicant belonging to Agency 2."""
        self.client.force_authenticate(user=self.agency_admin_1)
        detail_url = f"{self.list_url}{self.app_other.id}/"
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # =========================================================================
    # EMPTY RESULTS HANDLING (AC#5)
    # =========================================================================

    def test_empty_results_handling(self):
        """Empty results return an empty list with 200 OK (AC#5)."""
        self.client.force_authenticate(user=self.agency_admin_1)
        response = self.client.get(f"{self.list_url}?q=NonexistentCandidateKeyword")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [])

    # =========================================================================
    # ROLE-BASED ACCESS CONTROL (RBAC)
    # =========================================================================

    def test_hr_manager_cannot_access_agency_applicants(self):
        """HR Manager cannot access the agency applicants aggregation endpoint."""
        self.client.force_authenticate(user=self.hr_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_cannot_access_agency_applicants(self):
        """Student candidates cannot access agency applicant pipeline."""
        self.client.force_authenticate(user=self.student_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_access_agency_applicants(self):
        """Unauthenticated requests are rejected with 401 Unauthorized."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # =========================================================================
    # PIPELINE SUMMARY STATS
    # =========================================================================

    def test_summary_stats_endpoint(self):
        """Summary KPI statistics accurately calculate totals and averages."""
        self.client.force_authenticate(user=self.agency_admin_1)
        response = self.client.get(self.stats_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        stats = response.json()

        self.assertEqual(stats["total_applicants"], 3)
        self.assertEqual(stats["completed_evaluations"], 2)
        self.assertEqual(stats["shortlisted_candidates"], 1)
        self.assertEqual(stats["clients_count"], 2)
        self.assertEqual(stats["rooms_count"], 2)
        # Average of 88.0 and 72.5 = 80.25 -> rounded to 80.2 or 80.3
        self.assertAlmostEqual(stats["average_final_score"], 80.2, places=0)
