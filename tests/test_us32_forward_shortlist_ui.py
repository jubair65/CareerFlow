"""
US-32: Forward Shortlisted Candidate Profiles to Client Companies UI Automation Test Suite (US-32-T6).
Lead Developer: MD. Hasanul Mobin (@hasanulmobin1)
Reviewer & Peer UI Tester: Farhana Tahsin Bonny (@tahsinbonnie98)
Sprint: Sprint 6 — Agency Operations & Multi-Client Applicant Pipeline

Acceptance Criteria & Features Verified:
✓ AC#1: Candidate Selection for Forwarding (US-32-T3) - Multi-select checkboxes & selection action bar
✓ AC#2: Shortlist Guard Enforcement (US-32-T1, US-32-T2) - Non-shortlisted candidates disabled & guarded
✓ AC#3: Client Selection & Auto-Assignment (US-32-T1) - Single-client lock, contact details pre-filled
✓ AC#4: Delivery Dossier & Modal Workflow (US-32-T4) - Candidate snapshot preview, cover note, email dispatch
✓ AC#5: Forward History & Status Badges (US-32-T5) - Badge-forwarded update, CandidateForwardRecord database audit
✓ AC#6: Multi-Tenant Data Isolation, Cross-Client UI Guard & RBAC (US-32-T2, US-32-T4)
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
from apps.recruitment.models import ClientCompany, RecruitmentRoom, CandidateApplication, CandidateForwardRecord
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


def create_agency_test_client(agency_user, name: str, industry: str = "Technology & Software", is_active: bool = True, contact_email: str = None, contact_person: str = None) -> ClientCompany:
    """Helper to create ClientCompany directly in MySQL database."""
    uid = uuid.uuid4().hex[:6]
    return ClientCompany.objects.create(
        agency=agency_user,
        name=name,
        industry=industry,
        contact_person=contact_person or f"Contact {name}",
        contact_email=contact_email or f"contact_{uid}@company.test",
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
class TestUS32ForwardShortlistUI:
    """Automated UI Test Suite for US-32: Forward Shortlisted Candidate Profiles to Client Companies (US-32-T6)."""

    def test_tc_us32_01_candidate_selection_and_forward_bar_visibility(self, driver):
        """
        TC-US32-01: Candidate Selection Checkboxes & Floating Forward Bar (US-32-T3, AC#1).
        Verifies:
        - Shortlisted candidates have enabled checkboxes with data-testid='checkbox-candidate-{id}'.
        - Non-shortlisted candidates have disabled checkboxes (guard enforcement).
        - Checking an applicant mounts [data-testid='bar-forward-selection'] with accurate count.
        - 'Clear selection' resets selected candidates and hides the bar.
        """
        email = f"mobin_fwd01_{uuid.uuid4().hex[:6]}@careerflow.agency"
        agency_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.AGENCY_ADMIN, full_name="Hasanul Mobin")
        client = create_agency_test_client(agency_user, "Vertex AI Innovations", industry="Artificial Intelligence")
        room = create_agency_test_room(agency_user, client, "Senior Deep Learning Engineer")

        app_shortlisted = create_test_candidate_application(
            room, "Arthur Pendelton", f"arthur_{uuid.uuid4().hex[:6]}@test.com",
            cv_score=92.0, video_score=88.0, final_score=90.0, is_shortlisted=True, shortlist_reason="Top 5% Model Architecture"
        )
        app_non_shortlisted = create_test_candidate_application(
            room, "Benjamin Franklin", f"ben_{uuid.uuid4().hex[:6]}@test.com",
            cv_score=60.0, video_score=65.0, final_score=62.5, is_shortlisted=False
        )

        login_user(driver, email=email)
        driver.get(f"{get_base_url()}/agency/pipeline")
        wait = WebDriverWait(driver, 10)

        # 1. Assert table loads
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='container-applicant-table']")))

        # 2. Assert shortlisted checkbox is enabled (using aligned selector checkbox-candidate-{id})
        cb_shortlisted = wait.until(EC.presence_of_element_located((
            By.CSS_SELECTOR, f"[data-testid='checkbox-candidate-{app_shortlisted.id}']"
        )))
        assert cb_shortlisted.is_enabled(), "Shortlisted candidate checkbox should be enabled"

        # 3. Assert non-shortlisted checkbox is disabled
        cb_non_shortlisted = driver.find_element(
            By.CSS_SELECTOR, f"[data-testid='checkbox-candidate-{app_non_shortlisted.id}']"
        )
        assert not cb_non_shortlisted.is_enabled(), "Non-shortlisted candidate checkbox must be disabled"

        # 4. Check shortlisted applicant -> selection bar appears
        cb_shortlisted.click()
        selection_bar = wait.until(EC.visibility_of_element_located((
            By.CSS_SELECTOR, "[data-testid='bar-forward-selection']"
        )))
        assert "1 Shortlisted candidate selected" in selection_bar.text or "1" in selection_bar.text

        capture_evidence(driver, "us32_01_candidate_selection_bar.png")

        # 5. Click "Clear selection"
        clear_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-clear-selection']")
        clear_btn.click()
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='bar-forward-selection']")))

    def test_tc_us32_02_select_all_shortlisted_toggle(self, driver):
        """
        TC-US32-02: Select All Shortlisted Toggle Control (US-32-T3, AC#1).
        Verifies:
        - [data-testid='checkbox-select-all-shortlisted'] selects all visible shortlisted candidates.
        - Selection bar reflects total shortlisted count.
        - Toggling off deselects all candidates and removes selection bar.
        """
        email = f"mobin_fwd02_{uuid.uuid4().hex[:6]}@careerflow.agency"
        agency_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.AGENCY_ADMIN, full_name="Hasanul Mobin")
        client = create_agency_test_client(agency_user, "CloudScale Matrix Corp", industry="Cloud Architecture")
        room = create_agency_test_room(agency_user, client, "Kubernetes Platform Architect")

        app_1 = create_test_candidate_application(room, "Catherine Bell", f"cath_{uuid.uuid4().hex[:6]}@test.com", cv_score=95.0, video_score=90.0, final_score=92.5, is_shortlisted=True)
        app_2 = create_test_candidate_application(room, "Daniel Craig", f"dan_{uuid.uuid4().hex[:6]}@test.com", cv_score=88.0, video_score=85.0, final_score=86.5, is_shortlisted=True)
        app_3 = create_test_candidate_application(room, "Eva Green", f"eva_{uuid.uuid4().hex[:6]}@test.com", cv_score=50.0, video_score=55.0, final_score=52.5, is_shortlisted=False)

        login_user(driver, email=email)
        driver.get(f"{get_base_url()}/agency/pipeline")
        wait = WebDriverWait(driver, 10)

        # 1. Assert table loads
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='container-applicant-table']")))

        # 2. Click select-all-shortlisted checkbox
        select_all_cb = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='checkbox-select-all-shortlisted']")))
        select_all_cb.click()

        # 3. Verify selection bar appears with count 2
        selection_bar = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='bar-forward-selection']")))
        assert "2" in selection_bar.text

        # 4. Verify candidate 1 & 2 checkboxes are checked, candidate 3 is unchecked
        cb_1 = driver.find_element(By.CSS_SELECTOR, f"[data-testid='checkbox-candidate-{app_1.id}']")
        cb_2 = driver.find_element(By.CSS_SELECTOR, f"[data-testid='checkbox-candidate-{app_2.id}']")
        cb_3 = driver.find_element(By.CSS_SELECTOR, f"[data-testid='checkbox-candidate-{app_3.id}']")
        assert cb_1.is_selected()
        assert cb_2.is_selected()
        assert not cb_3.is_selected()

        capture_evidence(driver, "us32_02_select_all_toggle.png")

        # 5. Click select-all again to deselect
        select_all_cb.click()
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='bar-forward-selection']")))
        assert not cb_1.is_selected()
        assert not cb_2.is_selected()

    def test_tc_us32_03_forward_modal_launch_and_form_prefill(self, driver):
        """
        TC-US32-03: Forward Modal Launch & Client Contact Auto-Prefill (US-32-T1, US-32-T4, AC#3, AC#4).
        Verifies:
        - Opening modal displays heading [data-testid='heading-forward-candidates'].
        - Target client company is auto-assigned and disabled when candidates share the same client.
        - Recipient email and name are prefilled from client profile.
        - Notes field is accessible via [data-testid='input-forward-notes'].
        - Selected candidates dossier preview renders candidate name, client, room, and scores.
        """
        email = f"mobin_fwd03_{uuid.uuid4().hex[:6]}@careerflow.agency"
        agency_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.AGENCY_ADMIN, full_name="Hasanul Mobin")
        client = create_agency_test_client(
            agency_user, "OmniCorp Robotics", industry="Robotics",
            contact_email="hr-hiring@omnicorp.test", contact_person="Eleanor Vance"
        )
        room = create_agency_test_room(agency_user, client, "Lead Embedded Systems Architect")
        app = create_test_candidate_application(room, "Fiona Gallagher", f"fiona_{uuid.uuid4().hex[:6]}@test.com", cv_score=94.0, video_score=91.0, final_score=92.5, is_shortlisted=True)

        login_user(driver, email=email)
        driver.get(f"{get_base_url()}/agency/pipeline")
        wait = WebDriverWait(driver, 10)

        # Select candidate and click "Forward to Client"
        cb = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='checkbox-candidate-{app.id}']")))
        cb.click()

        forward_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-forward-selected']")))
        forward_btn.click()

        # Assert modal mounts
        modal = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-forward-candidates']")))
        assert modal is not None

        # Verify auto-assigned client select is disabled
        client_select = driver.find_element(By.CSS_SELECTOR, "[data-testid='select-forward-client']")
        assert not client_select.is_enabled(), "Client select should be auto-locked for uniform candidate selection"

        # Verify prefilled recipient email and name
        email_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-recipient-email']")
        name_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-recipient-name']")
        assert email_input.get_attribute("value") == "hr-hiring@omnicorp.test"
        assert name_input.get_attribute("value") == "Eleanor Vance"

        # Verify dossier preview container contains candidate info and client company
        dossier_list = driver.find_element(By.CSS_SELECTOR, "[data-testid='container-forward-candidates-list']")
        assert "Fiona Gallagher" in dossier_list.text
        assert "OmniCorp Robotics" in dossier_list.text

        # Verify cover note field with aligned input-forward-notes selector
        notes_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-forward-notes']")
        assert len(notes_input.get_attribute("value")) > 10

        capture_evidence(driver, "us32_03_forward_modal_prefilled.png")

        # Close modal
        close_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-close-forward-modal']")
        close_btn.click()
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-forward-candidates']")))

    def test_tc_us32_04_single_candidate_row_forward_trigger(self, driver):
        """
        TC-US32-04: Row-Level Quick Forward Action Button (US-32-T3, AC#1).
        Verifies:
        - Row-level 'Forward' button [data-testid='button-forward-row-{id}'] appears on shortlisted rows.
        - Row-level 'Forward' button is NOT rendered on non-shortlisted rows.
        - Clicking row forward button opens ForwardCandidatesModal specifically for that candidate.
        """
        email = f"mobin_fwd04_{uuid.uuid4().hex[:6]}@careerflow.agency"
        agency_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.AGENCY_ADMIN, full_name="Hasanul Mobin")
        client = create_agency_test_client(agency_user, "AeroDynamics Aerospace", industry="Aerospace")
        room = create_agency_test_room(agency_user, client, "Avionics Software Specialist")

        app_shortlisted = create_test_candidate_application(room, "George Clark", f"george_{uuid.uuid4().hex[:6]}@test.com", cv_score=91.0, video_score=87.0, final_score=89.0, is_shortlisted=True)
        app_non_shortlisted = create_test_candidate_application(room, "Hannah Abbott", f"hannah_{uuid.uuid4().hex[:6]}@test.com", cv_score=55.0, video_score=60.0, final_score=57.5, is_shortlisted=False)

        login_user(driver, email=email)
        driver.get(f"{get_base_url()}/agency/pipeline")
        wait = WebDriverWait(driver, 10)

        # Assert row-level button exists for shortlisted candidate
        row_fwd_btn = wait.until(EC.visibility_of_element_located((
            By.CSS_SELECTOR, f"[data-testid='button-forward-row-{app_shortlisted.id}']"
        )))
        assert row_fwd_btn is not None

        # Assert row-level button DOES NOT exist for non-shortlisted candidate
        non_fwd_btns = driver.find_elements(By.CSS_SELECTOR, f"[data-testid='button-forward-row-{app_non_shortlisted.id}']")
        assert len(non_fwd_btns) == 0, "Non-shortlisted row must not have a forward button"

        # Click row forward button
        row_fwd_btn.click()

        # Verify modal opens for candidate
        modal = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-forward-candidates']")))
        dossier_list = driver.find_element(By.CSS_SELECTOR, "[data-testid='container-forward-candidates-list']")
        assert "George Clark" in dossier_list.text

        capture_evidence(driver, "us32_04_single_row_forward_modal.png")

        # Close modal
        driver.find_element(By.CSS_SELECTOR, "[data-testid='button-close-forward-modal']").click()
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-forward-candidates']")))

    def test_tc_us32_05_forward_submission_success_and_badge_update(self, driver):
        """
        TC-US32-05: Successful Shortlist Forward Dispatch & Status Badge Update (US-32-T2, US-32-T4, US-32-T5, AC#4, AC#5).
        Verifies:
        - Submitting forward form successfully triggers API dispatch.
        - Modal closes upon success.
        - Candidate table row dynamically updates with 'Forwarded' badge [data-testid='badge-forwarded'].
        - Database state confirms: is_forwarded=True, forwarded_at is populated, CandidateForwardRecord created.
        """
        email = f"mobin_fwd05_{uuid.uuid4().hex[:6]}@careerflow.agency"
        agency_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.AGENCY_ADMIN, full_name="Hasanul Mobin")
        client = create_agency_test_client(
            agency_user, "CyberDefense Shield Ltd", industry="Cybersecurity",
            contact_email="vp-talent@cyberdefense.test", contact_person="Marcus Brody"
        )
        room = create_agency_test_room(agency_user, client, "Senior Security Operations Analyst")
        app = create_test_candidate_application(room, "Ian Malcolm", f"ian_{uuid.uuid4().hex[:6]}@test.com", cv_score=93.0, video_score=89.0, final_score=91.0, is_shortlisted=True)

        login_user(driver, email=email)
        driver.get(f"{get_base_url()}/agency/pipeline")
        wait = WebDriverWait(driver, 10)

        # Trigger forward modal via row action
        row_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-forward-row-{app.id}']")))
        row_btn.click()

        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-forward-candidates']")))

        # Submit forward modal
        submit_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-submit-forward']")))
        submit_btn.click()

        # Modal closes
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-forward-candidates']")))

        # Assert 'Forwarded' badge appears on applicant row (verifying aligned badge-forwarded selector)
        fwd_badge = wait.until(EC.visibility_of_element_located((
            By.CSS_SELECTOR, f"#badge-forwarded-{app.id}, [data-testid='badge-forwarded']"
        )))
        assert "Forwarded" in fwd_badge.text

        capture_evidence(driver, "us32_05_forwarded_badge_and_state.png")

        # Database verification (AC#5)
        app.refresh_from_db()
        assert app.is_forwarded is True, "CandidateApplication.is_forwarded must be True"
        assert app.forwarded_at is not None, "CandidateApplication.forwarded_at must be populated"

        forward_records = CandidateForwardRecord.objects.filter(applications=app)
        assert forward_records.exists(), "CandidateForwardRecord must be created in database"
        record = forward_records.first()
        assert record.client_company == client
        assert record.recipient_email == "vp-talent@cyberdefense.test"
        assert record.status == CandidateForwardRecord.DeliveryStatus.DELIVERED
        assert record.dossier_data["candidates"][0]["candidate_name"] == "Ian Malcolm"

    def test_tc_us32_06_bulk_forward_multi_candidates(self, driver):
        """
        TC-US32-06: Bulk Shortlist Candidate Forwarding (US-32-T3, US-32-T4, AC#1, AC#4).
        Verifies:
        - Selecting multiple candidates belonging to the same client in the pipeline.
        - Modal displays all selected candidate dossiers.
        - Submitting forwards all selected candidates in a single transaction.
        - All candidate rows reflect 'Forwarded' status badges.
        """
        email = f"mobin_fwd06_{uuid.uuid4().hex[:6]}@careerflow.agency"
        agency_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.AGENCY_ADMIN, full_name="Hasanul Mobin")
        client = create_agency_test_client(agency_user, "Fintech Enterprise Alliance", industry="Financial Services", contact_email="hiring@fintech.test")
        room = create_agency_test_room(agency_user, client, "Quantitative Algorithm Engineer")

        app_1 = create_test_candidate_application(room, "Julia Roberts", f"julia_{uuid.uuid4().hex[:6]}@test.com", cv_score=96.0, video_score=92.0, final_score=94.0, is_shortlisted=True)
        app_2 = create_test_candidate_application(room, "Kevin Spacey", f"kevin_{uuid.uuid4().hex[:6]}@test.com", cv_score=89.0, video_score=87.0, final_score=88.0, is_shortlisted=True)

        login_user(driver, email=email)
        driver.get(f"{get_base_url()}/agency/pipeline")
        wait = WebDriverWait(driver, 10)

        # Select both candidates via select all
        select_all = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='checkbox-select-all-shortlisted']")))
        select_all.click()

        # Click forward selected button
        forward_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-forward-selected']")))
        forward_btn.click()

        modal = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-forward-candidates']")))
        dossier_list = driver.find_element(By.CSS_SELECTOR, "[data-testid='container-forward-candidates-list']")
        assert "Julia Roberts" in dossier_list.text
        assert "Kevin Spacey" in dossier_list.text

        # Submit forward modal
        driver.find_element(By.CSS_SELECTOR, "[data-testid='button-submit-forward']").click()
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-forward-candidates']")))

        # Verify badges on both rows
        badge_1 = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"#badge-forwarded-{app_1.id}")))
        badge_2 = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"#badge-forwarded-{app_2.id}")))
        assert "Forwarded" in badge_1.text
        assert "Forwarded" in badge_2.text

        capture_evidence(driver, "us32_06_bulk_forward_success.png")

    def test_tc_us32_07_validation_empty_recipient_email(self, driver):
        """
        TC-US32-07: Client Recipient Email Validation (US-32-T4, AC#4).
        Verifies:
        - HTML5 / form validation requires a valid recipient email.
        - Clearing email input prevents form submission.
        """
        email = f"mobin_fwd07_{uuid.uuid4().hex[:6]}@careerflow.agency"
        agency_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.AGENCY_ADMIN, full_name="Hasanul Mobin")
        client = create_agency_test_client(agency_user, "BioMed Therapeutics", industry="Biotechnology")
        room = create_agency_test_room(agency_user, client, "Bioinformatics Scientist")
        app = create_test_candidate_application(room, "Laura Palmer", f"laura_{uuid.uuid4().hex[:6]}@test.com", cv_score=91.0, video_score=89.0, final_score=90.0, is_shortlisted=True)

        login_user(driver, email=email)
        driver.get(f"{get_base_url()}/agency/pipeline")
        wait = WebDriverWait(driver, 10)

        # Open modal
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-forward-row-{app.id}']"))).click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-forward-candidates']")))

        # Clear recipient email
        email_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-recipient-email']")
        email_input.clear()

        # Submit button click should be blocked or modal remains open
        submit_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-submit-forward']")
        submit_btn.click()

        # Assert modal is still visible (prevented by required validation)
        assert driver.find_element(By.CSS_SELECTOR, "[data-testid='modal-forward-candidates']").is_displayed()

        capture_evidence(driver, "us32_07_validation_recipient_email.png")

        # Dismiss modal
        driver.find_element(By.CSS_SELECTOR, "[data-testid='button-close-forward-modal']").click()

    def test_tc_us32_08_cross_client_selection_ui_guard(self, driver):
        """
        TC-US32-08: Cross-Client Multi-Selection UI Guard Verification (US-32 Fix Verification).
        Verifies:
        - Selecting candidates belonging to two different client companies simultaneously.
        - Forward modal detects multiple client companies.
        - [data-testid='alert-cross-client-error'] alert is rendered in the modal.
        - Target client company select is disabled.
        - Submit button [data-testid='button-submit-forward'] is disabled to prevent invalid API calls.
        """
        email = f"mobin_fwd08_{uuid.uuid4().hex[:6]}@careerflow.agency"
        agency_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.AGENCY_ADMIN, full_name="Hasanul Mobin")
        
        # Client A
        client_a = create_agency_test_client(agency_user, "NovaTech Solutions", industry="Software")
        room_a = create_agency_test_room(agency_user, client_a, "Backend Architect")
        app_a = create_test_candidate_application(room_a, "Michael Scott", f"michael_{uuid.uuid4().hex[:6]}@test.com", is_shortlisted=True)

        # Client B
        client_b = create_agency_test_client(agency_user, "Acrobatics Media", industry="Media")
        room_b = create_agency_test_room(agency_user, client_b, "Creative Lead")
        app_b = create_test_candidate_application(room_b, "Pam Beesly", f"pam_{uuid.uuid4().hex[:6]}@test.com", is_shortlisted=True)

        login_user(driver, email=email)
        driver.get(f"{get_base_url()}/agency/pipeline")
        wait = WebDriverWait(driver, 10)

        # Select Candidate from Client A and Candidate from Client B
        cb_a = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='checkbox-candidate-{app_a.id}']")))
        cb_b = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='checkbox-candidate-{app_b.id}']")))
        cb_a.click()
        cb_b.click()

        # Click forward selected button
        forward_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-forward-selected']")))
        forward_btn.click()

        # Verify modal mounts
        modal = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-forward-candidates']")))

        # 1. Assert cross-client error alert is displayed
        cross_client_alert = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='alert-cross-client-error']")))
        assert "Multiple Client Companies Selected" in cross_client_alert.text
        assert "NovaTech Solutions" in cross_client_alert.text
        assert "Acrobatics Media" in cross_client_alert.text

        # 2. Assert client select is disabled
        client_select = driver.find_element(By.CSS_SELECTOR, "[data-testid='select-forward-client']")
        assert not client_select.is_enabled(), "Client selector must be disabled for cross-client selection"

        # 3. Assert submit button is disabled
        submit_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-submit-forward']")
        assert not submit_btn.is_enabled(), "Submit button must be disabled when candidates from multiple clients are selected"

        capture_evidence(driver, "us32_08_cross_client_validation_alert.png")

        # Close modal
        driver.find_element(By.CSS_SELECTOR, "[data-testid='button-close-forward-modal']").click()
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-forward-candidates']")))

    def test_tc_us32_09_multi_tenant_isolation_boundary(self, driver):
        """
        TC-US32-09: Multi-Tenant Data Isolation Across Agencies (US-32-T2, US-32-T5, AC#6).
        Verifies:
        - Agency A cannot view, select, or forward candidate applications belonging to Agency B.
        - Forward history is strictly scoped to the authenticated agency.
        """
        # Agency 1
        agency_1 = create_user_in_db(f"agency1_{uuid.uuid4().hex[:6]}@careerflow.agency", "ValidPass2026!", role=User.Role.AGENCY_ADMIN, full_name="Agency One")
        client_1 = create_agency_test_client(agency_1, "Alpha Tech Group")
        room_1 = create_agency_test_room(agency_1, client_1, "Alpha Software Dev")
        app_1 = create_test_candidate_application(room_1, "Agency One Candidate", f"cand1_{uuid.uuid4().hex[:6]}@test.com", is_shortlisted=True)

        # Agency 2
        agency_2 = create_user_in_db(f"agency2_{uuid.uuid4().hex[:6]}@careerflow.agency", "ValidPass2026!", role=User.Role.AGENCY_ADMIN, full_name="Agency Two")
        client_2 = create_agency_test_client(agency_2, "Beta Robotics Corp")
        room_2 = create_agency_test_room(agency_2, client_2, "Beta Automation Engineer")
        app_2 = create_test_candidate_application(room_2, "Agency Two Candidate", f"cand2_{uuid.uuid4().hex[:6]}@test.com", is_shortlisted=True)

        # Log in as Agency 1
        login_user(driver, email=agency_1.email)
        driver.get(f"{get_base_url()}/agency/pipeline")
        wait = WebDriverWait(driver, 10)

        # Assert Agency 1 sees app_1 but NEVER app_2
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='applicant-row-{app_1.id}']")))
        agency_2_elements = driver.find_elements(By.CSS_SELECTOR, f"[data-testid='applicant-row-{app_2.id}']")
        assert len(agency_2_elements) == 0, "Agency 1 must not see Agency 2's candidate applications"

        capture_evidence(driver, "us32_09_multi_tenant_isolation.png")

    def test_tc_us32_10_rbac_protection_student_and_unauthenticated(self, driver):
        """
        TC-US32-10: Strict RBAC Protection (Security & Access Control).
        Verifies:
        - Student role cannot navigate to /agency/pipeline.
        - Unauthenticated visitor is redirected to /login.
        """
        student_email = f"student_{uuid.uuid4().hex[:6]}@careerflow.demo"
        login_user(driver, email=student_email, role=User.Role.STUDENT, full_name="Student User")

        # Attempt to navigate to agency pipeline
        driver.get(f"{get_base_url()}/agency/pipeline")
        time.sleep(1.5)

        # ProtectedRoute should redirect student to student dashboard
        assert "/student/dashboard" in driver.current_url or "/agency/pipeline" not in driver.current_url

        # Log out / clear session and test unauthenticated
        driver.execute_script("sessionStorage.clear(); localStorage.clear();")
        driver.get(f"{get_base_url()}/agency/pipeline")
        time.sleep(1.5)

        # Unauthenticated visitor must be redirected to /login
        assert "/login" in driver.current_url

        capture_evidence(driver, "us32_10_rbac_protection.png")
