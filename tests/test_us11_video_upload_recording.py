import os
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
from apps.presentation.models import PresentationVideo
from conftest import FRONTEND_URL, create_user_in_db

FIXTURES_DIR = TESTS_DIR / "fixtures" / "video"


def login_student(driver, email="student_video_test@careerflow.test", password="ValidPass2026!"):
    """Helper to register/ensure student exists and log in via UI."""
    create_user_in_db(email, password, role=User.Role.STUDENT, full_name="Video Candidate")

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


class TestUS11VideoUploadRecording:
    """
    US-11: Video Upload & Recording UI Automation Tests
    Task: US-11-T6
    Owner: MD. Jubair Bin Hasan (Software Developer)

    Acceptance Criteria Verified:
    ✓ UI supports switching between Webcam Recording and File Upload tabs
    ✓ Displays 250MB maximum upload capacity with auto-compression badge
    ✓ Valid MP4 presentation video uploads via UI and renders active video card
    ✓ Re-uploading a new take deactivates previous video and archives it in take history
    ✓ Client-side validation protects against unsupported file formats
    """

    def test_tc_us11_t6_01_navigation_and_ui_layout(self, driver):
        """TC-US11-T6-01: Verify navigation to Presentation Studio, tabs and 250MB banner."""
        login_student(driver, email="student_nav_test@careerflow.test")
        driver.get(f"{FRONTEND_URL}/student/presentation")

        wait = WebDriverWait(driver, 10)
        # Check tabs exist
        rec_tab = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='tab-record-webcam']")))
        upload_tab = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='tab-upload-file']")))
        assert rec_tab is not None
        assert upload_tab is not None

        # Verify 250MB support banner and FFmpeg badge
        body_text = driver.find_element(By.TAG_NAME, "body").text
        assert "250 MB" in body_text
        assert "FFmpeg" in body_text

    def test_tc_us11_t6_02_upload_valid_mp4_video(self, driver):
        """TC-US11-T6-02: Upload an MP4 presentation video through the upload dropzone."""
        test_email = "student_upload_ui@careerflow.test"
        login_student(driver, email=test_email)
        driver.get(f"{FRONTEND_URL}/student/presentation")

        wait = WebDriverWait(driver, 10)

        # Switch to upload file tab
        upload_tab = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='tab-upload-file']")))
        upload_tab.click()

        # Send sample mp4 to hidden file input
        file_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='input-video-file']")))
        mp4_fixture = FIXTURES_DIR / "sample_pitch.mp4"
        file_input.send_keys(str(mp4_fixture.resolve()))

        submit_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='button-upload-file-submit']")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_btn)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", submit_btn)

        # Await active video card
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='active-video-player']")))
        status_badge = driver.find_element(By.CSS_SELECTOR, "[data-testid='badge-video-status']")
        assert "READY FOR ANALYSIS" in status_badge.text or "COMPLETED" in status_badge.text

        # Verify in database
        user = User.objects.get(email=test_email)
        active_video = PresentationVideo.objects.get(user=user, is_active=True)
        assert active_video.original_filename == "sample_pitch.mp4"
        assert active_video.file_type == "mp4"

    def test_tc_us11_t6_03_reupload_take_replacement(self, driver):
        """TC-US11-T6-03: Uploading a 2nd take sets it as active and pushes 1st take into history."""
        test_email = "student_reupload_ui@careerflow.test"
        login_student(driver, email=test_email)
        driver.get(f"{FRONTEND_URL}/student/presentation")

        wait = WebDriverWait(driver, 10)

        # First take upload
        upload_tab = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='tab-upload-file']")))
        upload_tab.click()

        file_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='input-video-file']")))
        file_input.send_keys(str((FIXTURES_DIR / "sample_pitch.mp4").resolve()))
        submit_1 = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='button-upload-file-submit']")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_1)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", submit_1)
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='active-video-player']")))

        # Click record/upload new take button
        new_take_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='button-record-new-take']")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", new_take_btn)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", new_take_btn)

        # Switch to upload tab for second take
        upload_tab_2 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='tab-upload-file']")))
        driver.execute_script("arguments[0].click();", upload_tab_2)

        file_input_2 = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='input-video-file']")))
        file_input_2.send_keys(str((FIXTURES_DIR / "sample_take.webm").resolve()))
        submit_2 = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='button-upload-file-submit']")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_2)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", submit_2)

        # Wait for new active video
        time.sleep(1)
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='active-video-player']")))

        # Check database records
        user = User.objects.get(email=test_email)
        videos = PresentationVideo.objects.filter(user=user).order_by('uploaded_at')
        assert videos.count() == 2
        assert videos[0].is_active is False
        assert videos[1].is_active is True
        assert videos[1].original_filename == "sample_take.webm"

    def test_tc_us11_t6_04_unsupported_format_client_rejection(self, driver):
        """TC-US11-T6-04: Non-video file formats trigger client-side validation error banner."""
        test_email = "student_badfmt_ui@careerflow.test"
        login_student(driver, email=test_email)
        driver.get(f"{FRONTEND_URL}/student/presentation")

        wait = WebDriverWait(driver, 10)

        # Switch to upload tab
        upload_tab = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='tab-upload-file']")))
        upload_tab.click()

        # Create temporary invalid file
        invalid_file = FIXTURES_DIR / "invalid_resume.pdf"
        if not invalid_file.exists():
            with open(invalid_file, "w") as f:
                f.write("Dummy PDF content")

        file_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='input-video-file']")))
        file_input.send_keys(str(invalid_file.resolve()))

        # Check error banner appears
        error_banner = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='upload-error-banner']")))
        assert "Unsupported video format" in error_banner.text
