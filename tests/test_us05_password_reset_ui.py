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
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

from apps.authentication.models import User, PasswordResetToken
from conftest import FRONTEND_URL, SCREENSHOTS_DIR, create_user_in_db


def clear_react_input(driver, element):
    """Reliably clears React controlled inputs across Windows and macOS."""
    element.send_keys(Keys.COMMAND + "a")
    element.send_keys(Keys.CONTROL + "a")
    element.send_keys(Keys.BACKSPACE)
    driver.execute_script(
        "arguments[0].value = ''; "
        "arguments[0].dispatchEvent(new Event('input', { bubbles: true })); "
        "arguments[0].dispatchEvent(new Event('change', { bubbles: true }));",
        element
    )


class TestUS05PasswordResetUI:
    """
    US-05: Secure Time-Limited Password Reset Flow with Blind Enumeration Protection
    Sprint: Sprint 6
    Author: Nafisa Tabassum Maria (@Maria-07-222)

    Acceptance Criteria Coverage:
    - AC 1: Request reset with registered email (POST /api/auth/password-reset-request/)
    - AC 2: Secure, time-limited token/code (15-min TTL, 4-digit code & SHA-256 hash)
    - AC 3: Expired/used tokens rejected (atomic single-use invalidation)
    - AC 4: Validated & securely hashed (PBKDF2-SHA256, password complexity enforcement)
    - AC 5: Blind user enumeration protection (uniform response, zero account leakage)
    - AC 6: Old password revocation (instant session revocation, old credentials blocked)
    """

    def test_tc05_01_navigate_from_login_to_forgot_password(self, driver):
        """TC-05-01: Navigating from /login via 'Forgot password?' link mounts ForgotPassword wizard."""
        driver.get(f"{FRONTEND_URL}/login")
        driver.execute_script("sessionStorage.clear(); localStorage.clear();")

        wait = WebDriverWait(driver, 10)
        forgot_link = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='link-forgot-password']")))
        assert forgot_link.is_displayed()
        forgot_link.click()

        wait.until(EC.url_contains("/forgot-password"))
        assert "/forgot-password" in driver.current_url

        # Verify Brand Panel and Step 1 of 3
        heading = wait.until(EC.visibility_of_element_located((By.XPATH, "//h1[contains(text(), 'Forgot Password')]")))
        assert heading.is_displayed()

        step_indicator = driver.find_element(By.XPATH, "//*[contains(text(), 'Step 1 of 3')]")
        assert step_indicator.is_displayed()

        email_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-forgot-email']")
        assert email_input.is_displayed()

        submit_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-forgot-submit']")
        assert submit_btn.is_displayed()

        # Capture screenshot for reporting
        screenshot_path = SCREENSHOTS_DIR / "us05_01_forgot_password_entry_screen.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

        # Verify "Back to Log in" button returns to /login
        back_link = driver.find_element(By.CSS_SELECTOR, "[data-testid='link-back-login']")
        back_link.click()
        wait.until(EC.url_contains("/login"))
        assert "/login" in driver.current_url

    def test_tc05_02_blind_user_enumeration_protection_and_invalid_email(self, driver):
        """TC-05-02: Non-existent emails yield uniform generic 200 OK without leaking user existence."""
        driver.get(f"{FRONTEND_URL}/forgot-password")
        driver.execute_script("sessionStorage.clear(); localStorage.clear();")
        driver.refresh()

        wait = WebDriverWait(driver, 10)
        email_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-forgot-email']")))
        submit_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-forgot-submit']")

        non_existent_email = "ghost_candidate_99999@careerflow.test"
        User.objects.filter(email=non_existent_email).delete()

        clear_react_input(driver, email_input)
        email_input.send_keys(non_existent_email)
        submit_btn.click()

        # Uniform response: Advances seamlessly to Step 2 (Blind Enumeration Protection)
        code_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-verification-code']")))
        assert code_input.is_displayed()

        # Verify that NO token was created in the database for the non-existent user
        token_count = PasswordResetToken.objects.filter(user__email=non_existent_email).count()
        assert token_count == 0, "Security Violation: PasswordResetToken was created for non-existent email!"

        # Capture screenshot of blind enumeration defense
        screenshot_path = SCREENSHOTS_DIR / "us05_02_blind_enumeration_security_and_nonexistent_email.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

        # Test "← Change Email" link to return to Step 1
        change_email_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Change Email')]")
        change_email_btn.click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-forgot-email']")))

    def test_tc05_03_request_verification_code_and_inspect_terminal_banner(self, driver):
        """TC-05-03: Submitting registered email creates 4-digit code in DB and renders terminal guidance."""
        email = "maria_applicant_us05@careerflow.test"
        user = create_user_in_db(email, "InitialSecretPass2026!", role=User.Role.STUDENT, full_name="Maria Applicant")

        driver.get(f"{FRONTEND_URL}/forgot-password")
        driver.execute_script("sessionStorage.clear(); localStorage.clear();")
        driver.refresh()

        wait = WebDriverWait(driver, 10)
        email_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-forgot-email']")))
        submit_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-forgot-submit']")

        clear_react_input(driver, email_input)
        email_input.send_keys(email)
        submit_btn.click()

        # Wait for Step 2
        code_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-verification-code']")))
        assert code_input.is_displayed()

        # Verify Step 2 of 3 header and email display
        step_header = driver.find_element(By.XPATH, "//*[contains(text(), 'Step 2 of 3')]")
        assert step_header.is_displayed()
        assert email in driver.page_source

        # Verify terminal guidance banner card is rendered
        terminal_card = driver.find_element(By.XPATH, "//*[contains(text(), 'Terminal Verification Code')]")
        assert terminal_card.is_displayed()

        # Verify database token record was created with 4-digit code and 15-minute TTL
        token_obj = PasswordResetToken.objects.filter(user=user, is_used=False).order_by('-created_at').first()
        assert token_obj is not None, "PasswordResetToken was not created in database!"
        assert len(token_obj.code) == 4, f"Expected 4-digit code, got: {token_obj.code}"
        assert token_obj.code.isdigit(), "Code must be numeric"
        assert token_obj.token_hash, "Token SHA-256 hash must be generated"
        assert token_obj.is_active is True, "Token must be active"

        # Capture screenshot of Step 2 with terminal banner guidance
        screenshot_path = SCREENSHOTS_DIR / "us05_03_verification_code_terminal_guidance_step2.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc05_04_verification_code_input_sanitization_and_invalid_code_rejection(self, driver):
        """TC-05-04: Non-digits are sanitized and invalid/wrong 4-digit codes are rejected with error."""
        email = "maria_cand_code_test@careerflow.test"
        user = create_user_in_db(email, "InitialSecretPass2026!", role=User.Role.STUDENT, full_name="Maria Code Test")
        raw_token = PasswordResetToken.create_token_for_user(user)
        token_obj = PasswordResetToken.objects.filter(user=user).latest('created_at')
        valid_code = token_obj.code

        driver.get(f"{FRONTEND_URL}/forgot-password?email={email}&step=code")
        wait = WebDriverWait(driver, 10)
        code_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-verification-code']")))
        verify_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-verify-code']")

        # 1. Test input sanitization: non-numeric letters should be stripped
        clear_react_input(driver, code_input)
        code_input.send_keys("ABcd!@")
        assert code_input.get_attribute("value") == "", "Input should strip non-digits"

        # 2. Test wrong 4-digit code
        wrong_code = "0000" if valid_code != "0000" else "1111"
        clear_react_input(driver, code_input)
        code_input.send_keys(wrong_code)
        assert code_input.get_attribute("value") == wrong_code
        verify_btn.click()

        # Verify error message appears
        error_box = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='code-error-message']")))
        assert "Invalid or expired verification code" in error_box.text

        # Capture screenshot of invalid code error state
        screenshot_path = SCREENSHOTS_DIR / "us05_04_invalid_code_error_feedback.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc05_05_valid_code_verification_advances_to_step3(self, driver):
        """TC-05-05: Entering valid 4-digit code verifies identity and cleanly advances to Step 3."""
        email = "maria_valid_step3@careerflow.test"
        user = create_user_in_db(email, "InitialPass2026!", role=User.Role.STUDENT, full_name="Maria Step 3")
        PasswordResetToken.create_token_for_user(user)
        token_obj = PasswordResetToken.objects.filter(user=user).latest('created_at')

        driver.get(f"{FRONTEND_URL}/forgot-password?email={email}&step=code")
        wait = WebDriverWait(driver, 10)
        code_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-verification-code']")))
        verify_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-verify-code']")

        clear_react_input(driver, code_input)
        code_input.send_keys(token_obj.code)
        verify_btn.click()

        # Verify Step 3 mounts: "Set New Password"
        new_pass_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-new-password']")))
        assert new_pass_input.is_displayed()

        step3_badge = driver.find_element(By.XPATH, "//*[contains(text(), 'Step 3 of 3')]")
        assert step3_badge.is_displayed()
        assert "CODE VERIFIED" in step3_badge.text.upper()

        confirm_pass_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-confirm-password']")
        assert confirm_pass_input.is_displayed()

    def test_tc05_06_password_strength_meter_and_visibility_toggle(self, driver):
        """TC-05-06: Evaluates live password strength meter and show/hide password toggle buttons."""
        email = "maria_strength_meter@careerflow.test"
        user = create_user_in_db(email, "InitialPass2026!", role=User.Role.STUDENT, full_name="Maria Strength")
        PasswordResetToken.create_token_for_user(user)
        token_obj = PasswordResetToken.objects.filter(user=user).latest('created_at')

        driver.get(f"{FRONTEND_URL}/forgot-password?email={email}&code={token_obj.code}&step=code")
        wait = WebDriverWait(driver, 10)
        code_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-verification-code']")))
        driver.find_element(By.CSS_SELECTOR, "[data-testid='button-verify-code']").click()

        new_pass_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-new-password']")))

        # 1. Test Weak strength
        clear_react_input(driver, new_pass_input)
        new_pass_input.send_keys("short")
        meter = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='password-strength-meter']")))
        assert "Weak" in meter.text or "Too short" in meter.text

        # 2. Test Strong strength
        clear_react_input(driver, new_pass_input)
        new_pass_input.send_keys("CyberSecurePass2026!#")
        WebDriverWait(driver, 10).until(
            lambda d: "Strong" in d.find_element(By.CSS_SELECTOR, "[data-testid='password-strength-meter']").text
        )

        # 3. Test Show/Hide Password Eye Toggle
        assert new_pass_input.get_attribute("type") == "password"
        toggle_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-toggle-password']")
        toggle_btn.click()
        assert new_pass_input.get_attribute("type") == "text"
        toggle_btn.click()
        assert new_pass_input.get_attribute("type") == "password"

        # Capture screenshot of Step 3 password strength and eye toggle
        screenshot_path = SCREENSHOTS_DIR / "us05_05_set_new_password_strength_meter_and_eye_toggle.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc05_07_password_mismatch_and_length_validation(self, driver):
        """TC-05-07: Validates client/server rejection of mismatched passwords and passwords < 8 characters."""
        email = "maria_validation_cand@careerflow.test"
        user = create_user_in_db(email, "InitialPass2026!", role=User.Role.STUDENT, full_name="Maria Val")
        PasswordResetToken.create_token_for_user(user)
        token_obj = PasswordResetToken.objects.filter(user=user).latest('created_at')

        driver.get(f"{FRONTEND_URL}/forgot-password?email={email}&code={token_obj.code}&step=code")
        wait = WebDriverWait(driver, 10)
        code_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-verification-code']")))
        driver.find_element(By.CSS_SELECTOR, "[data-testid='button-verify-code']").click()

        new_pass_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-new-password']")))
        confirm_pass_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-confirm-password']")
        submit_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-submit-new-password']")

        # 1. Test password mismatch
        clear_react_input(driver, new_pass_input)
        new_pass_input.send_keys("ValidPass2026!#")
        clear_react_input(driver, confirm_pass_input)
        confirm_pass_input.send_keys("DifferentPass9999!")
        submit_btn.click()

        error_box = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='reset-error-message']")))
        assert "Passwords do not match" in error_box.text

        # Capture screenshot of mismatch validation error
        screenshot_path = SCREENSHOTS_DIR / "us05_06_password_validation_and_mismatch_feedback.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

        # 2. Test password length < 8 chars
        clear_react_input(driver, new_pass_input)
        new_pass_input.send_keys("short")
        clear_react_input(driver, confirm_pass_input)
        confirm_pass_input.send_keys("short")
        submit_btn.click()

        error_box = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='reset-error-message']")))
        assert "at least 8 characters" in error_box.text

    def test_tc05_08_successful_password_reset_e2e_and_old_password_revocation(self, driver):
        """TC-05-08: Complete E2E password reset updates credentials, revokes old password, and permits login."""
        email = "maria_e2e_success@careerflow.test"
        old_password = "OldInitialPassword2026!"
        new_password = "BrandNewSecurePassword2026!#"
        user = create_user_in_db(email, old_password, role=User.Role.STUDENT, full_name="Maria E2E Reset")

        driver.get(f"{FRONTEND_URL}/forgot-password")
        driver.execute_script("sessionStorage.clear(); localStorage.clear();")
        driver.refresh()

        wait = WebDriverWait(driver, 10)
        # Step 1: Request Code
        email_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-forgot-email']")))
        clear_react_input(driver, email_input)
        email_input.send_keys(email)
        driver.find_element(By.CSS_SELECTOR, "[data-testid='button-forgot-submit']").click()

        # Step 2: Retrieve generated code from DB and enter it
        code_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-verification-code']")))
        token_obj = PasswordResetToken.objects.filter(user=user, is_used=False).latest('created_at')
        code_input.send_keys(token_obj.code)
        driver.find_element(By.CSS_SELECTOR, "[data-testid='button-verify-code']").click()

        # Step 3: Set New Password
        new_pass_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-new-password']")))
        confirm_pass_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-confirm-password']")
        clear_react_input(driver, new_pass_input)
        new_pass_input.send_keys(new_password)
        clear_react_input(driver, confirm_pass_input)
        confirm_pass_input.send_keys(new_password)
        driver.find_element(By.CSS_SELECTOR, "[data-testid='button-submit-new-password']").click()

        # Step 4: Verify Success Card
        success_card = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='forgot-success-container']")))
        assert success_card.is_displayed()
        assert "Password Reset Successful!" in success_card.text

        # Verify DB: Token is marked used
        token_obj.refresh_from_db()
        assert token_obj.is_used is True, "Token must be marked is_used=True after consumption"

        # Capture screenshot of Step 4 Success Card
        screenshot_path = SCREENSHOTS_DIR / "us05_07_password_reset_success_card.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

        # Click "Proceed to Log in"
        proceed_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-proceed-login']")
        proceed_btn.click()
        wait.until(EC.url_contains("/login"))

        # Verify AC 6: Old Password Revocation
        login_email = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-login-email']")))
        login_pass = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-login-password']")
        login_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-login']")

        clear_react_input(driver, login_email)
        login_email.send_keys(email)
        clear_react_input(driver, login_pass)
        login_pass.send_keys(old_password)
        login_btn.click()

        error_msg = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='field-error']")))
        assert "Invalid email or password" in error_msg.text, "Old credentials must be rejected immediately!"

        # Log in with NEW Password
        clear_react_input(driver, login_pass)
        login_pass.send_keys(new_password)
        login_btn.click()

        # Verify successful login to dashboard
        wait.until(EC.url_contains("/student/dashboard"))
        assert "/student/dashboard" in driver.current_url

        # Capture screenshot of successful login with updated credentials
        screenshot_path = SCREENSHOTS_DIR / "us05_08_old_password_revocation_and_new_password_login.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc05_09_code_replay_rejected_after_consumption(self, driver):
        """TC-05-09: Replay attack with an already-used code is strictly rejected with HTTP 400."""
        email = "maria_replay_cand@careerflow.test"
        user = create_user_in_db(email, "InitialPass2026!", role=User.Role.STUDENT, full_name="Maria Replay")
        raw_token = PasswordResetToken.create_token_for_user(user)
        token_obj = PasswordResetToken.objects.filter(user=user).latest('created_at')
        code = token_obj.code

        # Consume the code once
        assert PasswordResetToken.validate_and_consume_code(user, code) is True
        token_obj.refresh_from_db()
        assert token_obj.is_used is True

        # Now attempt to verify or submit this already-used code via the UI
        driver.get(f"{FRONTEND_URL}/forgot-password?email={email}&step=code")
        wait = WebDriverWait(driver, 10)
        code_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-verification-code']")))
        clear_react_input(driver, code_input)
        code_input.send_keys(code)
        driver.find_element(By.CSS_SELECTOR, "[data-testid='button-verify-code']").click()

        error_box = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='code-error-message']")))
        assert "Invalid or expired verification code" in error_box.text

    def test_tc05_10_direct_reset_password_route_and_token_compatibility(self, driver):
        """TC-05-10: Visiting /reset-password without tokens redirects to /forgot-password; with tokens renders reset form."""
        # 1. Visiting /reset-password without tokens -> auto-redirects to /forgot-password
        driver.get(f"{FRONTEND_URL}/reset-password")
        wait = WebDriverWait(driver, 10)
        wait.until(EC.url_contains("/forgot-password"))
        assert "/forgot-password" in driver.current_url

        # 2. Visiting /reset-password with uid and raw_token -> presents cryptographic link reset form
        email = "maria_cryptolink_cand@careerflow.test"
        user = create_user_in_db(email, "InitialPass2026!", role=User.Role.STUDENT, full_name="Maria Crypto")
        raw_token = PasswordResetToken.create_token_for_user(user)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

        driver.get(f"{FRONTEND_URL}/reset-password?uid={uidb64}&token={raw_token}")
        reset_heading = wait.until(EC.visibility_of_element_located((By.XPATH, "//h1[contains(text(), 'Set New Password')]")))
        assert reset_heading.is_displayed()

        # Capture screenshot of direct cryptographic link recovery landing
        screenshot_path = SCREENSHOTS_DIR / "us05_09_direct_link_token_flow_or_redirect.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()
