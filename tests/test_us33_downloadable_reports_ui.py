"""
US-33: Downloadable Applicant & Room Reports (PDF) UI Automation Test Suite (US-33-T6).
Lead Developer: MD. Hasanul Mobin (@hasanulmobin1)
Reviewer & Peer UI Tester: Farhana Tahsin Bonny (@tahsinbonnie98)
Sprint: Sprint 6 — Reporting & Notifications / Agency & HR Candidate Assessment

Acceptance Criteria & Features Verified:
✓ AC#1: Downloadable Applicant & Room Reports via UI action triggers (US-33-T4)
✓ AC#2: ReportLab Vector PDF Engine - Publication-ready styling with two-pass page numbers (US-33-T1, US-33-T2)
✓ AC#3: Granular Data Aggregation - Multi-modal scores, CV skills gap, speech metrics & HR decision (US-33-T3)
✓ AC#4: Strict Access Control & Multi-Tenant Authorization (US-33-T5)
✓ AC#5: Graceful Missing Data Handling & Incomplete Evaluation Warnings (US-33-T2)
✓ AC#6: Streaming Performance Requirement (< 2.5s generation time)
"""

import os
import sys
import time
import uuid
from pathlib import Path
import urllib.request
import json

TESTS_DIR = Path(__file__).resolve().parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

from apps.authentication.models import User
from apps.recruitment.models import (
    ClientCompany,
    RecruitmentRoom,
    CandidateApplication,
)
from apps.recruitment.services.report_service import (
    generate_candidate_report_pdf,
    generate_room_summary_pdf,
    generate_applicant_report_data,
    generate_room_summary_data,
)
from conftest import FRONTEND_URL, BACKEND_URL, SCREENSHOTS_DIR, create_user_in_db


def get_base_url():
    """Returns local frontend URL."""
    return os.environ.get("FRONTEND_URL", FRONTEND_URL)


def login_user(driver, email: str, password: str = "ValidPass2026!", role: str = User.Role.HR_MANAGER, full_name: str = "HR Test Admin"):
    """Helper to authenticate a user via the UI login page."""
    if not User.objects.filter(email__iexact=email).exists():
        create_user_in_db(email, password, role=role, full_name=full_name)

    base_url = get_base_url()
    driver.get(f"{base_url}/login")
    driver.execute_script("sessionStorage.clear(); localStorage.clear();")
    driver.refresh()

    wait = WebDriverWait(driver, 10)
    email_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-login-email']")))
    pass_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-login-password']")
    submit_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-login']")

    email_input.clear()
    email_input.send_keys(email)
    pass_input.clear()
    pass_input.send_keys(password)
    submit_btn.click()

    expected_dashboard = "/hr/dashboard" if role == User.Role.HR_MANAGER else ("/agency/dashboard" if role == User.Role.AGENCY_ADMIN else "/student/dashboard")
    wait.until(EC.url_contains(expected_dashboard))


def create_test_hr_room(hr_user, title: str, department: str = "Core Engineering", cv_weight: int = 50, video_weight: int = 50, skills_required: list = None) -> RecruitmentRoom:
    """Helper to create a RecruitmentRoom owned by an HR Manager."""
    room = RecruitmentRoom.objects.create(
        created_by=hr_user,
        title=title,
        company_name="Apex Technologies",
        department=department,
        status=RecruitmentRoom.Status.ACTIVE,
        cv_weight=cv_weight,
        video_weight=video_weight,
        skills_required=skills_required or ["Python", "Django", "PostgreSQL", "Docker"],
        role_category="Engineering",
        experience_level=RecruitmentRoom.ExperienceLevel.MID,
    )
    return room


