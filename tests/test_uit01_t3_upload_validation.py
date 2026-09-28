import sys
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from apps.authentication.models import User
from apps.cv.models import CandidateCV
from conftest import FRONTEND_URL, create_user_in_db

FIXTURES_DIR = TESTS_DIR / "fixtures" / "cv"


def login_student(driver, email="test_student_validation@careerflow.test", password="ValidPass2026!"):
    """Helper to log in as candidate/student."""
    create_user_in_db(email, password, role=User.Role.STUDENT, full_name="Mobin QA Tester")

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

    wait.until(EC.url_contains("/student/dashboard"))


class TestUIT01T3CVUploadValidation:
    """
    UIT-01-T3: Test CV upload UI validation for unsupported format & oversized file.
    Owner: Mobin

    Acceptance Criteria:
    ✓ Invalid File Type (.png, .txt, .exe) triggers error message and disables upload button.
    ✓ Oversized File (> 10 MB) triggers error message ('File size exceeds 10 MB limit') and disables upload button.
    ✓ DB remains clean without invalid/oversized file entries.
    ✓ Validation error clears when a valid file (.pdf / .docx) is subsequently selected.
    """

    def test_tc_uit01_t3_01_unsupported_file_format_rejection(self, driver):
        """TC-UIT-01-T3-01: Candidate selects unsupported format (.png) -> error banner displays and upload is blocked."""
        student_email = "test_unsupported_format@careerflow.test"
        login_student(driver, email=student_email)

        driver.get(f"{FRONTEND_URL}/student/cv")
        wait = WebDriverWait(driver, 10)

        unsupported_file = FIXTURES_DIR / "unsupported_format.png"
        assert unsupported_file.exists(), f"Missing fixture file: {unsupported_file}"

        file_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='input-cv-file']")))
        file_input.send_keys(str(unsupported_file.resolve()))

        # Verify validation error banner appears
        error_banner = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='upload-error-message']")))
        assert "Unsupported file format" in error_banner.text
        assert ".png" in error_banner.text

        # Verify upload button is disabled
        upload_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-upload-cv']")
        assert not upload_btn.is_enabled() or upload_btn.get_attribute("disabled") is not None

        # Verify database has no active CV records for this user
        user = User.objects.get(email=student_email)
        cv_count = CandidateCV.objects.filter(user=user).count()
        assert cv_count == 0

    def test_tc_uit01_t3_02_oversized_file_rejection(self, driver):
        """TC-UIT-01-T3-02: Candidate selects file exceeding 10MB limit -> error banner displays and upload is blocked."""
        student_email = "test_oversized_file@careerflow.test"
        login_student(driver, email=student_email)

        driver.get(f"{FRONTEND_URL}/student/cv")
        wait = WebDriverWait(driver, 10)

        oversized_file = FIXTURES_DIR / "oversized_sample.pdf"
        assert oversized_file.exists(), f"Missing fixture file: {oversized_file}"

        file_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='input-cv-file']")))
        file_input.send_keys(str(oversized_file.resolve()))

        # Verify validation error banner displays size limit message
        error_banner = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='upload-error-message']")))
        assert "exceeds 10 MB limit" in error_banner.text

        # Verify upload button is disabled
        upload_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-upload-cv']")
        assert not upload_btn.is_enabled() or upload_btn.get_attribute("disabled") is not None

        # Verify database remains untouched
        user = User.objects.get(email=student_email)
        cv_count = CandidateCV.objects.filter(user=user).count()
        assert cv_count == 0

    def test_tc_uit01_t3_03_validation_error_clears_on_valid_file_select(self, driver):
        """TC-UIT-01-T3-03: Selection of invalid file followed by valid PDF clears validation error and enables upload."""
        student_email = "test_validation_recovery@careerflow.test"
        login_student(driver, email=student_email)

        driver.get(f"{FRONTEND_URL}/student/cv")
        wait = WebDriverWait(driver, 10)

        unsupported_file = FIXTURES_DIR / "unsupported_format.png"
        valid_file = FIXTURES_DIR / "valid_sample.pdf"

        file_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='input-cv-file']")))
        
        # 1. Trigger error
        file_input.send_keys(str(unsupported_file.resolve()))
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='upload-error-message']")))

        # 2. Select valid file
        file_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-cv-file']")
        file_input.send_keys(str(valid_file.resolve()))

        # 3. Assert error banner disappears or is cleared
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='upload-error-message']")))

        # 4. Verify upload button is now enabled
        upload_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-upload-cv']")))
        assert upload_btn.is_enabled()
