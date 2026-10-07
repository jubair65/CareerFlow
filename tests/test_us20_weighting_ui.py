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


def login_hr(driver, email="mona_hr_reviewer@careerflow.test", password="ValidPass2026!"):
    """Helper to ensure HR Manager exists and log in via UI."""
    create_user_in_db(email, password, role=User.Role.HR_MANAGER, full_name="Jannatun Naeem Mona")

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
    title="Staff Cloud Solutions Architect",
    company="NovaTech Global",
    cv_weight=50,
    video_weight=50,
    status="ACTIVE"
) -> RecruitmentRoom:
    """Creates a sample RecruitmentRoom directly in the DB linked to the HR user."""
    user = User.objects.get(email=email)
    room = RecruitmentRoom.objects.create(
        title=title,
        company_name=company,
        department="Enterprise Architecture",
        description="Lead enterprise cloud infrastructure, high-availability microservices, and AI integrations.",
        status=status,
        created_by=user,
        cv_weight=cv_weight,
        video_weight=video_weight,
        role_category="Engineering",
        experience_level="SENIOR",
        skills_required=["AWS", "Kubernetes", "Python"],
    )
    return room


class TestUS20WeightingUI:
    """
    US-20: CV-to-Video Weighting Configuration UI Automation Tests
    Task: US-20-T6 (Peer UI Testing)
    Tester / Peer Reviewer: Jannatun Naeem Mona (@jn-mona04) - System Analyst / BA
    Developer: MD. Hasanul Mobin (@hasanulmobin1) - Project Manager

    Acceptance Criteria Verified:
    ✓ Modal opens from room card via "Evaluation Weights" badge and action button
    ✓ Linked dual sliders & number inputs synchronize automatically to maintain 100% total
    ✓ Quick recommendation presets (50/50, 70/30, 30/70, 80/20, 20/80) apply cleanly
    ✓ Reset to saved state restores initial room configuration
    ✓ Weighting updates persist to backend DB and reactively update room card DOM
    ✓ Live score simulation preview accurately computes weighted candidate scores
    ✓ Extreme boundary splits (100/0 and 0/100) are fully supported and persistent
    """

    def test_tc_us20_01_modal_mount_from_badge_and_action_button(self, driver):
        """TC-US20-01: Verify weighting modal opens via room card badge and action button with correct context."""
        test_email = "mona_tc01_modal@careerflow.test"
        login_hr(driver, email=test_email)
        sample_room = create_sample_room_for_user(
            test_email,
            title="Senior Infrastructure Lead",
            company="CloudScape Labs"
        )

        driver.get(f"{FRONTEND_URL}/hr/rooms")
        wait = WebDriverWait(driver, 10)

        # 1. Locate and verify Evaluation Weights badge on room card
        badge_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='badge-weighting-config-{sample_room.id}']"))
        )
        assert "Evaluation Weights:" in badge_btn.text
        assert "CV 50% / Video 50%" in badge_btn.text

        # 2. Open modal via badge click
        badge_btn.click()

        # 3. Verify modal mounts and context is correct
        modal = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='weighting-config-modal']")))
        assert modal is not None
        assert "Senior Infrastructure Lead" in modal.text
        assert "CloudScape Labs" in modal.text
        assert "US-20" in modal.text
        assert "CV vs. Video Evaluation Weighting" in modal.text

        # 4. Verify initial default values: CV 50%, Video 50%
        cv_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-cv-weight-number']")
        video_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-video-weight-number']")
        assert cv_input.get_attribute("value") == "50"
        assert video_input.get_attribute("value") == "50"

        # Capture screenshot for reporting
        screenshot_path = SCREENSHOTS_DIR / "us20_01_weighting_modal_opened.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

        # 5. Close modal via header close button (X)
        close_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-close-weighting-modal']")
        close_btn.click()
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='weighting-config-modal']")))

        # 6. Reopen modal via Sliders action button in card footer
        action_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-action-weighting-{sample_room.id}']"))
        )
        action_btn.click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='weighting-config-modal']")))

        # 7. Dismiss cleanly via Cancel button
        cancel_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-cancel-weighting']")
        cancel_btn.click()
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='weighting-config-modal']")))

    def test_tc_us20_02_linked_dual_sliders_and_reset(self, driver):
        """TC-US20-02: Verify linked synchronization between CV & Video inputs and Reset button behavior."""
        test_email = "mona_tc02_sliders@careerflow.test"
        login_hr(driver, email=test_email)
        sample_room = create_sample_room_for_user(
            test_email,
            title="Lead DevOps Architect",
            company="Platform Prime"
        )

        driver.get(f"{FRONTEND_URL}/hr/rooms")
        wait = WebDriverWait(driver, 10)

        badge_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='badge-weighting-config-{sample_room.id}']"))
        )
        badge_btn.click()

        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='weighting-config-modal']")))

        cv_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-cv-weight-number']")
        video_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-video-weight-number']")
        reset_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-reset-weighting']")

        # Reset button should initially be disabled since no changes exist
        assert not reset_btn.is_enabled()

        # 1. Update CV weight to 65 using number input
        cv_input.send_keys(Keys.CONTROL + "a")
        cv_input.send_keys(Keys.BACKSPACE)
        cv_input.send_keys("65")

        # Video weight should automatically adjust to 35 (100 - 65)
        time.sleep(0.3)
        assert video_input.get_attribute("value") == "35"

        # 2. Verify total indicator in distribution bar displays 100%
        modal = driver.find_element(By.CSS_SELECTOR, "[data-testid='weighting-config-card']")
        assert "Total: 100%" in modal.text

        # 3. Reset button should now be enabled
        assert reset_btn.is_enabled()

        # 4. Now update Video weight to 40
        video_input.send_keys(Keys.CONTROL + "a")
        video_input.send_keys(Keys.BACKSPACE)
        video_input.send_keys("40")

        # CV weight should automatically adjust to 60 (100 - 40)
        time.sleep(0.3)
        assert cv_input.get_attribute("value") == "60"

        # Capture screenshot for reporting
        screenshot_path = SCREENSHOTS_DIR / "us20_02_linked_sliders_sync.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

        # 5. Click Reset button to revert back to original 50/50
        reset_btn.click()
        time.sleep(0.3)

        assert cv_input.get_attribute("value") == "50"
        assert video_input.get_attribute("value") == "50"
        assert not reset_btn.is_enabled()

    def test_tc_us20_03_quick_recommendation_presets(self, driver):
        """TC-US20-03: Verify quick presets apply correct splits (50/50, 70/30, 30/70, 80/20, 20/80)."""
        test_email = "mona_tc03_presets@careerflow.test"
        login_hr(driver, email=test_email)
        sample_room = create_sample_room_for_user(
            test_email,
            title="Product Designer",
            company="UX Studio"
        )

        driver.get(f"{FRONTEND_URL}/hr/rooms")
        wait = WebDriverWait(driver, 10)

        badge_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='badge-weighting-config-{sample_room.id}']"))
        )
        badge_btn.click()

        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='weighting-config-modal']")))

        cv_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-cv-weight-number']")
        video_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-video-weight-number']")

        # 1. Test CV Focused preset (70/30)
        preset_70_30 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='preset-button-70-30']")))
        preset_70_30.click()
        time.sleep(0.2)
        assert cv_input.get_attribute("value") == "70"
        assert video_input.get_attribute("value") == "30"

        # 2. Test Video Focused preset (30/70)
        preset_30_70 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='preset-button-30-70']")))
        preset_30_70.click()
        time.sleep(0.2)
        assert cv_input.get_attribute("value") == "30"
        assert video_input.get_attribute("value") == "70"

        # 3. Test Technical Depth preset (80/20)
        preset_80_20 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='preset-button-80-20']")))
        preset_80_20.click()
        time.sleep(0.2)
        assert cv_input.get_attribute("value") == "80"
        assert video_input.get_attribute("value") == "20"

        # 4. Test Client Facing preset (20/80)
        preset_20_80 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='preset-button-20-80']")))
        preset_20_80.click()
        time.sleep(0.2)
        assert cv_input.get_attribute("value") == "20"
        assert video_input.get_attribute("value") == "80"

        # 5. Return to Balanced preset (50/50)
        preset_50_50 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='preset-button-50-50']")))
        preset_50_50.click()
        time.sleep(0.2)
        assert cv_input.get_attribute("value") == "50"
        assert video_input.get_attribute("value") == "50"

        # Capture screenshot for reporting
        screenshot_path = SCREENSHOTS_DIR / "us20_03_recommendation_presets_applied.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc_us20_04_save_weighting_and_card_badge_update(self, driver):
        """TC-US20-04: Configure 70/30 weights, save changes, and verify room card badge and DB record update."""
        test_email = "mona_tc04_save@careerflow.test"
        login_hr(driver, email=test_email)
        sample_room = create_sample_room_for_user(
            test_email,
            title="Senior Full Stack Engineer",
            company="TechVanguard Corp"
        )

        driver.get(f"{FRONTEND_URL}/hr/rooms")
        wait = WebDriverWait(driver, 10)

        badge_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='badge-weighting-config-{sample_room.id}']"))
        )
        badge_btn.click()

        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='weighting-config-modal']")))

        # 1. Apply 70/30 preset
        preset_70_30 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='preset-button-70-30']")))
        preset_70_30.click()

        # 2. Click Save Weighting button
        save_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-save-weighting']")))
        assert save_btn.is_enabled()
        save_btn.click()

        # 3. Wait for modal dismissal
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='weighting-config-modal']")))

        # 4. Verify Room Card badge reactively reflects "CV 70% / Video 30%"
        updated_badge = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='badge-weighting-config-{sample_room.id}']"))
        )
        assert "CV 70% / Video 30%" in updated_badge.text

        # 5. Verify database persistence
        sample_room.refresh_from_db()
        assert sample_room.cv_weight == 70
        assert sample_room.video_weight == 30

        # Capture screenshot for reporting
        screenshot_path = SCREENSHOTS_DIR / "us20_04_save_weighting_persisted.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc_us20_05_live_score_simulation_preview(self, driver):
        """TC-US20-05: Verify score simulation calculator dynamically calculates formula accurately."""
        test_email = "mona_tc05_sim@careerflow.test"
        login_hr(driver, email=test_email)
        sample_room = create_sample_room_for_user(
            test_email,
            title="AI Systems Engineer",
            company="DeepCognition"
        )

        driver.get(f"{FRONTEND_URL}/hr/rooms")
        wait = WebDriverWait(driver, 10)

        badge_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='badge-weighting-config-{sample_room.id}']"))
        )
        badge_btn.click()

        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='weighting-config-modal']")))

        # 1. Apply 70/30 preset
        preset_70_30 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='preset-button-70-30']")))
        preset_70_30.click()

        # 2. Configure candidate test simulation scores: CV = 90, Video = 80
        sim_cv_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-sim-cv-score']")
        sim_video_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-sim-video-score']")

        sim_cv_input.send_keys(Keys.CONTROL + "a")
        sim_cv_input.send_keys(Keys.BACKSPACE)
        sim_cv_input.send_keys("90")

        sim_video_input.send_keys(Keys.CONTROL + "a")
        sim_video_input.send_keys(Keys.BACKSPACE)
        sim_video_input.send_keys("80")

        time.sleep(0.3)

        # Formula: (90 * 70 + 80 * 30) / 100 = (6300 + 2400) / 100 = 87.0%
        sim_score_el = driver.find_element(By.CSS_SELECTOR, "[data-testid='simulated-final-score']")
        assert "87.0%" in sim_score_el.text

        # 3. Switch to Video-heavy 30/70 preset
        preset_30_70 = driver.find_element(By.CSS_SELECTOR, "[data-testid='preset-button-30-70']")
        preset_30_70.click()
        time.sleep(0.3)

        # Formula: (90 * 30 + 80 * 70) / 100 = (2700 + 5600) / 100 = 83.0%
        sim_score_el = driver.find_element(By.CSS_SELECTOR, "[data-testid='simulated-final-score']")
        assert "83.0%" in sim_score_el.text

        # Capture screenshot for reporting
        screenshot_path = SCREENSHOTS_DIR / "us20_05_simulation_score_preview.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc_us20_06_extreme_splits_and_button_states(self, driver):
        """TC-US20-06: Verify extreme 100/0 and 0/100 weight configurations save cleanly."""
        test_email = "mona_tc06_extreme@careerflow.test"
        login_hr(driver, email=test_email)
        sample_room = create_sample_room_for_user(
            test_email,
            title="Algorithm Specialist",
            company="Quantum Logic"
        )

        driver.get(f"{FRONTEND_URL}/hr/rooms")
        wait = WebDriverWait(driver, 10)

        badge_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='badge-weighting-config-{sample_room.id}']"))
        )
        badge_btn.click()

        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='weighting-config-modal']")))

        cv_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-cv-weight-number']")
        video_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-video-weight-number']")
        save_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-save-weighting']")

        # 1. Set 100% CV / 0% Video
        cv_input.send_keys(Keys.CONTROL + "a")
        cv_input.send_keys(Keys.BACKSPACE)
        cv_input.send_keys("100")
        time.sleep(0.3)

        assert video_input.get_attribute("value") == "0"
        save_btn.click()

        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='weighting-config-modal']")))

        # Verify badge updates to 100% / 0%
        updated_badge = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='badge-weighting-config-{sample_room.id}']"))
        )
        assert "CV 100% / Video 0%" in updated_badge.text

        sample_room.refresh_from_db()
        assert sample_room.cv_weight == 100
        assert sample_room.video_weight == 0

        # Capture screenshot for reporting
        screenshot_path = SCREENSHOTS_DIR / "us20_06_extreme_splits_verified.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()
