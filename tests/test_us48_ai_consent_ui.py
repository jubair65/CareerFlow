"""
US-48: AI Biometric & Evaluation Consent Notice Gatekeeper UI Automation Test Suite (US-48-T6).
User Story: US-48 – AI Biometric & Evaluation Consent Notice Gatekeeper
Sprint: Sprint 7 – System Enhancements & Platform Maturity
Epic: Epic 9 – Security, Governance & Regulatory Compliance
Lead Developer: MD. Hasanul Mobin (@hasanulmobin)
Dedicated Peer UI Automation Tester & Reviewer: MD. Jubair Bin Hasan (@jubair65)
Target Branch: feat/us-48-ai-biometric-consent -> develop

Acceptance Criteria & Scenarios Verified:
✔ TC-48-01: Consent Modal Blocking on Webcam Start [AC-1, AC-2]
✔ TC-48-02: Explicit Agreement Unlocks Video Recording & Issues Token [AC-1, AC-3]
✔ TC-48-03: Decline & Cancel Cleanly Aborts with Refusal Banner [AC-4]
✔ TC-48-04: File Upload Tab Consent Interception & Gateway [AC-1, AC-2]
✔ TC-48-05: Dedicated Policy Link Read-Only Inspection Modal [AC-6]
✔ TC-48-06: Applicant Portal Video Upload Gate & Interception [AC-1, AC-2]
✔ TC-48-07: Audit Record Database Persistence & Telemetry Logging [AC-5]
✔ TC-48-08: Backend Gatekeeper 403 AI_CONSENT_REQUIRED Enforcement [US-48-T5]
"""

import os
import sys
import time
import uuid
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import pytest
import requests
from django.conf import settings
from django.utils import timezone
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from apps.authentication.models import User
from apps.core.models import AIConsentLog
from apps.recruitment.models import RecruitmentRoom
from conftest import FRONTEND_URL, BACKEND_URL, SCREENSHOTS_DIR, create_user_in_db

FIXTURES_VIDEO_DIR = TESTS_DIR / "fixtures" / "video"
SAMPLE_MP4_PATH = FIXTURES_VIDEO_DIR / "sample_pitch.mp4"


def clear_react_input(driver, element):
    """Reliably clears React controlled inputs across platforms."""
    element.send_keys(Keys.CONTROL + "a")
    element.send_keys(Keys.BACKSPACE)
    driver.execute_script(
        "arguments[0].value = ''; "
        "arguments[0].dispatchEvent(new Event('input', { bubbles: true })); "
        "arguments[0].dispatchEvent(new Event('change', { bubbles: true }));",
        element,
    )


def set_react_input(driver, element, text: str):
    """Clears and types into React controlled input, firing required synthetic events."""
    clear_react_input(driver, element)
    if text:
        element.send_keys(text)
        driver.execute_script(
            "arguments[0].dispatchEvent(new Event('input', { bubbles: true })); "
            "arguments[0].dispatchEvent(new Event('change', { bubbles: true }));",
            element,
        )


def login_student_user(driver, email: str, password: str = "ValidPass2026!", full_name: str = "Alex Student"):
    """Helper to ensure student exists and authenticates via UI login page."""
    if not User.objects.filter(email__iexact=email).exists():
        create_user_in_db(email, password, role=User.Role.STUDENT, full_name=full_name)

    driver.get(f"{FRONTEND_URL}/login")
    driver.execute_script("sessionStorage.clear(); localStorage.clear();")
    driver.refresh()

    wait = WebDriverWait(driver, 10)
    email_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-login-email']")))
    pass_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-login-password']")
    submit_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-login']")

    set_react_input(driver, email_input, email)
    set_react_input(driver, pass_input, password)
    submit_btn.click()

    wait.until(lambda d: "/student" in d.current_url or "/dashboard" in d.current_url)
    time.sleep(1)