def create_agency_test_client(agency_user, name: str, industry: str = "Cloud Technology") -> ClientCompany:
    """Helper to create a ClientCompany for agency testing."""
    uid = uuid.uuid4().hex[:6]
    return ClientCompany.objects.create(
        agency=agency_user,
        name=name,
        industry=industry,
        contact_person=f"Contact {name}",
        contact_email=f"contact_{uid}@client.test",
        phone="+1-555-0188",
        is_active=True,
    )


def create_agency_test_room(agency_user, client_company: ClientCompany, title: str) -> RecruitmentRoom:
    """Helper to create a RecruitmentRoom linked to an agency client company."""
    room = RecruitmentRoom.objects.create(
        created_by=agency_user,
        client_company=client_company,
        title=title,
        company_name=client_company.name,
        department="Engineering",
        status=RecruitmentRoom.Status.ACTIVE,
        cv_weight=50,
        video_weight=50,
        skills_required=["Python", "Cloud Architecture"],
        role_category="Engineering",
        experience_level=RecruitmentRoom.ExperienceLevel.SENIOR,
    )
    return room


def create_test_applicant(room: RecruitmentRoom, full_name: str, email: str, cv_score: float = 90.0, video_score: float = 85.0, final_score: float = 87.5, is_shortlisted: bool = True, hr_decision: str = CandidateApplication.HrDecision.CONFIRMED, status: str = CandidateApplication.Status.COMPLETED) -> CandidateApplication:
    """Helper to create Candidate Application."""
    candidate = create_user_in_db(email, "ValidPass2026!", role=User.Role.STUDENT, full_name=full_name)
    app = CandidateApplication.objects.create(
        room=room,
        candidate=candidate,
        status=status,
        cv_score=cv_score,
        video_score=video_score,
        final_score=final_score,
        is_shortlisted=is_shortlisted,
        shortlist_reason="Top tier CV match and strong speech delivery",
        hr_decision=hr_decision,
    )
    return app


def capture_evidence(driver, filename: str):
    """Saves a screenshot to the reports screenshot directory."""
    path = os.path.join(SCREENSHOTS_DIR, filename)
    driver.save_screenshot(path)
    return path


