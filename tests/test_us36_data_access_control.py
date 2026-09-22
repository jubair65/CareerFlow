import sys
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

import os
import pytest
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from django.conf import settings
from apps.authentication.models import User
from apps.core.models import DataAccessLog
from conftest import FRONTEND_URL, BACKEND_URL, create_user_in_db, setup_test_media_files


def get_jwt_token(email, password):
    resp = requests.post(f"{BACKEND_URL}/api/auth/login/", json={"email": email, "password": password})
    assert resp.status_code == 200, f"Login failed for {email}"
    return resp.json()["access"]


class TestUS36DataAccessControl:
    """
    US-36: Data Access Control
    Acceptance Criteria:
    ✓ Only authorized users can access files
    ✓ Only authorized users can access candidate information
    ✓ File permissions are enforced at system level
    ✓ User data isolation is verified
    ✓ Access logs are maintained for audit
    """

    @pytest.fixture(autouse=True)
    def setup_files(self):
        """Prepare test candidate files in backend/media."""
        media_root = setup_test_media_files()

        # Seed Student A and Student B
        self.student_a = create_user_in_db("test_student_a@careerflow.test", "PassA2026!", role=User.Role.STUDENT, full_name="Student A")
        self.student_b = create_user_in_db("test_student_b@careerflow.test", "PassB2026!", role=User.Role.STUDENT, full_name="Student B")
        self.hr_user = create_user_in_db("test_hr_data@careerflow.test", "PassHR2026!", role=User.Role.HR_MANAGER, full_name="HR Reviewer")
        self.agency_user = create_user_in_db("test_agency_data@careerflow.test", "PassAgency2026!", role=User.Role.AGENCY_ADMIN, full_name="Agency Reviewer")

        # Create dummy candidate files
        self.file_dir_a = media_root / "students" / str(self.student_a.id)
        self.file_dir_a.mkdir(parents=True, exist_ok=True)
        self.file_a_path = self.file_dir_a / "resume.pdf"
        self.file_a_path.write_bytes(b"%PDF-1.4 Mock CV Candidate A content")

        self.file_dir_b = media_root / "students" / str(self.student_b.id)
        self.file_dir_b.mkdir(parents=True, exist_ok=True)
        self.file_b_path = self.file_dir_b / "resume.pdf"
        self.file_b_path.write_bytes(b"%PDF-1.4 Mock CV Candidate B content")

        # Clean prior logs for these test users
        DataAccessLog.objects.filter(user__in=[self.student_a, self.student_b, self.hr_user, self.agency_user]).delete()

    def test_tc36_01_student_can_access_own_cv_file(self):
        """TC-36-01: Candidate is GRANTED access to download their own CV file (HTTP 200)."""
        token = get_jwt_token(self.student_a.email, "PassA2026!")
        headers = {"Authorization": f"Bearer {token}"}
        url = f"{BACKEND_URL}/api/core/files/students/{self.student_a.id}/resume.pdf"

        resp = requests.get(url, headers=headers)
        assert resp.status_code == 200, f"Expected 200 OK for own file, got {resp.status_code}"
        assert b"Candidate A" in resp.content

    def test_tc36_02_student_data_isolation_cross_access_blocked(self):
        """TC-36-02: Student A attempting to access Student B's CV is DENIED with HTTP 403 Forbidden."""
        token_a = get_jwt_token(self.student_a.email, "PassA2026!")
        headers = {"Authorization": f"Bearer {token_a}"}
        # Student A tries to read Student B's CV
        url = f"{BACKEND_URL}/api/core/files/students/{self.student_b.id}/resume.pdf"

        resp = requests.get(url, headers=headers)
        assert resp.status_code == 403, f"Expected 403 Forbidden for cross-access, got {resp.status_code}"
        assert "Access denied" in resp.json().get("error", "")

    def test_tc36_03_hr_and_agency_can_access_candidate_information(self):
        """TC-36-03: HR Manager and Agency Admin roles are authorized to access any candidate files (HTTP 200)."""
        token_hr = get_jwt_token(self.hr_user.email, "PassHR2026!")
        token_agency = get_jwt_token(self.agency_user.email, "PassAgency2026!")

        # HR accesses Student A file
        resp_hr = requests.get(
            f"{BACKEND_URL}/api/core/files/students/{self.student_a.id}/resume.pdf",
            headers={"Authorization": f"Bearer {token_hr}"}
        )
        assert resp_hr.status_code == 200, f"HR Manager should access candidate file, got {resp_hr.status_code}"

        # Agency Admin accesses Student B file
        resp_agency = requests.get(
            f"{BACKEND_URL}/api/core/files/students/{self.student_b.id}/resume.pdf",
            headers={"Authorization": f"Bearer {token_agency}"}
        )
        assert resp_agency.status_code == 200, f"Agency Admin should access candidate file, got {resp_agency.status_code}"

    def test_tc36_04_access_logs_maintained_for_audit(self):
        """TC-36-04: System logs all access attempts (GRANTED and DENIED) in careerflow_data_access_logs."""
        # 1. Trigger granted access
        token_a = get_jwt_token(self.student_a.email, "PassA2026!")
        requests.get(
            f"{BACKEND_URL}/api/core/files/students/{self.student_a.id}/resume.pdf",
            headers={"Authorization": f"Bearer {token_a}"}
        )

        # 2. Trigger denied access
        requests.get(
            f"{BACKEND_URL}/api/core/files/students/{self.student_b.id}/resume.pdf",
            headers={"Authorization": f"Bearer {token_a}"}
        )

        # Query database audit logs
        granted_log = DataAccessLog.objects.filter(
            user=self.student_a,
            status=DataAccessLog.Status.GRANTED,
            resource_path=f"students/{self.student_a.id}/resume.pdf"
        ).first()

        denied_log = DataAccessLog.objects.filter(
            user=self.student_a,
            status=DataAccessLog.Status.DENIED,
            resource_path=f"students/{self.student_b.id}/resume.pdf"
        ).first()

        assert granted_log is not None, "GRANTED audit log was not recorded!"
        assert denied_log is not None, "DENIED audit log was not recorded!"
        assert granted_log.action == DataAccessLog.Action.DOWNLOAD
        assert granted_log.timestamp is not None

    def test_tc36_05_path_traversal_attempts_prevented(self):
        """TC-36-05: Path traversal attack (using ../) outside MEDIA_ROOT is rejected."""
        token_hr = get_jwt_token(self.hr_user.email, "PassHR2026!")
        headers = {"Authorization": f"Bearer {token_hr}"}

        # Attempt to access outside MEDIA_ROOT
        traversal_url = f"{BACKEND_URL}/api/core/files/../../careerflow/settings.py"
        resp = requests.get(traversal_url, headers=headers)

        # Must return 400 Bad Request or 404 Not Found, never 200
        assert resp.status_code in [400, 404], f"Path traversal should be rejected, got {resp.status_code}"

    def test_tc36_06_dashboard_displays_data_access_control_card(self, driver):
        """TC-36-06: Selenium UI test verifying the Data Access Control & Audit card is rendered on Dashboard."""
        driver.get(f"{FRONTEND_URL}/login")

        wait = WebDriverWait(driver, 10)
        email_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-login-email']")))
        pass_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-login-password']")
        submit_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-login']")

        email_input.clear()
        email_input.send_keys(self.student_a.email)
        pass_input.clear()
        pass_input.send_keys("PassA2026!")
        submit_btn.click()

        wait.until(EC.url_contains("/dashboard"))

        # Verify Data Access Control & Security Auditing card
        card_header = wait.until(EC.visibility_of_element_located((
            By.XPATH, "//*[contains(text(), 'Data Access Control & Security Auditing (US-36)')]"
        )))
        assert card_header is not None
        assert "Active" in driver.page_source