class TestAIConsentGatekeeperUI:
    """Suite of 8 automated UI tests verifying US-48 AI Biometric Consent Gatekeeper."""

    def test_tc48_01_consent_modal_blocking_on_webcam_start(self, driver):
        """
        TC-48-01: In /student/presentation, click [data-testid="button-start-recording"]
        without prior consent; verify [data-testid="modal-ai-consent"] mounts and recording is blocked.
        """
        uid = uuid.uuid4().hex[:6]
        student_email = f"tc48_01_{uid}@careerflow.test"
        login_student_user(driver, email=student_email, full_name="Alex ConsentTester")

        # Ensure no consent in DB or localStorage
        AIConsentLog.objects.filter(email=student_email).delete()
        user = User.objects.filter(email=student_email).first()
        if user:
            AIConsentLog.objects.filter(user=user).delete()

        driver.get(f"{FRONTEND_URL}/student/presentation")
        driver.execute_script("localStorage.removeItem('careerflow_ai_consent_token');")
        driver.refresh()

        wait = WebDriverWait(driver, 10)

        # Verify Studio page mounted and webcam tab active
        rec_tab = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='tab-record-webcam']")))
        assert rec_tab.is_displayed()

        # Find Start Recording button
        start_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-start-recording']")))
        driver.execute_script("arguments[0].click();", start_btn)

        # Verify AI Consent Modal mounts cleanly
        modal = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-ai-consent']")))
        assert modal.is_displayed(), "AI Consent Modal did not mount on unconsented recording attempt!"

        # Verify modal header and version badge
        title_elem = modal.find_element(By.CSS_SELECTOR, "[data-testid='text-ai-consent-title']")
        assert "AI Biometric & Presentation Evaluation Privacy Notice" in title_elem.text

        version_badge = modal.find_element(By.CSS_SELECTOR, "[data-testid='badge-policy-version']")
        assert "1.0" in version_badge.text

        # Verify recording did not start (no stop button present)
        stop_buttons = driver.find_elements(By.CSS_SELECTOR, "[data-testid='button-stop-recording']")
        assert len(stop_buttons) == 0, "Recording unexpectedly started before user consent!"

        screenshot_path = SCREENSHOTS_DIR / "us48_01_consent_modal_blocking.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc48_02_agree_and_unlock_webcam_recording(self, driver):
        """
        TC-48-02: In consent modal, check [data-testid="checkbox-ai-consent-agree"];
        click [data-testid="button-ai-consent-agree"]; verify modal closes and consent token is saved.
        """
        uid = uuid.uuid4().hex[:6]
        student_email = f"tc48_02_{uid}@careerflow.test"
        login_student_user(driver, email=student_email, full_name="Taylor ConsentAgreed")

        # Clear consent state
        AIConsentLog.objects.filter(email=student_email).delete()
        user = User.objects.filter(email=student_email).first()
        if user:
            AIConsentLog.objects.filter(user=user).delete()

        driver.get(f"{FRONTEND_URL}/student/presentation")
        driver.execute_script("localStorage.removeItem('careerflow_ai_consent_token');")
        driver.refresh()

        wait = WebDriverWait(driver, 10)

        # Trigger consent modal via start recording
        start_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-start-recording']")))
        driver.execute_script("arguments[0].click();", start_btn)

        modal = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-ai-consent']")))

        # Verify Agree button is initially disabled
        agree_btn = modal.find_element(By.CSS_SELECTOR, "[data-testid='button-ai-consent-agree']")
        assert not agree_btn.is_enabled() or agree_btn.get_attribute("disabled") is not None

        # Check agreement checkbox
        agree_checkbox = modal.find_element(By.CSS_SELECTOR, "[data-testid='checkbox-ai-consent-agree']")
        driver.execute_script("arguments[0].click();", agree_checkbox)
        time.sleep(0.3)

        # Verify Agree button is now enabled
        assert agree_btn.is_enabled()

        # Click Agree & Continue
        driver.execute_script("arguments[0].click();", agree_btn)

        # Wait for modal to dismiss
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-ai-consent']")))

        # Verify consent token is persisted in localStorage
        token = driver.execute_script("return localStorage.getItem('careerflow_ai_consent_token');")
        assert token and len(token) >= 16, f"Expected valid consent token in localStorage, got {token}"

        # Verify consent log recorded in database for this user
        log = AIConsentLog.objects.filter(user=user, agreed=True).first()
        assert log is not None, "AIConsentLog record was not saved in DB after agreement!"
        assert log.policy_version == "v1.0"

        screenshot_path = SCREENSHOTS_DIR / "us48_02_consent_agreed_recording_unlocked.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc48_03_decline_and_cancel_cleanly_aborts(self, driver):
        """
        TC-48-03: In consent modal, click [data-testid="button-ai-consent-decline"];
        verify modal closes without errors and [data-testid="alert-ai-consent-refused"] is displayed.
        """
        uid = uuid.uuid4().hex[:6]
        student_email = f"tc48_03_{uid}@careerflow.test"
        login_student_user(driver, email=student_email, full_name="Jordan RefusalTester")

        AIConsentLog.objects.filter(email=student_email).delete()
        user = User.objects.filter(email=student_email).first()
        if user:
            AIConsentLog.objects.filter(user=user).delete()

        driver.get(f"{FRONTEND_URL}/student/presentation")
        driver.execute_script("localStorage.removeItem('careerflow_ai_consent_token');")
        driver.refresh()

        wait = WebDriverWait(driver, 10)

        # Open consent modal
        start_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-start-recording']")))
        driver.execute_script("arguments[0].click();", start_btn)

        modal = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-ai-consent']")))

        # Click Decline & Cancel button
        decline_btn = modal.find_element(By.CSS_SELECTOR, "[data-testid='button-ai-consent-decline']")
        driver.execute_script("arguments[0].click();", decline_btn)

        # Verify modal closes
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-ai-consent']")))

        # Verify refusal explanation alert is mounted
        alert_banner = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='alert-ai-consent-refused']"))
        )
        assert alert_banner.is_displayed()
        assert "declined" in alert_banner.text.lower() or "paused" in alert_banner.text.lower()

        # Verify "Review Consent" re-open button is present
        reopen_btn = alert_banner.find_element(By.CSS_SELECTOR, "[data-testid='button-reopen-ai-consent']")
        assert reopen_btn.is_displayed()

        # Verify DB recorded refusal
        refused_log = AIConsentLog.objects.filter(user=user, agreed=False).first()
        assert refused_log is not None, "Refusal log was not recorded in AIConsentLog!"

        screenshot_path = SCREENSHOTS_DIR / "us48_03_consent_declined_alert_shown.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc48_04_file_upload_consent_gate(self, driver):
        """
        TC-48-04: In Upload File tab, attempt file upload without consent;
        verify consent modal intercepts before file staging.
        """
        uid = uuid.uuid4().hex[:6]
        student_email = f"tc48_04_{uid}@careerflow.test"
        login_student_user(driver, email=student_email, full_name="Riley UploadTester")

        user = User.objects.filter(email=student_email).first()
        if user:
            AIConsentLog.objects.filter(user=user).delete()
        AIConsentLog.objects.filter(email=student_email).delete()

        driver.get(f"{FRONTEND_URL}/student/presentation")
        driver.execute_script("localStorage.removeItem('careerflow_ai_consent_token');")
        driver.refresh()

        wait = WebDriverWait(driver, 10)

        # Switch to upload tab
        upload_tab = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='tab-upload-file']")))
        driver.execute_script("arguments[0].click();", upload_tab)

        # Send sample video fixture to hidden input without prior consent
        file_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='input-video-file']")))
        file_input.send_keys(str(SAMPLE_MP4_PATH.resolve()))

        # Verify modal intercepts immediately
        modal = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-ai-consent']")))
        assert modal.is_displayed()

        # Agree to unlock
        agree_checkbox = modal.find_element(By.CSS_SELECTOR, "[data-testid='checkbox-ai-consent-agree']")
        driver.execute_script("arguments[0].click();", agree_checkbox)
        agree_btn = modal.find_element(By.CSS_SELECTOR, "[data-testid='button-ai-consent-agree']")
        driver.execute_script("arguments[0].click();", agree_btn)

        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-ai-consent']")))

        # Verify file upload is now staged with submit button visible
        submit_btn = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='button-upload-file-submit']"))
        )
        assert submit_btn is not None

        screenshot_path = SCREENSHOTS_DIR / "us48_04_file_upload_consent_modal.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc48_05_dedicated_policy_link_accessibility(self, driver):
        """
        TC-48-05: On studio page, click [data-testid="link-ai-consent-policy"];
        verify policy notice opens in inspectable read-only mode (AC-6).
        """
        uid = uuid.uuid4().hex[:6]
        student_email = f"tc48_05_{uid}@careerflow.test"
        login_student_user(driver, email=student_email, full_name="Casey PolicyAuditor")

        driver.get(f"{FRONTEND_URL}/student/presentation")
        wait = WebDriverWait(driver, 10)

        # Click dedicated policy notice link in header
        policy_link = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='link-ai-consent-policy']"))
        )
        assert policy_link.is_displayed()
        driver.execute_script("arguments[0].click();", policy_link)

        # Modal opens in read-only inspection mode
        modal = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-ai-consent']")))
        assert modal.is_displayed()

        modal_text = modal.text
        assert "Audio & Speech Telemetry" in modal_text
        assert "Facial Telemetry & Posture Tracking" in modal_text
        assert "Human-in-the-Loop & Anti-Discrimination" in modal_text
        assert "Data Retention & Automated Purge Policy" in modal_text

        # Verify read-only close button functions cleanly
        close_btn = modal.find_element(By.CSS_SELECTOR, "[data-testid='button-close-ai-consent-modal']")
        driver.execute_script("arguments[0].click();", close_btn)

        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-ai-consent']")))

        screenshot_path = SCREENSHOTS_DIR / "us48_05_policy_notice_modal_inspectable.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc48_06_applicant_portal_video_upload_gate(self, driver):
        """
        TC-48-06: In /apply/{token}, attempt video file selection;
        verify consent modal intercepts before submission.
        """
        uid = uuid.uuid4().hex[:6]
        hr_user = create_user_in_db(
            f"hr_us48_{uid}@careerflow.test", "ValidPass2026!", role=User.Role.HR_MANAGER, full_name="HR Director"
        )
        room = RecruitmentRoom.objects.create(
            created_by=hr_user,
            title="Senior Security Architect",
            company_name="Ethical AI Labs",
            department="Governance",
            status=RecruitmentRoom.Status.OPEN,
            link_is_active=True,
        )

        candidate_email = f"morgan_{uid}@applicant.test"
        AIConsentLog.objects.filter(email=candidate_email).delete()

        driver.get(FRONTEND_URL)
        driver.execute_script("sessionStorage.clear(); localStorage.clear();")
        driver.get(f"{FRONTEND_URL}/apply/{room.share_token}")
        wait = WebDriverWait(driver, 10)

        # Verify public application form mounted
        name_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-candidate-name']")))
        email_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-candidate-email']")

        set_react_input(driver, name_input, "Morgan Applicant")
        set_react_input(driver, email_input, candidate_email)

        # Select video file via input
        video_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-video-file']")
        video_input.send_keys(str(SAMPLE_MP4_PATH.resolve()))

        # Verify AI Consent modal intercepts
        modal = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-ai-consent']")))
        assert modal.is_displayed()

        agree_checkbox = modal.find_element(By.CSS_SELECTOR, "[data-testid='checkbox-ai-consent-agree']")
        driver.execute_script("arguments[0].click();", agree_checkbox)
        agree_btn = modal.find_element(By.CSS_SELECTOR, "[data-testid='button-ai-consent-agree']")
        driver.execute_script("arguments[0].click();", agree_btn)

        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-ai-consent']")))

        screenshot_path = SCREENSHOTS_DIR / "us48_06_applicant_portal_consent_modal.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc48_07_audit_record_persistence(self, driver):
        """
        TC-48-07: Complete consent agreement; inspect AIConsentLog in database;
        verify client IP, timestamp, v1.0 policy version, and consent token are saved (AC-5).
        """
        uid = uuid.uuid4().hex[:6]
        test_email = f"audit_candidate_{uid}@careerflow.test"

        # Record consent via direct endpoint to simulate client telemetry
        resp = requests.post(
            f"{BACKEND_URL}/api/core/ai-consent/",
            json={"agreed": True, "email": test_email, "policy_version": "v1.0"},
            headers={"User-Agent": "CareerFlow-Automated-UI-Audit/1.0"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "recorded"
        consent_token = data["consent_token"]

        # Inspect database record
        log = AIConsentLog.objects.filter(consent_token=consent_token).first()
        assert log is not None, "AIConsentLog entry not found in database!"
        assert log.email == test_email
        assert log.agreed is True
        assert log.policy_version == "v1.0"
        assert log.ip_address is not None
        assert log.timestamp is not None

        # Authenticate student via UI to view studio
        login_student_user(driver, email=test_email, full_name="Audit Candidate")
        driver.get(f"{FRONTEND_URL}/student/presentation")
        driver.execute_script(f"localStorage.setItem('careerflow_ai_consent_token', '{consent_token}');")
        driver.refresh()
        wait = WebDriverWait(driver, 10)

        # Policy link should display and be clickable without refusal alerts
        policy_link = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='link-ai-consent-policy']"))
        )
        assert policy_link.is_displayed()

        refusal_alerts = driver.find_elements(By.CSS_SELECTOR, "[data-testid='alert-ai-consent-refused']")
        assert len(refusal_alerts) == 0, "Refusal alert should not display when consent is active!"

        screenshot_path = SCREENSHOTS_DIR / "us48_07_audit_log_persisted_in_db.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc48_08_backend_gatekeeper_403_enforcement(self, driver):
        """
        TC-48-08: Send direct POST /api/presentation/upload/ without consent;
        assert HTTP 403 Forbidden with AI_CONSENT_REQUIRED (US-48-T5).
        """
        uid = uuid.uuid4().hex[:6]
        student = create_user_in_db(
            f"gatekeeper_{uid}@careerflow.test", "ValidPass2026!", role=User.Role.STUDENT, full_name="Gatekeeper Tester"
        )
        AIConsentLog.objects.filter(user=student).delete()

        # Log in student via UI to get JWT session tokens
        driver.get(f"{FRONTEND_URL}/login")
        driver.execute_script("sessionStorage.clear(); localStorage.clear();")
        driver.refresh()
        wait = WebDriverWait(driver, 10)

        email_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-login-email']")))
        pass_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-login-password']")
        submit_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-login']")

        set_react_input(driver, email_input, student.email)
        set_react_input(driver, pass_input, "ValidPass2026!")
        submit_btn.click()
        wait.until(lambda d: "/student" in d.current_url or "/dashboard" in d.current_url)

        # Extract JWT access token from localStorage using careerflow_access_token key
        access_token = driver.execute_script("return localStorage.getItem('careerflow_access_token');")
        assert access_token, "Failed to retrieve careerflow_access_token from localStorage!"

        # 1. Unconsented upload attempt without consent token
        with open(SAMPLE_MP4_PATH, "rb") as f:
            files = {"file": ("test_take.mp4", f, "video/mp4")}
            headers = {"Authorization": f"Bearer {access_token}"}
            resp = requests.post(f"{BACKEND_URL}/api/presentation/upload/", files=files, headers=headers)

        assert resp.status_code == 403, f"Expected 403 Forbidden for unconsented upload, got {resp.status_code}"
        resp_data = resp.json()
        assert resp_data.get("code") == "AI_CONSENT_REQUIRED", f"Expected AI_CONSENT_REQUIRED, got {resp_data}"

        # 2. Upload attempt with valid consent token header
        consent_record = requests.post(
            f"{BACKEND_URL}/api/core/ai-consent/",
            json={"agreed": True, "email": student.email, "policy_version": "v1.0"},
            headers=headers,
        ).json()
        valid_token = consent_record["consent_token"]

        headers["X-AI-Consent-Token"] = valid_token
        with open(SAMPLE_MP4_PATH, "rb") as f:
            files = {"file": ("test_take.mp4", f, "video/mp4")}
            resp_consented = requests.post(f"{BACKEND_URL}/api/presentation/upload/", files=files, headers=headers)

        # Status should NOT be 403 AI_CONSENT_REQUIRED
        assert resp_consented.status_code != 403 or resp_consented.json().get("code") != "AI_CONSENT_REQUIRED"

        # Capture visual proof
        driver.get(f"{FRONTEND_URL}/student/presentation")
        screenshot_path = SCREENSHOTS_DIR / "us48_08_backend_gatekeeper_403_enforced.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()