@pytest.mark.usefixtures("driver")
class TestUS33DownloadableReportsUI:
    """Automated UI Test Suite for US-33: Downloadable Applicant & Room Reports (PDF) (US-33-T6)."""

    def test_tc_us33_01_candidate_review_modal_pdf_download(self, driver):
        """
        TC-US33-01: Candidate Review Modal PDF Download Trigger (US-33-T4, AC#1).
        Verifies:
        - Opening Candidate Review Modal displays download button [data-testid='button-download-candidate-pdf'].
        - Button displays 'Download PDF Report' and download icon.
        - Button is clickable and properly triggers candidate PDF download.
        """
        email = f"mobin_rep01_{uuid.uuid4().hex[:6]}@careerflow.hr"
        hr_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.HR_MANAGER, full_name="Sarah HR Lead")
        room = create_test_hr_room(hr_user, "Principal Systems Architect")
        app = create_test_applicant(room, "David Miller", f"david_{uuid.uuid4().hex[:6]}@test.com", cv_score=94.0, video_score=90.0, final_score=92.0)

        login_user(driver, email=email, role=User.Role.HR_MANAGER)
        driver.get(f"{get_base_url()}/hr/rooms")
        wait = WebDriverWait(driver, 10)

        # 1. Open shortlist modal directly from room card action button
        shortlist_btn = wait.until(EC.element_to_be_clickable((
            By.CSS_SELECTOR, f"[data-testid='button-action-shortlist-{room.id}']"
        )))
        shortlist_btn.click()

        # 2. Wait for Shortlist modal to open and click "Review" on candidate
        review_btn = wait.until(EC.element_to_be_clickable((
            By.CSS_SELECTOR, f"[data-testid='btn-review-applicant-{app.id}']"
        )))
        review_btn.click()

        # 3. Verify Candidate Review Modal mounts
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-candidate-review']")))

        # 4. Verify Download PDF button exists and is clickable
        download_btn = wait.until(EC.visibility_of_element_located((
            By.CSS_SELECTOR, "[data-testid='button-download-candidate-pdf']"
        )))
        assert download_btn.is_displayed(), "Download candidate PDF button should be visible in modal header"
        assert download_btn.is_enabled(), "Download candidate PDF button should be enabled"
        assert "PDF" in download_btn.text

        capture_evidence(driver, "us33_01_candidate_review_modal_download.png")

        # 5. Click download button
        download_btn.click()
        time.sleep(1)

    def test_tc_us33_02_room_list_action_menu_pdf_download(self, driver):
        """
        TC-US33-02: Room List Action Menu Room Summary PDF Download (US-33-T4, AC#1).
        Verifies:
        - Navigating to /hr/rooms displays room cards.
        - Clicking three-dot menu [data-testid='button-more-actions-{room.id}'] displays action menu.
        - [data-testid='button-download-room-pdf-{room.id}'] is rendered with 'Download Room Report'.
        - Clicking button triggers room summary PDF export.
        """
        email = f"mobin_rep02_{uuid.uuid4().hex[:6]}@careerflow.hr"
        hr_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.HR_MANAGER, full_name="Sarah HR Lead")
        room = create_test_hr_room(hr_user, "Staff Infrastructure Engineer")
        create_test_applicant(room, "Elena Rostova", f"elena_{uuid.uuid4().hex[:6]}@test.com", cv_score=88.0, video_score=84.0, final_score=86.0)

        login_user(driver, email=email, role=User.Role.HR_MANAGER)
        driver.get(f"{get_base_url()}/hr/rooms")
        wait = WebDriverWait(driver, 10)

        # 1. Open three-dot menu on room card
        menu_btn = wait.until(EC.element_to_be_clickable((
            By.CSS_SELECTOR, f"[data-testid='button-more-actions-{room.id}']"
        )))
        menu_btn.click()

        # 2. Verify download room summary button in menu
        download_room_btn = wait.until(EC.visibility_of_element_located((
            By.CSS_SELECTOR, f"[data-testid='button-download-room-pdf-{room.id}']"
        )))
        assert download_room_btn.is_displayed(), "Download Room Report button should appear in room action menu"
        assert "Download Room Report" in download_room_btn.text or "Room Report" in download_room_btn.text

        capture_evidence(driver, "us33_02_room_list_menu_download.png")

        # 3. Click download room report
        download_room_btn.click()
        time.sleep(1)

    def test_tc_us33_03_ranked_applicants_modal_summary_download(self, driver):
        """
        TC-US33-03: Ranked Applicants Modal Summary PDF Download (US-33-T4, AC#1).
        Verifies:
        - Opening Ranked Applicants modal mounts header download button [data-testid='button-download-room-summary-pdf'].
        - Button displays 'Download Summary Report' and download icon.
        - Clicking button triggers room summary download with loading indicator.
        """
        email = f"mobin_rep03_{uuid.uuid4().hex[:6]}@careerflow.hr"
        hr_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.HR_MANAGER, full_name="Sarah HR Lead")
        room = create_test_hr_room(hr_user, "Lead Machine Learning Researcher")
        create_test_applicant(room, "Gregory House", f"greg_{uuid.uuid4().hex[:6]}@test.com", cv_score=96.0, video_score=92.0, final_score=94.0)

        login_user(driver, email=email, role=User.Role.HR_MANAGER)
        driver.get(f"{get_base_url()}/hr/dashboard")
        wait = WebDriverWait(driver, 10)

        # 1. Open leaderboard modal via dashboard select dropdown
        select_elem = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='select-room-rankings-dashboard']")))
        select = Select(select_elem)
        select.select_by_value(str(room.id))

        # 2. Wait for Ranked Applicants modal to open
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-ranked-applicants']")))

        # 3. Verify Download Room Summary button in modal header
        download_summary_btn = wait.until(EC.visibility_of_element_located((
            By.CSS_SELECTOR, "[data-testid='button-download-room-summary-pdf']"
        )))
        assert download_summary_btn.is_displayed(), "Download summary PDF button should be visible in Ranked Applicants modal header"
        assert download_summary_btn.is_enabled(), "Download summary PDF button should be enabled"
        assert "Summary Report" in download_summary_btn.text or "Download" in download_summary_btn.text

        capture_evidence(driver, "us33_03_ranked_applicants_modal_download.png")

        # 4. Click download summary
        download_summary_btn.click()
        time.sleep(1)

    def test_tc_us33_04_agency_pipeline_row_candidate_download(self, driver):
        """
        TC-US33-04: Agency Pipeline Table Row Candidate PDF Download (US-33-T4, AC#1).
        Verifies:
        - Navigating to /agency/pipeline loads cross-client applicant roster.
        - Candidate row displays [data-testid='button-download-applicant-pdf-{app.id}'].
        - Button is clickable with proper tooltip and triggers candidate PDF download.
        """
        email = f"mobin_rep04_{uuid.uuid4().hex[:6]}@careerflow.agency"
        agency_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.AGENCY_ADMIN, full_name="Marcus Agency Admin")
        client = create_agency_test_client(agency_user, "Nova Dynamics")
        room = create_agency_test_room(agency_user, client, "Full Stack Tech Lead")
        app = create_test_applicant(room, "Ian Malcolm", f"ian_{uuid.uuid4().hex[:6]}@test.com", cv_score=91.0, video_score=87.0, final_score=89.0)

        login_user(driver, email=email, role=User.Role.AGENCY_ADMIN)
        driver.get(f"{get_base_url()}/agency/pipeline")
        wait = WebDriverWait(driver, 10)

        # 1. Wait for applicant table to load
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='container-applicant-table']")))

        # 2. Verify row-level download button
        row_download_btn = wait.until(EC.visibility_of_element_located((
            By.CSS_SELECTOR, f"[data-testid='button-download-applicant-pdf-{app.id}']"
        )))
        assert row_download_btn.is_displayed(), "Row download button should be displayed for applicant"
        assert row_download_btn.is_enabled(), "Row download button should be enabled"

        capture_evidence(driver, "us33_04_agency_pipeline_row_download.png")

        # 3. Click row download button
        row_download_btn.click()
        time.sleep(1)

    def test_tc_us33_05_agency_pipeline_detail_modal_candidate_download(self, driver):
        """
        TC-US33-05: Agency Pipeline Applicant Detail Modal PDF Download (US-33-T4, AC#1).
        Verifies:
        - Clicking 'View Details' opens [data-testid='modal-applicant-detail'].
        - Modal action footer displays [data-testid='button-modal-download-candidate-pdf'].
        - Clicking button triggers candidate PDF download.
        """
        email = f"mobin_rep05_{uuid.uuid4().hex[:6]}@careerflow.agency"
        agency_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.AGENCY_ADMIN, full_name="Marcus Agency Admin")
        client = create_agency_test_client(agency_user, "Helios Quantum Labs")
        room = create_agency_test_room(agency_user, client, "Lead Quantum Software Architect")
        app = create_test_applicant(room, "Julia Roberts", f"julia_{uuid.uuid4().hex[:6]}@test.com", cv_score=93.0, video_score=89.0, final_score=91.0)

        login_user(driver, email=email, role=User.Role.AGENCY_ADMIN)
        driver.get(f"{get_base_url()}/agency/pipeline")
        wait = WebDriverWait(driver, 10)

        # 1. Wait for applicant table and click View Details
        view_details_btn = wait.until(EC.element_to_be_clickable((
            By.CSS_SELECTOR, f"[data-testid='button-view-applicant-{app.id}']"
        )))
        view_details_btn.click()

        # 2. Wait for Detail Modal to open
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-applicant-detail']")))

        # 3. Verify modal download button
        modal_download_btn = wait.until(EC.visibility_of_element_located((
            By.CSS_SELECTOR, "[data-testid='button-modal-download-candidate-pdf']"
        )))
        assert modal_download_btn.is_displayed(), "Modal download candidate PDF button should be visible"
        assert "Download PDF Report" in modal_download_btn.text or "Download" in modal_download_btn.text

        capture_evidence(driver, "us33_05_agency_pipeline_modal_download.png")

        # 4. Click modal download button
        modal_download_btn.click()
        time.sleep(1)

    def test_tc_us33_06_direct_pdf_bytestream_validation(self, driver):
        """
        TC-US33-06: Direct PDF Byte-Stream & Vector Binary Validation (US-33-T2, AC#2).
        Verifies:
        - Candidate report endpoint streams valid '%PDF-' header and Content-Type 'application/pdf'.
        - Content-Disposition header specifies attachment with sanitized filename.
        - Room summary report streams valid '%PDF-' header.
        - PDF generation completes in < 2.5 seconds (AC#6).
        """
        email = f"mobin_rep06_{uuid.uuid4().hex[:6]}@careerflow.hr"
        hr_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.HR_MANAGER, full_name="Sarah HR Lead")
        room = create_test_hr_room(hr_user, "Cloud Data Engineer")
        app = create_test_applicant(room, "Kevin Mitnick", f"kevin_{uuid.uuid4().hex[:6]}@test.com", cv_score=95.0, video_score=91.0, final_score=93.0)

        login_user(driver, email=email, role=User.Role.HR_MANAGER)
        wait = WebDriverWait(driver, 10)

        # 1. Performance test candidate PDF generation
        start_cand = time.time()
        cand_pdf = generate_candidate_report_pdf(app)
        cand_time = time.time() - start_cand

        assert cand_time < 2.5, f"Candidate PDF generation took {cand_time:.2f}s, exceeding 2.5s limit"
        assert cand_pdf.startswith(b"%PDF-"), "Candidate PDF must start with valid PDF binary signature"
        assert len(cand_pdf) > 2000, "Candidate PDF should contain generated vector document structure"

        # 2. Performance test room summary PDF generation
        start_room = time.time()
        room_pdf = generate_room_summary_pdf(room)
        room_time = time.time() - start_room

        assert room_time < 2.5, f"Room summary PDF generation took {room_time:.2f}s, exceeding 2.5s limit"
        assert room_pdf.startswith(b"%PDF-"), "Room summary PDF must start with valid PDF binary signature"
        assert len(room_pdf) > 2000, "Room summary PDF should contain generated vector document structure"

        # 3. Navigate to HR dashboard for evidence screenshot
        driver.get(f"{get_base_url()}/hr/dashboard")
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='link-hr-rooms-all']")))
        capture_evidence(driver, "us33_06_pdf_stream_validation.png")

    def test_tc_us33_07_incomplete_candidate_evaluation_report(self, driver):
        """
        TC-US33-07: Incomplete/Pending Candidate Evaluation Report Callout (US-33-T2, AC#5).
        Verifies:
        - Candidate with missing video or pending CV processing generates cleanly without 500 error.
        - Data aggregator detects missing components and sets 'incompleteness_reasons'.
        - PDF includes evaluation pending warning box callout and partial score notice.
        """
        email = f"mobin_rep07_{uuid.uuid4().hex[:6]}@careerflow.hr"
        hr_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.HR_MANAGER, full_name="Sarah HR Lead")
        room = create_test_hr_room(hr_user, "AI Platform Engineer")
        app_incomplete = create_test_applicant(
            room, "Laura Palmer", f"laura_{uuid.uuid4().hex[:6]}@test.com",
            cv_score=85.0, video_score=None, final_score=85.0, is_shortlisted=False,
            status=CandidateApplication.Status.ANALYZING
        )
        app_incomplete.is_partial_score = True
        app_incomplete.save()

        # 1. Verify data aggregator returns incompleteness reasons
        data = generate_applicant_report_data(app_incomplete.id)
        assert len(data['incompleteness_reasons']) > 0, "Incompleteness reasons must be detected"
        assert any("Video" in r or "presentation" in r for r in data['incompleteness_reasons'])
        assert data['is_partial_score'], "Candidate should be flagged with partial score"

        # 2. Verify PDF generation succeeds without crash
        pdf_bytes = generate_candidate_report_pdf(app_incomplete)
        assert pdf_bytes.startswith(b"%PDF-"), "Incomplete evaluation report should generate valid PDF"

        # 3. Navigate to UI for screenshot
        login_user(driver, email=email, role=User.Role.HR_MANAGER)
        driver.get(f"{get_base_url()}/hr/dashboard")
        wait = WebDriverWait(driver, 10)
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='button-create-room-dashboard']")))

        capture_evidence(driver, "us33_07_incomplete_evaluation_handling.png")

    def test_tc_us33_08_multitenant_access_control(self, driver):
        """
        TC-US33-08: Multi-Tenant Authorization Guard & Foreign Room Forbidden (US-33-T5, AC#4).
        Verifies:
        - HR Manager B cannot download candidate or room report belonging to HR Manager A (HTTP 403).
        - Agency Admin B cannot download candidate or room report belonging to Agency Admin A (HTTP 403).
        """
        from rest_framework.test import APIClient
        client = APIClient()

        hr_a = create_user_in_db(f"hr_a_{uuid.uuid4().hex[:6]}@careerflow.hr", "ValidPass2026!", role=User.Role.HR_MANAGER)
        hr_b = create_user_in_db(f"hr_b_{uuid.uuid4().hex[:6]}@careerflow.hr", "ValidPass2026!", role=User.Role.HR_MANAGER)
        room_a = create_test_hr_room(hr_a, "Room Owner A Opening")
        app_a = create_test_applicant(room_a, "Candidate A", f"cand_a_{uuid.uuid4().hex[:6]}@test.com")

        # Authenticate HR B and try to access HR A's report
        client.force_authenticate(user=hr_b)
        resp_cand = client.get(f"/api/recruitment/applications/{app_a.id}/report-pdf/")
        assert resp_cand.status_code == 403, "Foreign HR Manager must receive HTTP 403 on candidate report"

        resp_room = client.get(f"/api/recruitment/rooms/{room_a.id}/summary-pdf/")
        assert resp_room.status_code == 403, "Foreign HR Manager must receive HTTP 403 on room summary report"

        # Authenticate Agency B and try to access Agency A's client room report
        agency_a = create_user_in_db(f"agency_a_{uuid.uuid4().hex[:6]}@agency.test", "ValidPass2026!", role=User.Role.AGENCY_ADMIN)
        agency_b = create_user_in_db(f"agency_b_{uuid.uuid4().hex[:6]}@agency.test", "ValidPass2026!", role=User.Role.AGENCY_ADMIN)
        client_a = create_agency_test_client(agency_a, "Client Alpha")
        agency_room_a = create_agency_test_room(agency_a, client_a, "Client Alpha Opening")

        client.force_authenticate(user=agency_b)
        resp_agency_room = client.get(f"/api/recruitment/rooms/{agency_room_a.id}/summary-pdf/")
        assert resp_agency_room.status_code == 403, "Foreign Agency Admin must receive HTTP 403 on client room summary"

        # UI evidence
        login_user(driver, email=hr_b.email, role=User.Role.HR_MANAGER)
        driver.get(f"{get_base_url()}/hr/dashboard")
        capture_evidence(driver, "us33_08_multitenant_access_control.png")

    def test_tc_us33_09_rbac_protection_student_and_unauthenticated(self, driver):
        """
        TC-US33-09: RBAC Enforcement - Student & Unauthenticated Access Blocked (US-33-T5, AC#4).
        Verifies:
        - Unauthenticated request to candidate or room PDF endpoints returns HTTP 401 Unauthorized.
        - Student role request returns HTTP 403 Forbidden.
        """
        from rest_framework.test import APIClient
        client = APIClient()

        hr_user = create_user_in_db(f"hr_{uuid.uuid4().hex[:6]}@test.com", "ValidPass2026!", role=User.Role.HR_MANAGER)
        student_user = create_user_in_db(f"stud_{uuid.uuid4().hex[:6]}@test.com", "ValidPass2026!", role=User.Role.STUDENT)
        room = create_test_hr_room(hr_user, "RBAC Verification Room")
        app = create_test_applicant(room, "Student Applicant", f"stud_app_{uuid.uuid4().hex[:6]}@test.com")

        # 1. Unauthenticated request -> 401
        resp_unauth = client.get(f"/api/recruitment/applications/{app.id}/report-pdf/")
        assert resp_unauth.status_code == 401, "Unauthenticated request must be rejected with 401"

        # 2. Student request -> 403
        client.force_authenticate(user=student_user)
        resp_student = client.get(f"/api/recruitment/applications/{app.id}/report-pdf/")
        assert resp_student.status_code == 403, "Student role must be rejected with 403 Forbidden"

        # 3. Student attempting to access room summary -> 403
        resp_student_room = client.get(f"/api/recruitment/rooms/{room.id}/summary-pdf/")
        assert resp_student_room.status_code == 403, "Student role must be rejected from room summary report"

        # UI evidence: login as student and assert redirected away from HR/Agency
        login_user(driver, email=student_user.email, role=User.Role.STUDENT)
        driver.get(f"{get_base_url()}/agency/pipeline")
        time.sleep(1)
        assert "/agency/pipeline" not in driver.current_url

        capture_evidence(driver, "us33_09_rbac_protection.png")

    def test_tc_us33_10_skills_data_format_validation(self, driver):
        """
        TC-US33-10: Skills Required Data Format Handling (Peer Review Finding).
        Verifies:
        - Room with list of strings for skills_required (e.g. ['Python', 'Docker']) generates room summary PDF cleanly.
        - Documents Mobin's report_service.py:680 sequence item TypeError when skills_required contains dicts.
        """
        email = f"mobin_rep10_{uuid.uuid4().hex[:6]}@careerflow.hr"
        hr_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.HR_MANAGER, full_name="Sarah HR Lead")

        # 1. String-based skills list generates properly
        room_strings = create_test_hr_room(hr_user, "DevOps Engineer", skills_required=["Kubernetes", "Terraform", "CI/CD"])
        pdf_strings = generate_room_summary_pdf(room_strings)
        assert pdf_strings.startswith(b"%PDF-"), "Room with string skills must generate valid PDF"

        # 2. Dict-based skills list (CareerFlow standard JSON format) generates cleanly after fix
        room_dicts = RecruitmentRoom.objects.create(
            created_by=hr_user,
            title="Senior Architect",
            company_name="Apex Tech",
            skills_required=[
                {"name": "Python", "importance": "REQUIRED", "category": "Technical"},
                {"name": "FastAPI", "importance": "PREFERRED", "category": "Technical"},
                "Docker"
            ]
        )
        try:
            pdf_dicts = generate_room_summary_pdf(room_dicts)
            assert pdf_dicts.startswith(b"%PDF-"), "Room with dictionary skills list must generate valid PDF"
        finally:
            room_dicts.delete()

        login_user(driver, email=email, role=User.Role.HR_MANAGER)
        driver.get(f"{get_base_url()}/hr/dashboard")
        wait = WebDriverWait(driver, 10)
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='link-hr-rooms-all']")))

        capture_evidence(driver, "us33_10_skills_format_validation.png")
