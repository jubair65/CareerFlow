import sys
import time
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


def login_student(driver, email="test_student_upload@careerflow.test", password="ValidPass2026!"):
    """Helper to log in as candidate/student."""
    create_user_in_db(email, password, role=User.Role.STUDENT, full_name="Alex Rahman")

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
    """Helper to upload a CV via the UI dropzone and await success confirmation."""
    wait = WebDriverWait(driver, 10)
    file_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='input-cv-file']")))
    file_input.send_keys(str(file_path.resolve()))
    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='selected-filename']")))
    upload_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-upload-cv']")))
    upload_btn.click()
    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='toast-message']")))


class TestUIT01T2CVUploadValid:
    """
    UIT-01-T2: Test CV upload UI with valid PDF and DOCX files.
    Owner: Jubair
    
    Acceptance Criteria:
    ✓ Valid PDF file uploads via dropzone/file input
    ✓ Valid DOCX file uploads via dropzone/file input
    ✓ Real-time success toast notification appears upon completion
    ✓ Active CV card updates with filename, Active badge, size, and document link
    ✓ Active CV state persists across page reload
    ✓ Navigation from Student Dashboard directly enters CV Studio
    """

    def test_tc_uit01_t2_01_upload_valid_pdf_ui(self, driver):
        """TC-UIT-01-T2-01: Candidate uploads a valid PDF resume and verifies Active CV card display."""
        student_email = "test_pdf_upload@careerflow.test"
        login_student(driver, email=student_email)

        # Navigate to CV Studio
        driver.get(f"{FRONTEND_URL}/student/cv")
        wait = WebDriverWait(driver, 10)

        # Verify page heading
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='page-title']")))

        pdf_path = FIXTURES_DIR / "valid_sample.pdf"
        assert pdf_path.exists(), f"Missing fixture file: {pdf_path}"

        upload_cv_via_ui(driver, pdf_path)

        # Verify Active CV card displays updated metadata
        current_cv_name = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='text-current-cv-name']")))
        assert "valid_sample.pdf" in current_cv_name.text

        # Verify document download/view link exists
        view_link = driver.find_element(By.CSS_SELECTOR, "[data-testid='link-download-cv']")
        assert view_link.is_displayed()
        assert view_link.get_attribute("href") is not None

        # Verify database record
        user = User.objects.get(email=student_email)
        active_cv = CandidateCV.objects.filter(user=user, is_active=True).first()
        assert active_cv is not None
        assert active_cv.original_filename == "valid_sample.pdf"
        assert active_cv.file_type == "pdf"

    def test_tc_uit01_t2_02_upload_valid_docx_ui(self, driver):
        """TC-UIT-01-T2-02: Candidate uploads a valid DOCX resume and verifies Active CV card updates to DOCX."""
        student_email = "test_docx_upload@careerflow.test"
        login_student(driver, email=student_email)

        driver.get(f"{FRONTEND_URL}/student/cv")
        wait = WebDriverWait(driver, 10)

        docx_path = FIXTURES_DIR / "valid_sample.docx"
        assert docx_path.exists(), f"Missing fixture file: {docx_path}"

        upload_cv_via_ui(driver, docx_path)

        # Verify active card updates to DOCX
        current_cv_name = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='text-current-cv-name']")))
        assert "valid_sample.docx" in current_cv_name.text

        # Verify database record
        user = User.objects.get(email=student_email)
        active_cv = CandidateCV.objects.filter(user=user, is_active=True).first()
        assert active_cv is not None
        assert active_cv.original_filename == "valid_sample.docx"
        assert active_cv.file_type == "docx"

    def test_tc_uit01_t2_03_active_cv_persists_on_page_reload(self, driver):
        """TC-UIT-01-T2-03: Active CV details persist and reload properly on refresh."""
        student_email = "test_cv_persist@careerflow.test"
        login_student(driver, email=student_email)

        # Upload a CV first via UI
        driver.get(f"{FRONTEND_URL}/student/cv")
        wait = WebDriverWait(driver, 10)
        upload_cv_via_ui(driver, FIXTURES_DIR / "valid_sample.pdf")

        # Reload the page
        driver.refresh()

        # Assert Active CV is still displayed immediately without error
        current_name = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='text-current-cv-name']")))
        assert "valid_sample.pdf" in current_name.text

        # Assert Analyze CV button is active
        analyze_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-view-cv-suggestions']")
        assert analyze_btn.is_enabled()

    def test_tc_uit01_t2_04_dashboard_navigation_to_cv_studio(self, driver):
        """TC-UIT-01-T2-04: Student dashboard action card and sidebar directly navigate to CV Studio."""
        student_email = "test_nav_cv@careerflow.test"
        login_student(driver, email=student_email)

        wait = WebDriverWait(driver, 10)

        # 1. Test clicking "Review your CV suggestions" action card on dashboard
        cv_action_card = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='action-review-cv']")))
        cv_action_card.click()

        wait.until(EC.url_contains("/student/cv"))
        assert "/student/cv" in driver.current_url
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='text-current-cv-name'], [data-testid='empty-cv-state']")))

        # 2. Test clicking sidebar "CV studio" link
        sidebar_link = driver.find_element(By.CSS_SELECTOR, "[data-testid='nav-cv-studio']")
        sidebar_link.click()
        assert "/student/cv" in driver.current_url
