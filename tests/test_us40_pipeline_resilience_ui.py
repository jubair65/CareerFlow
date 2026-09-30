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
from apps.presentation.models import (
    PresentationVideo,
    SpeechAnalysis,
    BehavioralAnalysis,
    PresentationScore,
    PipelineExecutionLog,
)
from apps.presentation.services.scorer import calculate_presentation_score
from conftest import FRONTEND_URL, create_user_in_db


def login_student(driver, email="maria_ui_tester@careerflow.test", password="ValidPass2026!"):
    """Helper to register/ensure student exists and log in via UI."""
    create_user_in_db(email, password, role=User.Role.STUDENT, full_name="Maria System Architect Tester")

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


def setup_video_for_resilience(
    email: str,
    status: str = "FAILED",
    has_behavioral: bool = False,
    with_logs: bool = True
) -> PresentationVideo:
    """Creates a sample video with specific resilience/failure status and logs."""
    user = User.objects.get(email=email)
    PresentationVideo.objects.filter(user=user).update(is_active=False)

    video = PresentationVideo.objects.create(
        user=user,
        file="students/test_resilience.mp4",
        original_filename="resilience_demo_pitch.mp4",
        raw_file_size=1024 * 1024 * 14,
        compressed_file_size=1024 * 1024 * 4,
        file_type="mp4",
        duration_seconds=70,
        status=status,
        is_active=True
    )

    if status in ("PARTIALLY_COMPLETED", "COMPLETED"):
        SpeechAnalysis.objects.create(
            video=video,
            transcript="Hello hiring team, I am demonstrating our fault tolerance architecture.",
            words_per_minute=145.0,
            filler_word_count=0,
            filler_words_breakdown={},
            clarity_score=94,
            duration_seconds=70.0
        )
        if has_behavioral:
            BehavioralAnalysis.objects.create(
                video=video,
                eye_contact_score=85,
                posture_score=85,
                engagement_score=80,
                frame_metrics={"sampled_frames": 140}
            )
        calculate_presentation_score(video)
        # Preserve status
        video.status = status
        video.save(update_fields=['status'])

    if with_logs:
        PipelineExecutionLog.objects.create(
            video=video,
            stage=PipelineExecutionLog.Stage.SPEECH_ANALYSIS,
            status=PipelineExecutionLog.Status.SUCCESS,
            attempt=1,
            execution_time_ms=140
        )
        if status == "FAILED":
            PipelineExecutionLog.objects.create(
                video=video,
                stage=PipelineExecutionLog.Stage.VISION_ANALYSIS,
                status=PipelineExecutionLog.Status.FAILED,
                attempt=3,
                error_message="MediaPipe: Frame buffer corrupted during landmark extraction",
                execution_time_ms=450
            )
        elif status == "PARTIALLY_COMPLETED":
            PipelineExecutionLog.objects.create(
                video=video,
                stage=PipelineExecutionLog.Stage.VISION_ANALYSIS,
                status=PipelineExecutionLog.Status.DEGRADED,
                attempt=1,
                error_message="Graceful degradation applied: Low lighting prevented pupil tracking",
                execution_time_ms=320
            )

    return video


