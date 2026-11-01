"""
Unit and Integration Tests for US-46: Bulk Applicant Data Export — CSV / Excel.

Acceptance Criteria Verified:
- AC-1: HR can export all applicants in a Room as a downloadable CSV or Excel (.xlsx) file.
- AC-2: Export includes applicant name, email, CV score, video score, final weighted score, rank, application status, and shortlist status.
- AC-3: Export preserves current filter and sorting selections (shortlisted only, search term, min score, status, ordering).
- AC-4: Generated file uses clean formatting, escaped commas/quotes, and UTF-8 encoding (with BOM for Excel compatibility).
- AC-5: Large candidate lists export efficiently without timing out via streaming response.
- AC-6: Non-HR users and unauthorized recruiters cannot access or export applicant data (RBAC & room ownership checks).
"""

import io
import csv
import uuid
import openpyxl
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
from apps.recruitment.services.export_service import (
    stream_applicants_csv,
    generate_applicants_excel,
    get_export_filename,
)

User = get_user_model()


class BulkApplicantExportTestCase(TestCase):
    def setUp(self):
        self.uid = uuid.uuid4().hex[:8]
        self.client = APIClient()

        # 1. Primary HR User (Room Owner)
        self.hr_user = User.objects.create_user(
            username=f'hr_{self.uid}',
            email=f'hr_{self.uid}@careerflow.test',
            password='Password123!',
            role=User.Role.HR_MANAGER,
            full_name='Maria Lead HR'
        )

        # 2. Unauthorized HR User (Different Recruiter)
        self.other_hr_user = User.objects.create_user(
            username=f'other_hr_{self.uid}',
            email=f'other_hr_{self.uid}@externalcorp.test',
            password='Password123!',
            role=User.Role.HR_MANAGER,
            full_name='David Unauthorized Recruiter'
        )

        # 3. Agency Admin
        self.agency_user = User.objects.create_user(
            username=f'agency_{self.uid}',
            email=f'agency_{self.uid}@recruitinghub.test',
            password='Password123!',
            role=User.Role.AGENCY_ADMIN,
            full_name='Sophia Agency Director'
        )

        # 4. Unauthorized Agency User
        self.other_agency_user = User.objects.create_user(
            username=f'other_agency_{self.uid}',
            email=f'other_agency_{self.uid}@otheragency.test',
            password='Password123!',
            role=User.Role.AGENCY_ADMIN,
            full_name='Rogue Agency Admin'
        )

        # 5. Client Company managed by Agency
        self.client_company = ClientCompany.objects.create(
            agency=self.agency_user,
            name=f'Acme Corporation {self.uid}',
            industry='Technology',
            contact_person='John Contact',
            contact_email=f'j.contact_{self.uid}@acme.test'
        )

        # 6. Standard HR Recruitment Room
        self.room = RecruitmentRoom.objects.create(
            created_by=self.hr_user,
            title='Staff Python Engineer',
            company_name='CareerFlow Tech',
            department='Engineering',
            cv_weight=50,
            video_weight=50,
            status=RecruitmentRoom.Status.ACTIVE
        )

        # 7. Agency Recruitment Room
        self.agency_room = RecruitmentRoom.objects.create(
            created_by=self.agency_user,
            client_company=self.client_company,
            title='DevOps Specialist',
            company_name=self.client_company.name,
            department='Cloud Infrastructure',
            cv_weight=40,
            video_weight=60,
            status=RecruitmentRoom.Status.ACTIVE
        )

        # 8. Candidates
        self.candidate1 = User.objects.create_user(
            username=f'cand1_{self.uid}',
            email=f'alice.smith_{self.uid}@test.com',
            password='Password123!',
            role=User.Role.STUDENT,
            full_name='Alice Smith'
        )
        self.candidate2 = User.objects.create_user(
            username=f'cand2_{self.uid}',
            email=f'bob.jones_{self.uid}@test.com',
            password='Password123!',
            role=User.Role.STUDENT,
            full_name='Bob "The Builder" Jones'
        )
        self.candidate3 = User.objects.create_user(
            username=f'cand3_{self.uid}',
            email=f'clara.oswald_{self.uid}@test.com',
            password='Password123!',
            role=User.Role.STUDENT,
            full_name='Oswald, Clara'
        )

        # 9. Candidate Applications for Standard Room
        # Application 1: High score, shortlisted
        self.app1 = CandidateApplication.objects.create(
            room=self.room,
            candidate=self.candidate1,
            status=CandidateApplication.Status.COMPLETED,
            cv_score=92.0,
            video_score=88.0,
            final_score=90.0,
            is_shortlisted=True,
            shortlist_reason='Top scorer with excellent skills',
            hr_decision=CandidateApplication.HrDecision.CONFIRMED
        )

        # Application 2: Moderate score, not shortlisted
        self.app2 = CandidateApplication.objects.create(
            room=self.room,
            candidate=self.candidate2,
            status=CandidateApplication.Status.COMPLETED,
            cv_score=74.0,
            video_score=76.0,
            final_score=75.0,
            is_shortlisted=False,
            shortlist_reason='',
            hr_decision=CandidateApplication.HrDecision.UNDECIDED
        )

        # Application 3: Name with commas and quotes
        self.app3 = CandidateApplication.objects.create(
            room=self.room,
            candidate=self.candidate3,
            status=CandidateApplication.Status.ANALYZING,
            cv_score=82.0,
            video_score=None,
            final_score=82.0,
            is_partial_score=True,
            is_shortlisted=False,
            shortlist_reason='Evaluation pending',
            hr_decision=CandidateApplication.HrDecision.UNDECIDED
        )

    # --------------------------------------------------------------------------
    # CSV Export Tests (AC-1, AC-2, AC-4, AC-5)
    # --------------------------------------------------------------------------

    def test_csv_export_streaming_and_bom_success(self):
        """Verify CSV export streams with status 200, UTF-8 BOM, headers, and candidate rows."""
        self.client.force_authenticate(user=self.hr_user)
        url = reverse('recruitment:room-export-csv', kwargs={'room_id': self.room.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.streaming)
        self.assertIn('text/csv', response['Content-Type'])
        self.assertIn('utf-8', response['Content-Type'].lower())
        self.assertIn('attachment;', response['Content-Disposition'])
        self.assertIn('.csv', response['Content-Disposition'])

        content_bytes = b"".join(response.streaming_content)
        # AC-4: UTF-8 BOM present
        self.assertTrue(content_bytes.startswith(b'\xef\xbb\xbf'), "CSV must start with UTF-8 BOM")

        # Parse CSV text
        csv_text = content_bytes.decode('utf-8-sig')
        reader = list(csv.reader(io.StringIO(csv_text)))

        # Header row
        expected_headers = [
            'Rank',
            'Candidate Name',
            'Email Address',
            'CV Match Score (%)',
            'Video Presentation Score (%)',
            'Final Weighted Score (%)',
            'Shortlisted',
            'Application Status',
            'Applied Date'
        ]
        self.assertEqual(reader[0], expected_headers)

        # 3 candidate rows present
        self.assertEqual(len(reader), 4)

        # Check Rank 1 applicant details
        rank_1_row = reader[1]
        self.assertEqual(rank_1_row[0], '1')
        self.assertEqual(rank_1_row[1], 'Alice Smith')
        self.assertEqual(rank_1_row[2], self.candidate1.email)
        self.assertEqual(rank_1_row[3], '92.0%')
        self.assertEqual(rank_1_row[4], '88.0%')
        self.assertEqual(rank_1_row[5], '90.0%')
        self.assertEqual(rank_1_row[6], 'Yes')
        self.assertEqual(rank_1_row[7], 'COMPLETED')

    def test_csv_export_escapes_commas_and_quotes(self):
        """AC-4: Verify candidate names containing quotes and commas are properly escaped."""
        self.client.force_authenticate(user=self.hr_user)
        url = reverse('recruitment:room-export-csv', kwargs={'room_id': self.room.id})
        response = self.client.get(url)

        content = b"".join(response.streaming_content).decode('utf-8-sig')
        reader = list(csv.reader(io.StringIO(content)))

        names = [row[1] for row in reader[1:]]
        self.assertIn('Bob "The Builder" Jones', names)
        self.assertIn('Oswald, Clara', names)

    # --------------------------------------------------------------------------
    # Excel (.xlsx) Export Tests (AC-1, AC-2, AC-4)
    # --------------------------------------------------------------------------

    def test_excel_export_format_and_styles_success(self):
        """Verify Excel (.xlsx) export returns valid workbook with correct sheets and values."""
        self.client.force_authenticate(user=self.hr_user)
        url = reverse('recruitment:room-export-excel', kwargs={'room_id': self.room.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', response['Content-Type'])
        self.assertIn('.xlsx', response['Content-Disposition'])

        workbook = openpyxl.load_workbook(io.BytesIO(response.content))
        sheet = workbook.active
        self.assertEqual(sheet.title, "Ranked Applicants")

        # Find header row in sheet
        header_row_values = None
        for row in sheet.iter_rows(values_only=True):
            if row and row[0] == 'Rank':
                header_row_values = list(row)
                break

        self.assertIsNotNone(header_row_values, "Table header row with 'Rank' must exist in Excel")
        self.assertIn('Candidate Name', header_row_values)
        self.assertIn('Final Weighted Score (%)', header_row_values)
        self.assertIn('Shortlisted', header_row_values)

    # --------------------------------------------------------------------------
    # Filter Preservation Tests (AC-3)
    # --------------------------------------------------------------------------

    def test_export_preserves_shortlisted_only_filter(self):
        """AC-3: Verify passing ?shortlisted=true exports only shortlisted applicants."""
        self.client.force_authenticate(user=self.hr_user)
        url = reverse('recruitment:room-export-csv', kwargs={'room_id': self.room.id})
        response = self.client.get(f'{url}?shortlisted=true')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = b"".join(response.streaming_content).decode('utf-8-sig')
        reader = list(csv.reader(io.StringIO(content)))

        # Header + 1 shortlisted candidate
        self.assertEqual(len(reader), 2)
        self.assertEqual(reader[1][1], 'Alice Smith')
        self.assertEqual(reader[1][6], 'Yes')

    def test_export_preserves_min_score_filter(self):
        """AC-3: Verify passing ?min_score=85 exports only candidates with score >= 85."""
        self.client.force_authenticate(user=self.hr_user)
        url = reverse('recruitment:room-export-csv', kwargs={'room_id': self.room.id})
        response = self.client.get(f'{url}?min_score=85')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = b"".join(response.streaming_content).decode('utf-8-sig')
        reader = list(csv.reader(io.StringIO(content)))

        self.assertEqual(len(reader), 2)
        self.assertEqual(reader[1][1], 'Alice Smith')

    def test_export_preserves_search_filter(self):
        """AC-3: Verify search filter restricts exported candidates."""
        self.client.force_authenticate(user=self.hr_user)
        url = reverse('recruitment:room-export-csv', kwargs={'room_id': self.room.id})
        response = self.client.get(f'{url}?search=Jones')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = b"".join(response.streaming_content).decode('utf-8-sig')
        reader = list(csv.reader(io.StringIO(content)))

        self.assertEqual(len(reader), 2)
        self.assertEqual(reader[1][1], 'Bob "The Builder" Jones')

    def test_export_empty_room_returns_headers_gracefully(self):
        """AC-5: Exporting an empty recruitment room returns headers without crash."""
        empty_room = RecruitmentRoom.objects.create(
            created_by=self.hr_user,
            title='Empty Engineering Room',
            company_name='CareerFlow Tech',
            status=RecruitmentRoom.Status.ACTIVE
        )

        self.client.force_authenticate(user=self.hr_user)
        url_csv = reverse('recruitment:room-export-csv', kwargs={'room_id': empty_room.id})
        res_csv = self.client.get(url_csv)
        self.assertEqual(res_csv.status_code, status.HTTP_200_OK)

        content = b"".join(res_csv.streaming_content).decode('utf-8-sig')
        reader = list(csv.reader(io.StringIO(content)))
        self.assertEqual(len(reader), 1, "Only header row should exist for empty room")

        url_excel = reverse('recruitment:room-export-excel', kwargs={'room_id': empty_room.id})
        res_excel = self.client.get(url_excel)
        self.assertEqual(res_excel.status_code, status.HTTP_200_OK)

    # --------------------------------------------------------------------------
    # RBAC and Authorization Enforcement (AC-6)
    # --------------------------------------------------------------------------

    def test_export_unauthenticated_returns_401(self):
        """AC-6: Unauthenticated request is rejected with 401."""
        url = reverse('recruitment:room-export-csv', kwargs={'room_id': self.room.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_export_candidate_user_forbidden(self):
        """AC-6: Student candidate cannot export applicant data (403 Forbidden)."""
        self.client.force_authenticate(user=self.candidate1)
        url = reverse('recruitment:room-export-csv', kwargs={'room_id': self.room.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_export_unauthorized_hr_user_forbidden(self):
        """AC-6: Different HR recruiter cannot export a room they do not own."""
        self.client.force_authenticate(user=self.other_hr_user)
        url = reverse('recruitment:room-export-csv', kwargs={'room_id': self.room.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        url_excel = reverse('recruitment:room-export-excel', kwargs={'room_id': self.room.id})
        res_excel = self.client.get(url_excel)
        self.assertEqual(res_excel.status_code, status.HTTP_403_FORBIDDEN)

    def test_agency_admin_can_export_client_company_room(self):
        """AC-6: Agency Admin managing the client company can export applicants."""
        self.client.force_authenticate(user=self.agency_user)
        url = reverse('recruitment:room-export-csv', kwargs={'room_id': self.agency_room.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthorized_agency_admin_cannot_export_different_agency_room(self):
        """AC-6: Rogue Agency Admin cannot export another agency's client company room."""
        self.client.force_authenticate(user=self.other_agency_user)
        url = reverse('recruitment:room-export-csv', kwargs={'room_id': self.agency_room.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
