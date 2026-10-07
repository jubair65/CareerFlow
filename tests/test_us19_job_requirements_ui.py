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
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

from apps.authentication.models import User
from apps.recruitment.models import RecruitmentRoom
from conftest import FRONTEND_URL, SCREENSHOTS_DIR, create_user_in_db


def login_hr(driver, email="jubair_hr_reviewer@careerflow.test", password="ValidPass2026!"):
    """Helper to ensure HR Manager exists and log in via UI."""
    create_user_in_db(email, password, role=User.Role.HR_MANAGER, full_name="MD. Jubair Bin Hasan")

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
    title="Staff Software Engineer",
    company="TechNova Solutions",
    role_category="Engineering",
    experience_level="MID",
    skills=None,
    status="ACTIVE"
) -> RecruitmentRoom:
    """Creates a sample RecruitmentRoom directly in the DB linked to the HR user."""
    user = User.objects.get(email=email)
    room = RecruitmentRoom.objects.create(
        title=title,
        company_name=company,
        department="Platform Engineering",
        description="Scalable cloud architectures, event-driven pipelines, and high-load web systems.",
        status=status,
        created_by=user,
        cv_weight=50,
        video_weight=50,
        role_category=role_category,
        experience_level=experience_level,
        skills_required=skills if skills is not None else [],
    )
    return room


