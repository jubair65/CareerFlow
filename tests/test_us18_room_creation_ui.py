import os
import sys
import time
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
from apps.recruitment.models import RecruitmentRoom
from conftest import FRONTEND_URL, create_user_in_db


def login_hr(driver, email="maria_hr_tester@careerflow.test", password="ValidPass2026!"):
    """Helper to register/ensure HR Manager exists and log in via UI."""
    create_user_in_db(email, password, role=User.Role.HR_MANAGER, full_name="Mira Chowdhury")

    driver.get(f"{FRONTEND_URL}/login")
    wait = WebDriverWait(driver, 10)
    email_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-login-email']")))
    pass_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-login-password']")
    submit_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-login']")

    email_input.clear()
    email_input.send_keys(email)
    pass_input.clear()
    pass_input.send_keys(password)
    submit_btn.click()

    wait.until(EC.url_contains("/hr/dashboard"))


def create_sample_room_for_user(email: str, title="Backend Engineer", company="CareerFlow Partner", status="ACTIVE") -> RecruitmentRoom:
    """Creates a sample RecruitmentRoom directly in DB linked to the HR user."""
    user = User.objects.get(email=email)
    room = RecruitmentRoom.objects.create(
        title=title,
        company_name=company,
        department="Platform Engineering",
        description="Scalable microservices and cloud deployment.",
        status=status,
        created_by=user,
        cv_weight=50,
        video_weight=50,
    )
    return room


