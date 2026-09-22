import sys
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

import time
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from apps.authentication.models import User
from conftest import FRONTEND_URL, create_user_in_db


class TestUS01UserRegistration:
    """
    US-01: User Registration
    Acceptance Criteria:
    ✓ Valid users can register with email and password
    ✓ Invalid email format is rejected
    ✓ Password meets security requirements
    ✓ Clear error messages display for invalid input
    ✓ Confirmation email / feedback sent to user
    ✓ User account is created in database
    """

    def test_tc01_01_valid_registration_and_db_creation(self, driver):
        """TC-01-01: Valid user registers via UI, sees confirmation, and account is created in MySQL DB."""
        email = "test_register_student@careerflow.test"
        User.objects.filter(email=email).delete()

        driver.get(f"{FRONTEND_URL}/register")

        wait = WebDriverWait(driver, 10)
        name_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-register-name']")))
        email_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-register-email']")
        pass_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-register-password']")
        confirm_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-register-confirm-password']")
        submit_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-register']")

        # Choose candidate (student) role
        role_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-role-student']")
        role_btn.click()

        name_input.send_keys("Test Student Alex")
        email_input.send_keys(email)
        pass_input.send_keys("SecurePass2026!")
        confirm_input.send_keys("SecurePass2026!")

        submit_btn.click()

        # Verify UI success confirmation screen
        wait.until(EC.visibility_of_element_located((By.XPATH, "//*[contains(text(), 'Registration Confirmed in Database')]")))
        
        # Verify toast notification displayed
        toast = driver.find_element(By.CSS_SELECTOR, "[data-testid='toast-message']")
        assert "registered successfully in MySQL" in toast.text

        # Verify database record creation
        db_user = User.objects.filter(email=email).first()
        assert db_user is not None, "User record was not created in MySQL database!"
        assert db_user.full_name == "Test Student Alex"
        assert db_user.role == User.Role.STUDENT
        assert db_user.check_password("SecurePass2026!") is True, "Password was not hashed properly!"

    def test_tc01_02_invalid_email_format_rejected(self, driver):
        """TC-01-02: Invalid email format (missing @) is rejected by browser validation and backend API."""
        driver.get(f"{FRONTEND_URL}/register")

        wait = WebDriverWait(driver, 10)
        name_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-register-name']")))
        email_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-register-email']")
        pass_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-register-password']")
        confirm_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-register-confirm-password']")
        submit_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-register']")

        name_input.send_keys("Invalid User")
        email_input.send_keys("invalidemailformat.com")  # No '@'
        pass_input.send_keys("SecurePass2026!")
        confirm_input.send_keys("SecurePass2026!")

        # 1. Verify browser HTML5 constraint validation catches invalid email format
        is_valid = driver.execute_script("return arguments[0].checkValidity();", email_input)
        assert is_valid is False, "HTML5 email validation did not flag invalid email format!"
        validation_msg = driver.execute_script("return arguments[0].validationMessage;", email_input)
        assert len(validation_msg) > 0, "Validation message was empty for invalid email format!"

        # 2. Clicking submit does not navigate or create account
        submit_btn.click()
        assert "/register" in driver.current_url
        assert not User.objects.filter(email="invalidemailformat.com").exists()

        # 3. Verify backend rejects invalid email format with HTTP 400
        import requests
        from conftest import BACKEND_URL
        resp = requests.post(f"{BACKEND_URL}/api/auth/register/", json={
            "email": "invalidemailformat.com",
            "password": "SecurePass2026!",
            "confirm_password": "SecurePass2026!",
            "full_name": "Invalid User"
        })
        assert resp.status_code == 400
        assert "email" in resp.json().get("errors", {})

    def test_tc01_03_short_password_rejected(self, driver):
        """TC-01-03: Password shorter than 8 characters is rejected with clear error message."""
        driver.get(f"{FRONTEND_URL}/register")

        wait = WebDriverWait(driver, 10)
        name_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-register-name']")))
        email_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-register-email']")
        pass_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-register-password']")
        confirm_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-register-confirm-password']")
        submit_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-register']")

        name_input.send_keys("Short Pass User")
        email_input.send_keys("test_shortpass@careerflow.test")
        pass_input.send_keys("pass1")  # Less than 8 characters
        confirm_input.send_keys("pass1")

        submit_btn.click()

        error_elem = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='register-error']")))
        assert "at least 8 characters" in error_elem.text

    def test_tc01_04_password_mismatch_rejected(self, driver):
        """TC-01-04: Mismatched password and confirm_password are rejected with error."""
        driver.get(f"{FRONTEND_URL}/register")

        wait = WebDriverWait(driver, 10)
        name_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-register-name']")))
        email_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-register-email']")
        pass_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-register-password']")
        confirm_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-register-confirm-password']")
        submit_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-register']")

        name_input.send_keys("Mismatch User")
        email_input.send_keys("test_mismatch@careerflow.test")
        pass_input.send_keys("SecurePass2026!")
        confirm_input.send_keys("DifferentPassword123!")

        submit_btn.click()

        error_elem = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='register-error']")))
        assert "passwords do not match" in error_elem.text.lower()

    def test_tc01_05_duplicate_email_rejected_by_backend(self, driver):
        """TC-01-05: Attempting to register an already existing email displays backend validation error."""
        existing_email = "test_duplicate@careerflow.test"
        create_user_in_db(existing_email, "SecurePass2026!", role=User.Role.STUDENT, full_name="Original User")

        driver.get(f"{FRONTEND_URL}/register")

        wait = WebDriverWait(driver, 10)
        name_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-register-name']")))
        email_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-register-email']")
        pass_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-register-password']")
        confirm_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-register-confirm-password']")
        submit_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-register']")

        name_input.send_keys("Duplicate User")
        email_input.send_keys(existing_email)
        pass_input.send_keys("SecurePass2026!")
        confirm_input.send_keys("SecurePass2026!")

        submit_btn.click()

        error_elem = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='register-error']")))
        assert "already exists" in error_elem.text.lower()

    def test_tc01_06_proceed_to_login_flow(self, driver):
        """TC-01-06: After registration, clicking 'Proceed to Log in' transitions to the login screen."""
        email = "test_proceed_login@careerflow.test"
        User.objects.filter(email=email).delete()

        driver.get(f"{FRONTEND_URL}/register")

        wait = WebDriverWait(driver, 10)
        name_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-register-name']")))
        email_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-register-email']")
        pass_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-register-password']")
        confirm_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-register-confirm-password']")
        submit_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-register']")

        name_input.send_keys("Login Next")
        email_input.send_keys(email)
        pass_input.send_keys("SecurePass2026!")
        confirm_input.send_keys("SecurePass2026!")
        submit_btn.click()

        proceed_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-registered-login']")))
        proceed_btn.click()

        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='button-login']")))
        assert "/login" in driver.current_url
