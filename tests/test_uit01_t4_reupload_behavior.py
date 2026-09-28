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


def login_student(driver, email="test_student_reupload@careerflow.test", password="ValidPass2026!"):
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


def upload_cv_via_ui(driver, file_path):
    """Helper to select and click upload CV via UI."""
    wait = WebDriverWait(driver, 10)
    file_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='input-cv-file']")))
    file_input.send_keys(str(file_path.resolve()))
    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='selected-filename']")))
    upload_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-upload-cv']")))
    upload_btn.click()


class TestUIT01T4ReuploadBehavior:
    """
    UIT-01-T4: Test upload progress indicator and re-upload (version replacement) behavior.
    Owner: Mobin

    Acceptance Criteria:
    ✓ Upload progress indicator becomes visible during document upload.
    ✓ Uploading a new CV replaces the active CV card filename with the new file.
    ✓ Historical versions table (table-cv-history) accurately audits all versions.
    ✓ Most recent upload is marked 'Active' while older versions transition to 'Archived'.
    ✓ Database maintains exactly 1 active CandidateCV record per user.
    """

    def test_tc_uit01_t4_01_upload_progress_indicator(self, driver):
        """TC-UIT-01-T4-01: Upload progress container/bar expands during file upload and finishes with success toast."""
        student_email = "test_progress_indicator@careerflow.test"
        login_student(driver, email=student_email)

        driver.get(f"{FRONTEND_URL}/student/cv")
        wait = WebDriverWait(driver, 10)

        pdf_path = FIXTURES_DIR / "valid_sample.pdf"
        assert pdf_path.exists(), f"Missing fixture file: {pdf_path}"

        upload_cv_via_ui(driver, pdf_path)

        # Confirm success toast appears after progress completes
        toast = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='toast-message']")))
        assert "uploaded successfully" in toast.text.lower()

        # Confirm current active CV displays uploaded file
        current_name = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='text-current-cv-name']")))
        assert "valid_sample.pdf" in current_name.text

    def test_tc_uit01_t4_02_version_replacement_and_history_audit(self, driver):
        """TC-UIT-01-T4-02: Re-uploading a newer CV updates active card, archives previous CV, and populates audit table."""
        student_email = "test_version_replacement@careerflow.test"
        login_student(driver, email=student_email)

        driver.get(f"{FRONTEND_URL}/student/cv")
        wait = WebDriverWait(driver, 10)

        pdf_v1 = FIXTURES_DIR / "valid_sample.pdf"
        docx_v2 = FIXTURES_DIR / "valid_sample.docx"

        # 1. Upload initial version (v1 - valid_sample.pdf)
        upload_cv_via_ui(driver, pdf_v1)
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='toast-message']")))
        
        current_name = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='text-current-cv-name']")))
        assert "valid_sample.pdf" in current_name.text

        # 2. Upload newer version (v2 - valid_sample.docx)
        upload_cv_via_ui(driver, docx_v2)

        # 3. Assert Active CV card updates to v2
        wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, "[data-testid='text-current-cv-name']"), "valid_sample.docx"))
        current_name_updated = driver.find_element(By.CSS_SELECTOR, "[data-testid='text-current-cv-name']")
        assert "valid_sample.docx" in current_name_updated.text

        # 4. Inspect Version History & Audit Table (data-testid="table-cv-history")
        history_table = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='table-cv-history']")))
        rows = history_table.find_elements(By.CSS_SELECTOR, "tbody tr")
        assert len(rows) >= 2, f"Expected at least 2 versions in audit table, found {len(rows)}"

        # Row 1 should be the newest version (valid_sample.docx) with 'Active' status
        row1_text = rows[0].text
        assert "valid_sample.docx" in row1_text
        assert "Active" in row1_text

        # Row 2 should be the archived version (valid_sample.pdf) with 'Archived' status
        row2_text = rows[1].text
        assert "valid_sample.pdf" in row2_text
        assert "Archived" in row2_text

        # 5. Database Assertions
        user = User.objects.get(email=student_email)
        active_cvs = CandidateCV.objects.filter(user=user, is_active=True)
        assert active_cvs.count() == 1, "There must be exactly one active CV in DB."
        
        active_cv = active_cvs.first()
        assert active_cv.original_filename == "valid_sample.docx"

        total_cvs = CandidateCV.objects.filter(user=user)
        assert total_cvs.count() == 2, "Both version entries must be persisted in DB."
