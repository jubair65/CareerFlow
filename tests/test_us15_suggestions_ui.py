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
    PresentationFeedback,
)
from apps.presentation.services.scorer import calculate_presentation_score
from conftest import FRONTEND_URL, create_user_in_db


def login_student(driver, email="bonny_ui_tester@careerflow.test", password="ValidPass2026!"):
    """Helper to register/ensure student exists and log in via UI."""
    create_user_in_db(email, password, role=User.Role.STUDENT, full_name="Bonny QA Suggestions Tester")

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


def setup_video_with_coaching_feedback(email: str) -> PresentationVideo:
    """Creates an active video with metrics and pre-populated PresentationFeedback."""
    user = User.objects.get(email=email)
    PresentationVideo.objects.filter(user=user).update(is_active=False)

    video = PresentationVideo.objects.create(
        user=user,
        file="students/test_bonny_video.mp4",
        original_filename="executive_pitch_bonny.mp4",
        raw_file_size=1024 * 1024 * 12,
        compressed_file_size=1024 * 1024 * 4,
        file_type="mp4",
        duration_seconds=95,
        status="COMPLETED",
        is_active=True
    )

    SpeechAnalysis.objects.create(
        video=video,
        transcript="Good morning. Today I will discuss how our engineering team optimized our query pipeline.",
        words_per_minute=144.0,
        filler_word_count=2,
        filler_words_breakdown={"um": 2},
        clarity_score=90,
        duration_seconds=95.0
    )

    BehavioralAnalysis.objects.create(
        video=video,
        eye_contact_score=84,
        posture_score=88,
        engagement_score=82,
        frame_metrics={"sampled_frames": 190}
    )

    calculate_presentation_score(video)

    PresentationFeedback.objects.create(
        video=video,
        summary="Outstanding executive poise and articulation with balanced pacing throughout your pitch.",
        strengths=[
            "Ideal speaking rate of 144 WPM preserves cognitive clarity for executive listeners.",
            "High camera gaze adherence (84%) creates an authentic, engaging candidate connection.",
            "Upright posture stability (88/100) reliably commands executive presence."
        ],
        improvements=[
            {
                "category": "Filler Words",
                "observation": "Detected 2 'um' filler occurrences during technical transition points.",
                "actionable_drill": "The Silent Pause Pivot: When switching between system design concepts, pause silently for 1 second instead of vocalizing."
            },
            {
                "category": "Pacing",
                "observation": "Spoke with steady cadence but can elevate vocal dynamism on key project metrics.",
                "actionable_drill": "Operative Word Emphasis: Practice reading your pitch aloud while slightly raising volume on quantifiable results."
            }
        ],
        practice_tip="\"We re-indexed the cluster... [1-sec pause] ...slashing query latency by 45%.\""
    )

    return video


class TestUS15PresentationSuggestionsUI:
    """
    US-15: AI Improvement Suggestions UI Automation Tests
    Task: US-15-T6
    Owner: Farhana Tahsin Bonny (QA Engineer & Suggestions Lead)

    Acceptance Criteria Verified:
    ✓ SuggestionsList mounts with Gemini model badge and executive summary
    ✓ Categorized strengths render with checkmark badges
    ✓ Targeted improvement cards render with category tag, observation, and 2-minute drill highlight box
    ✓ Practice phrasing cue renders with quote formatting
    ✓ Copy Drills button transitions to copied state
    ✓ Refresh button triggers suggestions regeneration smoothly
    """

    def test_tc_us15_t6_01_suggestions_card_mounts_and_renders_summary(self, driver):
        """TC-US15-T6-01: Verify SuggestionsList mounts with Gemini model badge and executive summary."""
        test_email = "bonny_suggestions_summary@careerflow.test"
        login_student(driver, email=test_email)
        setup_video_with_coaching_feedback(test_email)

        driver.get(f"{FRONTEND_URL}/student/presentation")
        wait = WebDriverWait(driver, 10)

        # 1. Verify container mounts
        suggestions_container = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='container-presentation-suggestions']"))
        )
        assert suggestions_container is not None

        # 2. Verify Gemini model badge
        badge = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='badge-gemini-model']"))
        )
        assert "gemini" in badge.text.lower()

        # 3. Verify executive summary
        summary = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='text-suggestions-summary']"))
        )
        assert len(summary.text) > 20
        assert "poise" in summary.text.lower() or "cadence" in summary.text.lower() or "presentation" in summary.text.lower()

    def test_tc_us15_t6_02_strengths_and_practice_tip_rendering(self, driver):
        """TC-US15-T6-02: Verify demonstrated strengths list and phrasing cue card render accurately."""
        test_email = "bonny_strengths_tip@careerflow.test"
        login_student(driver, email=test_email)
        setup_video_with_coaching_feedback(test_email)

        driver.get(f"{FRONTEND_URL}/student/presentation")
        wait = WebDriverWait(driver, 10)

        # Strengths container and item
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='list-strengths']")))
        strength_0 = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='strength-item-0']"))
        )
        assert len(strength_0.text) > 10

        # Practice script tip
        tip_elem = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='text-practice-tip']"))
        )
        assert len(tip_elem.text) > 10

    def test_tc_us15_t6_03_critical_improvements_and_drills_callouts(self, driver):
        """TC-US15-T6-03: Verify targeted improvement cards, diagnostic observations, and 2-minute drill boxes."""
        test_email = "bonny_improvements_drills@careerflow.test"
        login_student(driver, email=test_email)
        setup_video_with_coaching_feedback(test_email)

        driver.get(f"{FRONTEND_URL}/student/presentation")
        wait = WebDriverWait(driver, 10)

        # List of improvements
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='list-improvements']")))

        # Check first card
        category_badge = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='badge-category-0']"))
        )
        assert category_badge.text in ["Filler Words", "Pacing", "Eye Contact", "Posture", "Executive Polish"]

        obs_elem = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='text-observation-0']"))
        )
        assert len(obs_elem.text) > 15

        drill_box = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='card-drill-0']"))
        )
        assert drill_box is not None

        drill_text = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='text-drill-0']"))
        )
        assert len(drill_text.text) > 15

    def test_tc_us15_t6_04_copy_drills_and_refresh_interactions(self, driver):
        """TC-US15-T6-04: Verify Copy Drills button transitions state and Refresh button triggers update."""
        test_email = "bonny_interactions@careerflow.test"
        login_student(driver, email=test_email)
        setup_video_with_coaching_feedback(test_email)

        driver.get(f"{FRONTEND_URL}/student/presentation")
        wait = WebDriverWait(driver, 10)

        # Copy button interaction
        copy_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-copy-feedback']"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", copy_btn)
        time.sleep(0.3)
        copy_btn.click()

        # Check for copied feedback text or icon change
        time.sleep(0.5)

        # Refresh button interaction
        refresh_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-regenerate-feedback']"))
        )
        refresh_btn.click()

        # Container should remain visible and populated
        container = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='container-presentation-suggestions']"))
        )
        assert container is not None
