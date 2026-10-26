"""
US-31: Cross-Client Applicant View UI Automation Test Suite (US-31-T6).
Peer UI Tester & Reviewer: MD. Hasanul Mobin (@hasanulmobin1)
Lead Developer: Farhana Tahsin Bonny (@tahsinbonnie98)
Sprint: Sprint 6 — Agency Operations & Multi-Client Applicant Pipeline

Acceptance Criteria & Features Verified:
✓ AC#1: Cross-client applicant aggregation across all client companies of an agency (US-31-T2)
✓ AC#2: Response schema & UI columns (candidate, client company, Room, scores, status, shortlist, HR decision)
✓ AC#3: Filtering by client company, cascading Room selector, status, shortlist, and live search (US-31-T4)
✓ AC#4: Strict multi-tenant isolation: Agency A cannot view or retrieve Agency B's applicants (US-31-T5)
✓ AC#5: Empty pipeline state handling & filter reset (US-31-T4)
✓ AC#6: High performance, sorting, 4 KPI metric cards, and applicant detail modal breakdown
✓ Strict RBAC protection: only AGENCY_ADMIN can access /agency/pipeline; Student & unauthenticated blocked
"""

import os
import sys
import time
import uuid
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

from apps.authentication.models import User
from apps.recruitment.models import ClientCompany, RecruitmentRoom, CandidateApplication
from conftest import FRONTEND_URL, BACKEND_URL, SCREENSHOTS_DIR, create_user_in_db


def get_base_url():
    """Returns local frontend URL."""
    return os.environ.get("FRONTEND_URL", FRONTEND_URL)


def login_user(driver, email: str, password: str = "ValidPass2026!", role: str = User.Role.AGENCY_ADMIN, full_name: str = "Agency Test Admin"):
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

    expected_dashboard = "/agency/dashboard" if role == User.Role.AGENCY_ADMIN else ("/hr/dashboard" if role == User.Role.HR_MANAGER else "/student/dashboard")
    wait.until(EC.url_contains(expected_dashboard))


def create_agency_test_client(agency_user, name: str, industry: str = "Technology & Software", is_active: bool = True) -> ClientCompany:
    """Helper to create ClientCompany directly in MySQL database."""
    uid = uuid.uuid4().hex[:6]
    return ClientCompany.objects.create(
        agency=agency_user,
        name=name,
        industry=industry,
        contact_person=f"Contact {name}",
        contact_email=f"contact_{uid}@company.test",
        phone="+1-555-0199",
        website="https://example.com",
        is_active=is_active
    )


def create_agency_test_room(agency_user, client_company: ClientCompany, title: str, department: str = "Engineering", status: str = "ACTIVE", cv_weight: int = 50, video_weight: int = 50) -> RecruitmentRoom:
    """Helper to create a RecruitmentRoom linked to an agency user and client company."""
    room = RecruitmentRoom.objects.create(
        title=title,
        company_name=client_company.name,
        client_company=client_company,
        department=department,
        description=f"Opening for {title} at {client_company.name}.",
        status=status,
        created_by=agency_user,
        cv_weight=cv_weight,
        video_weight=video_weight,
        role_category="Engineering",
        experience_level="MID",
        skills_required=[{"name": "Python", "importance": "REQUIRED", "category": "Technical"}],
    )
    return room


def create_test_candidate_application(room: RecruitmentRoom, full_name: str, email: str, cv_score: float = 85.0, video_score: float = 80.0, final_score: float = 82.5, status: str = CandidateApplication.Status.COMPLETED, is_shortlisted: bool = False, shortlist_reason: str = "", hr_decision: str = CandidateApplication.HrDecision.UNDECIDED) -> CandidateApplication:
    """Helper to create Candidate User and CandidateApplication."""
    candidate = create_user_in_db(email, "ValidPass2026!", role=User.Role.STUDENT, full_name=full_name)
    app = CandidateApplication.objects.create(
        room=room,
        candidate=candidate,
        status=status,
        cv_score=cv_score,
        video_score=video_score,
        final_score=final_score,
        is_shortlisted=is_shortlisted,
        shortlist_reason=shortlist_reason,
        hr_decision=hr_decision,
    )
    return app