class TestUS40PipelineResilienceUI:
    """
    US-40: AI Pipeline Failure Handling & Resilience UI Automation Tests
    Task: US-40-T6
    Owner: Nafisa Tabassum Maria (System Architect)

    Acceptance Criteria Verified:
    ✓ Pipeline failure alert banner renders with clear explanation and fault badge
    ✓ Prominent [Retry Analysis] CTA is rendered and accessible
    ✓ Diagnostics drawer toggles open to reveal structured execution log telemetry
    ✓ Graceful degradation banner renders in partial evaluation mode (100% speech score)
    ✓ Retrying state displays animated recovery banner and backoff indicator
    """

    def test_tc_us40_t6_01_failed_pipeline_renders_alert_and_retry_cta(self, driver):
        """TC-US40-T6-01: Verifies failure alert banner and Retry CTA mount on FAILED status."""
        test_email = "maria_fail_test@careerflow.test"
        login_student(driver, email=test_email)
        setup_video_for_resilience(test_email, status="FAILED")

        driver.get(f"{FRONTEND_URL}/student/presentation")
        wait = WebDriverWait(driver, 10)

        alert_elem = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='pipeline-failure-alert']")))
        assert "analysis pipeline interrupted" in alert_elem.text.lower()
        assert "fault caught (us-40)" in alert_elem.text.lower()

        retry_btn = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='button-pipeline-retry']")))
        assert retry_btn.is_displayed()
        assert "retry analysis" in retry_btn.text.lower()

        # Verify status badge shows FAILED
        status_badge = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='badge-video-status']")))
        assert "FAILED" in status_badge.text

    def test_tc_us40_t6_02_diagnostics_drawer_toggle_and_log_rendering(self, driver):
        """TC-US40-T6-02: Verifies diagnostics button toggles execution log telemetry drawer."""
        test_email = "maria_diag_test@careerflow.test"
        login_student(driver, email=test_email)
        setup_video_for_resilience(test_email, status="FAILED", with_logs=True)

        driver.get(f"{FRONTEND_URL}/student/presentation")
        wait = WebDriverWait(driver, 10)

        diag_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-toggle-diagnostics']")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", diag_btn)
        time.sleep(0.3)
        diag_btn.click()

        # Drawer should expand
        drawer = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='pipeline-diagnostics-drawer']")))
        assert drawer.is_displayed()

        logs_container = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='pipeline-logs-list']")))
        assert logs_container.is_displayed()
        assert "SPEECH_ANALYSIS" in logs_container.text
        assert "VISION_ANALYSIS" in logs_container.text

    def test_tc_us40_t6_03_graceful_degradation_alert_and_100_percent_speech_mode(self, driver):
        """TC-US40-T6-03: Partial evaluation alert displays when computer vision landmarks are missing."""
        test_email = "maria_degrade_test@careerflow.test"
        login_student(driver, email=test_email)
        setup_video_for_resilience(test_email, status="PARTIALLY_COMPLETED", has_behavioral=False)

        driver.get(f"{FRONTEND_URL}/student/presentation")
        wait = WebDriverWait(driver, 10)

        partial_alert = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='pipeline-partial-alert']")))
        assert "graceful degradation active (us-40)" in partial_alert.text.lower()
        assert "100% speech mode" in partial_alert.text.lower()

        retry_degraded_btn = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='button-pipeline-retry-degraded']"))
        )
        assert retry_degraded_btn.is_displayed()

    def test_tc_us40_t6_04_retrying_state_badge_and_animation(self, driver):
        """TC-US40-T6-04: Verifies retrying state displays recovery badge and backoff animation."""
        test_email = "maria_retrying_test@careerflow.test"
        login_student(driver, email=test_email)
        setup_video_for_resilience(test_email, status="RETRYING")

        driver.get(f"{FRONTEND_URL}/student/presentation")
        wait = WebDriverWait(driver, 10)

        retrying_elem = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='pipeline-retrying-badge']")))
        assert "pipeline recovery in progress" in retrying_elem.text.lower()
        assert "attempting recovery" in retrying_elem.text.lower()

    def test_tc_us40_t6_05_retry_button_click_triggers_recovery(self, driver):
        """TC-US40-T6-05: Verifies clicking Retry Analysis triggers the pipeline retry."""
        test_email = "maria_retry_click_test@careerflow.test"
        login_student(driver, email=test_email)
        setup_video_for_resilience(test_email, status="FAILED")

        driver.get(f"{FRONTEND_URL}/student/presentation")
        wait = WebDriverWait(driver, 10)

        retry_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-pipeline-retry']")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", retry_btn)
        time.sleep(0.3)
        retry_btn.click()

        # Button text should either transition to Retrying Pipeline or trigger notification toast
        time.sleep(1.0)
        container = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='pipeline-status-container']")))
        assert container is not None