class TestUS18RoomCreationUI:
    """
    US-18: Create Recruitment Room UI Automation Tests
    Task: US-18-T6 (Peer UI Testing)
    Tester / Peer Reviewer: Nafisa Tabassum Maria (System Architect)
    Developer: MD. Jubair Bin Hasan

    Acceptance Criteria Verified:
    ✓ Sidebar navigation opens /hr/rooms from HR workspace
    ✓ Room creation modal opens and enforces form validation (empty/short title, company name)
    ✓ Valid Room creation succeeds, modal dismisses, and new card mounts in DOM
    ✓ Room status toggle transitions between ACTIVE and PAUSED states
    ✓ Copy Shareable Link triggers clipboard copy with feedback
    """

    def test_tc_us18_01_create_room_modal_validation(self, driver):
        """TC-US18-01: Verify Sidebar Navigation to /hr/rooms and Room Creation Modal input validation."""
        test_email = "maria_modal_val@careerflow.test"
        login_hr(driver, email=test_email)
        wait = WebDriverWait(driver, 10)

        # 1. Verify sidebar navigation to /hr/rooms (BUG-US18-01 resolution check)
        nav_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='nav-recruitment-rooms']")))
        nav_btn.click()
        wait.until(EC.url_contains("/hr/rooms"))
        assert "/hr/rooms" in driver.current_url

        # 2. Open Create Room modal
        create_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-create-room-page']")))
        create_btn.click()

        modal = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-create-room']")))
        assert modal is not None

        # 3. Submit empty title -> assert validation error
        title_in = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-room-title']")
        title_in.clear()
        submit_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-submit-create-room']")
        submit_btn.click()

        err_title = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='error-room-title']")))
        assert "Job title is required." in err_title.text

        # 4. Enter short title (< 3 chars) -> assert length validation error
        title_in.send_keys("ab")
        submit_btn.click()
        err_title_short = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='error-room-title']")))
        assert "at least 3 characters" in err_title_short.text

        # 5. Clear company name -> assert company validation error
        comp_in = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-room-company']")
        comp_in.send_keys(Keys.COMMAND + "a")
        comp_in.send_keys(Keys.BACKSPACE)
        comp_in.send_keys(Keys.CONTROL + "a")
        comp_in.send_keys(Keys.BACKSPACE)

        title_in.clear()
        title_in.send_keys("Frontend Engineer")
        submit_btn.click()

        err_comp = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='error-room-company']")))
        assert "Company name is required." in err_comp.text

        # 6. Cancel button cleanly dismisses modal
        cancel_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-cancel-create-room']")
        cancel_btn.click()
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-create-room']")))

    def test_tc_us18_02_create_room_success(self, driver):
        """TC-US18-02: Successfully create a Room, verify modal dismissal, and assert card renders in DOM."""
        test_email = "maria_create_success@careerflow.test"
        login_hr(driver, email=test_email)

        driver.get(f"{FRONTEND_URL}/hr/rooms")
        wait = WebDriverWait(driver, 10)

        # 1. Open Create Room modal
        create_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-create-room-page']")))
        create_btn.click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-create-room']")))

        # 2. Fill form with valid room data
        title_in = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-room-title']")
        title_in.clear()
        title_in.send_keys("Lead Full Stack Engineer")

        comp_in = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-room-company']")
        comp_in.send_keys(Keys.COMMAND + "a")
        comp_in.send_keys(Keys.BACKSPACE)
        comp_in.send_keys(Keys.CONTROL + "a")
        comp_in.send_keys(Keys.BACKSPACE)
        comp_in.send_keys("Google Cloud")

        dept_in = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-room-department']")
        dept_in.send_keys("Distributed Systems")

        desc_in = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-room-description']")
        desc_in.send_keys("Building resilient cloud infrastructure and developer tooling.")

        # 3. Submit
        submit_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-submit-create-room']")
        submit_btn.click()

        # 4. Wait for modal dismissal
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-create-room']")))

        # 5. Assert card rendered in DOM
        card_heading = wait.until(EC.visibility_of_element_located((By.XPATH, "//*[contains(text(), 'Lead Full Stack Engineer')]")))
        assert card_heading is not None

        # Verify company and status badge
        assert "Google Cloud" in driver.page_source
        assert "ACTIVE" in driver.page_source

    def test_tc_us18_03_room_list_status_toggle(self, driver):
        """TC-US18-03: Toggle Room status between ACTIVE and PAUSED on the rooms list."""
        test_email = "maria_toggle_status@careerflow.test"
        login_hr(driver, email=test_email)
        sample_room = create_sample_room_for_user(test_email, title="DevOps Specialist", status="ACTIVE")

        driver.get(f"{FRONTEND_URL}/hr/rooms")
        wait = WebDriverWait(driver, 10)

        # 1. Verify initial ACTIVE status
        status_badge = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='room-status-{sample_room.id}']")))
        assert status_badge.text == "ACTIVE"

        # 2. Click toggle button to pause room
        toggle_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-toggle-status-{sample_room.id}']")))
        toggle_btn.click()

        # 3. Verify status transitioned to PAUSED
        wait.until(lambda d: d.find_element(By.CSS_SELECTOR, f"[data-testid='room-status-{sample_room.id}']").text == "PAUSED")
        status_badge = driver.find_element(By.CSS_SELECTOR, f"[data-testid='room-status-{sample_room.id}']")
        assert status_badge.text == "PAUSED"

        # 4. Click toggle button again to re-activate room
        toggle_btn.click()
        wait.until(lambda d: d.find_element(By.CSS_SELECTOR, f"[data-testid='room-status-{sample_room.id}']").text == "ACTIVE")
        status_badge = driver.find_element(By.CSS_SELECTOR, f"[data-testid='room-status-{sample_room.id}']")
        assert status_badge.text == "ACTIVE"

    def test_tc_us18_04_copy_shareable_link(self, driver):
        """TC-US18-04: Click Copy Link button on room card and verify copy state feedback."""
        test_email = "maria_copy_link@careerflow.test"
        login_hr(driver, email=test_email)
        sample_room = create_sample_room_for_user(test_email, title="Mobile Architect", status="ACTIVE")

        driver.get(f"{FRONTEND_URL}/hr/rooms")
        wait = WebDriverWait(driver, 10)

        # 1. Locate Copy Link button
        copy_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-copy-room-link-{sample_room.id}']")))
        assert "Copy Link" in copy_btn.text

        # 2. Click Copy Link
        copy_btn.click()

        # 3. Assert button transitioned to 'Copied!' state
        wait.until(lambda d: "Copied" in d.find_element(By.CSS_SELECTOR, f"[data-testid='button-copy-room-link-{sample_room.id}']").text)
        assert "Copied" in copy_btn.text
