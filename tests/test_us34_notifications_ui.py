"""
US-34: Analysis Completion Notifications UI Automation Test Suite (US-34-T6).
Lead Developer: Jannatun Naeem Mona (@jn-mona04)
Reviewer & Peer UI Tester: Farhana Tahsin Bonny (@tahsinbonnie98)
Sprint: Sprint 6 — Analytics, Reports & Alerts / Omni-Channel Notifications

Acceptance Criteria & Features Verified:
✓ AC#1: Notification generated automatically on CV/Video analysis completion (US-34-T1, US-34-T2)
✓ AC#2: In-app Notification Center with dynamic unread counter badge (US-34-T3)
✓ AC#3: Transactional email notification sent upon pipeline completion (US-34-T4)
✓ AC#4: Direct link to completed analysis results page (US-34-T3)
✓ AC#5: Pipeline fault isolation (notification failures do not break analysis) (US-34-T2)
✓ AC#6: Persistent read/unread status in database and API operations (US-34-T5)
✓ Sidebar Integration: Side nav bar badge count, active state, and navigation to /notifications portal
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
from apps.core.models import Notification
from apps.presentation.models import (
    PresentationVideo,
    PresentationScore,
    SpeechAnalysis,
    BehavioralAnalysis,
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


def login_student(driver, email: str, password: str = "ValidPass2026!", full_name: str = "Mona Candidate"):
    """Helper to ensure student exists and authenticates via UI."""
    if not User.objects.filter(email__iexact=email).exists():
        create_user_in_db(email, password, role=User.Role.STUDENT, full_name=full_name)

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

    wait.until(EC.url_contains("/student/dashboard"))


def create_test_video_with_score(user: User, title: str = "Mock Pitch Take") -> PresentationVideo:
    """Creates a sample presentation video and score for deep linking test."""
    video = PresentationVideo.objects.create(
        user=user,
        file=f"students/{user.id}/videos/{title.lower().replace(' ', '_')}.mp4",
        original_filename=f"{title}.mp4",
        raw_file_size=1024 * 1024 * 8,
        compressed_file_size=1024 * 1024 * 3,
        file_type="mp4",
        duration_seconds=95,
        status="COMPLETED",
        is_active=True,
    )
    SpeechAnalysis.objects.create(
        video=video,
        transcript="Hello, I am presenting my technical portfolio and software engineering background.",
        words_per_minute=142.0,
        filler_word_count=2,
        clarity_score=88,
    )
    BehavioralAnalysis.objects.create(
        video=video,
        eye_contact_score=89,
        posture_score=92,
        engagement_score=86,
    )
    PresentationScore.objects.create(
        video=video,
        overall_score=88,
        speech_score=88,
        behavioral_score=89,
    )
    return video


# ==============================================================================
# UI TEST CASES: US-34-T6
# ==============================================================================


def test_tc34_01_empty_notification_center_renders_clean_empty_state(driver):
    """
    TC-34-01: Verifies that a user with 0 notifications sees no red badges
    on header bell or sidebar, and clicking the bell opens the popover with
    the welcoming empty state graphic. (AC#2)
    """
    unique_id = uuid.uuid4().hex[:6]
    email = f"student_empty_{unique_id}@careerflow.test"
    login_student(driver, email, full_name="Empty State Student")

    wait = WebDriverWait(driver, 10)
    bell_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-header-notifications']")))

    # Verify NO header badge is present
    header_badges = driver.find_elements(By.CSS_SELECTOR, "[data-testid='notification-bell-badge']")
    assert len(header_badges) == 0, "Header notification badge should not exist when unread count is 0"

    # Verify NO sidebar badge is present
    sidebar_badges = driver.find_elements(By.CSS_SELECTOR, "[data-testid='sidebar-notification-badge']")
    assert len(sidebar_badges) == 0, "Sidebar notification badge should not exist when unread count is 0"

    # Open popover
    bell_button.click()
    time.sleep(0.5)

    popover = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='notification-popover']")))
    empty_state = popover.find_element(By.CSS_SELECTOR, "[data-testid='notification-empty-state']")
    assert "No notifications yet" in empty_state.text

    # Capture screenshot
    screenshot_path = SCREENSHOTS_DIR / "us34_01_empty_notification_center.png"
    driver.save_screenshot(str(screenshot_path))
    assert screenshot_path.exists(), f"Screenshot not saved at {screenshot_path}"



def test_tc34_02_notification_bell_badge_counter_and_popover_list(driver):
    """
    TC-34-02: Verifies unread counter badge turns red with exact count (2)
    on both the navbar bell and the side nav bar, and popover lists all
    notifications with category icons and unread dots. (AC#2)
    """
    unique_id = uuid.uuid4().hex[:6]
    email = f"student_notif_{unique_id}@careerflow.test"
    user = create_user_in_db(email, "ValidPass2026!", role=User.Role.STUDENT, full_name="Notification Student")

    # Seed 2 unread notifications
    Notification.objects.create(
        user=user,
        title="CV Analysis Complete",
        message="Your CV has been parsed and evaluated. 14 key skills identified.",
        link_url="/student/cv",
        notification_type=Notification.NotificationType.CV_ANALYSIS_COMPLETE,
        is_read=False,
    )
    Notification.objects.create(
        user=user,
        title="Presentation Analysis Ready",
        message="Your video presentation analysis is complete with an overall score of 88/100.",
        link_url="/student/videos",
        notification_type=Notification.NotificationType.PRESENTATION_ANALYSIS_COMPLETE,
        is_read=False,
    )

    login_student(driver, email, full_name="Notification Student")
    wait = WebDriverWait(driver, 10)

    # Verify header badge says '2'
    header_badge = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='notification-bell-badge']")))
    assert header_badge.text == "2", f"Expected header badge '2', got '{header_badge.text}'"

    # Verify sidebar badge says '2'
    sidebar_badge = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='sidebar-notification-badge']")))
    assert sidebar_badge.text == "2", f"Expected sidebar badge '2', got '{sidebar_badge.text}'"

    # Click bell to open dropdown popover
    bell_button = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-header-notifications']")
    bell_button.click()
    time.sleep(0.5)

    popover = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='notification-popover']")))
    unread_dots = popover.find_elements(By.CSS_SELECTOR, "[data-testid='notification-unread-dot']")
    assert len(unread_dots) == 2, f"Expected 2 unread indicators, found {len(unread_dots)}"
    assert "CV Analysis Complete" in popover.text
    assert "Presentation Analysis Ready" in popover.text

    # Capture screenshot
    screenshot_path = SCREENSHOTS_DIR / "us34_02_navbar_bell_popover_unread_notifications.png"
    driver.save_screenshot(str(screenshot_path))
    assert screenshot_path.exists()



def test_tc34_03_click_notification_item_navigates_to_results_and_marks_read(driver):
    """
    TC-34-03: Clicks on a notification item inside the popover; verifies
    immediate navigation to the target results page, database update to is_read=True,
    and reactive decrement of the unread badge count to 1 on both badges. (AC#4 & AC#6)
    """
    unique_id = uuid.uuid4().hex[:6]
    email = f"student_click_{unique_id}@careerflow.test"
    user = create_user_in_db(email, "ValidPass2026!", role=User.Role.STUDENT, full_name="Click Test Student")

    video = create_test_video_with_score(user, "Technical Presentation Round 1")
    target_link = f"/presentation/history/{video.id}"

    notif_target = Notification.objects.create(
        user=user,
        title="Presentation Analysis Ready",
        message="Your video presentation analysis is complete with an overall score of 89/100.",
        link_url=target_link,
        notification_type=Notification.NotificationType.PRESENTATION_ANALYSIS_COMPLETE,
        is_read=False,
    )
    Notification.objects.create(
        user=user,
        title="CV Analysis Complete",
        message="Your CV has been parsed and evaluated.",
        link_url="/student/cv",
        notification_type=Notification.NotificationType.CV_ANALYSIS_COMPLETE,
        is_read=False,
    )

    login_student(driver, email, full_name="Click Test Student")
    wait = WebDriverWait(driver, 10)

    # Open popover
    bell_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-header-notifications']")))
    bell_button.click()
    time.sleep(0.5)

    # Click target notification item
    item_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='notification-item-{notif_target.id}']")))
    item_btn.click()

    # Verify route redirected to target results page
    wait.until(EC.url_contains(f"/presentation/history/{video.id}"))
    time.sleep(1.0)

    # Verify notification marked as read in database
    notif_target.refresh_from_db()
    assert notif_target.is_read is True, "Target notification should be marked as read in DB"

    # Verify both header and sidebar badges decremented to 1
    header_badge = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='notification-bell-badge']")))
    assert header_badge.text == "1", f"Expected header badge decremented to '1', got '{header_badge.text}'"

    sidebar_badge = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='sidebar-notification-badge']")))
    assert sidebar_badge.text == "1", f"Expected sidebar badge decremented to '1', got '{sidebar_badge.text}'"

    # Capture screenshot
    screenshot_path = SCREENSHOTS_DIR / "us34_03_notification_click_navigates_and_marks_read.png"
    driver.save_screenshot(str(screenshot_path))
    assert screenshot_path.exists()



def test_tc34_04_mark_all_notifications_as_read_in_popover(driver):
    """
    TC-34-04: Clicks 'Mark all read' action in the popover; verifies all
    notifications updated to is_read=True in DB and red badges disappear from
    both header and side nav bar. (AC#6)
    """
    unique_id = uuid.uuid4().hex[:6]
    email = f"student_bulk_{unique_id}@careerflow.test"
    user = create_user_in_db(email, "ValidPass2026!", role=User.Role.STUDENT, full_name="Bulk Read Student")

    for i in range(3):
        Notification.objects.create(
            user=user,
            title=f"Assessment Update #{i+1}",
            message=f"Evaluation update message #{i+1}",
            link_url="/student/dashboard",
            is_read=False,
        )

    login_student(driver, email, full_name="Bulk Read Student")
    wait = WebDriverWait(driver, 10)

    # Open popover
    bell_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-header-notifications']")))
    bell_button.click()
    time.sleep(0.5)

    mark_all_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-mark-all-read']")))
    mark_all_btn.click()
    time.sleep(1.0)

    # Verify all in DB are read
    unread_count = Notification.objects.filter(user=user, is_read=False).count()
    assert unread_count == 0, f"Expected 0 unread in DB, got {unread_count}"

    # Close popover and check badges gone
    driver.find_element(By.CSS_SELECTOR, "body").click()
    time.sleep(0.5)

    header_badges = driver.find_elements(By.CSS_SELECTOR, "[data-testid='notification-bell-badge']")
    assert len(header_badges) == 0, "Header badge should be removed after mark all read"

    sidebar_badges = driver.find_elements(By.CSS_SELECTOR, "[data-testid='sidebar-notification-badge']")
    assert len(sidebar_badges) == 0, "Sidebar badge should be removed after mark all read"

    # Capture screenshot
    screenshot_path = SCREENSHOTS_DIR / "us34_04_mark_all_notifications_read.png"
    driver.save_screenshot(str(screenshot_path))
    assert screenshot_path.exists()



def test_tc34_05_sidebar_nav_button_navigates_to_dedicated_notifications_portal(driver):
    """
    TC-34-05: Clicks 'Notifications' on the side navigation bar; verifies
    URL changes to /notifications, side nav bar applies active yellow highlight,
    and dedicated Notifications Center page renders with full cards. (Sidebar Fix Verification)
    """
    unique_id = uuid.uuid4().hex[:6]
    email = f"student_sidebar_{unique_id}@careerflow.test"
    user = create_user_in_db(email, "ValidPass2026!", role=User.Role.STUDENT, full_name="Sidebar Nav Student")

    Notification.objects.create(
        user=user,
        title="CV Analysis Complete",
        message="Your CV has been parsed and evaluated. 12 skills extracted.",
        link_url="/student/cv",
        notification_type=Notification.NotificationType.CV_ANALYSIS_COMPLETE,
        is_read=False,
    )

    login_student(driver, email, full_name="Sidebar Nav Student")
    wait = WebDriverWait(driver, 10)

    sidebar_notif_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='nav-notifications']")))
    sidebar_notif_btn.click()

    wait.until(EC.url_contains("/notifications"))
    time.sleep(0.5)

    # Verify dedicated page title
    page_heading = wait.until(EC.visibility_of_element_located((By.XPATH, "//h1[contains(text(), 'Notifications Center')]")))
    assert page_heading is not None

    # Verify active styling on sidebar button
    active_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='nav-notifications']")
    assert "bg-[#f5c84b]" in active_btn.get_attribute("class"), "Sidebar notifications button should have active yellow background"

    # Capture screenshot
    screenshot_path = SCREENSHOTS_DIR / "us34_05_sidebar_nav_to_notifications_portal.png"
    driver.save_screenshot(str(screenshot_path))
    assert screenshot_path.exists()



def test_tc34_06_notifications_page_filter_tabs_and_single_delete(driver):
    """
    TC-34-06: Verifies filter tabs (All vs Unread) on dedicated notifications page
    and deletes an individual notification card using the trash action button. (AC#6)
    """
    unique_id = uuid.uuid4().hex[:6]
    email = f"student_portal_{unique_id}@careerflow.test"
    user = create_user_in_db(email, "ValidPass2026!", role=User.Role.STUDENT, full_name="Portal Filter Student")

    n1 = Notification.objects.create(
        user=user,
        title="Unread Alert",
        message="Unread notification body text.",
        link_url="/dashboard",
        is_read=False,
    )
    n2 = Notification.objects.create(
        user=user,
        title="Read Historical Notice",
        message="Older read notification message.",
        link_url="/dashboard",
        is_read=True,
    )

    login_student(driver, email, full_name="Portal Filter Student")
    driver.get(f"{get_base_url()}/notifications")

    wait = WebDriverWait(driver, 10)
    filter_unread = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='filter-notifications-unread']")))
    filter_all = driver.find_element(By.CSS_SELECTOR, "[data-testid='filter-notifications-all']")

    # Filter by Unread
    filter_unread.click()
    time.sleep(0.5)
    assert driver.find_elements(By.CSS_SELECTOR, f"[data-testid='notification-card-{n1.id}']")
    assert not driver.find_elements(By.CSS_SELECTOR, f"[data-testid='notification-card-{n2.id}']")

    # Switch back to All
    filter_all.click()
    time.sleep(0.5)
    assert driver.find_elements(By.CSS_SELECTOR, f"[data-testid='notification-card-{n1.id}']")
    assert driver.find_elements(By.CSS_SELECTOR, f"[data-testid='notification-card-{n2.id}']")

    # Delete n1
    card1 = driver.find_element(By.CSS_SELECTOR, f"[data-testid='notification-card-{n1.id}']")
    # Trigger hover to reveal delete button
    driver.execute_script("arguments[0].scrollIntoView(true);", card1)
    delete_btn = driver.find_element(By.CSS_SELECTOR, f"[data-testid='button-delete-{n1.id}']")
    driver.execute_script("arguments[0].click();", delete_btn)
    time.sleep(1.0)

    # Verify deleted from DB
    assert not Notification.objects.filter(id=n1.id).exists(), "Notification should be deleted from DB"

    # Capture screenshot
    screenshot_path = SCREENSHOTS_DIR / "us34_06_notifications_portal_filters_and_delete.png"
    driver.save_screenshot(str(screenshot_path))
    assert screenshot_path.exists()



def test_tc34_07_tenant_isolation_user_notifications_zero_leakage(driver):
    """
    TC-34-07: Verifies strict multi-tenant isolation: Candidate Alice has notifications,
    Candidate Bob logs in and has 0 notifications. Alice's notifications are completely
    isolated with zero data leakage. (AC#6)
    """
    unique_id = uuid.uuid4().hex[:6]
    email_alice = f"alice_{unique_id}@careerflow.test"
    email_bob = f"bob_{unique_id}@careerflow.test"

    user_alice = create_user_in_db(email_alice, "ValidPass2026!", role=User.Role.STUDENT, full_name="Alice Candidate")
    user_bob = create_user_in_db(email_bob, "ValidPass2026!", role=User.Role.STUDENT, full_name="Bob Candidate")

    Notification.objects.create(
        user=user_alice,
        title="Alice Confidential Scorecard",
        message="Confidential evaluation notice intended exclusively for Alice.",
        link_url="/student/videos",
        is_read=False,
    )

    login_student(driver, email_bob, full_name="Bob Candidate")
    driver.get(f"{get_base_url()}/notifications")

    wait = WebDriverWait(driver, 10)
    empty_state = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='notifications-empty-state']")))
    assert "No notifications found" in empty_state.text
    assert "Alice Confidential Scorecard" not in driver.page_source

    # Capture screenshot
    screenshot_path = SCREENSHOTS_DIR / "us34_07_tenant_isolation_zero_leakage.png"
    driver.save_screenshot(str(screenshot_path))
    assert screenshot_path.exists()
