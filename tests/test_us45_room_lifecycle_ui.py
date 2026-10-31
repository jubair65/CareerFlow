"""
US-45: Recruitment Room Lifecycle & Expiration Management UI Test Suite (US-45-T6).
User Story: US-45 – Recruitment Room Lifecycle & Expiration Management
Sprint: Sprint 7 – Final Platform Maturity & Release
Lead Developer: Nafisa Tabassum Maria (@Maria-07-222)
Dedicated Peer UI Automation Tester & Reviewer: MD. Hasanul Mobin (@hasanulmobin)
Target Branch: feat/us-45-room-lifecycle -> develop

Acceptance Criteria & Scenarios Verified:
✔ TC-45-01: HR Status Filter Pills (filter rooms by OPEN, PAUSED, CLOSED, DRAFT, ALL) [AC-6]
✔ TC-45-02: Set & Update Room Deadline (modal date entry, immediate UI badge & DB update) [AC-1]
✔ TC-45-03: Pause & Close Room (more actions menu, state transitions to PAUSED and CLOSED) [AC-2, AC-3]
✔ TC-45-04: Manual Reopening (reopen paused/closed room, restores OPEN status & acceptance) [AC-5]
✔ TC-45-05: Applicant Live Urgency Banner (<24h deadline countdown alert on public portal) [AC-1, AC-3]
✔ TC-45-06: Applicant Submission Blocked on Paused Room (HTTP 410 gatekeeper & card-link-error) [AC-3]
✔ TC-45-07: Applicant Submission Blocked Past Deadline (HTTP 410 gatekeeper & expired card) [AC-4]
✔ TC-45-08: Clear Deadline (remove deadline, revert to open indefinitely, DB cleared) [AC-1]
"""

import os
import sys
import time
import uuid
from pathlib import Path
from datetime import timedelta

TESTS_DIR = Path(__file__).resolve().parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

import pytest
import requests
from django.conf import settings
from django.utils import timezone
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from apps.authentication.models import User
from apps.recruitment.models import RecruitmentRoom
from conftest import FRONTEND_URL, BACKEND_URL, SCREENSHOTS_DIR, create_user_in_db


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


def set_react_input(driver, element, text: str):
    """Clears and types into React controlled input, firing required synthetic events."""
    clear_react_input(driver, element)
    if text:
        element.send_keys(text)
        driver.execute_script(
            "arguments[0].dispatchEvent(new Event('input', { bubbles: true })); "
            "arguments[0].dispatchEvent(new Event('change', { bubbles: true }));",
            element,
        )


def set_datetime_local_input(driver, element, dt_str: str):
    """Sets a datetime-local input value through React's native setter and triggers input/change events."""
    driver.execute_script(
        "const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set; "
        "setter.call(arguments[0], arguments[1]); "
        "arguments[0].dispatchEvent(new Event('input', { bubbles: true })); "
        "arguments[0].dispatchEvent(new Event('change', { bubbles: true }));",
        element,
        dt_str,
    )


def login_hr_user(driver, email: str, password: str = "ValidPass2026!", full_name: str = "HR Lifecycle Manager"):
    """Helper to authenticate an HR Manager via the UI login page and navigate to /hr/rooms."""
    user = User.objects.filter(email__iexact=email).first()
    if not user:
        user = create_user_in_db(email, password, role=User.Role.HR_MANAGER, full_name=full_name)

    driver.get(f"{FRONTEND_URL}/login")
    driver.execute_script("sessionStorage.clear(); localStorage.clear();")
    driver.refresh()

    wait = WebDriverWait(driver, 10)
    email_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-login-email']")))
    pass_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-login-password']")
    submit_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-login']")

    set_react_input(driver, email_input, email)
    set_react_input(driver, pass_input, password)
    submit_btn.click()

    wait.until(EC.url_contains("/hr/dashboard"))
    # Navigate to the rooms management view
    driver.get(f"{FRONTEND_URL}/hr/rooms")
    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='section-recruitment-rooms']")))
    return user


def create_room_for_hr(
    user: User,
    title: str,
    company: str = "TechNova Solutions",
    status: str = RecruitmentRoom.Status.OPEN,
    deadline=None,
    cv_weight: int = 50,
    video_weight: int = 50,
    skills=None,
) -> RecruitmentRoom:
    """Helper to instantiate a recruitment room in a specified lifecycle status."""
    if skills is None:
        skills = ["Python", "Django", "React"]

    room = RecruitmentRoom.objects.create(
        created_by=user,
        title=title,
        company_name=company,
        status=status,
        application_deadline=deadline,
        cv_weight=cv_weight,
        video_weight=video_weight,
        skills_required=skills,
        link_is_active=True,
    )
    return room