class TestUS19JobRequirementsUI:
    """
    US-19: Job Role & Required Skills UI Automation Tests
    Task: US-19-T6 (Peer UI Testing)
    Tester / Peer Reviewer: MD. Jubair Bin Hasan (Peer Tester & Reviewer)
    Developer: Nafisa Tabassum Maria (@Maria-07-222)

    Acceptance Criteria Verified:
    ✓ Modal opens from room card via [Configure] button with correct room context
    ✓ Default role category & experience level selectors mount correctly
    ✓ Interactive skill tag validation (empty string, <2 chars, duplicates, min 1 required)
    ✓ Quick preset skill suggestions and custom Enter-key skill tag additions
    ✓ Full requirements submission persists to backend and updates room card DOM chips
    ✓ Skill tag removal persists changes reactively
    """

    def test_tc_us19_01_requirements_modal_mount_and_context(self, driver):
        """TC-US19-01: Verify requirements modal opens from room card, renders correct room context and closes cleanly."""
        test_email = "jubair_tc01_modal@careerflow.test"
        login_hr(driver, email=test_email)
        sample_room = create_sample_room_for_user(
            test_email,
            title="Senior AI Platform Engineer",
            company="DeepMind Partner Lab"
        )

        driver.get(f"{FRONTEND_URL}/hr/rooms")
        wait = WebDriverWait(driver, 10)

        # 1. Locate and click Configure button on room card
        config_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-configure-requirements-{sample_room.id}']"))
        )
        assert "Configure" in config_btn.text
        config_btn.click()

        # 2. Wait for requirements modal to mount
        modal = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-job-requirements']")))
        assert modal is not None

        # 3. Verify room title and company in modal header
        assert "Senior AI Platform Engineer" in modal.text
        assert "DeepMind Partner Lab" in modal.text
        assert "US-19" in modal.text

        # 4. Verify default role category and experience level
        role_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-role-category']")
        assert role_input.get_attribute("value") == "Engineering"

        exp_select = Select(driver.find_element(By.CSS_SELECTOR, "[data-testid='select-experience-level']"))
        assert exp_select.first_selected_option.get_attribute("value") == "MID"

        # Capture screenshot for reporting
        screenshot_path = SCREENSHOTS_DIR / "us19_01_requirements_modal_opened.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

        # 5. Close modal cleanly via close button (X)
        close_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-close-requirements-modal']")
        close_btn.click()
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-job-requirements']")))

    def test_tc_us19_02_skill_validation_rules(self, driver):
        """TC-US19-02: Verify inline validation for empty skill, short length (<2), duplicates, and empty submit."""
        test_email = "jubair_tc02_val@careerflow.test"
        login_hr(driver, email=test_email)
        sample_room = create_sample_room_for_user(
            test_email,
            title="DevOps Lead",
            company="CloudScale Corp"
        )

        driver.get(f"{FRONTEND_URL}/hr/rooms")
        wait = WebDriverWait(driver, 10)

        config_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-configure-requirements-{sample_room.id}']"))
        )
        config_btn.click()

        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-job-requirements']")))

        skill_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-skill-tag']")
        add_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-add-skill']")
        save_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-save-requirements']")

        # 1. Click Add Skill with empty input -> assert validation error
        add_btn.click()
        err_banner = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='error-skills-validation']")))
        assert "Please type a skill name before adding" in err_banner.text

        # 2. Enter single character "A" -> assert minimum length validation (< 2 characters)
        skill_input.send_keys("A")
        add_btn.click()
        err_banner = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='error-skills-validation']")))
        assert "must be at least 2 characters long" in err_banner.text

        # 3. Add valid skill "Python"
        skill_input.clear()
        skill_input.send_keys("Python")
        add_btn.click()

        # Verify "Python" pill mounts inside container
        tags_container = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='container-skill-tags']")))
        assert "Python" in tags_container.text

        # 4. Try adding case-insensitive duplicate "python"
        skill_input.clear()
        skill_input.send_keys("python")
        add_btn.click()

        err_banner = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='error-skills-validation']")))
        assert 'Skill "python" is already added' in err_banner.text

        # 5. Remove "Python" tag so the skills list is completely empty
        remove_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-remove-skill-python']")
        remove_btn.click()
        time.sleep(0.3)

        # 6. Try saving with 0 skills defined -> assert submission block validation
        save_btn.click()
        err_banner = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='error-skills-validation']")))
        assert "At least one required skill must be defined" in err_banner.text

        # Capture screenshot for reporting
        screenshot_path = SCREENSHOTS_DIR / "us19_02_skill_validation_empty_and_duplicate.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc_us19_03_quick_preset_suggestions_and_enter_key(self, driver):
        """TC-US19-03: Verify quick preset buttons add tags and custom input responds to Enter key."""
        test_email = "jubair_tc03_presets@careerflow.test"
        login_hr(driver, email=test_email)
        sample_room = create_sample_room_for_user(
            test_email,
            title="Backend Architect",
            company="Nexus Systems"
        )

        driver.get(f"{FRONTEND_URL}/hr/rooms")
        wait = WebDriverWait(driver, 10)

        config_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-configure-requirements-{sample_room.id}']"))
        )
        config_btn.click()

        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-job-requirements']")))

        # 1. Click Quick Suggestion button for "Docker"
        docker_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Docker')]")))
        docker_btn.click()

        # 2. Click Quick Suggestion button for "PostgreSQL"
        postgres_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'PostgreSQL')]")))
        postgres_btn.click()

        # 3. Add custom skill via Enter key in the text field
        skill_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-skill-tag']")
        skill_input.send_keys("FastAPI")
        skill_input.send_keys(Keys.ENTER)

        # 4. Verify all 3 skills are present in tags container
        tags_container = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='container-skill-tags']")))
        assert "Docker" in tags_container.text
        assert "PostgreSQL" in tags_container.text
        assert "FastAPI" in tags_container.text

        # 5. Verify the skill count indicator displays "(3)"
        modal = driver.find_element(By.CSS_SELECTOR, "[data-testid='modal-job-requirements']")
        assert "Required Skills & Tech Stack (3)" in modal.text

        # Capture screenshot for reporting
        screenshot_path = SCREENSHOTS_DIR / "us19_03_skills_tag_builder_and_quick_presets.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc_us19_04_save_requirements_and_room_card_updates(self, driver):
        """TC-US19-04: Configure role details, seniority, text & skills, save and verify room card renders new chips in DOM."""
        test_email = "jubair_tc04_save@careerflow.test"
        login_hr(driver, email=test_email)
        sample_room = create_sample_room_for_user(
            test_email,
            title="Lead Full Stack Engineer",
            company="Global Financial Corp"
        )

        driver.get(f"{FRONTEND_URL}/hr/rooms")
        wait = WebDriverWait(driver, 10)

        config_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-configure-requirements-{sample_room.id}']"))
        )
        config_btn.click()

        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-job-requirements']")))

        # Wait for initial load synchronization to finish
        time.sleep(0.6)

        # 1. Update Role Category
        role_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-role-category']")
        role_input.send_keys(Keys.CONTROL + "a")
        role_input.send_keys(Keys.BACKSPACE)
        role_input.send_keys("Full Stack Engineering")

        # 2. Select Seniority Level: SENIOR
        exp_select = Select(driver.find_element(By.CSS_SELECTOR, "[data-testid='select-experience-level']"))
        exp_select.select_by_value("SENIOR")

        # 3. Add Skills: React, TypeScript, Python
        skill_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-skill-tag']")
        add_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-add-skill']")

        for skill in ["React", "TypeScript", "Python"]:
            skill_input.clear()
            skill_input.send_keys(skill)
            add_btn.click()
            time.sleep(0.15)

        # 4. Fill Detailed Requirements Text
        req_text = driver.find_element(By.CSS_SELECTOR, "[data-testid='textarea-requirements-text']")
        req_text.clear()
        req_text.send_keys("5+ years building distributed React and Python web apps. Solid understanding of CI/CD and DB optimization.")

        # 5. Submit form
        save_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-save-requirements']")
        save_btn.click()

        # 6. Wait for modal dismissal
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-job-requirements']")))

        # 7. Assert Room Card reflects the updated role category, experience level badge, and skills chips
        card = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='card-room-{sample_room.id}']")))
        assert "Full Stack Engineering" in card.text
        assert "SENIOR" in card.text

        skills_list = driver.find_element(By.CSS_SELECTOR, f"[data-testid='room-skills-list-{sample_room.id}']")
        assert "React" in skills_list.text
        assert "TypeScript" in skills_list.text
        assert "Python" in skills_list.text

        # Capture screenshot for reporting
        screenshot_path = SCREENSHOTS_DIR / "us19_04_save_requirements_success_and_room_card_chips.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc_us19_05_skill_tag_removal_and_persistence(self, driver):
        """TC-US19-05: Re-open modal, remove a skill tag, save, and verify room card reactively drops the removed chip."""
        test_email = "jubair_tc05_removal@careerflow.test"
        login_hr(driver, email=test_email)
        sample_room = create_sample_room_for_user(
            test_email,
            title="Data Platform Engineer",
            company="Analytics Cloud",
            role_category="Data Engineering",
            experience_level="MID",
            skills=["Python", "Docker", "PostgreSQL"]
        )

        driver.get(f"{FRONTEND_URL}/hr/rooms")
        wait = WebDriverWait(driver, 10)

        # Initial check: room card has Python, Docker, PostgreSQL
        skills_list = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='room-skills-list-{sample_room.id}']"))
        )
        assert "Python" in skills_list.text
        assert "Docker" in skills_list.text
        assert "PostgreSQL" in skills_list.text

        # 1. Open Configure modal
        config_btn = driver.find_element(By.CSS_SELECTOR, f"[data-testid='button-configure-requirements-{sample_room.id}']")
        config_btn.click()

        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-job-requirements']")))

        # Wait for skills to populate from API
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='button-remove-skill-docker']")))

        # 2. Remove "Docker" skill
        remove_docker = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-remove-skill-docker']")
        remove_docker.click()
        time.sleep(0.3)

        # Verify "Docker" is removed from the active tags container
        tags_container = driver.find_element(By.CSS_SELECTOR, "[data-testid='container-skill-tags']")
        assert "Docker" not in tags_container.text
        assert "Python" in tags_container.text
        assert "PostgreSQL" in tags_container.text

        # 3. Save updated requirements
        save_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-save-requirements']")
        save_btn.click()

        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-job-requirements']")))

        # 4. Verify room card no longer contains Docker, but retains Python and PostgreSQL
        updated_skills_list = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='room-skills-list-{sample_room.id}']"))
        )
        assert "Docker" not in updated_skills_list.text
        assert "Python" in updated_skills_list.text
        assert "PostgreSQL" in updated_skills_list.text

        # Capture screenshot for reporting
        screenshot_path = SCREENSHOTS_DIR / "us19_05_remove_skill_tag_and_modal_dismissal.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()
