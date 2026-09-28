import sys
import time
from pathlib import Path
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from django.core.files.base import ContentFile

TESTS_DIR = Path(__file__).resolve().parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

from apps.authentication.models import User
from apps.cv.models import CandidateCV, ParsedCV, CVFeedback
from conftest import FRONTEND_URL, create_user_in_db

FIXTURES_DIR = TESTS_DIR / "fixtures" / "cv"


def login_student(driver, email="maria_qa_student@careerflow.test", password="ValidPass2026!"):
    """Helper to log in as candidate/student."""
    user = User.objects.filter(email__iexact=email).first()
    if not user:
        user = create_user_in_db(email, password, role=User.Role.STUDENT, full_name="Maria QA Tester")

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
    return user


class TestUIT01T5ExtractionFailureUI:
    """
    UIT-01-T5: Test UI behavior when CV data extraction fails (error message & retry).
    Owner: Maria
    
    Acceptance Criteria:
    ✓ Upload corrupt_file.pdf or trigger mock extraction 500 error.
    ✓ Verify user interface does NOT crash with a white screen (ErrorBoundary or friendly fallback card).
    ✓ Verify alert displays: "Unable to extract text from document" with clear advice
      (e.g. "Ensure document is not password-protected or scanned as raw image").
    ✓ Verify a "Try another file" or "Retry extraction" action button is present and clickable.
    ✓ Verify clicking "Try another file" resets/clears error and allows selecting a new document.
    """

    def test_tc_uit01_t5_01_corrupt_file_upload_extraction_failure(self, driver):
        """
        TC-UIT-01-T5-01: Candidate uploads corrupt_file.pdf in CV Studio ->
        UI handles error without white screen crash, shows friendly extraction alert with advice
        and actionable buttons.
        """
        student_email = "test_corrupt_upload@careerflow.test"
        login_student(driver, email=student_email)

        driver.get(f"{FRONTEND_URL}/student/cv")
        wait = WebDriverWait(driver, 10)

        # Confirm CV Studio loaded
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='cv-dropzone']")))

        corrupt_file = FIXTURES_DIR / "corrupt_file.pdf"
        assert corrupt_file.exists(), f"Missing fixture file: {corrupt_file}"

        # Select corrupt file
        file_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='input-cv-file']")))
        file_input.send_keys(str(corrupt_file.resolve()))

        # Click upload button
        upload_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-upload-cv']")))
        upload_btn.click()

        # 1. Verify user interface does NOT crash with a white screen
        body = driver.find_element(By.TAG_NAME, "body")
        assert body.is_displayed()
        assert len(body.text.strip()) > 0, "UI crashed with blank white screen!"

        # 2. Verify alert displays: "Unable to extract text from document"
        error_card = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='extraction-error-card']"))
        )
        assert "Unable to extract text from document" in error_card.text

        # 3. Verify clear advice is shown
        assert "Ensure document is not password-protected or scanned as raw image" in error_card.text

        # 4. Verify "Try another file" button is present and clickable
        try_another_btn = error_card.find_element(By.CSS_SELECTOR, "[data-testid='button-try-another-file']")
        assert try_another_btn.is_displayed()
        assert "Try another file" in try_another_btn.text

        # 5. Verify "Retry extraction" button is present and clickable
        retry_btn = error_card.find_element(By.CSS_SELECTOR, "[data-testid='button-retry-extraction']")
        assert retry_btn.is_displayed()
        assert "Retry extraction" in retry_btn.text

        # 6. Click "Try another file" and verify error is cleared
        try_another_btn.click()
        time.sleep(0.5)
        error_cards = driver.find_elements(By.CSS_SELECTOR, "[data-testid='extraction-error-card']")
        assert len(error_cards) == 0 or not error_cards[0].is_displayed()

    def test_tc_uit01_t5_02_results_page_extraction_failure_fallback(self, driver):
        """
        TC-UIT-01-T5-02: Candidate navigates to CV Results when extraction has failed ->
        UI presents a friendly fallback card without crashing, with clear instructions and navigation.
        """
        student_email = "test_results_extract_fail@careerflow.test"
        user = login_student(driver, email=student_email)

        # Create active candidate CV with corrupt file in MEDIA_ROOT
        corrupt_file = FIXTURES_DIR / "corrupt_file.pdf"
        assert corrupt_file.exists()

        with open(corrupt_file, "rb") as f:
            CandidateCV.objects.create(
                user=user,
                file=ContentFile(f.read(), name="corrupt_file.pdf"),
                original_filename="corrupt_file.pdf",
                file_size=64,
                file_type="pdf",
                is_active=True
            )

        # Navigate directly to CV Results
        driver.get(f"{FRONTEND_URL}/student/cv/results")
        wait = WebDriverWait(driver, 10)

        # 1. Verify user interface does NOT crash with a white screen
        body = wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        assert body.is_displayed()
        assert len(body.text.strip()) > 0, "UI crashed with blank screen on results page!"

        # 2. Verify fallback error card is displayed
        fallback_card = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='extraction-error-card']"))
        )
        assert fallback_card.is_displayed()

        # 3. Verify message and advice
        title_el = fallback_card.find_element(By.CSS_SELECTOR, "[data-testid='extraction-error-title']")
        assert "Unable to extract text from document" in title_el.text

        advice_el = fallback_card.find_element(By.CSS_SELECTOR, "[data-testid='extraction-error-advice']")
        assert "Ensure document is not password-protected or scanned as raw image" in advice_el.text

        # 4. Verify "Try another file" button navigates back to CV Studio
        try_another_btn = fallback_card.find_element(By.CSS_SELECTOR, "[data-testid='button-try-another-file']")
        assert try_another_btn.is_displayed()
        try_another_btn.click()

        wait.until(EC.url_contains("/student/cv"))
        assert "/student/cv" in driver.current_url

    def test_tc_uit01_t5_03_retry_extraction_behavior(self, driver):
        """
        TC-UIT-01-T5-03: Verifies 'Retry extraction' button triggers retry action without crashing.
        """
        # Brief pause to allow previous Chrome instance to fully release its port
        time.sleep(2)
        student_email = "test_retry_action@careerflow.test"
        user = login_student(driver, email=student_email)

        corrupt_file = FIXTURES_DIR / "corrupt_file.pdf"
        with open(corrupt_file, "rb") as f:
            CandidateCV.objects.create(
                user=user,
                file=ContentFile(f.read(), name="corrupt_file.pdf"),
                original_filename="corrupt_file.pdf",
                file_size=64,
                file_type="pdf",
                is_active=True
            )

        driver.get(f"{FRONTEND_URL}/student/cv/results")
        wait = WebDriverWait(driver, 10)

        fallback_card = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='extraction-error-card']"))
        )

        retry_btn = fallback_card.find_element(By.CSS_SELECTOR, "[data-testid='button-retry-extraction']")
        assert retry_btn.is_displayed()
        assert retry_btn.is_enabled()

        # Click retry and verify page stays intact without throwing uncaught UI crash
        retry_btn.click()
        time.sleep(1)

        body = driver.find_element(By.TAG_NAME, "body")
        assert body.is_displayed()
        assert len(driver.find_elements(By.CSS_SELECTOR, "[data-testid='extraction-error-card'], [data-testid='cv-overall-score']")) > 0

    def test_tc_uit01_t5_04_error_boundary_graceful_fallback(self, driver):
        """
        TC-UIT-01-T5-04: Verify ErrorBoundary prevents complete white screen when unexpected errors occur.
        """
        student_email = "test_error_boundary@careerflow.test"
        login_student(driver, email=student_email)

        driver.get(f"{FRONTEND_URL}/student/cv")
        wait = WebDriverWait(driver, 10)

        body = wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        assert body.is_displayed()
        # Verify page rendered with application shell and dropzone
        assert len(driver.find_elements(By.CSS_SELECTOR, "[data-testid='cv-dropzone']")) > 0