# ---------------------------------------------------------------------------
# Test Cases TC-45-01 through TC-45-08
# ---------------------------------------------------------------------------

def test_tc45_01_hr_status_filter_pills(driver):
    """
    TC-45-01: HR Status Filter Pills
    Scenario: Verify that clicking OPEN, PAUSED, CLOSED, DRAFT, and ALL filter pills
    correctly isolates and displays only rooms in the corresponding lifecycle state.
    """
    email = f"tc45_01_{uuid.uuid4().hex[:6]}@careerflow.test"
    hr_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.HR_MANAGER, full_name="Filter HR Tester")

    room_open = create_room_for_hr(hr_user, f"Open Role {uuid.uuid4().hex[:4]}", status=RecruitmentRoom.Status.OPEN)
    room_paused = create_room_for_hr(hr_user, f"Paused Role {uuid.uuid4().hex[:4]}", status=RecruitmentRoom.Status.PAUSED)
    room_closed = create_room_for_hr(hr_user, f"Closed Role {uuid.uuid4().hex[:4]}", status=RecruitmentRoom.Status.CLOSED)
    room_draft = create_room_for_hr(hr_user, f"Draft Role {uuid.uuid4().hex[:4]}", status=RecruitmentRoom.Status.DRAFT)

    login_hr_user(driver, email)
    wait = WebDriverWait(driver, 10)

    # 1. Filter by OPEN
    open_filter = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='filter-status-open']")))
    driver.execute_script("arguments[0].click();", open_filter)
    time.sleep(0.5)

    visible_cards = [c.get_attribute("data-testid") for c in driver.find_elements(By.CSS_SELECTOR, "[data-testid^='card-room-']")]
    assert f"card-room-{room_open.id}" in visible_cards
    assert f"card-room-{room_paused.id}" not in visible_cards
    assert f"card-room-{room_closed.id}" not in visible_cards
    assert f"card-room-{room_draft.id}" not in visible_cards

    # 2. Filter by PAUSED
    paused_filter = driver.find_element(By.CSS_SELECTOR, "[data-testid='filter-status-paused']")
    driver.execute_script("arguments[0].click();", paused_filter)
    time.sleep(0.5)

    visible_cards = [c.get_attribute("data-testid") for c in driver.find_elements(By.CSS_SELECTOR, "[data-testid^='card-room-']")]
    assert f"card-room-{room_paused.id}" in visible_cards
    assert f"card-room-{room_open.id}" not in visible_cards

    # 3. Filter by CLOSED
    closed_filter = driver.find_element(By.CSS_SELECTOR, "[data-testid='filter-status-closed']")
    driver.execute_script("arguments[0].click();", closed_filter)
    time.sleep(0.5)

    visible_cards = [c.get_attribute("data-testid") for c in driver.find_elements(By.CSS_SELECTOR, "[data-testid^='card-room-']")]
    assert f"card-room-{room_closed.id}" in visible_cards
    assert f"card-room-{room_paused.id}" not in visible_cards

    # 4. Filter by DRAFT
    draft_filter = driver.find_element(By.CSS_SELECTOR, "[data-testid='filter-status-draft']")
    driver.execute_script("arguments[0].click();", draft_filter)
    time.sleep(0.5)

    visible_cards = [c.get_attribute("data-testid") for c in driver.find_elements(By.CSS_SELECTOR, "[data-testid^='card-room-']")]
    assert f"card-room-{room_draft.id}" in visible_cards
    assert f"card-room-{room_closed.id}" not in visible_cards

    # 5. Filter by ALL
    all_filter = driver.find_element(By.CSS_SELECTOR, "[data-testid='filter-status-all']")
    driver.execute_script("arguments[0].click();", all_filter)
    time.sleep(0.5)

    visible_cards = [c.get_attribute("data-testid") for c in driver.find_elements(By.CSS_SELECTOR, "[data-testid^='card-room-']")]
    assert f"card-room-{room_open.id}" in visible_cards
    assert f"card-room-{room_paused.id}" in visible_cards
    assert f"card-room-{room_closed.id}" in visible_cards
    assert f"card-room-{room_draft.id}" in visible_cards

    # Capture visual screenshot
    driver.save_screenshot(str(SCREENSHOTS_DIR / "us45_01_status_filters.png"))


