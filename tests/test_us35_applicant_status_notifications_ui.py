"""
US-35: Applicant Application Status Notifications & Portal Navigation UI Test Suite (US-35-T6).
User Story: US-35 — Applicant Application Status Notification
Lead Developer: Maria (@Maria-07-222)
Reviewer & Peer UI Automation Tester: Farhana Tahsin Bonny (@tahsinbonnie98)
Sprint: Sprint 6 — Analytics, Reports & Alerts / Applicant Status Tracking

Acceptance Criteria & Features Verified:
✓ AC#1: Real-time application status notifications upon shortlist or HR decision changes (US-35-T2).
✓ AC#2: Applicant Portal Status Page (/applications/my-status) with interactive 4-stage milestone stepper (US-35-T4).
✓ AC#3: HR decision status reflection, live composite & multi-modal score breakdowns, and hiring notes (US-35-T4).
✓ AC#4: Strict multi-tenant candidate isolation (candidates only access their own status) (US-35-T4).
✓ AC#5: Non-blocking notification dispatch and SMTP error tolerance (US-35-T3).
✓ AC#6: Comprehensive audit logging in StatusNotificationLog with expandable accordion view (US-35-T1, US-35-T5).
✓ Sidebar Navigation & Dedicated Views: HR Portal (/hr/applicants, /hr/shortlisted, /hr/reports) and Agency Portal (/agency/shortlisted, /agency/reports).
✓ Agency Portal Improvements: Modal render trap elimination and shortlist rules configuration trigger.
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
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from apps.authentication.models import User
from apps.recruitment.models import (
    RecruitmentRoom,
    CandidateApplication,
    StatusNotificationLog,
    ClientCompany,
)
from conftest import FRONTEND_URL, BACKEND_URL, SCREENSHOTS_DIR, create_user_in_db


def get_base_url():
    """Returns local frontend URL."""
    return os.environ.get("FRONTEND_URL", FRONTEND_URL)


def clear_react_input(driver, element):
    """Reliably clears React controlled inputs across platforms."""
    element.send_keys(Keys.COMMAND + "a")
    element.send_keys(Keys.CONTROL + "a")
    element.send_keys(Keys.BACKSPACE)
    driver.execute_script(
        "arguments[0].value = ''; "
        "arguments[0].dispatchEvent(new Event('input', { bubbles: true })); "
        "arguments[0].dispatchEvent(new Event('change', { bubbles: true }));",
        element,
    )


def login_user(driver, email: str, password: str = "ValidPass2026!", role: str = User.Role.STUDENT, full_name: str = "Candidate User"):
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

    clear_react_input(driver, email_input)
    email_input.send_keys(email)
    clear_react_input(driver, pass_input)
    pass_input.send_keys(password)
    submit_btn.click()

    expected_dashboard = (
        "/agency/dashboard"
        if role == User.Role.AGENCY_ADMIN
        else ("/hr/dashboard" if role == User.Role.HR_MANAGER else "/student/dashboard")
    )
    wait.until(EC.url_contains(expected_dashboard))


# ==============================================================================
# UI TEST CASES: US-35-T6
# ==============================================================================


def test_tc35_01_applicant_status_page_milestones_and_shortlisted_badge(driver):
    """
    TC-35-01: Verifies that a candidate with a shortlisted application sees:
    - 4 milestone evaluation stages (Submitted, AI Analysis, HR Review, Final Decision)
    - Shortlisted badge and composite score pill
    - Multi-modal score breakdown (CV score, Video score)
    - Hiring committee decision note. (AC#2, AC#3)
    """
    uid = uuid.uuid4().hex[:6]
    candidate_email = f"candidate_shortlisted_{uid}@careerflow.test"
    hr_email = f"hr_owner_{uid}@careerflow.test"

    hr_user = create_user_in_db(hr_email, "ValidPass2026!", role=User.Role.HR_MANAGER, full_name="Sarah HR")
    candidate_user = create_user_in_db(candidate_email, "ValidPass2026!", role=User.Role.STUDENT, full_name="Alice Candidate")

    room = RecruitmentRoom.objects.create(
        title=f"Senior Cloud Architect {uid}",
        company_name="InnovateTech Solutions",
        department="Platform Infrastructure",
        role_category="ENGINEERING",
        created_by=hr_user,
        cv_weight=50.0,
        video_weight=50.0,
    )

    app = CandidateApplication.objects.create(
        room=room,
        candidate=candidate_user,
        status=CandidateApplication.Status.COMPLETED,
        cv_score=91.0,
        video_score=95.0,
        final_score=93.0,
        is_shortlisted=True,
        shortlist_reason="Top 5% composite performance in AI evaluation",
        hr_decision=CandidateApplication.HrDecision.CONFIRMED,
        hr_decision_notes="Confirmed for final interview round by Technical Panel.",
    )

    login_user(driver, candidate_email, full_name="Alice Candidate")

    base_url = get_base_url()
    driver.get(f"{base_url}/applications/my-status")

    wait = WebDriverWait(driver, 10)
    card = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='application-card-{app.id}']")))
    assert card is not None, "Application card should be rendered"

    # Verify Room Title and Shortlisted Badge
    title_elem = driver.find_element(By.CSS_SELECTOR, f"[data-testid='app-title-{app.id}']")
    assert f"Senior Cloud Architect {uid}" in title_elem.text

    shortlisted_badge = driver.find_element(By.CSS_SELECTOR, f"[data-testid='badge-status-shortlisted-{app.id}']")
    assert "Shortlisted" in shortlisted_badge.text

    # Verify 4 Evaluation Milestones
    stage_submitted = driver.find_element(By.CSS_SELECTOR, f"[data-testid='stage-submitted-{app.id}']")
    stage_ai = driver.find_element(By.CSS_SELECTOR, f"[data-testid='stage-ai_analysis-{app.id}']")
    stage_hr = driver.find_element(By.CSS_SELECTOR, f"[data-testid='stage-hr_review-{app.id}']")
    stage_decision = driver.find_element(By.CSS_SELECTOR, f"[data-testid='stage-final_decision-{app.id}']")

    assert stage_submitted is not None
    assert stage_ai is not None
    assert stage_hr is not None
    assert stage_decision is not None
    assert "Shortlisted" in stage_decision.text or "Decision" in stage_decision.text

    # Verify Score Card and Breakdown
    final_score_elem = driver.find_element(By.CSS_SELECTOR, f"[data-testid='app-final-score-{app.id}']")
    assert "93" in final_score_elem.text

    page_source = driver.page_source
    assert "91/100" in page_source or "91" in page_source
    assert "95/100" in page_source or "95" in page_source
    assert "Confirmed for final interview round by Technical Panel." in page_source

    screenshot_path = SCREENSHOTS_DIR / "us35_01_applicant_status_stepper_shortlisted.png"
    driver.save_screenshot(str(screenshot_path))
    assert screenshot_path.exists()


def test_tc35_02_applicant_status_rejected_state_and_filter_tabs(driver):
    """
    TC-35-02: Verifies that multiple applications across different statuses
    (Shortlisted, Not Selected, In Review) are accurately grouped and filtered
    by the status tab pills. (AC#2, AC#3)
    """
    uid = uuid.uuid4().hex[:6]
    candidate_email = f"candidate_tabs_{uid}@careerflow.test"
    hr_email = f"hr_tabs_{uid}@careerflow.test"

    hr_user = create_user_in_db(hr_email, "ValidPass2026!", role=User.Role.HR_MANAGER, full_name="Dave HR")
    candidate_user = create_user_in_db(candidate_email, "ValidPass2026!", role=User.Role.STUDENT, full_name="Jordan Candidate")

    room1 = RecruitmentRoom.objects.create(
        title=f"Lead Data Scientist {uid}",
        company_name="Apex Analytics",
        department="Data Science",
        created_by=hr_user,
    )
    room2 = RecruitmentRoom.objects.create(
        title=f"Junior Frontend Dev {uid}",
        company_name="WebCraft Labs",
        department="Engineering",
        created_by=hr_user,
    )
    room3 = RecruitmentRoom.objects.create(
        title=f"Backend Engineer {uid}",
        company_name="CloudMatrix",
        department="Core Services",
        created_by=hr_user,
    )

    # 1. Shortlisted App
    app1 = CandidateApplication.objects.create(
        room=room1,
        candidate=candidate_user,
        status=CandidateApplication.Status.COMPLETED,
        final_score=89.0,
        is_shortlisted=True,
        hr_decision=CandidateApplication.HrDecision.CONFIRMED,
    )

    # 2. Rejected App
    app2 = CandidateApplication.objects.create(
        room=room2,
        candidate=candidate_user,
        status=CandidateApplication.Status.COMPLETED,
        final_score=62.0,
        is_shortlisted=False,
        hr_decision=CandidateApplication.HrDecision.REJECTED,
        hr_decision_notes="Candidate experience does not meet minimum threshold.",
    )

    # 3. In Review App
    app3 = CandidateApplication.objects.create(
        room=room3,
        candidate=candidate_user,
        status=CandidateApplication.Status.ANALYZING,
        final_score=None,
        is_shortlisted=False,
        hr_decision=CandidateApplication.HrDecision.UNDECIDED,
    )

    login_user(driver, candidate_email, full_name="Jordan Candidate")

    base_url = get_base_url()
    driver.get(f"{base_url}/applications/my-status")

    wait = WebDriverWait(driver, 10)
    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='application-card-{app1.id}']")))

    # Verify All 3 applications visible on "All Applications"
    assert driver.find_element(By.CSS_SELECTOR, f"[data-testid='application-card-{app1.id}']").is_displayed()
    assert driver.find_element(By.CSS_SELECTOR, f"[data-testid='application-card-{app2.id}']").is_displayed()
    assert driver.find_element(By.CSS_SELECTOR, f"[data-testid='application-card-{app3.id}']").is_displayed()

    # Click "Shortlisted" tab
    tab_shortlisted = driver.find_element(By.CSS_SELECTOR, "[data-testid='filter-tab-shortlisted']")
    tab_shortlisted.click()
    time.sleep(0.5)

    assert driver.find_element(By.CSS_SELECTOR, f"[data-testid='application-card-{app1.id}']").is_displayed()
    rejected_cards = driver.find_elements(By.CSS_SELECTOR, f"[data-testid='application-card-{app2.id}']")
    assert len(rejected_cards) == 0, "Rejected card should be hidden when Shortlisted tab is active"

    # Click "Not Selected" tab
    tab_rejected = driver.find_element(By.CSS_SELECTOR, "[data-testid='filter-tab-rejected']")
    tab_rejected.click()
    time.sleep(0.5)

    assert driver.find_element(By.CSS_SELECTOR, f"[data-testid='application-card-{app2.id}']").is_displayed()
    rejected_badge = driver.find_element(By.CSS_SELECTOR, f"[data-testid='badge-status-rejected-{app2.id}']")
    assert "Not Selected" in rejected_badge.text

    shortlisted_cards = driver.find_elements(By.CSS_SELECTOR, f"[data-testid='application-card-{app1.id}']")
    assert len(shortlisted_cards) == 0, "Shortlisted card should be hidden when Not Selected tab is active"

    screenshot_path = SCREENSHOTS_DIR / "us35_02_applicant_status_rejected_and_filters.png"
    driver.save_screenshot(str(screenshot_path))
    assert screenshot_path.exists()


def test_tc35_03_notification_audit_log_accordion_toggle(driver):
    """
    TC-35-03: Verifies that the Notification Audit Log accordion renders
    historical dispatch events and can be toggled open to view delivery details. (AC#6)
    """
    uid = uuid.uuid4().hex[:6]
    candidate_email = f"candidate_audit_{uid}@careerflow.test"
    hr_email = f"hr_audit_{uid}@careerflow.test"

    hr_user = create_user_in_db(hr_email, "ValidPass2026!", role=User.Role.HR_MANAGER)
    candidate_user = create_user_in_db(candidate_email, "ValidPass2026!", role=User.Role.STUDENT)

    room = RecruitmentRoom.objects.create(
        title=f"DevOps Lead {uid}",
        company_name="ScaleCloud Inc",
        created_by=hr_user,
    )

    app = CandidateApplication.objects.create(
        room=room,
        candidate=candidate_user,
        status=CandidateApplication.Status.COMPLETED,
        final_score=86.0,
        is_shortlisted=True,
        hr_decision=CandidateApplication.HrDecision.CONFIRMED,
    )

    # Seed 2 StatusNotificationLog records
    log1 = StatusNotificationLog.objects.create(
        application=app,
        recipient_email=candidate_email,
        status_type=StatusNotificationLog.StatusType.SHORTLISTED,
        email_sent=True,
    )
    log2 = StatusNotificationLog.objects.create(
        application=app,
        recipient_email=candidate_email,
        status_type=StatusNotificationLog.StatusType.CONFIRMED,
        email_sent=True,
    )

    login_user(driver, candidate_email)

    base_url = get_base_url()
    driver.get(f"{base_url}/applications/my-status")

    wait = WebDriverWait(driver, 10)
    toggle_btn = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-toggle-audit-logs-{app.id}']"))
    )
    assert "Notification Audit Log (2 events)" in toggle_btn.text

    # Accordion initially collapsed
    initial_containers = driver.find_elements(By.CSS_SELECTOR, f"[data-testid='audit-logs-container-{app.id}']")
    assert len(initial_containers) == 0, "Audit logs container should be collapsed initially"

    # Click to expand
    toggle_btn.click()
    time.sleep(0.5)

    container = wait.until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='audit-logs-container-{app.id}']"))
    )
    assert container is not None
    container_text = container.text
    assert "Shortlisted" in container_text or "SHORTLISTED" in container_text
    assert "Confirmed" in container_text or "CONFIRMED" in container_text
    assert "Email delivered" in container_text

    screenshot_path = SCREENSHOTS_DIR / "us35_03_notification_audit_log_accordion.png"
    driver.save_screenshot(str(screenshot_path))
    assert screenshot_path.exists()


def test_tc35_04_tenant_isolation_candidate_sees_only_own_applications(driver):
    """
    TC-35-04: Confirms candidate tenant isolation. When Candidate Bob logs in,
    he sees an empty state and cannot see Candidate Alice's applications or decisions. (AC#4)
    """
    uid = uuid.uuid4().hex[:6]
    alice_email = f"alice_confidential_{uid}@careerflow.test"
    bob_email = f"bob_clean_{uid}@careerflow.test"
    hr_email = f"hr_isolation_{uid}@careerflow.test"

    hr_user = create_user_in_db(hr_email, "ValidPass2026!", role=User.Role.HR_MANAGER)
    alice_user = create_user_in_db(alice_email, "ValidPass2026!", role=User.Role.STUDENT, full_name="Alice Confidential")
    bob_user = create_user_in_db(bob_email, "ValidPass2026!", role=User.Role.STUDENT, full_name="Bob Clean")

    room = RecruitmentRoom.objects.create(
        title=f"Confidential Security Specialist {uid}",
        company_name="CyberVault Systems",
        created_by=hr_user,
    )

    # Alice's application
    app_alice = CandidateApplication.objects.create(
        room=room,
        candidate=alice_user,
        status=CandidateApplication.Status.COMPLETED,
        final_score=94.0,
        is_shortlisted=True,
        hr_decision=CandidateApplication.HrDecision.CONFIRMED,
        hr_decision_notes="Top secret recommendation.",
    )

    # Log in as Bob (who has 0 applications)
    login_user(driver, bob_email, full_name="Bob Clean")

    base_url = get_base_url()
    driver.get(f"{base_url}/applications/my-status")

    wait = WebDriverWait(driver, 10)
    empty_state = wait.until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='empty-applications-state']"))
    )
    assert "No applications found" in empty_state.text

    # Assert Alice's confidential room is 100% absent from Bob's DOM
    alice_cards = driver.find_elements(By.CSS_SELECTOR, f"[data-testid='application-card-{app_alice.id}']")
    assert len(alice_cards) == 0, "Alice's application card must not be present in Bob's portal"
    assert f"Confidential Security Specialist {uid}" not in driver.page_source
    assert "Top secret recommendation." not in driver.page_source

    screenshot_path = SCREENSHOTS_DIR / "us35_04_tenant_isolation_empty_state.png"
    driver.save_screenshot(str(screenshot_path))
    assert screenshot_path.exists()


def test_tc35_05_sidebar_navigation_to_status_portal(driver):
    """
    TC-35-05: Verifies that clicking 'Applications' in the Candidate side nav bar
    or the dashboard 'Applications' card transitions seamlessly to /applications/my-status.
    """
    uid = uuid.uuid4().hex[:6]
    student_email = f"nav_student_{uid}@careerflow.test"
    login_user(driver, student_email, full_name="Nav Student")

    wait = WebDriverWait(driver, 10)

    # 1. Click sidebar 'Applications' link
    nav_apps = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='nav-applications']")))
    nav_apps.click()

    wait.until(EC.url_contains("/applications/my-status"))
    assert "/applications/my-status" in driver.current_url

    # Check Page Title
    heading = wait.until(EC.visibility_of_element_located((By.TAG_NAME, "h1")))
    assert "Application Status" in heading.text

    # 2. Return to dashboard and test metric card navigation
    driver.get(f"{get_base_url()}/student/dashboard")
    metric_card = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='card-applications-status']"))
    )
    metric_card.click()

    wait.until(lambda d: "/student/applications" in d.current_url or "/applications" in d.current_url)
    heading_card = wait.until(EC.visibility_of_element_located((By.TAG_NAME, "h1")))
    assert "Application Status" in heading_card.text

    screenshot_path = SCREENSHOTS_DIR / "us35_05_sidebar_navigation_to_status_portal.png"
    driver.save_screenshot(str(screenshot_path))
    assert screenshot_path.exists()


def test_tc35_06_hr_portal_sidebar_navigation_dedicated_views(driver):
    """
    TC-35-06: Verifies dedicated side nav bar navigation for HR Managers:
    - /hr/applicants (Applicants)
    - /hr/shortlisted (Shortlisted)
    - /hr/reports (Reports)
    Asserts each view renders cleanly without bouncing.
    """
    uid = uuid.uuid4().hex[:6]
    hr_email = f"hr_nav_{uid}@careerflow.test"
    login_user(driver, hr_email, role=User.Role.HR_MANAGER, full_name="Elena HR Lead")

    wait = WebDriverWait(driver, 10)

    # 1. Navigate to Applicants
    nav_applicants = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='nav-applicants']")))
    nav_applicants.click()
    wait.until(EC.url_contains("/hr/applicants"))
    assert "/hr/applicants" in driver.current_url
    time.sleep(0.5)

    # 2. Navigate to Shortlisted
    nav_shortlisted = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='nav-shortlisted']")))
    nav_shortlisted.click()
    wait.until(EC.url_contains("/hr/shortlisted"))
    assert "/hr/shortlisted" in driver.current_url
    time.sleep(0.5)

    # 3. Navigate to Reports
    nav_reports = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='nav-reports']")))
    nav_reports.click()
    wait.until(EC.url_contains("/hr/reports"))
    assert "/hr/reports" in driver.current_url

    screenshot_path = SCREENSHOTS_DIR / "us35_06_hr_portal_navigation_dedicated_views.png"
    driver.save_screenshot(str(screenshot_path))
    assert screenshot_path.exists()


def test_tc35_07_agency_portal_sidebar_navigation_dedicated_views(driver):
    """
    TC-35-07: Verifies dedicated side nav bar navigation for Agency Administrators:
    - /agency/shortlisted (Shortlisted Dossiers)
    - /agency/reports (Agency Reports)
    Confirms zero modal trap or backdrop obstruction on initial load.
    """
    uid = uuid.uuid4().hex[:6]
    agency_email = f"agency_nav_{uid}@careerflow.test"
    login_user(driver, agency_email, role=User.Role.AGENCY_ADMIN, full_name="Nadia Agency")

    wait = WebDriverWait(driver, 10)

    # 1. Navigate to Shortlisted
    nav_shortlisted = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='nav-shortlisted']")))
    nav_shortlisted.click()
    wait.until(EC.url_contains("/agency/shortlisted"))
    assert "/agency/shortlisted" in driver.current_url
    time.sleep(0.5)

    # Ensure no blocking modal backdrop is trapped
    modals = driver.find_elements(By.CSS_SELECTOR, "[data-testid='modal-forward-candidates']")
    assert len(modals) == 0, "ForwardCandidatesModal should NOT be mounted or open on page load"

    # 2. Navigate to Reports
    nav_reports = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='nav-reports']")))
    nav_reports.click()
    wait.until(EC.url_contains("/agency/reports"))
    assert "/agency/reports" in driver.current_url

    screenshot_path = SCREENSHOTS_DIR / "us35_07_agency_portal_navigation_dedicated_views.png"
    driver.save_screenshot(str(screenshot_path))
    assert screenshot_path.exists()


def test_tc35_08_agency_shortlisted_configure_rules_and_forward_modal(driver):
    """
    TC-35-08: Verifies Agency Shortlisted page actions:
    - 'Configure Shortlist Rules' button opens criteria modal.
    - Candidate selection activates 'Forward to Client' button.
    - Clicking 'Forward to Client' opens ForwardCandidatesModal cleanly.
    - ESC or cancel button closes the modal.
    """
    uid = uuid.uuid4().hex[:6]
    agency_email = f"agency_actions_{uid}@careerflow.test"
    agency_user = create_user_in_db(agency_email, "ValidPass2026!", role=User.Role.AGENCY_ADMIN, full_name="Marcus Agency")

    client = ClientCompany.objects.create(
        agency=agency_user,
        name=f"Vertex Fintech {uid}",
        industry="Financial Services",
        contact_person="Patrick Finance",
        contact_email=f"patrick_{uid}@vertexfin.test",
        is_active=True,
    )

    room = RecruitmentRoom.objects.create(
        title=f"Quant Developer {uid}",
        company_name=client.name,
        client_company=client,
        created_by=agency_user,
        status="ACTIVE",
    )

    candidate = create_user_in_db(f"candidate_quant_{uid}@careerflow.test", "ValidPass2026!", role=User.Role.STUDENT, full_name="Leo Quant")
    app = CandidateApplication.objects.create(
        room=room,
        candidate=candidate,
        status=CandidateApplication.Status.COMPLETED,
        final_score=94.0,
        is_shortlisted=True,
        shortlist_reason="Top percentile score",
    )

    login_user(driver, agency_email, role=User.Role.AGENCY_ADMIN, full_name="Marcus Agency")

    base_url = get_base_url()
    driver.get(f"{base_url}/agency/shortlisted")

    wait = WebDriverWait(driver, 10)

    # 1. Test "Configure Shortlist Rules" button
    config_btn = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-agency-config-shortlist']"))
    )
    config_btn.click()

    # Modal appears
    config_modal = wait.until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-shortlist-config']"))
    )
    assert config_modal is not None

    # Close modal
    close_modal_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-close-shortlist-modal']")
    close_modal_btn.click()
    time.sleep(0.5)

    # 2. Test Candidate selection and Forward Button
    forward_btn = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='button-forward-selected-top']"))
    )
    assert not forward_btn.is_enabled(), "Forward button should be disabled when 0 candidates are selected"

    # Select candidate checkbox
    checkbox = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='checkbox-forward-{app.id}']"))
    )
    checkbox.click()
    time.sleep(0.3)

    assert forward_btn.is_enabled(), "Forward button should be enabled after candidate selection"
    assert "Forward to Client (1)" in forward_btn.text

    # Open Forward Modal
    forward_btn.click()

    forward_modal = wait.until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-forward-candidates']"))
    )
    assert forward_modal is not None

    # Verify recipient auto-populated with client company email
    email_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-recipient-email']")
    assert client.contact_email in email_input.get_attribute("value")

    # Close Forward Modal via Cancel button
    cancel_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-cancel-forward']")
    cancel_btn.click()
    time.sleep(0.5)

    forward_modals_after = driver.find_elements(By.CSS_SELECTOR, "[data-testid='modal-forward-candidates']")
    assert len(forward_modals_after) == 0, "ForwardCandidatesModal should close after clicking Cancel"

    screenshot_path = SCREENSHOTS_DIR / "us35_08_agency_shortlist_config_and_forward_modal.png"
    driver.save_screenshot(str(screenshot_path))
    assert screenshot_path.exists()
