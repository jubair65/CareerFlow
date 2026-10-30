"""
US-42: Candidate Profile & Career Objective Management UI Test Suite (US-42-T6).
User Story: US-42 — Candidate Profile & Career Objective Management
Sprint: Sprint 7 — Final Platform Maturity & Release
Lead Developer: MD. Jubair Bin Hasan (@jubair65)
Dedicated Peer UI Tester & System Architect: Nafisa Tabassum Maria (@Maria-07-222)
Target Branch: feat/us-42-candidate-profile -> develop

Acceptance Criteria Verified:
✓ AC-1: User can view and update their profile details (phone, LinkedIn/GitHub URLs, target role, bio).
✓ AC-2: Profile data is validated (valid URLs, proper international phone number formatting, auto-prefixing).
✓ AC-3: Updated profile information is stored securely in the database.
✓ AC-4: Candidate profile information is automatically reflected in room applications (US-42-T5).
✓ AC-5: Users can only edit their own profile (strict user isolation).
✓ AC-6: Profile updates load and save with clear feedback (success toasts, inline error markers, and reset capabilities).
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

from apps.authentication.models import User, CandidateProfile
from apps.recruitment.models import RecruitmentRoom
from conftest import FRONTEND_URL, SCREENSHOTS_DIR, create_user_in_db


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


def login_candidate(driver, email: str, password: str = "ValidPass2026!", full_name: str = "Candidate User"):
    """Helper to authenticate a student / candidate via the UI login page."""
    user = User.objects.filter(email__iexact=email).first()
    if not user:
        user = create_user_in_db(email, password, role=User.Role.STUDENT, full_name=full_name)

    driver.get(f"{FRONTEND_URL}/login")
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
    return user


class TestUS42CandidateProfileUI:
    """
    Automated Selenium UI Test Suite for US-42 Candidate Profile Management.
    Executed by Nafisa Tabassum Maria (@Maria-07-222).
    """

    def test_tc42_01_profile_loading_avatar_and_identity_display(self, driver):
        """
        Test Case 1: Profile Loading & Avatar Display
        Verifies navigation from sidebar and header avatar, initial fallback initials badge,
        email display, workspace role, and loading states. (AC-1, AC-6)
        """
        uid = uuid.uuid4().hex[:6]
        email = f"candidate_load_{uid}@careerflow.test"
        login_candidate(driver, email=email, full_name="Samantha Ray")

        wait = WebDriverWait(driver, 10)

        # Navigate via sidebar Profile button
        profile_nav = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='nav-profile']")))
        profile_nav.click()

        wait.until(EC.url_contains("/profile"))
        assert "/profile" in driver.current_url

        # Wait for profile container to finish loading
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='profile-container']")))

        # Verify fallback initials badge (SR for Samantha Ray)
        initials_badge = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='profile-avatar-fallback']")))
        assert "SR" in initials_badge.text

        # Verify email display
        email_display = driver.find_element(By.CSS_SELECTOR, "[data-testid='profile-display-email']")
        assert email in email_display.text

        # Verify workspace role
        role_element = driver.find_element(By.XPATH, "//*[contains(text(), 'Workspace Role:')]/..")
        assert "Student" in role_element.text or "student" in role_element.text.lower()

        # Verify default display name
        display_name = driver.find_element(By.CSS_SELECTOR, "[data-testid='profile-display-name']")
        assert "Samantha Ray" in display_name.text

        # Capture verification screenshot
        screenshot_path = SCREENSHOTS_DIR / "us42_01_profile_loading_and_identity.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc42_02_successful_profile_update_and_persistence(self, driver):
        """
        Test Case 2: Successful Profile Update
        Updates all fields (Full Name, Phone, Target Role, LinkedIn URL, GitHub URL, Bio),
        saves changes, checks success toast, and refreshes to verify DB persistence. (AC-1, AC-3, AC-6)
        """
        uid = uuid.uuid4().hex[:6]
        email = f"candidate_update_{uid}@careerflow.test"
        login_candidate(driver, email=email, full_name="Alex Original")

        wait = WebDriverWait(driver, 10)
        driver.get(f"{FRONTEND_URL}/profile")
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='profile-container']")))

        fullname_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-profile-fullname']")
        phone_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-profile-phone']")
        role_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-profile-target-role']")
        linkedin_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-profile-linkedin']")
        github_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-profile-github']")
        bio_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-profile-bio']")
        save_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-profile-save']")

        set_react_input(driver, fullname_input, "Alex Johnson")
        set_react_input(driver, phone_input, "+1 (555) 234-5678")
        set_react_input(driver, role_input, "Full Stack Software Engineer")
        set_react_input(driver, linkedin_input, "https://linkedin.com/in/alex-johnson")
        set_react_input(driver, github_input, "https://github.com/alex-johnson")
        set_react_input(driver, bio_input, "Passionate engineer with experience in React and Django.")

        save_btn.click()

        # Verify success toast notification
        toast = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='toast-message']")))
        assert "Profile updated successfully!" in toast.text

        screenshot_path1 = SCREENSHOTS_DIR / "us42_02_successful_profile_update.png"
        driver.save_screenshot(str(screenshot_path1))

        # Refresh page to verify database persistence
        time.sleep(1)
        driver.refresh()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='profile-container']")))

        # Re-fetch form inputs and assert values
        fn_val = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-profile-fullname']").get_attribute("value")
        phone_val = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-profile-phone']").get_attribute("value")
        role_val = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-profile-target-role']").get_attribute("value")
        linkedin_val = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-profile-linkedin']").get_attribute("value")
        github_val = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-profile-github']").get_attribute("value")
        bio_val = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-profile-bio']").get_attribute("value")

        assert fn_val == "Alex Johnson"
        assert phone_val == "+1 (555) 234-5678"
        assert role_val == "Full Stack Software Engineer"
        assert "linkedin.com/in/alex-johnson" in linkedin_val
        assert "github.com/alex-johnson" in github_val
        assert bio_val == "Passionate engineer with experience in React and Django."

        # Verify identity card shows updated name and initials
        display_name = driver.find_element(By.CSS_SELECTOR, "[data-testid='profile-display-name']").text
        assert display_name == "Alex Johnson"
        initials = driver.find_element(By.CSS_SELECTOR, "[data-testid='profile-avatar-fallback']").text
        assert initials == "AJ"

        screenshot_path2 = SCREENSHOTS_DIR / "us42_02b_profile_persistence_after_refresh.png"
        driver.save_screenshot(str(screenshot_path2))

    def test_tc42_03_phone_number_validation_errors(self, driver):
        """
        Test Case 3: Phone Number Validation Errors
        Enters invalid phone numbers (too short or illegal characters), clicks Save Changes,
        verifies inline error message and red border formatting. (AC-2, AC-6)
        """
        uid = uuid.uuid4().hex[:6]
        email = f"candidate_phone_{uid}@careerflow.test"
        login_candidate(driver, email=email, full_name="Phone Tester")

        wait = WebDriverWait(driver, 10)
        driver.get(f"{FRONTEND_URL}/profile")
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='profile-container']")))

        phone_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-profile-phone']")
        save_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-profile-save']")

        # Enter invalid short phone
        set_react_input(driver, phone_input, "123")
        save_btn.click()

        # Verify inline error message
        error_msg = wait.until(
            EC.visibility_of_element_located((By.XPATH, "//*[contains(., 'Enter a valid phone number with 7 to 15 digits')]"))
        )
        assert error_msg.is_displayed()

        # Verify input border styling indicates error
        input_class = phone_input.get_attribute("className")
        assert "border-[#a33d35]" in input_class or "bg-[#fff5f5]" in input_class

        screenshot_path = SCREENSHOTS_DIR / "us42_03_phone_validation_error.png"
        driver.save_screenshot(str(screenshot_path))

    def test_tc42_04_social_links_domain_validation(self, driver):
        """
        Test Case 4: Social Link Domain Validation
        Enters non-LinkedIn URL in LinkedIn field and non-GitHub URL in GitHub field.
        Verifies inline validation errors block form submission. (AC-2, AC-6)
        """
        uid = uuid.uuid4().hex[:6]
        email = f"candidate_social_{uid}@careerflow.test"
        login_candidate(driver, email=email, full_name="Social Tester")

        wait = WebDriverWait(driver, 10)
        driver.get(f"{FRONTEND_URL}/profile")
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='profile-container']")))

        linkedin_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-profile-linkedin']")
        github_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-profile-github']")
        save_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-profile-save']")

        # Enter invalid domains
        set_react_input(driver, linkedin_input, "https://facebook.com/alex")
        set_react_input(driver, github_input, "https://gitlab.com/alex")

        save_btn.click()

        # Verify inline error for LinkedIn
        linkedin_err = wait.until(
            EC.visibility_of_element_located((By.XPATH, "//*[contains(., 'Please provide a valid LinkedIn URL')]"))
        )
        assert linkedin_err.is_displayed()

        # Verify inline error for GitHub
        github_err = wait.until(
            EC.visibility_of_element_located((By.XPATH, "//*[contains(., 'Please provide a valid GitHub URL')]"))
        )
        assert github_err.is_displayed()

        screenshot_path = SCREENSHOTS_DIR / "us42_04_social_links_domain_validation.png"
        driver.save_screenshot(str(screenshot_path))

    def test_tc42_05_url_scheme_auto_prefixing(self, driver):
        """
        Test Case 5: URL Scheme Auto-Prefixing
        Enters bare URLs (e.g. linkedin.com/in/alex and github.com/alex).
        Verifies that URLs save successfully and Quick Links card renders clickable links pointing to https://. (AC-2)
        """
        uid = uuid.uuid4().hex[:6]
        email = f"candidate_prefix_{uid}@careerflow.test"
        login_candidate(driver, email=email, full_name="Prefix Tester")

        wait = WebDriverWait(driver, 10)
        driver.get(f"{FRONTEND_URL}/profile")
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='profile-container']")))

        linkedin_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-profile-linkedin']")
        github_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-profile-github']")
        save_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-profile-save']")

        set_react_input(driver, linkedin_input, "linkedin.com/in/alex")
        set_react_input(driver, github_input, "github.com/alex")

        save_btn.click()

        # Verify success toast
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='toast-message']")))

        # Check Quick Links card links
        linkedin_link = wait.until(EC.visibility_of_element_located((By.XPATH, "//a[contains(., 'LinkedIn Profile')]")))
        github_link = wait.until(EC.visibility_of_element_located((By.XPATH, "//a[contains(., 'GitHub Profile')]")))

        assert linkedin_link.get_attribute("href") == "https://linkedin.com/in/alex"
        assert github_link.get_attribute("href") == "https://github.com/alex"

        screenshot_path = SCREENSHOTS_DIR / "us42_05_url_scheme_auto_prefixing.png"
        driver.save_screenshot(str(screenshot_path))

    def test_tc42_06_room_application_autofill_flow(self, driver):
        """
        Test Case 6: Room Application Autofill Flow (US-42-T5)
        Ensures profile has Full Name and Email saved. Navigates to an active recruitment room application
        link (/apply/:token). Verifies Full Name and Email are auto-filled without retyping. (AC-4)
        """
        uid = uuid.uuid4().hex[:6]
        candidate_email = f"autofill_candidate_{uid}@careerflow.test"
        hr_email = f"autofill_hr_{uid}@careerflow.test"

        hr_user = create_user_in_db(hr_email, "ValidPass2026!", role=User.Role.HR_MANAGER, full_name="Elena HR")
        candidate_user = login_candidate(driver, email=candidate_email, full_name="Morgan Autofill")

        # Create active RecruitmentRoom with share token
        room = RecruitmentRoom.objects.create(
            title=f"Senior Cloud Platform Engineer {uid}",
            company_name="Apex Nexus Corp",
            department="Cloud Operations",
            description="Build scalable distributed microservices.",
            status="OPEN",
            created_by=hr_user,
            cv_weight=50.0,
            video_weight=50.0,
            link_is_active=True,
        )

        wait = WebDriverWait(driver, 10)

        # Ensure profile full_name and email are persisted in candidate profile
        driver.get(f"{FRONTEND_URL}/profile")
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='profile-container']")))
        fn_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-profile-fullname']")
        set_react_input(driver, fn_input, "Morgan Autofill")
        driver.find_element(By.CSS_SELECTOR, "[data-testid='button-profile-save']").click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='toast-message']")))

        # Open public recruitment room application link
        driver.get(f"{FRONTEND_URL}/apply/{room.share_token}")
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='page-public-application']")))

        # Wait for autofill fields
        name_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-candidate-name']")))
        email_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-candidate-email']")))

        # Give small delay for async profile autofill effect to resolve
        time.sleep(1)

        auto_name = name_input.get_attribute("value")
        auto_email = email_input.get_attribute("value")

        assert auto_name == "Morgan Autofill"
        assert auto_email == candidate_email

        screenshot_path = SCREENSHOTS_DIR / "us42_06_room_application_autofill.png"
        driver.save_screenshot(str(screenshot_path))

    def test_tc42_07_reset_button_behavior(self, driver):
        """
        Test Case 7: Reset Button Behavior
        Makes modifications to form inputs without saving, clicks Reset button,
        verifies inputs revert back to their saved database values. (AC-6)
        """
        uid = uuid.uuid4().hex[:6]
        email = f"candidate_reset_{uid}@careerflow.test"
        login_candidate(driver, email=email, full_name="Baseline Name")

        wait = WebDriverWait(driver, 10)
        driver.get(f"{FRONTEND_URL}/profile")
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='profile-container']")))

        # First save baseline data
        fullname_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-profile-fullname']")
        role_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-profile-target-role']")
        set_react_input(driver, fullname_input, "Baseline Name")
        set_react_input(driver, role_input, "Baseline Role")
        driver.find_element(By.CSS_SELECTOR, "[data-testid='button-profile-save']").click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='toast-message']")))

        # Modify inputs without saving
        set_react_input(driver, fullname_input, "Unsaved Draft Name")
        set_react_input(driver, role_input, "Temporary Role Draft")

        assert fullname_input.get_attribute("value") == "Unsaved Draft Name"
        assert role_input.get_attribute("value") == "Temporary Role Draft"

        # Click Reset button
        reset_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-profile-reset']")
        reset_btn.click()

        # Verify toast and input reversion
        toast = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='toast-message']")))
        assert "Profile form changes reset." in toast.text

        reverted_name = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-profile-fullname']").get_attribute("value")
        reverted_role = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-profile-target-role']").get_attribute("value")

        assert reverted_name == "Baseline Name"
        assert reverted_role == "Baseline Role"

        screenshot_path = SCREENSHOTS_DIR / "us42_07_reset_button_reverts_inputs.png"
        driver.save_screenshot(str(screenshot_path))

    def test_tc42_08_avatar_image_upload_and_preview(self, driver):
        """
        Test Case 8: Avatar Image Upload & Real-Time Preview
        Simulates file selection for profile avatar, asserts preview image renders in place of initials badge. (AC-1, AC-6)
        """
        uid = uuid.uuid4().hex[:6]
        email = f"candidate_avatar_{uid}@careerflow.test"
        login_candidate(driver, email=email, full_name="Avatar Tester")

        wait = WebDriverWait(driver, 10)
        driver.get(f"{FRONTEND_URL}/profile")
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='profile-container']")))

        # Initially fallback badge is rendered
        fallback = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='profile-avatar-fallback']")))
        assert fallback.is_displayed()

        # Create temporary valid test image with PIL
        from PIL import Image
        temp_img = TESTS_DIR / "fixtures" / "temp_avatar.png"
        temp_img.parent.mkdir(parents=True, exist_ok=True)
        img = Image.new('RGB', (128, 128), color=(39, 114, 84))
        img.save(str(temp_img), format='PNG')

        # Upload image file
        file_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-profile-avatar']")
        file_input.send_keys(str(temp_img.resolve()))

        # Verify avatar image element now renders real-time preview
        avatar_img = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='profile-avatar-img']")))
        assert avatar_img.is_displayed()

        # Save profile
        driver.find_element(By.CSS_SELECTOR, "[data-testid='button-profile-save']").click()
        toast = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='toast-message']")))
        assert "Profile updated successfully!" in toast.text

        screenshot_path = SCREENSHOTS_DIR / "us42_08_avatar_upload_preview.png"
        driver.save_screenshot(str(screenshot_path))

        # Cleanup test fixture
        try:
            if temp_img.exists():
                temp_img.unlink()
        except Exception:
            pass

    def test_tc42_09_multitenant_user_isolation(self, driver):
        """
        Test Case 9: Multi-Tenant & User Isolation
        Candidate A saves profile details. Candidate B logs in and verifies they cannot see Candidate A's
        data (strict data privacy). (AC-5)
        """
        uid = uuid.uuid4().hex[:6]
        email_a = f"candidate_iso_a_{uid}@careerflow.test"
        email_b = f"candidate_iso_b_{uid}@careerflow.test"

        user_a = login_candidate(driver, email=email_a, full_name="Candidate Alpha")
        wait = WebDriverWait(driver, 10)

        driver.get(f"{FRONTEND_URL}/profile")
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='profile-container']")))

        # Alpha sets distinct profile
        role_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-profile-target-role']")
        set_react_input(driver, role_input, "Quantum Cryptographer")
        driver.find_element(By.CSS_SELECTOR, "[data-testid='button-profile-save']").click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='toast-message']")))

        # Log in as Beta
        login_candidate(driver, email=email_b, full_name="Candidate Beta")
        driver.get(f"{FRONTEND_URL}/profile")
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='profile-container']")))

        # Assert Beta does not see Alpha's target role or email
        beta_email_display = driver.find_element(By.CSS_SELECTOR, "[data-testid='profile-display-email']").text
        beta_role_val = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-profile-target-role']").get_attribute("value")

        assert beta_email_display == email_b
        assert beta_role_val != "Quantum Cryptographer"

        screenshot_path = SCREENSHOTS_DIR / "us42_09_user_isolation.png"
        driver.save_screenshot(str(screenshot_path))

    def test_tc42_10_account_security_and_logout_navigation(self, driver):
        """
        Test Case 10: Account Security & Session Logout Navigation
        Verifies Reset Password navigation to /forgot-password and Logout button clearing session.
        """
        uid = uuid.uuid4().hex[:6]
        email = f"candidate_nav_{uid}@careerflow.test"
        login_candidate(driver, email=email, full_name="Navigation User")

        wait = WebDriverWait(driver, 10)
        driver.get(f"{FRONTEND_URL}/profile")
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='profile-container']")))

        # Test Reset Password button
        reset_pwd_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-profile-reset-pwd']")))
        reset_pwd_btn.click()

        wait.until(EC.url_contains("/forgot-password"))
        assert "/forgot-password" in driver.current_url

        # Navigate back to profile
        driver.get(f"{FRONTEND_URL}/profile")
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='profile-container']")))

        # Click Log out button
        logout_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-profile-logout']")))
        logout_btn.click()

        wait.until(EC.url_contains("/login"))
        assert "/login" in driver.current_url

        screenshot_path = SCREENSHOTS_DIR / "us42_10_logout_and_navigation.png"
        driver.save_screenshot(str(screenshot_path))
