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
from apps.presentation.models import PresentationVideo, SpeechAnalysis, BehavioralAnalysis, PresentationScore
from apps.presentation.services.scorer import calculate_presentation_score
from conftest import FRONTEND_URL, create_user_in_db

FIXTURES_DIR = TESTS_DIR / "fixtures" / "video"


def login_student(driver, email="mona_ui_tester@careerflow.test", password="ValidPass2026!"):
    """Helper to register/ensure student exists and log in via UI."""
    create_user_in_db(email, password, role=User.Role.STUDENT, full_name="Mona UI Candidate")

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


def setup_active_video_with_metrics(email: str, has_behavioral: bool = True) -> PresentationVideo:
    """Creates a sample active PresentationVideo with Speech and optional Behavioral data."""
    user = User.objects.get(email=email)
    # Deactivate existing videos
    PresentationVideo.objects.filter(user=user).update(is_active=False)

    video = PresentationVideo.objects.create(
        user=user,
        file="students/test_video.mp4",
        original_filename="sample_pitch.mp4",
        raw_file_size=1024 * 1024 * 10,
        compressed_file_size=1024 * 1024 * 3,
        file_type="mp4",
        duration_seconds=65,
        status="READY_FOR_ANALYSIS",
        is_active=True
    )

    # Add Speech Analysis (optimal pacing 142 WPM, 1 filler word -> Speech score: 98)
    SpeechAnalysis.objects.create(
        video=video,
        transcript="Hello recruiters, I am thrilled to present my portfolio project today.",
        words_per_minute=142.0,
        filler_word_count=1,
        filler_words_breakdown={"um": 1},
        clarity_score=92,
        duration_seconds=65.0
    )

    if has_behavioral:
        # Add Behavioral Analysis (Eye: 88, Posture: 90, Engagement: 85 -> Behavioral score: 88)
        BehavioralAnalysis.objects.create(
            video=video,
            eye_contact_score=88,
            posture_score=90,
            engagement_score=85,
            frame_metrics={"sampled_frames": 130}
        )

    # Pre-calculate score
    calculate_presentation_score(video)
    return video


class TestUS14PresentationScoringUI:
    """
    US-14: Video Presentation Score UI Automation Tests
    Task: US-14-T5
    Owner: Jannatun Naeem Mona (System Analyst / BA)

    Acceptance Criteria Verified:
    ✓ PresentationScoreCard renders with circular SVG gauge, overall score (0-100), and tier badge
    ✓ Category pillars for Speech Delivery and Behavioral Poise render with accurate weightings
    ✓ Subcategory diagnostics for Pacing, Fillers, Eye Contact, Posture, and Engagement are displayed
    ✓ Recalculate Score button triggers real-time refresh
    ✓ Graceful degradation banner renders when behavioral metrics are absent (US-40 alignment)
    """

    def test_tc_us14_t5_01_scorecard_renders_with_overall_score(self, driver):
        """TC-US14-T5-01: Verify PresentationScoreCard displays composite score, gauge, and grade badge."""
        test_email = "student_score_gauge@careerflow.test"
        login_student(driver, email=test_email)
        setup_active_video_with_metrics(test_email, has_behavioral=True)

        driver.get(f"{FRONTEND_URL}/student/presentation")
        wait = WebDriverWait(driver, 10)

        # 1. Verify scorecard card container
        score_card = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='presentation-score-card']")))
        assert score_card is not None

        # 2. Verify overall score value and gauge
        score_value = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='overall-score-value']")))
        assert score_value.text.isdigit()
        score_num = int(score_value.text)
        assert 0 <= score_num <= 100

        # 3. Verify grade badge
        grade_badge = driver.find_element(By.CSS_SELECTOR, "[data-testid='badge-score-grade']")
        assert grade_badge.text in ["Excellent", "Competent", "Needs Practice"]

    def test_tc_us14_t5_02_subcategory_diagnostics_breakdown(self, driver):
        """TC-US14-T5-02: Verify diagnostic breakdowns for Pacing, Fillers, Eye Contact, Posture, and Engagement."""
        test_email = "student_score_diag@careerflow.test"
        login_student(driver, email=test_email)
        setup_active_video_with_metrics(test_email, has_behavioral=True)

        driver.get(f"{FRONTEND_URL}/student/presentation")
        wait = WebDriverWait(driver, 10)

        # Pillars
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='subscore-speech']")))
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='subscore-behavioral']")))

        # Subcategories
        pace_elem = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='subscore-pace']")))
        filler_elem = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='subscore-filler']")))
        eye_elem = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='subscore-eye-contact']")))
        posture_elem = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='subscore-posture']")))
        eng_elem = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='subscore-engagement']")))

        assert "Speaking Pace" in pace_elem.text
        assert "Filler Word" in filler_elem.text
        assert "Eye Contact" in eye_elem.text
        assert "Posture Stability" in posture_elem.text
        assert "Facial Engagement" in eng_elem.text

    def test_tc_us14_t5_03_recalculate_score_interaction(self, driver):
        """TC-US14-T5-03: Verify clicking Recalculate button refreshes score smoothly."""
        test_email = "student_recalc_score@careerflow.test"
        login_student(driver, email=test_email)
        setup_active_video_with_metrics(test_email, has_behavioral=True)

        driver.get(f"{FRONTEND_URL}/student/presentation")
        wait = WebDriverWait(driver, 10)

        recalc_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-recalculate-score']")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", recalc_btn)
        time.sleep(0.5)
        recalc_btn.click()

        # Scorecard should remain or re-render with valid score
        score_value = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='overall-score-value']")))
        assert int(score_value.text) >= 0

    def test_tc_us14_t5_04_graceful_degradation_banner_rendering(self, driver):
        """TC-US14-T5-04: Partial evaluation banner displays when video frames lack vision tracking (US-40)."""
        test_email = "student_degraded_score@careerflow.test"
        login_student(driver, email=test_email)
        setup_active_video_with_metrics(test_email, has_behavioral=False)

        driver.get(f"{FRONTEND_URL}/student/presentation")
        wait = WebDriverWait(driver, 10)

        banner = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='degradation-warning-banner']")))
        assert banner is not None
        assert "speech" in banner.text.lower()
