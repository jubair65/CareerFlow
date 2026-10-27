"""
Unit and Integration Tests for US-33: Downloadable Applicant & Room Reports (PDF).
Verifies:
- Individual applicant PDF report generation and byte-stream download.
- Room summary PDF report with ranked candidate roster.
- Multi-tenant security & HR ownership authorization enforcement (AC#4).
- Graceful handling of missing or incomplete applicant evaluation data (AC#5).
- Performance requirement (< 2.5s generation stream) (AC#6).
"""

import time
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.recruitment.models import (
    RecruitmentRoom,
    ClientCompany,
    CandidateApplication,
)
from apps.recruitment.services.report_service import (
    generate_applicant_report_data,
    generate_candidate_report_pdf,
    generate_room_summary_data,
    generate_room_summary_pdf,
)

User = get_user_model()


class DownloadableReportsTestCase(TestCase):
    def setUp(self):
        import uuid
        self.uid = uuid.uuid4().hex[:8]
        self.client = APIClient()

        # 1. Primary HR Manager (Room Owner)
        self.hr_user = User.objects.create_user(
            username=f'hr_{self.uid}',
            email=f'hr_{self.uid}@techcorp.com',
            password='Password123!',
            role=User.Role.HR_MANAGER,
            full_name='Sarah HR Manager'
        )

        # 2. Unauthorized HR Manager (Different Owner)
        self.other_hr_user = User.objects.create_user(
            username=f'other_hr_{self.uid}',
            email=f'other_hr_{self.uid}@companya.com',
            password='Password123!',
            role=User.Role.HR_MANAGER,
            full_name='Alex Other HR'
        )

        # 3. Agency Admin
        self.agency_user = User.objects.create_user(
            username=f'agency_{self.uid}',
            email=f'agency_{self.uid}@recruitmenthub.com',
            password='Password123!',
            role=User.Role.AGENCY_ADMIN,
            full_name='Marcus Agency Director'
        )

        # 4. Unauthorized Agency Admin (Different Agency)
        self.other_agency_user = User.objects.create_user(
            username=f'other_agency_{self.uid}',
            email=f'other_agency_{self.uid}@external.com',
            password='Password123!',
            role=User.Role.AGENCY_ADMIN,
            full_name='Rogue Agency'
        )

        # 5. Client Company managed by Agency
        self.client_company = ClientCompany.objects.create(
            agency=self.agency_user,
            name=f'Vertex Global Innovations {self.uid}',
            industry='FinTech',
            contact_person='David Chen',
            contact_email=f'd.chen_{self.uid}@vertexinnovations.com'
        )

        # 6. Standard HR Recruitment Room
        self.room = RecruitmentRoom.objects.create(
            created_by=self.hr_user,
            title='Lead Backend Systems Architect',
            company_name='TechCorp International',
            department='Core Platform',
            status=RecruitmentRoom.Status.ACTIVE
        )

        # 7. Agency Recruitment Room (linked to Client Company)
        self.agency_room = RecruitmentRoom.objects.create(
            created_by=self.agency_user,
            client_company=self.client_company,
            title='Senior Full-Stack Engineer',
            company_name=self.client_company.name,
            department='Engineering',
            status=RecruitmentRoom.Status.ACTIVE
        )

        # 8. Candidates
        self.candidate1 = User.objects.create_user(
            username=f'cand1_{self.uid}',
            email=f'alex.mercer_{self.uid}@example.com',
            password='Password123!',
            role=User.Role.STUDENT,
            full_name='Alex Mercer'
        )
        self.candidate2 = User.objects.create_user(
            username=f'cand2_{self.uid}',
            email=f'beatrice.vance_{self.uid}@example.com',
            password='Password123!',
            role=User.Role.STUDENT,
            full_name='Beatrice Vance'
        )
        self.candidate3 = User.objects.create_user(
            username=f'cand3_{self.uid}',
            email=f'charles.lee_{self.uid}@example.com',
            password='Password123!',
            role=User.Role.STUDENT,
            full_name='Charles Lee'
        )

        # 9. Candidate Applications in standard room
        self.app_completed = CandidateApplication.objects.create(
            room=self.room,
            candidate=self.candidate1,
            status=CandidateApplication.Status.COMPLETED,
            cv_score=92.5,
            video_score=88.0,
            final_score=90.25,
            is_shortlisted=True,
            shortlist_reason='Exemplary CV match and confident speech delivery',
            hr_decision=CandidateApplication.HrDecision.CONFIRMED,
        )

        self.app_incomplete = CandidateApplication.objects.create(
            room=self.room,
            candidate=self.candidate2,
            status=CandidateApplication.Status.ANALYZING,
            cv_score=84.0,
            video_score=None,
            final_score=84.0,
            is_partial_score=True,
            is_shortlisted=False,
            shortlist_reason='Pending video evaluation',
            hr_decision=CandidateApplication.HrDecision.UNDECIDED,
        )

        # 10. Candidate Application in Agency room
        self.app_agency = CandidateApplication.objects.create(
            room=self.agency_room,
            candidate=self.candidate3,
            status=CandidateApplication.Status.COMPLETED,
            cv_score=95.0,
            video_score=91.0,
            final_score=93.0,
            is_shortlisted=True,
            shortlist_reason='Top percentile technical match',
            hr_decision=CandidateApplication.HrDecision.CONFIRMED,
        )

    # -------------------------------------------------------------------------
    # Individual Candidate Report Tests (AC#1, AC#2, AC#3, AC#4)
    # -------------------------------------------------------------------------

    def test_generate_candidate_report_pdf_success_by_room_owner(self):
        """Room owner HR Manager can download candidate report PDF."""
        self.client.force_authenticate(user=self.hr_user)
        url = reverse('recruitment:application-report-pdf', kwargs={'application_id': self.app_completed.id})

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('CareerFlow_Candidate_', response['Content-Disposition'])
        self.assertTrue(response.content.startswith(b'%PDF-'))

    def test_generate_candidate_report_pdf_by_agency_admin(self):
        """Agency Admin managing client company can download candidate report PDF."""
        self.client.force_authenticate(user=self.agency_user)
        url = reverse('recruitment:application-report-pdf', kwargs={'application_id': self.app_agency.id})

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(response.content.startswith(b'%PDF-'))

    def test_candidate_report_unauthorized_hr_forbidden(self):
        """AC#4: An HR Manager who does not own the room is rejected with 403."""
        self.client.force_authenticate(user=self.other_hr_user)
        url = reverse('recruitment:application-report-pdf', kwargs={'application_id': self.app_completed.id})

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_candidate_report_unauthorized_agency_forbidden(self):
        """AC#4: An Agency Admin not associated with the client company is rejected with 403."""
        self.client.force_authenticate(user=self.other_agency_user)
        url = reverse('recruitment:application-report-pdf', kwargs={'application_id': self.app_agency.id})

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_candidate_report_unauthenticated_rejected(self):
        """Anonymous user cannot download report (HTTP 401)."""
        url = reverse('recruitment:application-report-pdf', kwargs={'application_id': self.app_completed.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_candidate_report_nonexistent_application_404(self):
        """Non-existent application ID returns 404."""
        self.client.force_authenticate(user=self.hr_user)
        url = reverse('recruitment:application-report-pdf', kwargs={'application_id': 999999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_candidate_report_with_incomplete_data_graceful(self):
        """AC#5: Missing/incomplete evaluation data generates cleanly without 500 errors."""
        self.client.force_authenticate(user=self.hr_user)
        url = reverse('recruitment:application-report-pdf', kwargs={'application_id': self.app_incomplete.id})

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(response.content.startswith(b'%PDF-'))

        # Also verify data aggregator returns incompleteness reasons
        data = generate_applicant_report_data(self.app_incomplete.id)
        self.assertTrue(len(data['incompleteness_reasons']) > 0)
        self.assertTrue(data['is_partial_score'])

    # -------------------------------------------------------------------------
    # Room Summary Report Tests (AC#1, AC#2, AC#3, AC#4)
    # -------------------------------------------------------------------------

    def test_room_summary_pdf_success_by_owner(self):
        """Room owner can download executive room summary PDF."""
        self.client.force_authenticate(user=self.hr_user)
        url = reverse('recruitment:room-summary-pdf', kwargs={'room_id': self.room.id})

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('CareerFlow_Room_', response['Content-Disposition'])
        self.assertTrue(response.content.startswith(b'%PDF-'))

    def test_room_summary_pdf_empty_roster_graceful(self):
        """Empty room with no applicants generates clean PDF without crash."""
        empty_room = RecruitmentRoom.objects.create(
            created_by=self.hr_user,
            title='Empty Opening',
            company_name='TechCorp',
            status=RecruitmentRoom.Status.ACTIVE
        )
        self.client.force_authenticate(user=self.hr_user)
        url = reverse('recruitment:room-summary-pdf', kwargs={'room_id': empty_room.id})

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.content.startswith(b'%PDF-'))

        data = generate_room_summary_data(empty_room.id)
        self.assertEqual(data['total_applicants'], 0)
        self.assertEqual(len(data['roster']), 0)

    def test_room_summary_unauthorized_forbidden(self):
        """AC#4: Unauthorized HR Manager cannot download room summary."""
        self.client.force_authenticate(user=self.other_hr_user)
        url = reverse('recruitment:room-summary-pdf', kwargs={'room_id': self.room.id})

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # -------------------------------------------------------------------------
    # Performance Test (AC#6: < 2.5s)
    # -------------------------------------------------------------------------

    def test_report_generation_performance(self):
        """AC#6: PDF generation completes in well under 2.5 seconds."""
        start_time = time.time()
        pdf_bytes = generate_candidate_report_pdf(self.app_completed)
        elapsed = time.time() - start_time

        self.assertLess(elapsed, 2.5, f"PDF generation took {elapsed:.2f}s, exceeding 2.5s limit")
        self.assertTrue(len(pdf_bytes) > 1000)
