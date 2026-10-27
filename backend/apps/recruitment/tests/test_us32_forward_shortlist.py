"""
US-32: Forward Shortlisted Candidate Profiles to Client Companies Unit & Integration Tests (US-32-T7).
Tests cover:
- Forwarding shortlisted candidates to client company contact (AC#1, AC#3)
- Shortlist validation guard: only is_shortlisted=True can be forwarded (AC#2)
- Dossier data snapshot: scores, skills, evaluation summary (AC#4)
- Forwarding history and CandidateForwardRecord audit trail in database (AC#5)
- Confirmation response and error handling (AC#6)
- Multi-tenant data isolation: Agency A cannot forward to or access Agency B's clients/records
- Deactivated client protection
- Transactional email dispatch simulation
- RBAC permissions: Unauthenticated (401), Student (403), HR Manager (403), Agency Admin (200/201)
"""

import os
import uuid
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'careerflow.settings')
django.setup()

from django.core import mail
from rest_framework import status
from rest_framework.test import APITestCase
from apps.authentication.models import User
from apps.recruitment.models import ClientCompany, RecruitmentRoom, CandidateApplication, CandidateForwardRecord


class US32ForwardShortlistUnitTests(APITestCase):
    def setUp(self):
        self.uid = uuid.uuid4().hex[:8]

        # 1. Primary Agency Admin (Agency 1)
        self.agency_admin_1 = User.objects.create_user(
            username=f"agency1_{self.uid}",
            email=f"agency1_{self.uid}@careerflow.agency",
            password="Password123!",
            role=User.Role.AGENCY_ADMIN,
            full_name="Mobin Agency Admin"
        )

        # 2. Secondary Agency Admin (Agency 2 - for multi-tenant isolation tests)
        self.agency_admin_2 = User.objects.create_user(
            username=f"agency2_{self.uid}",
            email=f"agency2_{self.uid}@careerflow.agency",
            password="Password123!",
            role=User.Role.AGENCY_ADMIN,
            full_name="Second Agency Admin"
        )

        # 3. HR Manager (Unauthorized for agency forward endpoint)
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
            full_name="Student Applicant"
        )

        # 5. Client Companies for Agency 1
        self.client_1a = ClientCompany.objects.create(
            agency=self.agency_admin_1,
            name="Apex Global Tech",
            industry="FinTech",
            contact_person="Sarah Jenkins",
            contact_email=f"s.jenkins_{self.uid}@apextech.com",
            phone="+1-555-0101",
            is_active=True
        )
        self.client_1b = ClientCompany.objects.create(
            agency=self.agency_admin_1,
            name="BioPulse Labs",
            industry="Healthcare",
            contact_person="Dr. Marcus Bell",
            contact_email=f"marcus_{self.uid}@biopulse.com",
            phone="+1-555-0102",
            is_active=True
        )
        self.inactive_client = ClientCompany.objects.create(
            agency=self.agency_admin_1,
            name="Deactivated Corp",
            industry="Legacy",
            contact_person="Retired Lead",
            contact_email=f"legacy_{self.uid}@legacy.com",
            is_active=False
        )

        # 6. Client Company for Agency 2 (Multi-tenant check)
        self.client_2 = ClientCompany.objects.create(
            agency=self.agency_admin_2,
            name="Foreign Systems Ltd",
            industry="Telecommunications",
            contact_person="Foreign Lead",
            contact_email=f"foreign_{self.uid}@foreign.com",
            is_active=True
        )

        # 7. Recruitment Rooms for Agency 1
        self.room_1a = RecruitmentRoom.objects.create(
            title="Senior Backend Engineer",
            company_name=self.client_1a.name,
            client_company=self.client_1a,
            department="Engineering",
            role_category="Engineering",
            experience_level="SENIOR",
            created_by=self.agency_admin_1,
            cv_weight=50,
            video_weight=50
        )
        self.room_1b = RecruitmentRoom.objects.create(
            title="Clinical Data Analyst",
            company_name=self.client_1b.name,
            client_company=self.client_1b,
            department="Research",
            role_category="Data & Analytics",
            experience_level="MID",
            created_by=self.agency_admin_1,
            cv_weight=60,
            video_weight=40
        )

        # 8. Recruitment Room for Agency 2
        self.room_2 = RecruitmentRoom.objects.create(
            title="Network Systems Architect",
            company_name=self.client_2.name,
            client_company=self.client_2,
            department="IT",
            role_category="Engineering",
            experience_level="LEAD",
            created_by=self.agency_admin_2,
            cv_weight=50,
            video_weight=50
        )

        # 9. Candidates
        self.candidate_1 = User.objects.create_user(
            username=f"cand1_{self.uid}",
            email=f"alice_{self.uid}@test.com",
            password="Password123!",
            role=User.Role.STUDENT,
            full_name="Alice Smith"
        )
        self.candidate_2 = User.objects.create_user(
            username=f"cand2_{self.uid}",
            email=f"bob_{self.uid}@test.com",
            password="Password123!",
            role=User.Role.STUDENT,
            full_name="Bob Johnson"
        )
        self.candidate_3 = User.objects.create_user(
            username=f"cand3_{self.uid}",
            email=f"carol_{self.uid}@test.com",
            password="Password123!",
            role=User.Role.STUDENT,
            full_name="Carol White"
        )

        # 10. Candidate Applications
        # App 1: Room 1a, Shortlisted (Ready to forward)
        self.app_shortlisted_1 = CandidateApplication.objects.create(
            room=self.room_1a,
            candidate=self.candidate_1,
            status=CandidateApplication.Status.COMPLETED,
            cv_score=92.0,
            video_score=88.0,
            final_score=90.0,
            is_shortlisted=True,
            shortlist_reason="Top 5% score match with extensive Django expertise",
            hr_decision=CandidateApplication.HrDecision.CONFIRMED
        )

        # App 2: Room 1a, Shortlisted (Ready to forward)
        self.app_shortlisted_2 = CandidateApplication.objects.create(
            room=self.room_1a,
            candidate=self.candidate_2,
            status=CandidateApplication.Status.COMPLETED,
            cv_score=85.0,
            video_score=83.0,
            final_score=84.0,
            is_shortlisted=True,
            shortlist_reason="Exceeded minimum qualification threshold",
            hr_decision=CandidateApplication.HrDecision.CONFIRMED
        )

        # App 3: Room 1a, NOT shortlisted (Should be rejected for forward)
        self.app_unshortlisted = CandidateApplication.objects.create(
            room=self.room_1a,
            candidate=self.candidate_3,
            status=CandidateApplication.Status.COMPLETED,
            cv_score=60.0,
            video_score=65.0,
            final_score=62.5,
            is_shortlisted=False,
            shortlist_reason="",
            hr_decision=CandidateApplication.HrDecision.UNDECIDED
        )

        # App 4: Room 1b (Belongs to Client 1b, not Client 1a)
        self.app_client_1b = CandidateApplication.objects.create(
            room=self.room_1b,
            candidate=self.candidate_1,
            status=CandidateApplication.Status.COMPLETED,
            cv_score=90.0,
            video_score=85.0,
            final_score=88.0,
            is_shortlisted=True,
            shortlist_reason="Excellent clinical research alignment",
            hr_decision=CandidateApplication.HrDecision.CONFIRMED
        )

        # App 5: Room 2 (Belongs to Agency 2)
        self.app_agency_2 = CandidateApplication.objects.create(
            room=self.room_2,
            candidate=self.candidate_2,
            status=CandidateApplication.Status.COMPLETED,
            cv_score=95.0,
            video_score=95.0,
            final_score=95.0,
            is_shortlisted=True
        )

        self.forward_url = "/api/recruitment/agency/forward-shortlist/"
        self.history_url = "/api/recruitment/agency/forward-history/"

    # =========================================================================
    # CORE FORWARDING & SHORTLIST GUARD (AC#1, AC#2, AC#3, AC#6)
    # =========================================================================

    def test_forward_shortlisted_candidates_success(self):
        """Agency Admin can forward shortlisted candidates to client company representative (AC#1, AC#3, AC#6)."""
        self.client.force_authenticate(user=self.agency_admin_1)
        mail.outbox = []

        payload = {
            "client_id": self.client_1a.id,
            "application_ids": [self.app_shortlisted_1.id, self.app_shortlisted_2.id],
            "recipient_email": self.client_1a.contact_email,
            "recipient_name": self.client_1a.contact_person,
            "notes": "Here are the top 2 shortlisted candidates for your final interview round."
        }

        response = self.client.post(self.forward_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()

        self.assertIn("forward_id", data)
        self.assertEqual(data["forwarded_candidates_count"], 2)
        self.assertEqual(data["recipient_email"], self.client_1a.contact_email)
        self.assertEqual(data["recipient_name"], self.client_1a.contact_person)
        self.assertEqual(data["status"], "DELIVERED")
        self.assertIn("Successfully forwarded 2 shortlisted candidate profile(s)", data["message"])

        # Verify DB audit record (AC#5)
        record = CandidateForwardRecord.objects.get(id=data["forward_id"])
        self.assertEqual(record.agency, self.agency_admin_1)
        self.assertEqual(record.client_company, self.client_1a)
        self.assertEqual(record.recipient_email, self.client_1a.contact_email)
        self.assertEqual(record.notes, payload["notes"])
        self.assertEqual(record.applications.count(), 2)

        # Verify application status flags updated
        self.app_shortlisted_1.refresh_from_db()
        self.app_shortlisted_2.refresh_from_db()
        self.assertTrue(self.app_shortlisted_1.is_forwarded)
        self.assertIsNotNone(self.app_shortlisted_1.forwarded_at)
        self.assertTrue(self.app_shortlisted_2.is_forwarded)
        self.assertIsNotNone(self.app_shortlisted_2.forwarded_at)

        # Verify email was dispatched (AC#4, US-32-T4)
        self.assertEqual(len(mail.outbox), 1)
        sent_email = mail.outbox[0]
        self.assertIn(self.client_1a.contact_email, sent_email.to)
        self.assertIn("Shortlisted Candidate Profiles (2)", sent_email.subject)
        self.assertIn("Alice Smith", sent_email.alternatives[0][0])
        self.assertIn("Bob Johnson", sent_email.alternatives[0][0])
        self.assertIn(payload["notes"], sent_email.alternatives[0][0])

    def test_forward_rejects_non_shortlisted_candidate(self):
        """Only shortlisted candidates (is_shortlisted=True) can be selected for forwarding (AC#2)."""
        self.client.force_authenticate(user=self.agency_admin_1)

        payload = {
            "client_id": self.client_1a.id,
            "application_ids": [self.app_shortlisted_1.id, self.app_unshortlisted.id],
            "recipient_email": self.client_1a.contact_email,
            "notes": "Testing guard against unshortlisted candidate"
        }

        response = self.client.post(self.forward_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertIn("Only shortlisted candidates can be forwarded", data["detail"])
        self.assertIn("Carol White", data["detail"])

        # Assert no forward record created and applications not marked as forwarded
        self.assertEqual(CandidateForwardRecord.objects.count(), 0)
        self.app_shortlisted_1.refresh_from_db()
        self.assertFalse(self.app_shortlisted_1.is_forwarded)

    def test_forward_rejects_deactivated_client_company(self):
        """Cannot forward candidates to a deactivated client company."""
        self.client.force_authenticate(user=self.agency_admin_1)

        payload = {
            "client_id": self.inactive_client.id,
            "application_ids": [self.app_shortlisted_1.id],
            "recipient_email": self.inactive_client.contact_email,
        }

        response = self.client.post(self.forward_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Cannot forward candidate profiles to a deactivated client company", response.json()["detail"])

    def test_forward_rejects_cross_client_mismatch(self):
        """Cannot forward candidates of Client B when Client A is selected as the recipient."""
        self.client.force_authenticate(user=self.agency_admin_1)

        payload = {
            "client_id": self.client_1a.id,
            "application_ids": [self.app_client_1b.id],  # belongs to BioPulse Labs
            "recipient_email": self.client_1a.contact_email,
        }

        response = self.client.post(self.forward_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("belongs to 'BioPulse Labs', not the selected target client", response.json()["detail"])

    # =========================================================================
    # MULTI-TENANT ISOLATION (AC#4)
    # =========================================================================

    def test_agency_cannot_forward_to_another_agencys_client(self):
        """Agency 1 cannot forward candidates to Agency 2's client company (AC#4)."""
        self.client.force_authenticate(user=self.agency_admin_1)

        payload = {
            "client_id": self.client_2.id,  # Agency 2's client
            "application_ids": [self.app_shortlisted_1.id],
            "recipient_email": self.client_2.contact_email,
        }

        response = self.client.post(self.forward_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("permission to forward candidates to another agency's client", response.json()["detail"])

    def test_agency_cannot_forward_another_agencys_application(self):
        """Agency 1 cannot forward an application belonging to Agency 2."""
        self.client.force_authenticate(user=self.agency_admin_1)

        payload = {
            "client_id": self.client_1a.id,
            "application_ids": [self.app_agency_2.id],  # Agency 2's application
            "recipient_email": self.client_1a.contact_email,
        }

        response = self.client.post(self.forward_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # =========================================================================
    # FORWARD AUDIT TRAIL & HISTORY (AC#5)
    # =========================================================================

    def test_forward_history_list_and_isolation(self):
        """Agency can view its own forwarding history, isolated from other agencies (AC#5)."""
        self.client.force_authenticate(user=self.agency_admin_1)

        # 1. Forward to Client 1a
        self.client.post(self.forward_url, {
            "client_id": self.client_1a.id,
            "application_ids": [self.app_shortlisted_1.id],
            "recipient_email": self.client_1a.contact_email,
            "notes": "First forward"
        }, format='json')

        # 2. Forward to Client 1b
        self.client.post(self.forward_url, {
            "client_id": self.client_1b.id,
            "application_ids": [self.app_client_1b.id],
            "recipient_email": self.client_1b.contact_email,
            "notes": "Second forward"
        }, format='json')

        # 3. Fetch history
        response = self.client.get(self.history_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        history = response.json()
        self.assertEqual(len(history), 2)
        client_names = [h["client_company_name"] for h in history]
        self.assertIn("Apex Global Tech", client_names)
        self.assertIn("BioPulse Labs", client_names)

        # 4. Filter history by client_id
        filtered_response = self.client.get(f"{self.history_url}?client_id={self.client_1a.id}")
        self.assertEqual(filtered_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(filtered_response.json()), 1)
        self.assertEqual(filtered_response.json()[0]["client_company_id"], self.client_1a.id)

        # 5. Agency 2 fetches history -> receives empty list (Tenant isolation)
        self.client.force_authenticate(user=self.agency_admin_2)
        agency2_history = self.client.get(self.history_url)
        self.assertEqual(agency2_history.status_code, status.HTTP_200_OK)
        self.assertEqual(len(agency2_history.json()), 0)

    # =========================================================================
    # RBAC & SECURITY
    # =========================================================================

    def test_unauthenticated_blocked(self):
        """Unauthenticated user blocked with 401 Unauthorized."""
        response = self.client.post(self.forward_url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_student_blocked(self):
        """Student blocked with 403 Forbidden."""
        self.client.force_authenticate(user=self.student_user)
        response = self.client.post(self.forward_url, {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_hr_manager_blocked(self):
        """HR Manager blocked from agency forward endpoint with 403 Forbidden."""
        self.client.force_authenticate(user=self.hr_user)
        response = self.client.post(self.forward_url, {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
