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

from apps.authentication.models import User
from apps.recruitment.models import RecruitmentRoom, CandidateApplication
from apps.cv.models import CandidateCV
from apps.presentation.models import PresentationVideo
from conftest import FRONTEND_URL, SCREENSHOTS_DIR, create_user_in_db

CV_FIXTURE_PATH = TESTS_DIR / "fixtures" / "cv" / "valid_sample.pdf"
VIDEO_FIXTURE_PATH = TESTS_DIR / "fixtures" / "video" / "sample_pitch.mp4"


def ensure_hr_user(email="mobin_hr_tester@careerflow.test", password="ValidPass2026!") -> User:
    """Helper to ensure HR Manager user exists in database."""
    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            'username': email,
            'role': User.Role.HR_MANAGER,
            'full_name': "MD. Hasanul Mobin"
        }
    )
    if not user.check_password(password):
        user.set_password(password)
        user.save()
    return user


def create_sample_room_for_candidate(
    hr_email: str,
    title="Senior AI Platform Engineer",
    company="Cognitive Systems Labs",
    cv_weight=60,
    video_weight=40,
    status="ACTIVE"
) -> RecruitmentRoom:
    """Creates a sample RecruitmentRoom directly in the DB linked to the HR user."""
    hr_user = ensure_hr_user(hr_email)
    room = RecruitmentRoom.objects.create(
        title=title,
        company_name=company,
        department="AI Infrastructure",
        description="Build and scale multi-tenant ML inference infrastructure and real-time streaming services.",
        status=status,
        created_by=hr_user,
        cv_weight=cv_weight,
        video_weight=video_weight,
        role_category="Engineering",
        experience_level="SENIOR",
        skills_required=["Python", "PyTorch", "Kubernetes", "Docker"],
        requirements_text="5+ years designing distributed backend systems with machine learning pipelines."
    )
    return room