def test_tc45_02_set_and_update_room_deadline(driver):
    """
    TC-45-02: Set & Update Room Deadline
    Scenario: In an open room without a deadline, open the Quick Deadline Modal,
    enter a future date/time, save, and verify immediate UI badge update and DB persistence.
    """
    email = f"tc45_02_{uuid.uuid4().hex[:6]}@careerflow.test"
    hr_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.HR_MANAGER, full_name="Deadline HR Tester")
    room = create_room_for_hr(hr_user, f"Deadline Target Role {uuid.uuid4().hex[:4]}", deadline=None)

    login_hr_user(driver, email)
    wait = WebDriverWait(driver, 10)

    # Verify initial text: "No deadline set"
    deadline_val_el = wait.until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='room-deadline-value-{room.id}']"))
    )
    assert "No deadline set" in deadline_val_el.text

    # Click 'Set Deadline' button
    set_deadline_btn = driver.find_element(By.CSS_SELECTOR, f"[data-testid='button-set-deadline-{room.id}']")
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", set_deadline_btn)
    driver.execute_script("arguments[0].click();", set_deadline_btn)

    # Verify Quick Deadline Modal appears
    modal = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-set-deadline']")))
    assert modal.is_displayed()

    # Enter a future deadline date (7 days from now)
    future_date = timezone.now() + timedelta(days=7)
    dt_str = future_date.strftime("%Y-%m-%dT18:00")
    date_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-room-deadline']")
    set_datetime_local_input(driver, date_input, dt_str)

    # Click Save Deadline
    save_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-save-deadline']")
    driver.execute_script("arguments[0].click();", save_btn)

    # Wait for modal to close
    wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-set-deadline']")))

    # Verify the card displays the updated formatted deadline and 'Active' badge
    updated_deadline_el = wait.until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='room-deadline-value-{room.id}']"))
    )
    assert str(future_date.year) in updated_deadline_el.text

    # Verify in DB
    room.refresh_from_db()
    assert room.application_deadline is not None
    assert room.application_deadline.year == future_date.year

    driver.save_screenshot(str(SCREENSHOTS_DIR / "us45_02_set_deadline.png"))


def test_tc45_03_pause_and_close_room(driver):
    """
    TC-45-03: Pause & Close Room
    Scenario: Transition an active room to PAUSED, and subsequently to CLOSED using
    the More Actions dropdown menu. Verify status badge updates and DB state changes.
    """
    email = f"tc45_03_{uuid.uuid4().hex[:6]}@careerflow.test"
    hr_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.HR_MANAGER, full_name="State Transitions HR")
    room = create_room_for_hr(hr_user, f"Lifecycle Role {uuid.uuid4().hex[:4]}", status=RecruitmentRoom.Status.OPEN)

    login_hr_user(driver, email)
    wait = WebDriverWait(driver, 10)

    # Verify starting status is OPEN
    status_badge = wait.until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='room-status-{room.id}']"))
    )
    assert "OPEN" in status_badge.text

    # Step 1: Pause Room
    more_btn = driver.find_element(By.CSS_SELECTOR, f"[data-testid='button-more-actions-{room.id}']")
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", more_btn)
    driver.execute_script("arguments[0].click();", more_btn)

    pause_btn = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-pause-room-{room.id}']"))
    )
    driver.execute_script("arguments[0].click();", pause_btn)

    # Wait for status badge to reflect PAUSED
    wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, f"[data-testid='room-status-{room.id}']"), "PAUSED"))
    room.refresh_from_db()
    assert room.status == RecruitmentRoom.Status.PAUSED

    # Step 2: Close Room
    more_btn_again = driver.find_element(By.CSS_SELECTOR, f"[data-testid='button-more-actions-{room.id}']")
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", more_btn_again)
    driver.execute_script("arguments[0].click();", more_btn_again)

    close_btn = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-close-room-{room.id}']"))
    )
    driver.execute_script("arguments[0].click();", close_btn)

    # Wait for status badge to reflect CLOSED
    wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, f"[data-testid='room-status-{room.id}']"), "CLOSED"))
    room.refresh_from_db()
    assert room.status == RecruitmentRoom.Status.CLOSED

    driver.save_screenshot(str(SCREENSHOTS_DIR / "us45_03_pause_close_room.png"))


