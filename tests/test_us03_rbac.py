import sys
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

import pytest
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from apps.authentication.models import User
from conftest import FRONTEND_URL, BACKEND_URL, create_user_in_db


class TestUS03RoleBasedAccessControl:
    """
    US-03: Role-Based Access Control (RBAC)
    Acceptance Criteria:
    ✓ System defines Student, HR Manager, and Agency Admin roles
    ✓ Each role has specific permissions
    ✓ Student users receive Student-specific permissions
    ✓ HR Manager users receive HR-specific permissions
    ✓ Agency Admin users receive Agency-specific permissions
    ✓ Unauthorized access attempts are blocked
    ✓ Role assignments are stored in database
    """

    def test_tc03_01_student_role_and_restricted_access(self, driver):
        """TC-03-01: Student logs in, sees Student role badge, and is BLOCKED (403) from HR/Admin audit logs."""
        email = "test_rbac_student@careerflow.test"
        password = "StudentPass2026!"
        user = create_user_in_db(email, password, role=User.Role.STUDENT, full_name="Student Alex")

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
        wait.until(lambda d: "Loading" not in d.find_element(By.TAG_NAME, "h1").text)

        # Verify Student role badge displayed on dashboard
        role_badge = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='user-role-badge']")))
        assert "student" in role_badge.text.lower()

        # Verify token in browser
        token = driver.execute_script("return localStorage.getItem('careerflow_access_token');")
        assert token is not None

        # Attempt to access HR/Admin audit logs endpoint with Student token -> MUST return 403 Forbidden
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(f"{BACKEND_URL}/api/core/audit-logs/", headers=headers)
        assert resp.status_code == 403, f"Expected 403 Forbidden for Student accessing audit logs, got {resp.status_code}"
        assert "Access denied" in resp.json().get("error", "")

    def test_tc03_02_hr_manager_role_and_privileged_access(self, driver):
        """TC-03-02: HR Manager logs in, sees HR role, and is GRANTED (200) access to audit logs."""
        email = "test_rbac_hr@careerflow.test"
        password = "HRManagerPass2026!"
        user = create_user_in_db(email, password, role=User.Role.HR_MANAGER, full_name="HR Manager Sarah")

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
        wait.until(lambda d: "Loading" not in d.find_element(By.TAG_NAME, "h1").text)

        # Verify HR role displayed
        role_badge = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='user-role-badge']")))
        assert "hr" in role_badge.text.lower()

        token = driver.execute_script("return localStorage.getItem('careerflow_access_token');")
        assert token is not None

        # Access privileged audit logs endpoint -> MUST return 200 OK
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(f"{BACKEND_URL}/api/core/audit-logs/", headers=headers)
        assert resp.status_code == 200, f"Expected 200 OK for HR Manager, got {resp.status_code}"
        assert "total_logs" in resp.json()

    def test_tc03_03_agency_admin_role_and_privileged_access(self, driver):
        """TC-03-03: Agency Admin logs in, sees Agency role, and is GRANTED (200) access to audit logs."""
        email = "test_rbac_agency@careerflow.test"
        password = "AgencyPass2026!"
        user = create_user_in_db(email, password, role=User.Role.AGENCY_ADMIN, full_name="Agency Admin Davis")

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
        wait.until(lambda d: "Loading" not in d.find_element(By.TAG_NAME, "h1").text)

        # Verify Agency role displayed
        role_badge = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='user-role-badge']")))
        assert "agency" in role_badge.text.lower()

        token = driver.execute_script("return localStorage.getItem('careerflow_access_token');")
        assert token is not None

        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(f"{BACKEND_URL}/api/core/audit-logs/", headers=headers)
        assert resp.status_code == 200, f"Expected 200 OK for Agency Admin, got {resp.status_code}"
        assert "total_logs" in resp.json()

    def test_tc03_04_role_assignments_persisted_in_database(self):
        """TC-03-04: Verify role definitions and assignments are properly stored in MySQL database."""
        # Check standard defined choices
        valid_roles = [choice[0] for choice in User.Role.choices]
        assert 'STUDENT' in valid_roles
        assert 'HR_MANAGER' in valid_roles
        assert 'AGENCY_ADMIN' in valid_roles

        # Seed one of each
        u_student = create_user_in_db("test_db_student@careerflow.test", "Pass123!", role=User.Role.STUDENT)
        u_hr = create_user_in_db("test_db_hr@careerflow.test", "Pass123!", role=User.Role.HR_MANAGER)
        u_agency = create_user_in_db("test_db_agency@careerflow.test", "Pass123!", role=User.Role.AGENCY_ADMIN)

        # Query database directly
        db_student = User.objects.get(id=u_student.id)
        db_hr = User.objects.get(id=u_hr.id)
        db_agency = User.objects.get(id=u_agency.id)

        assert db_student.role == 'STUDENT'
        assert db_hr.role == 'HR_MANAGER'
        assert db_agency.role == 'AGENCY_ADMIN'

    def test_tc03_05_unauthenticated_requests_blocked(self):
        """TC-03-05: Anonymous unauthenticated requests to protected endpoints return 401 Unauthorized."""
        resp = requests.get(f"{BACKEND_URL}/api/core/audit-logs/")
        assert resp.status_code == 401, f"Expected 401 Unauthorized for anonymous request, got {resp.status_code}"

        resp_me = requests.get(f"{BACKEND_URL}/api/auth/me/")
        assert resp_me.status_code == 401, f"Expected 401 Unauthorized for /api/auth/me/, got {resp_me.status_code}"
