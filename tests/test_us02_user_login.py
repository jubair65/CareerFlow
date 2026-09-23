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


class TestUS02UserLogin:
    """
    US-02: User Login
    Acceptance Criteria:
    ✓ Valid credentials allow login
    ✓ Invalid credentials are rejected with clear message
    ✓ Session token is generated upon successful login
    ✓ User remains logged in across page refresh
    ✓ Logout functionality works correctly
    ✓ Failed login attempts are handled
    """

    def test_tc02_01_valid_credentials_login_success(self, driver):
        """TC-02-01: Valid user credentials navigate to dashboard and show personalized welcome."""
        email = "test_valid_login@careerflow.test"
        password = "ValidPassword2026!"
        create_user_in_db(email, password, role=User.Role.STUDENT, full_name="Jane Applicant")

        driver.get(f"{FRONTEND_URL}/login")

        wait = WebDriverWait(driver, 10)
        email_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-login-email']")))
        pass_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-login-password']")
        submit_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-login']")

        # Clear existing default demo values
        email_input.clear()
        email_input.send_keys(email)
        pass_input.clear()
        pass_input.send_keys(password)

        submit_btn.click()

        # Verify redirect to dashboard
        wait.until(EC.url_contains("/dashboard"))

        # Wait until loading state is replaced with actual user name (async fetch)
        wait.until(EC.visibility_of_element_located((By.XPATH, "//h1[contains(text(), 'Welcome')]")))
        # Wait for async data load - poll until 'Loading' disappears from heading
        WebDriverWait(driver, 15).until(
            lambda d: "Loading" not in d.find_element(By.XPATH, "//h1[contains(text(), 'Welcome')]").text
        )
        heading = driver.find_element(By.XPATH, "//h1[contains(text(), 'Welcome')]")
        assert "Jane Applicant" in heading.text

    def test_tc02_02_invalid_credentials_rejected_with_message(self, driver):
        """TC-02-02: Invalid password displays 'Invalid email or password.' message and blocks login."""
        email = "test_wrong_pass@careerflow.test"
        create_user_in_db(email, "CorrectPass2026!", role=User.Role.STUDENT, full_name="User Wrong Pass")

        driver.get(f"{FRONTEND_URL}/login")

        wait = WebDriverWait(driver, 10)
        email_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-login-email']")))
        pass_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-login-password']")
        submit_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-login']")

        email_input.clear()
        email_input.send_keys(email)
        pass_input.clear()
        pass_input.send_keys("WrongPass123456!")

        submit_btn.click()

        # Verify error message
        error_msg = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='field-error']")))
        assert "Invalid email or password" in error_msg.text
        assert "/login" in driver.current_url

    def test_tc02_03_jwt_tokens_generated_in_localstorage(self, driver):
        """TC-02-03: Session tokens (access & refresh JWTs) are generated and stored in browser localStorage."""
        email = "test_jwt_tokens@careerflow.test"
        password = "TokenPassword2026!"
        create_user_in_db(email, password, role=User.Role.STUDENT, full_name="Token User")

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

        wait.until(EC.url_contains("/dashboard"))

        # Inspect localStorage for JWT tokens
        access_token = driver.execute_script("return localStorage.getItem('careerflow_access_token');")
        refresh_token = driver.execute_script("return localStorage.getItem('careerflow_refresh_token');")

        assert access_token is not None and len(access_token) > 20, "Access token missing from localStorage!"
        assert refresh_token is not None and len(refresh_token) > 20, "Refresh token missing from localStorage!"
        assert access_token.count('.') == 2, "Access token is not a valid JWT format!"
        assert refresh_token.count('.') == 2, "Refresh token is not a valid JWT format!"

    def test_tc02_04_session_persists_across_page_refresh(self, driver):
        """TC-02-04: User remains logged in across page refresh without being logged out."""
        email = "test_refresh_persist@careerflow.test"
        password = "PersistPassword2026!"
        create_user_in_db(email, password, role=User.Role.HR_MANAGER, full_name="Persist HR")

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

        wait.until(EC.url_contains("/dashboard"))
        # Wait for async loading to complete
        wait.until(EC.visibility_of_element_located((By.XPATH, "//h1[contains(text(), 'Welcome')]")))
        WebDriverWait(driver, 15).until(
            lambda d: "Loading" not in d.find_element(By.XPATH, "//h1[contains(text(), 'Welcome')]").text
        )

        # Reload browser page
        driver.refresh()

        # Verify user remains on /dashboard and welcome text is still displayed
        wait.until(EC.url_contains("/dashboard"))
        wait.until(EC.visibility_of_element_located((By.XPATH, "//h1[contains(text(), 'Welcome')]")))
        WebDriverWait(driver, 15).until(
            lambda d: "Loading" not in d.find_element(By.XPATH, "//h1[contains(text(), 'Welcome')]").text
        )
        heading_after_refresh = driver.find_element(By.XPATH, "//h1[contains(text(), 'Welcome')]")
        assert "Persist HR" in heading_after_refresh.text

    def test_tc02_05_logout_functionality_clears_session(self, driver):
        """TC-02-05: Logout button clears tokens and redirects user back to the login page."""
        email = "test_logout_user@careerflow.test"
        password = "LogoutPassword2026!"
        create_user_in_db(email, password, role=User.Role.STUDENT, full_name="Logout User")

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

        wait.until(EC.url_contains("/dashboard"))

        # Click logout button in header
        logout_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-dashboard-logout']")))
        logout_btn.click()

        # Verify redirect to login page
        wait.until(EC.url_contains("/login"))
        assert "/login" in driver.current_url

        # Verify tokens cleared from localStorage
        access_token = driver.execute_script("return localStorage.getItem('careerflow_access_token');")
        session_data = driver.execute_script("return localStorage.getItem('careerflow-session');")
        assert access_token is None, "Access token was not cleared upon logout!"
        assert session_data is None, "Session was not cleared upon logout!"