def test_tc45_04_manual_reopening(driver):
    """
    TC-45-04: Manual Reopening (AC-5)
    Scenario: Verify that an HR Manager can manually reopen a closed or paused room,
    restoring it to OPEN status and allowing applications to be accepted once more.
    """
    email = f"tc45_04_{uuid.uuid4().hex[:6]}@careerflow.test"
    hr_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.HR_MANAGER, full_name="Reopen HR Tester")
    room = create_room_for_hr(hr_user, f"Reopenable Role {uuid.uuid4().hex[:4]}", status=RecruitmentRoom.Status.CLOSED)

    login_hr_user(driver, email)
    wait = WebDriverWait(driver, 10)

    # Verify room is closed
    status_badge = wait.until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='room-status-{room.id}']"))
    )
    assert "CLOSED" in status_badge.text

    # Reopen room via more actions or toggle status button
    more_btn = driver.find_element(By.CSS_SELECTOR, f"[data-testid='button-more-actions-{room.id}']")
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", more_btn)
    driver.execute_script("arguments[0].click();", more_btn)

    reopen_btn = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-reopen-room-{room.id}']"))
    )
    driver.execute_script("arguments[0].click();", reopen_btn)

    # Wait for status badge to reflect OPEN
    wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, f"[data-testid='room-status-{room.id}']"), "OPEN"))
    room.refresh_from_db()
    assert room.status == RecruitmentRoom.Status.OPEN
    assert room.is_open is True
    assert room.is_accepting_applications is True

    driver.save_screenshot(str(SCREENSHOTS_DIR / "us45_04_manual_reopening.png"))


def test_tc45_05_applicant_live_urgency_banner(driver):
    """
    TC-45-05: Applicant Live Urgency Countdown Banner (AC-1, AC-3)
    Scenario: When a room deadline is less than 24 hours away, the public applicant
    portal (/apply/:token) renders the live urgency banner with remaining countdown.
    """
    email = f"tc45_05_{uuid.uuid4().hex[:6]}@careerflow.test"
    hr_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.HR_MANAGER, full_name="Urgency HR")
    
    # Set deadline 5 hours from now (< 24 hours)
    urgent_deadline = timezone.now() + timedelta(hours=5, minutes=30)
    room = create_room_for_hr(
        hr_user,
        f"Urgent Role {uuid.uuid4().hex[:4]}",
        status=RecruitmentRoom.Status.OPEN,
        deadline=urgent_deadline
    )

    # Navigate directly to public application page without HR authentication
    driver.get(f"{FRONTEND_URL}/apply/{room.share_token}")
    wait = WebDriverWait(driver, 10)

    # Ensure application page loads
    app_page = wait.until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='page-public-application']"))
    )
    assert app_page.is_displayed()

    # Verify Deadline Card exists
    deadline_card = wait.until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='public-room-deadline-card']"))
    )
    assert deadline_card.is_displayed()

    # Verify Live Urgency Banner is visible with countdown
    urgency_banner = wait.until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='public-deadline-urgency-banner']"))
    )
    assert urgency_banner.is_displayed()
    assert "Applications Close Soon" in urgency_banner.text
    assert "remaining" in urgency_banner.text

    # Verify submit application button is enabled
    submit_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-submit-application']")
    assert submit_btn.is_enabled()

    driver.save_screenshot(str(SCREENSHOTS_DIR / "us45_05_urgency_countdown.png"))


def test_tc45_06_applicant_submission_blocked_paused_room(driver):
    """
    TC-45-06: Applicant Submission Blocked on Paused Room (AC-3)
    Scenario: Verify that when an applicant attempts to access a paused recruitment room,
    the validate_share_token gatekeeper blocks access with HTTP 410 Gone, rendering
    the dedicated error screen (card-link-error) and disabling submissions.
    """
    email = f"tc45_06_{uuid.uuid4().hex[:6]}@careerflow.test"
    hr_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.HR_MANAGER, full_name="Paused Gate HR")
    room = create_room_for_hr(
        hr_user,
        f"Paused Role {uuid.uuid4().hex[:4]}",
        status=RecruitmentRoom.Status.PAUSED,
    )

    # Attempt to access public apply page
    driver.get(f"{FRONTEND_URL}/apply/{room.share_token}")
    wait = WebDriverWait(driver, 10)

    # Verify the dedicated error screen renders
    error_card = wait.until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='card-link-error']"))
    )
    assert error_card.is_displayed()

    # Verify error code badge and status heading
    card_text = error_card.text
    assert "ROOM_PAUSED" in card_text
    assert "Applications Temporarily Paused" in card_text

    # Verify API level gatekeeper: direct submission is blocked with HTTP 410 Gone
    api_url = f"{BACKEND_URL}/api/recruitment/apply/{room.share_token}/submit/"
    payload = {
        "full_name": "Evelyn Candidate",
        "email": "evelyn@candidate.test",
    }
    resp = requests.post(api_url, data=payload)
    assert resp.status_code == 410
    resp_json = resp.json()
    assert resp_json.get("code") == "ROOM_PAUSED"

    driver.save_screenshot(str(SCREENSHOTS_DIR / "us45_06_applicant_paused_blocked.png"))


