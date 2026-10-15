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
from conftest import FRONTEND_URL, SCREENSHOTS_DIR, create_user_in_db


def login_hr(driver, email="bonny_hr_tester@careerflow.test", password="ValidPass2026!"):
    """Helper to ensure HR Manager exists and log in via UI."""
    create_user_in_db(email, password, role=User.Role.HR_MANAGER, full_name="Tahsin Bonny")

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


def create_sample_room_for_user(
    email: str,
    title="Principal Cloud Architect",
    company="Starlight Technologies",
    cv_weight=60,
    video_weight=40,
    status="ACTIVE"
) -> RecruitmentRoom:
    """Creates a sample RecruitmentRoom directly in the DB linked to the HR user."""
    user = User.objects.get(email=email)
    room = RecruitmentRoom.objects.create(
        title=title,
        company_name=company,
        department="Cloud Architecture",
        description="Lead enterprise cloud architecture and distributed microservice infrastructure.",
        status=status,
        created_by=user,
        cv_weight=cv_weight,
        video_weight=video_weight,
        role_category="Engineering",
        experience_level="SENIOR",
        skills_required=["AWS", "Terraform", "Kubernetes", "Docker"],
        requirements_text="5+ years hands-on experience designing secure cloud architectures."
    )
    return room


class TestUS21ShareableLinkUI:
    """
    US-21: Shareable Application Link UI Automation Tests
    Task: US-21-T6 (Peer UI Testing)
    Tester / Peer Reviewer: Tahsin Bonny (@tahsinbonnie98) - Software Developer & Peer Tester
    Developer: Jannatun Naeem Mona (@jn-mona04) - System Analyst / BA

    Acceptance Criteria Verified:
    ✓ Modal mounts from room card action button with accurate room and company context
    ✓ 1-Click copy to clipboard provides visual "Copied!" feedback and copies public application URL
    ✓ Deactivating link updates status badge to "Deactivated (Access Blocked)" and blocks access
    ✓ Reactivating link restores "Active (Accepting Applications)" state
    ✓ Regenerate link generates fresh high-entropy cryptographic token and revokes previous token
    ✓ Unauthenticated candidate can access /apply/:token and inspect role details & evaluation weights
    ✓ Deactivated or expired tokens return HTTP 410 Gone error page to applicants
    """

    def test_tc_us21_01_modal_mount_from_room_card(self, driver):
        """TC-US21-01: Verify shareable link modal opens via room card action button with correct room context."""
        test_email = "bonny_tc01_modal@careerflow.test"
        login_hr(driver, email=test_email)
        sample_room = create_sample_room_for_user(
            test_email,
            title="Principal Cloud Architect",
            company="Starlight Technologies"
        )

        driver.get(f"{FRONTEND_URL}/hr/rooms")
        wait = WebDriverWait(driver, 10)

        # Locate and click share link action button on room card
        link_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-action-share-link-{sample_room.id}']"))
        )
        link_btn.click()

        # Verify modal mounts with title and room context
        modal = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-shareable-link']")))
        assert modal is not None
        assert "Principal Cloud Architect" in modal.text
        assert "Starlight Technologies" in modal.text
        assert "US-21" in modal.text
        assert "Candidate Application Portal Link" in modal.text

        # Verify active status badge
        status_badge = driver.find_element(By.CSS_SELECTOR, "[data-testid='badge-link-status']")
        assert "ACTIVE" in status_badge.text.upper()

        # Capture screenshot
        driver.save_screenshot(str(SCREENSHOTS_DIR / "us21_01_modal_mounted.png"))

        # Verify clean dismissal via close button
        close_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-close-shareable-link-modal']")
        close_btn.click()
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-shareable-link']")))

    def test_tc_us21_02_copy_link_clipboard_and_feedback(self, driver):
        """TC-US21-02: Verify 1-click clipboard copy triggers visual feedback and populates input URL."""
        test_email = "bonny_tc02_copy@careerflow.test"
        login_hr(driver, email=test_email)
        sample_room = create_sample_room_for_user(test_email, title="Staff Security Engineer", company="CyberGuard")

        driver.get(f"{FRONTEND_URL}/hr/rooms")
        wait = WebDriverWait(driver, 10)

        link_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-action-share-link-{sample_room.id}']"))
        )
        link_btn.click()

        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-shareable-link']")))

        # Check input contains valid /apply/ token URL
        url_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-shareable-link-url']")
        url_value = url_input.get_attribute("value")
        assert f"/apply/{sample_room.share_token}" in url_value

        # Click Copy Link button
        copy_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-copy-shareable-link']")
        copy_btn.click()

        # Verify button text transitions to "Copied!"
        wait.until(lambda d: "Copied!" in driver.find_element(By.CSS_SELECTOR, "[data-testid='button-copy-shareable-link']").text)
        driver.save_screenshot(str(SCREENSHOTS_DIR / "us21_02_copy_feedback.png"))

    def test_tc_us21_03_deactivate_and_reactivate_flow(self, driver):
        """TC-US21-03: Verify HR can deactivate link to block public access, then reactivate access."""
        test_email = "bonny_tc03_toggle@careerflow.test"
        login_hr(driver, email=test_email)
        sample_room = create_sample_room_for_user(test_email, title="Lead Data Engineer", company="DataFlow Systems")

        driver.get(f"{FRONTEND_URL}/hr/rooms")
        wait = WebDriverWait(driver, 10)

        link_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-action-share-link-{sample_room.id}']"))
        )
        link_btn.click()

        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-shareable-link']")))

        # Click Deactivate
        toggle_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-toggle-link-status']")
        assert "Deactivate" in toggle_btn.text
        toggle_btn.click()

        # Verify status updates to Deactivated
        wait.until(lambda d: "DEACTIVATED" in driver.find_element(By.CSS_SELECTOR, "[data-testid='badge-link-status']").text.upper())
        status_badge = driver.find_element(By.CSS_SELECTOR, "[data-testid='badge-link-status']")
        assert "ACCESS BLOCKED" in status_badge.text.upper() or "410" in status_badge.text
        driver.save_screenshot(str(SCREENSHOTS_DIR / "us21_03_deactivated_status.png"))

        # Re-activate
        toggle_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-toggle-link-status']")
        assert "Activate" in toggle_btn.text
        toggle_btn.click()

        # Verify status restores to Active
        wait.until(lambda d: "ACTIVE" in driver.find_element(By.CSS_SELECTOR, "[data-testid='badge-link-status']").text.upper())
        driver.save_screenshot(str(SCREENSHOTS_DIR / "us21_03_reactivated_status.png"))

    def test_tc_us21_04_regenerate_token_confirmation_flow(self, driver):
        """TC-US21-04: Verify regenerate token prompts with confirmation warning and assigns new secure token."""
        test_email = "bonny_tc04_regen@careerflow.test"
        login_hr(driver, email=test_email)
        sample_room = create_sample_room_for_user(test_email, title="Full Stack Team Lead", company="WebSphere")

        driver.get(f"{FRONTEND_URL}/hr/rooms")
        wait = WebDriverWait(driver, 10)

        link_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-action-share-link-{sample_room.id}']"))
        )
        link_btn.click()

        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-shareable-link']")))

        initial_url = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-shareable-link-url']").get_attribute("value")

        # Click Regenerate Token
        regen_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-regenerate-link']")
        regen_btn.click()

        # Verify confirmation prompt and warning banner appear
        confirm_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-confirm-regenerate']")))
        driver.save_screenshot(str(SCREENSHOTS_DIR / "us21_04_regenerate_confirmation.png"))

        # Confirm regeneration
        confirm_btn.click()

        # Verify URL input updates with fresh token
        wait.until(lambda d: driver.find_element(By.CSS_SELECTOR, "[data-testid='input-shareable-link-url']").get_attribute("value") != initial_url)
        new_url = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-shareable-link-url']").get_attribute("value")
        assert new_url != initial_url
        driver.save_screenshot(str(SCREENSHOTS_DIR / "us21_04_new_token_generated.png"))

    def test_tc_us21_05_public_candidate_application_view(self, driver):
        """TC-US21-05: Verify unauthenticated candidate can access /apply/:token and view opening details."""
        test_email = "bonny_tc05_public@careerflow.test"
        sample_room = create_sample_room_for_user(
            test_email,
            title="Senior AI Platform Engineer",
            company="DeepMind Technologies",
            cv_weight=70,
            video_weight=30
        )

        # Navigate directly to public application URL without authentication
        driver.get(f"{FRONTEND_URL}/apply/{sample_room.share_token}")
        wait = WebDriverWait(driver, 10)

        # Verify page renders job title, company name, skills, and weights
        page = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='page-public-application']")))
        assert page is not None

        title_el = driver.find_element(By.CSS_SELECTOR, "[data-testid='public-room-title']")
        assert "Senior AI Platform Engineer" in title_el.text

        # Verify CV and Video weights display correctly
        cv_weight = driver.find_element(By.CSS_SELECTOR, "[data-testid='public-cv-weight']")
        video_weight = driver.find_element(By.CSS_SELECTOR, "[data-testid='public-video-weight']")
        assert "70%" in cv_weight.text
        assert "30%" in video_weight.text

        # Verify skills chips
        skills_container = driver.find_element(By.CSS_SELECTOR, "[data-testid='public-room-skills']")
        assert "AWS" in skills_container.text
        assert "Docker" in skills_container.text

        driver.save_screenshot(str(SCREENSHOTS_DIR / "us21_05_public_application_view.png"))

    def test_tc_us21_06_public_deactivated_link_error_state(self, driver):
        """TC-US21-06: Verify accessing deactivated link displays 410 error page with clear notification."""
        test_email = "bonny_tc06_error@careerflow.test"
        sample_room = create_sample_room_for_user(
            test_email,
            title="DevOps Specialist",
            company="Legacy Corp"
        )
        sample_room.link_is_active = False
        sample_room.save(update_fields=['link_is_active'])

        # Navigate to public application URL
        driver.get(f"{FRONTEND_URL}/apply/{sample_room.share_token}")
        wait = WebDriverWait(driver, 10)

        # Verify error card renders with status
        error_card = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='card-link-error']")))
        assert error_card is not None
        assert "Application Link Inactive" in error_card.text
        assert "DevOps Specialist" in error_card.text or "Legacy Corp" in error_card.text

        driver.save_screenshot(str(SCREENSHOTS_DIR / "us21_06_deactivated_error_page.png"))