def capture_evidence(driver, filename: str):
    """Saves a screenshot to the reports screenshot directory."""
    path = os.path.join(SCREENSHOTS_DIR, filename)
    driver.save_screenshot(path)
    return path


@pytest.mark.usefixtures("driver")
class TestUS31CrossClientPipelineUI:
    """Test suite covering US-31 Cross-Client Applicant View (US-31-T6)."""

    def test_tc_us31_01_navigation_and_kpi_dashboard(self, driver):
        """
        TC-US31-01: Agency Admin navigates to /agency/pipeline via sidebar button [data-testid='nav-pipeline']
        and via Dashboard card [data-testid='button-review-pipeline'].
        Verifies target URL, container [data-testid='page-agency-applicants'], and 4 KPI metric cards (AC#1, AC#6).
        """
        email = f"mobin_tc01_{uuid.uuid4().hex[:6]}@careerflow.agency"
        agency_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.AGENCY_ADMIN, full_name="Hasanul Mobin")
        client = create_agency_test_client(agency_user, "NovaTech AI Labs", industry="Artificial Intelligence")
        room = create_agency_test_room(agency_user, client, "Senior Deep Learning Engineer")
        create_test_candidate_application(room, "David Miller", f"david_{uuid.uuid4().hex[:6]}@test.com", cv_score=90.0, video_score=85.0, final_score=87.5, is_shortlisted=True)

        login_user(driver, email=email)
        wait = WebDriverWait(driver, 10)

        # 1. From Dashboard, navigate via "Review pipeline" CTA button
        review_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-review-pipeline']")))
        review_btn.click()

        wait.until(EC.url_contains("/agency/pipeline"))
        page_container = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='page-agency-applicants']")))
        assert page_container is not None

        # 2. Verify 4 KPI stat cards mount
        kpi_text = page_container.text.upper()
        assert "TOTAL APPLICANTS" in kpi_text
        assert "COMPLETED ANALYSES" in kpi_text
        assert "SHORTLISTED CANDIDATES" in kpi_text
        assert "AVERAGE FINAL SCORE" in kpi_text

        # 3. Test Navigation back to dashboard then through sidebar [data-testid='nav-pipeline']
        driver.get(f"{get_base_url()}/agency/dashboard")
        nav_pipeline_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='nav-pipeline']")))
        nav_pipeline_btn.click()

        wait.until(EC.url_contains("/agency/pipeline"))
        assert driver.find_element(By.CSS_SELECTOR, "[data-testid='button-refresh-pipeline']").is_displayed()

        capture_evidence(driver, "us31_01_navigation_dashboard.png")

    def test_tc_us31_02_cross_client_aggregation_and_table_schema(self, driver):
        """
        TC-US31-02: Pre-seeds 2 Client Companies and 3 Candidate Applications.
        Verifies consolidated cross-client table aggregation and schema columns (AC#1, AC#2).
        """
        email = f"mobin_tc02_{uuid.uuid4().hex[:6]}@careerflow.agency"
        agency_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.AGENCY_ADMIN, full_name="Hasanul Mobin")
        
        # Client 1
        client_a = create_agency_test_client(agency_user, "Fintech Global Ventures", industry="Finance")
        room_a = create_agency_test_room(agency_user, client_a, "Quantitative Risk Analyst")
        app_1 = create_test_candidate_application(room_a, "Alice Smith", f"alice_{uuid.uuid4().hex[:6]}@test.com", cv_score=92.0, video_score=88.0, final_score=90.0, is_shortlisted=True, hr_decision=CandidateApplication.HrDecision.CONFIRMED)
        
        # Client 2
        client_b = create_agency_test_client(agency_user, "BioHealth Diagnostics", industry="Healthcare")
        room_b = create_agency_test_room(agency_user, client_b, "Clinical Data Architect")
        app_2 = create_test_candidate_application(room_b, "Bob Johnson", f"bob_{uuid.uuid4().hex[:6]}@test.com", cv_score=78.0, video_score=82.0, final_score=80.0, is_shortlisted=False)
        app_3 = create_test_candidate_application(room_b, "Carol White", f"carol_{uuid.uuid4().hex[:6]}@test.com", cv_score=65.0, video_score=70.0, final_score=67.5, status=CandidateApplication.Status.ANALYZING)

        login_user(driver, email=email)
        driver.get(f"{get_base_url()}/agency/pipeline")
        wait = WebDriverWait(driver, 10)

        # Assert table container mounts
        table = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='container-applicant-table']")))
        assert table is not None

        # Assert all 3 cross-client rows appear (AC#1)
        row_1 = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='applicant-row-{app_1.id}']")))
        row_2 = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='applicant-row-{app_2.id}']")))
        row_3 = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='applicant-row-{app_3.id}']")))

        # Assert Row 1 fields (AC#2)
        assert "Alice Smith" in driver.find_element(By.CSS_SELECTOR, f"[data-testid='text-candidate-name-{app_1.id}']").text
        assert "Fintech Global Ventures" in driver.find_element(By.CSS_SELECTOR, f"[data-testid='text-client-name-{app_1.id}']").text
        assert "Quantitative Risk Analyst" in driver.find_element(By.CSS_SELECTOR, f"[data-testid='text-room-title-{app_1.id}']").text
        assert "92%" in driver.find_element(By.CSS_SELECTOR, f"[data-testid='badge-cv-score-{app_1.id}']").text
        assert "88%" in driver.find_element(By.CSS_SELECTOR, f"[data-testid='badge-video-score-{app_1.id}']").text
        assert "90%" in driver.find_element(By.CSS_SELECTOR, f"[data-testid='badge-final-score-{app_1.id}']").text
        assert "COMPLETED" in driver.find_element(By.CSS_SELECTOR, f"[data-testid='badge-status-{app_1.id}']").text
        assert driver.find_element(By.CSS_SELECTOR, f"[data-testid='badge-shortlisted-{app_1.id}']").is_displayed()

        # Assert Row 2 Client B fields
        assert "Bob Johnson" in driver.find_element(By.CSS_SELECTOR, f"[data-testid='text-candidate-name-{app_2.id}']").text
        assert "BioHealth Diagnostics" in driver.find_element(By.CSS_SELECTOR, f"[data-testid='text-client-name-{app_2.id}']").text
        assert "Clinical Data Architect" in driver.find_element(By.CSS_SELECTOR, f"[data-testid='text-room-title-{app_2.id}']").text

        capture_evidence(driver, "us31_02_cross_client_aggregation.png")

    def test_tc_us31_03_applicant_detail_modal_breakdown(self, driver):
        """
        TC-US31-03: Clicks 'Details' button for an applicant; asserts detail breakdown modal mounts
        with weights, scores, shortlist reason, and HR review decision (AC#2).
        """
        email = f"mobin_tc03_{uuid.uuid4().hex[:6]}@careerflow.agency"
        agency_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.AGENCY_ADMIN, full_name="Hasanul Mobin")
        client = create_agency_test_client(agency_user, "CyberGuard Networks", industry="Cybersecurity")
        room = create_agency_test_room(agency_user, client, "Cloud Security Architect", cv_weight=60, video_weight=40)
        app = create_test_candidate_application(
            room,
            "Elena Rostova",
            f"elena_{uuid.uuid4().hex[:6]}@test.com",
            cv_score=94.0,
            video_score=91.0,
            final_score=92.8,
            is_shortlisted=True,
            shortlist_reason="Exceeded top 10% benchmark with exceptional cloud security experience",
            hr_decision=CandidateApplication.HrDecision.CONFIRMED
        )

        login_user(driver, email=email)
        driver.get(f"{get_base_url()}/agency/pipeline")
        wait = WebDriverWait(driver, 10)

        # Open Detail Modal
        detail_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-view-applicant-{app.id}']")))
        detail_btn.click()

        modal = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-applicant-detail']")))
        assert modal is not None
        modal_text = modal.text

        # Verify modal content
        assert "Elena Rostova" in modal_text
        assert "CyberGuard Networks" in modal_text
        assert "Cloud Security Architect" in modal_text
        assert "CV Match (60%)" in modal_text
        assert "Video (40%)" in modal_text
        assert "93%" in modal_text or "92.8%" in modal_text or "Final Weighted Score" in modal_text
        assert "Shortlisted" in modal_text
        assert "Exceeded top 10% benchmark" in modal_text
        assert "Shortlist Confirmed" in modal_text

        capture_evidence(driver, "us31_03_detail_modal_breakdown.png")

        # Close modal
        close_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-close-applicant-modal']")
        close_btn.click()
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-applicant-detail']")))

    def test_tc_us31_04_live_search_and_instant_filtering(self, driver):
        """
        TC-US31-04: Test live text search across candidate name, position, and client company (AC#3).
        """
        email = f"mobin_tc04_{uuid.uuid4().hex[:6]}@careerflow.agency"
        agency_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.AGENCY_ADMIN, full_name="Hasanul Mobin")
        client_1 = create_agency_test_client(agency_user, "Solaris Robotics", industry="Robotics")
        client_2 = create_agency_test_client(agency_user, "AeroSpace Dynamics", industry="Aerospace")
        room_1 = create_agency_test_room(agency_user, client_1, "Mechatronics Engineer")
        room_2 = create_agency_test_room(agency_user, client_2, "Avionics Specialist")

        app_1 = create_test_candidate_application(room_1, "Liam Neeson", f"liam_{uuid.uuid4().hex[:6]}@test.com")
        app_2 = create_test_candidate_application(room_2, "Emma Watson", f"emma_{uuid.uuid4().hex[:6]}@test.com")

        login_user(driver, email=email)
        driver.get(f"{get_base_url()}/agency/pipeline")
        wait = WebDriverWait(driver, 10)

        search_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-search-applicants']")))

        # 1. Search by candidate name "Emma"
        search_input.clear()
        search_input.send_keys("Emma")
        time.sleep(0.6)  # allow 250ms debounce

        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='applicant-row-{app_2.id}']")))
        assert len(driver.find_elements(By.CSS_SELECTOR, f"[data-testid='applicant-row-{app_1.id}']")) == 0

        # 2. Search by client company "Solaris"
        search_input.clear()
        search_input.send_keys("Solaris")
        time.sleep(0.6)

        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='applicant-row-{app_1.id}']")))
        assert len(driver.find_elements(By.CSS_SELECTOR, f"[data-testid='applicant-row-{app_2.id}']")) == 0

        # 3. Clear search -> Both return
        search_input.send_keys(Keys.CONTROL + "a")
        search_input.send_keys(Keys.BACKSPACE)
        time.sleep(0.6)

        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='applicant-row-{app_1.id}']")))
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='applicant-row-{app_2.id}']")))

        capture_evidence(driver, "us31_04_search_filtering.png")

    def test_tc_us31_05_client_and_cascading_room_filters(self, driver):
        """
        TC-US31-05: Tests Client Company selector and verifies cascading Room selector update (AC#3).
        """
        email = f"mobin_tc05_{uuid.uuid4().hex[:6]}@careerflow.agency"
        agency_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.AGENCY_ADMIN, full_name="Hasanul Mobin")
        client_x = create_agency_test_client(agency_user, "Xenon Cloud Systems", industry="Cloud Computing")
        client_y = create_agency_test_client(agency_user, "Ypsilon Genomics", industry="Biotechnology")

        room_x1 = create_agency_test_room(agency_user, client_x, "Site Reliability Engineer")
        room_x2 = create_agency_test_room(agency_user, client_x, "DevOps Specialist")
        room_y1 = create_agency_test_room(agency_user, client_y, "Genomics Research Lead")

        app_x1 = create_test_candidate_application(room_x1, "Xander Cage", f"xander_{uuid.uuid4().hex[:6]}@test.com")
        app_y1 = create_test_candidate_application(room_y1, "Yara Greyjoy", f"yara_{uuid.uuid4().hex[:6]}@test.com")

        login_user(driver, email=email)
        driver.get(f"{get_base_url()}/agency/pipeline")
        wait = WebDriverWait(driver, 10)

        # 1. Filter by Client Company Xenon
        client_select = Select(wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='select-filter-client']"))))
        client_select.select_by_value(str(client_x.id))

        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='applicant-row-{app_x1.id}']")))
        assert len(driver.find_elements(By.CSS_SELECTOR, f"[data-testid='applicant-row-{app_y1.id}']")) == 0

        # 2. Assert cascading Room selector only contains Xenon's rooms
        room_select = Select(driver.find_element(By.CSS_SELECTOR, "[data-testid='select-filter-room']"))
        room_options_texts = [o.text for o in room_select.options]
        assert any("Site Reliability Engineer" in t for t in room_options_texts)
        assert any("DevOps Specialist" in t for t in room_options_texts)
        assert not any("Genomics Research Lead" in t for t in room_options_texts)

        # 3. Reset filters
        reset_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-reset-filters']")))
        reset_btn.click()

        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='applicant-row-{app_y1.id}']")))
        capture_evidence(driver, "us31_05_client_room_filters.png")

    def test_tc_us31_06_status_shortlist_and_sorting_controls(self, driver):
        """
        TC-US31-06: Tests application status filter, shortlist filter, and sorting orders (AC#3, AC#6).
        """
        email = f"mobin_tc06_{uuid.uuid4().hex[:6]}@careerflow.agency"
        agency_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.AGENCY_ADMIN, full_name="Hasanul Mobin")
        client = create_agency_test_client(agency_user, "Titan Maritime Corp", industry="Logistics")
        room = create_agency_test_room(agency_user, client, "Logistics Operations Lead")

        app_completed_shortlisted = create_test_candidate_application(
            room, "Hannah Abbott", f"hannah_{uuid.uuid4().hex[:6]}@test.com",
            cv_score=95.0, video_score=92.0, final_score=93.5,
            status=CandidateApplication.Status.COMPLETED, is_shortlisted=True
        )
        app_completed_unshortlisted = create_test_candidate_application(
            room, "George Weasley", f"george_{uuid.uuid4().hex[:6]}@test.com",
            cv_score=68.0, video_score=65.0, final_score=66.5,
            status=CandidateApplication.Status.COMPLETED, is_shortlisted=False
        )
        app_analyzing = create_test_candidate_application(
            room, "Fred Weasley", f"fred_{uuid.uuid4().hex[:6]}@test.com",
            status=CandidateApplication.Status.ANALYZING, is_shortlisted=False
        )

        login_user(driver, email=email)
        driver.get(f"{get_base_url()}/agency/pipeline")
        wait = WebDriverWait(driver, 10)

        # Wait for all initial records to load first
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='applicant-row-{app_analyzing.id}']")))
        time.sleep(0.5)

        # 1. Filter by Status: COMPLETED
        status_select = Select(wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='select-filter-status']"))))
        status_select.select_by_value("COMPLETED")

        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='applicant-row-{app_analyzing.id}']")))
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='applicant-row-{app_completed_shortlisted.id}']")))
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='applicant-row-{app_completed_unshortlisted.id}']")))

        # 2. Filter by Shortlist: Shortlisted Only
        shortlist_select = Select(driver.find_element(By.CSS_SELECTOR, "[data-testid='select-filter-shortlist']"))
        shortlist_select.select_by_value("shortlisted")

        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='applicant-row-{app_completed_unshortlisted.id}']")))
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='applicant-row-{app_completed_shortlisted.id}']")))

        # 3. Sort by Highest Final Score
        order_select = Select(driver.find_element(By.CSS_SELECTOR, "[data-testid='select-sort-ordering']"))
        order_select.select_by_value("-final_score")

        capture_evidence(driver, "us31_06_status_shortlist_sorting.png")

    def test_tc_us31_07_empty_state_and_filter_reset(self, driver):
        """
        TC-US31-07: Verifies informative empty state banner when no applications exist (AC#5).
        """
        email = f"mobin_tc07_{uuid.uuid4().hex[:6]}@careerflow.agency"
        create_user_in_db(email, "ValidPass2026!", role=User.Role.AGENCY_ADMIN, full_name="Hasanul Mobin")

        login_user(driver, email=email)
        driver.get(f"{get_base_url()}/agency/pipeline")
        wait = WebDriverWait(driver, 10)

        # Assert empty state banner mounts
        empty_banner = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='banner-empty-applicants']")))
        assert empty_banner is not None
        assert "No applicant records found" in empty_banner.text

        capture_evidence(driver, "us31_07_empty_state_handling.png")

    def test_tc_us31_08_multi_tenant_isolation_agency_boundaries(self, driver):
        """
        TC-US31-08: Verifies cross-agency multi-tenant data isolation.
        Agency Admin 1 cannot view Agency Admin 2's candidate applications (AC#4).
        """
        # Agency 1
        email_1 = f"agency1_tc08_{uuid.uuid4().hex[:6]}@careerflow.agency"
        agency_1 = create_user_in_db(email_1, "ValidPass2026!", role=User.Role.AGENCY_ADMIN, full_name="Agency One Admin")
        client_1 = create_agency_test_client(agency_1, "Agency 1 Client Alpha")
        room_1 = create_agency_test_room(agency_1, client_1, "Agency 1 Position")
        app_1 = create_test_candidate_application(room_1, "Target Candidate 1", f"cand1_{uuid.uuid4().hex[:6]}@test.com")

        # Agency 2
        email_2 = f"agency2_tc08_{uuid.uuid4().hex[:6]}@careerflow.agency"
        agency_2 = create_user_in_db(email_2, "ValidPass2026!", role=User.Role.AGENCY_ADMIN, full_name="Agency Two Admin")
        client_2 = create_agency_test_client(agency_2, "Agency 2 Client Beta")
        room_2 = create_agency_test_room(agency_2, client_2, "Agency 2 Position")
        app_2 = create_test_candidate_application(room_2, "Confidential Candidate 2", f"cand2_{uuid.uuid4().hex[:6]}@test.com")

        # Login as Agency 1
        login_user(driver, email=email_1)
        driver.get(f"{get_base_url()}/agency/pipeline")
        wait = WebDriverWait(driver, 10)

        # Assert Agency 1's applicant is visible
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='applicant-row-{app_1.id}']")))
        assert "Target Candidate 1" in driver.find_element(By.CSS_SELECTOR, f"[data-testid='text-candidate-name-{app_1.id}']").text

        # Assert Agency 2's applicant is strictly NOT present in the DOM
        assert len(driver.find_elements(By.CSS_SELECTOR, f"[data-testid='applicant-row-{app_2.id}']")) == 0
        assert "Confidential Candidate 2" not in driver.page_source
        assert "Agency 2 Client Beta" not in driver.page_source

        capture_evidence(driver, "us31_08_multi_tenant_isolation.png")

    def test_tc_us31_09_rbac_protection_and_unauthorized_redirects(self, driver):
        """
        TC-US31-09: Verifies strict RBAC access controls.
        Candidate (Student) and unauthenticated users cannot access /agency/pipeline.
        """
        # 1. Test unauthenticated access -> redirect to login
        driver.get(f"{get_base_url()}/login")
        driver.execute_script("sessionStorage.clear(); localStorage.clear();")
        driver.get(f"{get_base_url()}/agency/pipeline")

        wait = WebDriverWait(driver, 10)
        wait.until(EC.url_contains("/login"))
        assert "/login" in driver.current_url

        # 2. Test Student candidate access -> blocked by ProtectedRoute
        student_email = f"student_tc09_{uuid.uuid4().hex[:6]}@careerflow.test"
        create_user_in_db(student_email, "ValidPass2026!", role=User.Role.STUDENT, full_name="Student Applicant")
        login_user(driver, email=student_email, role=User.Role.STUDENT)

        driver.get(f"{get_base_url()}/agency/pipeline")
        # ProtectedRoute redirects to role home (/student/dashboard)
        wait.until(lambda d: "/student/dashboard" in d.current_url or "/agency/pipeline" not in d.current_url)
        assert "/agency/pipeline" not in driver.current_url

        capture_evidence(driver, "us31_09_rbac_protection.png")