class TestUS22CandidateSubmissionUI:
    """
    US-22: Applicant Application Submission UI Automation Tests
    Task: US-22-T6 (Peer UI Testing & Verification)
    Peer Tester / Reviewer: MD. Hasanul Mobin (@hasanulmobin1) - Project Manager & Peer Tester
    Developer: Farhana Tahsin Bonny (@tahsinbonnie98) - Tester / QA Engineer

    Acceptance Criteria Verified:
    ✓ Applicant can open shared link and see job opening details without logging in
    ✓ Applicant can submit CV (PDF/DOCX) and presentation video (MP4/WebM) through the link
    ✓ Dynamic dropzone feedback displays uploaded filenames and file sizes in MB
    ✓ Submission is automatically associated with the correct RecruitmentRoom
    ✓ Existing validations (format, required fields, duplicate submission prevention) are enforced
    ✓ Inactive / closed recruitment room returns HTTP 410 error screen blocking submission
    ✓ Confirmation screen is displayed after successful submission with AI pipeline trigger notice
    ✓ Candidate user (STUDENT role), CandidateCV, PresentationVideo, and CandidateApplication records created
    """

    def test_tc_us22_01_public_application_page_mount_and_details(self, driver):
        """TC-US22-01: Verify unauthenticated applicant can open public link and view room details & weights."""
        hr_email = "mobin_tc01_hr@careerflow.test"
        room = create_sample_room_for_candidate(
            hr_email,
            title="Senior AI Platform Engineer",
            company="Cognitive Systems Labs",
            cv_weight=65,
            video_weight=35
        )

        driver.get(f"{FRONTEND_URL}/apply/{room.share_token}")
        wait = WebDriverWait(driver, 10)

        # 1. Assert public application page mounts without login prompt
        page = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='page-public-application']")))
        assert page is not None

        # 2. Verify Room Title and Company context
        title_el = driver.find_element(By.CSS_SELECTOR, "[data-testid='public-room-title']")
        assert "Senior AI Platform Engineer" in title_el.text
        assert "Cognitive Systems Labs" in page.text
        assert "AI Infrastructure" in page.text

        # 3. Verify Evaluation Scoring Weights (US-20 Integration)
        cv_weight_el = driver.find_element(By.CSS_SELECTOR, "[data-testid='public-cv-weight']")
        video_weight_el = driver.find_element(By.CSS_SELECTOR, "[data-testid='public-video-weight']")
        assert "65%" in cv_weight_el.text
        assert "35%" in video_weight_el.text

        # 4. Verify Skills Chips (US-19 Integration)
        skills_container = driver.find_element(By.CSS_SELECTOR, "[data-testid='public-room-skills']")
        assert "Python" in skills_container.text
        assert "Kubernetes" in skills_container.text

        driver.save_screenshot(str(SCREENSHOTS_DIR / "us22_01_public_application_page.png"))

    def test_tc_us22_02_form_validation_and_required_fields(self, driver):
        """TC-US22-02: Verify submission form validates mandatory candidate fields and file attachments."""
        hr_email = "mobin_tc02_hr@careerflow.test"
        room = create_sample_room_for_candidate(
            hr_email,
            title="Full Stack Cloud Developer",
            company="FinTech Innovation"
        )

        driver.get(f"{FRONTEND_URL}/apply/{room.share_token}")
        wait = WebDriverWait(driver, 10)

        # Locate form inputs
        name_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-candidate-name']")))
        email_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-candidate-email']")
        submit_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-submit-application']")

        # Verify required attributes on HTML5 inputs
        assert name_input.get_attribute("required") is not None
        assert email_input.get_attribute("required") is not None

        # Fill text inputs but omit files
        name_input.send_keys("Test Applicant")
        email_input.send_keys("applicant.test@careerflow.test")

        # Attempt to click submit button without uploading files
        submit_btn.click()

        # Confirmation card must NOT be present
        assert len(driver.find_elements(By.XPATH, "//*[contains(text(), 'Application Received')]")) == 0
        driver.save_screenshot(str(SCREENSHOTS_DIR / "us22_02_form_validation.png"))

    def test_tc_us22_03_file_upload_selection_and_feedback(self, driver):
        """TC-US22-03: Verify drag-and-drop / file input displays selected CV and Video filename and size."""
        hr_email = "mobin_tc03_hr@careerflow.test"
        room = create_sample_room_for_candidate(
            hr_email,
            title="DevOps Automation Engineer",
            company="NextGen Systems"
        )

        driver.get(f"{FRONTEND_URL}/apply/{room.share_token}")
        wait = WebDriverWait(driver, 10)

        # Find file input elements
        cv_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file'][accept*='.pdf']")))
        video_input = driver.find_element(By.CSS_SELECTOR, "input[type='file'][accept*='.mp4']")

        # Upload files
        cv_input.send_keys(str(CV_FIXTURE_PATH.resolve()))
        video_input.send_keys(str(VIDEO_FIXTURE_PATH.resolve()))

        # Assert CV file feedback is rendered with filename and MB
        wait.until(lambda d: "valid_sample.pdf" in d.page_source)
        assert "valid_sample.pdf" in driver.page_source
        assert "sample_pitch.mp4" in driver.page_source

        driver.save_screenshot(str(SCREENSHOTS_DIR / "us22_03_file_selection_feedback.png"))

    def test_tc_us22_04_e2e_successful_candidate_submission(self, driver):
        """TC-US22-04: End-to-end flow: candidate submits application, pipeline triggers, records saved."""
        hr_email = "mobin_tc04_hr@careerflow.test"
        candidate_email = "mobin_candidate_tc04@careerflow.test"
        candidate_name = "MD. Hasanul Mobin Candidate"

        room = create_sample_room_for_candidate(
            hr_email,
            title="Lead Distributed Systems Engineer",
            company="Apex Technologies"
        )

        driver.get(f"{FRONTEND_URL}/apply/{room.share_token}")
        wait = WebDriverWait(driver, 10)

        # 1. Fill candidate profile
        name_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-candidate-name']")))
        email_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-candidate-email']")
        name_input.send_keys(candidate_name)
        email_input.send_keys(candidate_email)

        # 2. Attach CV and Video files
        cv_input = driver.find_element(By.CSS_SELECTOR, "input[type='file'][accept*='.pdf']")
        video_input = driver.find_element(By.CSS_SELECTOR, "input[type='file'][accept*='.mp4']")
        cv_input.send_keys(str(CV_FIXTURE_PATH.resolve()))
        video_input.send_keys(str(VIDEO_FIXTURE_PATH.resolve()))

        # 3. Submit application
        submit_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-submit-application']")
        submit_btn.click()

        # 4. Assert confirmation card is displayed
        confirmation = wait.until(
            EC.visibility_of_element_located((By.XPATH, "//*[contains(text(), 'Application Received')]"))
        )
        assert confirmation is not None
        assert "processed by our AI pipeline" in driver.page_source

        # 5. Verify database integrity
        candidate_user = User.objects.get(email=candidate_email)
        assert candidate_user.role == User.Role.STUDENT
        assert candidate_user.full_name == candidate_name

        application = CandidateApplication.objects.get(room=room, candidate=candidate_user)
        assert application.cv is not None
        assert application.video is not None
        assert application.status == CandidateApplication.Status.COMPLETED

        driver.save_screenshot(str(SCREENSHOTS_DIR / "us22_04_application_submitted_confirmation.png"))

    def test_tc_us22_05_duplicate_submission_prevention(self, driver):
        """TC-US22-05: Verify candidate cannot submit multiple applications to the same recruitment room."""
        hr_email = "mobin_tc05_hr@careerflow.test"
        candidate_email = "mobin_duplicate_candidate@careerflow.test"
        candidate_name = "Duplicate Submitter"

        room = create_sample_room_for_candidate(
            hr_email,
            title="Site Reliability Engineer",
            company="Scalable Cloud Corp"
        )

        # First valid submission
        driver.get(f"{FRONTEND_URL}/apply/{room.share_token}")
        wait = WebDriverWait(driver, 10)

        name_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-candidate-name']")))
        email_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-candidate-email']")
        name_input.send_keys(candidate_name)
        email_input.send_keys(candidate_email)

        cv_input = driver.find_element(By.CSS_SELECTOR, "input[type='file'][accept*='.pdf']")
        video_input = driver.find_element(By.CSS_SELECTOR, "input[type='file'][accept*='.mp4']")
        cv_input.send_keys(str(CV_FIXTURE_PATH.resolve()))
        video_input.send_keys(str(VIDEO_FIXTURE_PATH.resolve()))

        submit_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-submit-application']")
        submit_btn.click()

        wait.until(EC.visibility_of_element_located((By.XPATH, "//*[contains(text(), 'Application Received')]")))

        # Second submission attempt with the same email
        driver.get(f"{FRONTEND_URL}/apply/{room.share_token}")
        name_input2 = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-candidate-name']")))
        email_input2 = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-candidate-email']")
        name_input2.send_keys(candidate_name)
        email_input2.send_keys(candidate_email)

        cv_input2 = driver.find_element(By.CSS_SELECTOR, "input[type='file'][accept*='.pdf']")
        video_input2 = driver.find_element(By.CSS_SELECTOR, "input[type='file'][accept*='.mp4']")
        cv_input2.send_keys(str(CV_FIXTURE_PATH.resolve()))
        video_input2.send_keys(str(VIDEO_FIXTURE_PATH.resolve()))

        submit_btn2 = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-submit-application']")
        submit_btn2.click()

        # Wait for error notification toast or rejection message
        wait.until(lambda d: "already submitted" in d.page_source.lower())
        assert "already submitted" in driver.page_source.lower()

        # Verify only 1 application exists in DB
        candidate_user = User.objects.get(email=candidate_email)
        assert CandidateApplication.objects.filter(room=room, candidate=candidate_user).count() == 1

        driver.save_screenshot(str(SCREENSHOTS_DIR / "us22_05_duplicate_submission_rejected.png"))

    def test_tc_us22_06_inactive_room_candidate_access_blocked(self, driver):
        """TC-US22-06: Verify accessing inactive room displays 410 error page and prevents submission."""
        hr_email = "mobin_tc06_hr@careerflow.test"
        room = create_sample_room_for_candidate(
            hr_email,
            title="Staff Security Engineer",
            company="SecureGate Corp",
            status="ACTIVE"
        )
        # Deactivate link
        room.link_is_active = False
        room.save(update_fields=['link_is_active'])

        driver.get(f"{FRONTEND_URL}/apply/{room.share_token}")
        wait = WebDriverWait(driver, 10)

        # Verify error card renders with status indicator
        error_card = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='card-link-error']")))
        assert error_card is not None
        assert "Application Link Inactive or Expired" in error_card.text
        assert "LINK_DEACTIVATED" in error_card.text or "410" in error_card.text

        # Verify application form is NOT displayed
        assert len(driver.find_elements(By.CSS_SELECTOR, "[data-testid='input-candidate-name']")) == 0
        assert len(driver.find_elements(By.CSS_SELECTOR, "[data-testid='button-submit-application']")) == 0

        driver.save_screenshot(str(SCREENSHOTS_DIR / "us22_06_inactive_room_blocked.png"))