def test_tc45_07_applicant_submission_blocked_past_deadline(driver):
    """
    TC-45-07: Applicant Submission Blocked Past Deadline (AC-4)
    Scenario: Verify that when a room's deadline has expired, public access is gated
    with HTTP 410 Gone and structured error code DEADLINE_PASSED, preventing submissions.
    """
    email = f"tc45_07_{uuid.uuid4().hex[:6]}@careerflow.test"
    hr_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.HR_MANAGER, full_name="Expired Gate HR")
    
    # Set deadline in past (3 hours ago)
    past_deadline = timezone.now() - timedelta(hours=3)
    room = create_room_for_hr(
        hr_user,
        f"Expired Role {uuid.uuid4().hex[:4]}",
        status=RecruitmentRoom.Status.OPEN,
        deadline=past_deadline
    )

    # Navigate to public apply link
    driver.get(f"{FRONTEND_URL}/apply/{room.share_token}")
    wait = WebDriverWait(driver, 10)

    # Verify dedicated error card renders
    error_card = wait.until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='card-link-error']"))
    )
    assert error_card.is_displayed()

    # Verify error code badge and status heading
    card_text = error_card.text
    assert "DEADLINE_PASSED" in card_text
    assert "Application Deadline Has Passed" in card_text

    # Verify API level gatekeeper: direct submission returns HTTP 410 Gone
    api_url = f"{BACKEND_URL}/api/recruitment/apply/{room.share_token}/submit/"
    payload = {
        "full_name": "Marcus Candidate",
        "email": "marcus@candidate.test",
    }
    resp = requests.post(api_url, data=payload)
    assert resp.status_code == 410
    resp_json = resp.json()
    assert resp_json.get("code") == "DEADLINE_PASSED"

    driver.save_screenshot(str(SCREENSHOTS_DIR / "us45_07_applicant_deadline_passed.png"))


def test_tc45_08_clear_deadline(driver):
    """
    TC-45-08: Clear Application Deadline (AC-1)
    Scenario: Open the Quick Deadline Modal on a room that has a deadline configured,
    click 'Clear Deadline', and verify that the deadline is wiped in DB and the UI
    reflects 'No deadline set (Open indefinitely)'.
    """
    email = f"tc45_08_{uuid.uuid4().hex[:6]}@careerflow.test"
    hr_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.HR_MANAGER, full_name="Clear Deadline HR")
    
    future_deadline = timezone.now() + timedelta(days=14)
    room = create_room_for_hr(
        hr_user,
        f"Clear Deadline Role {uuid.uuid4().hex[:4]}",
        status=RecruitmentRoom.Status.OPEN,
        deadline=future_deadline
    )

    login_hr_user(driver, email)
    wait = WebDriverWait(driver, 10)

    # Verify initial deadline is present
    deadline_val_el = wait.until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='room-deadline-value-{room.id}']"))
    )
    assert str(future_deadline.year) in deadline_val_el.text

    # Click 'Edit' button on deadline card
    edit_deadline_btn = driver.find_element(By.CSS_SELECTOR, f"[data-testid='button-set-deadline-{room.id}']")
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", edit_deadline_btn)
    driver.execute_script("arguments[0].click();", edit_deadline_btn)

    # Wait for modal to appear
    modal = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-set-deadline']")))
    assert modal.is_displayed()

    # Click 'Clear Deadline'
    clear_btn = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-clear-deadline']"))
    )
    driver.execute_script("arguments[0].click();", clear_btn)

    # Wait for modal to close
    wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-set-deadline']")))

    # Verify deadline value updates to "No deadline set (Open indefinitely)"
    updated_deadline_el = wait.until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='room-deadline-value-{room.id}']"))
    )
    assert "No deadline set" in updated_deadline_el.text

    # Verify DB update
    room.refresh_from_db()
    assert room.application_deadline is None

    driver.save_screenshot(str(SCREENSHOTS_DIR / "us45_08_clear_deadline.png"))
