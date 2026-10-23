import os
import sys
import time
from datetime import timedelta
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

import pytest
import requests
from django.utils import timezone
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
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
from conftest import FRONTEND_URL, BACKEND_URL, SCREENSHOTS_DIR, create_user_in_db


def clear_react_input(driver, element):
    """Reliably clears React controlled inputs across Windows and macOS."""
    element.send_keys(Keys.COMMAND + "a")
    element.send_keys(Keys.CONTROL + "a")
    element.send_keys(Keys.BACKSPACE)
    driver.execute_script(
        "arguments[0].value = ''; "
        "arguments[0].dispatchEvent(new Event('input', { bubbles: true })); "
        "arguments[0].dispatchEvent(new Event('change', { bubbles: true }));",
        element
    )


def login_student(driver, email: str, password: str = "ValidPass2026!", full_name: str = "Maria TrendTester"):
    """Helper to ensure student exists and logs in via UI without cascading deletes."""
    if not User.objects.filter(email__iexact=email).exists():
        create_user_in_db(email, password, role=User.Role.STUDENT, full_name=full_name)

    driver.get(f"{FRONTEND_URL}/login")
    driver.execute_script("sessionStorage.clear(); localStorage.clear();")
    driver.refresh()

    wait = WebDriverWait(driver, 10)
    email_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-login-email']")))
    pass_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-login-password']")
    submit_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-login']")

    clear_react_input(driver, email_input)
    email_input.send_keys(email)
    clear_react_input(driver, pass_input)
    pass_input.send_keys(password)
    submit_btn.click()

    wait.until(EC.url_contains("/student/dashboard"))


def create_sample_trend_video(
    user: User,
    filename: str,
    duration: int = 80,
    overall_score: int = 80,
    speech_score: int = 78,
    behavioral_score: int = 82,
    pace_score: int = 80,
    filler_score: int = 75,
    eye_score: int = 85,
    posture_score: int = 80,
    engagement_score: int = 80,
    wpm: float = 142.0,
    days_ago: int = 0,
    status: str = 'COMPLETED'
) -> PresentationVideo:
    """Populates a PresentationVideo with full analysis models and backdated timestamps for trend curves."""
    video = PresentationVideo.objects.create(
        user=user,
        file=f"students/{user.id}/videos/{filename}",
        original_filename=filename,
        raw_file_size=1024 * 1024 * 10,
        compressed_file_size=1024 * 1024 * 3,
        file_type="mp4",
        duration_seconds=duration,
        status=status,
        is_active=True
    )

    if days_ago > 0:
        uploaded_time = timezone.now() - timedelta(days=days_ago)
        PresentationVideo.objects.filter(pk=video.pk).update(uploaded_at=uploaded_time)
        video.refresh_from_db()

    if status == 'COMPLETED':
        SpeechAnalysis.objects.create(
            video=video,
            transcript="Welcome everyone. Today I am pitching our scalable architecture and AI trend analytics.",
            words_per_minute=wpm,
            filler_word_count=2,
            filler_words_breakdown={"um": 1, "like": 1},
            clarity_score=speech_score,
            duration_seconds=float(duration)
        )
        BehavioralAnalysis.objects.create(
            video=video,
            eye_contact_score=eye_score,
            posture_score=posture_score,
            engagement_score=engagement_score,
            frame_metrics={"sampled_frames": 120}
        )
        PresentationScore.objects.create(
            video=video,
            overall_score=overall_score,
            speech_score=speech_score,
            behavioral_score=behavioral_score,
            pace_score=pace_score,
            filler_score=filler_score,
            eye_contact_score=eye_score,
            posture_score=posture_score,
            engagement_score=engagement_score,
            has_behavioral_data=True
        )
        PresentationFeedback.objects.create(
            video=video,
            summary=f"Take performance overall: {overall_score}/100. Pacing was {int(wpm)} WPM.",
            strengths=[f"Strong eye contact at {eye_score}%", f"Steady posture stability at {posture_score}%"],
            improvements=[
                {
                    "category": "Pacing",
                    "observation": "Slight cadence variation between slides.",
                    "actionable_drill": "Maintain steady metronomic cadence."
                }
            ],
            practice_tip="Focus on steady diaphragmatic breathing."
        )

    return video


# ==============================================================================
# TEST SUITE: US-17 Score Trends Across Attempts (AC 1 – AC 6)
# ==============================================================================

@pytest.mark.django_db(transaction=True)
def test_tc17_01_tab_switching_and_navigation(driver):
    """
    TC-17-01: Tab Switching & Navigation
    Verifies tab button switching between Video Takes and Score Trends on /student/videos,
    and validates direct URL access via /presentation/trends and /student/videos?tab=trends.
    """
    email = "trend_nav_user@careerflow.test"
    user = create_user_in_db(email, "ValidPass2026!", role=User.Role.STUDENT, full_name="Nav Student")
    create_sample_trend_video(user, "test_take_sample.mp4", overall_score=80)

    login_student(driver, email, "ValidPass2026!")

    # 1. Navigate to Video History
    driver.get(f"{FRONTEND_URL}/student/videos")
    wait = WebDriverWait(driver, 10)

    # Asserts Takes tab is initially active
    takes_tab = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='tab-takes-history']")))
    trends_tab = driver.find_element(By.CSS_SELECTOR, "[data-testid='tab-score-trends']")
    assert "bg-[#253142]" in takes_tab.get_attribute("class")

    # 2. Click Score Trends Tab
    trends_tab.click()
    time.sleep(1.0)

    # Asserts Trends tab is now active
    trends_tab_updated = driver.find_element(By.CSS_SELECTOR, "[data-testid='tab-score-trends']")
    assert "bg-[#253142]" in trends_tab_updated.get_attribute("class")

    # 3. Switch back to Takes History
    takes_tab.click()
    time.sleep(0.8)
    assert driver.find_element(By.CSS_SELECTOR, "[data-testid='tab-takes-history']")

    # 4. Test direct URL deep-link /presentation/trends
    driver.get(f"{FRONTEND_URL}/presentation/trends")
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "body")))
    time.sleep(1.0)
    assert "trends" in driver.current_url

    # Screenshot
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    driver.save_screenshot(os.path.join(SCREENSHOTS_DIR, "us17_01_tab_switching_and_navigation.png"))


@pytest.mark.django_db(transaction=True)
def test_tc17_02_zero_attempts_welcoming_state(driver):
    """
    TC-17-02: Zero Attempts Empty State & Practice CTA (AC 4)
    Verifies that a student with 0 previous practice takes sees [data-testid='trends-zero-state'],
    informative guidance copy, and a working CTA to /student/practice.
    """
    email = "zero_trends_student@careerflow.test"
    create_user_in_db(email, "ValidPass2026!", role=User.Role.STUDENT, full_name="Zero Takes Student")

    login_student(driver, email, "ValidPass2026!")

    # Navigate to Score Trends
    driver.get(f"{FRONTEND_URL}/student/videos?tab=trends")
    wait = WebDriverWait(driver, 10)

    # Verify zero state card
    zero_state = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='trends-zero-state']")))
    assert "No Presentation Takes Recorded Yet" in zero_state.text
    assert "Record or upload your first presentation practice take" in zero_state.text

    # Verify CTA button
    cta_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-start-first-trend-take']")
    assert "Record Your First Practice Take" in cta_btn.text

    # Click CTA and verify redirect to practice
    cta_btn.click()
    wait.until(EC.url_contains("/student/practice"))
    assert "/student/practice" in driver.current_url

    # Screenshot
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    driver.save_screenshot(os.path.join(SCREENSHOTS_DIR, "us17_02_zero_attempts_welcoming_state.png"))


@pytest.mark.django_db(transaction=True)
def test_tc17_03_single_attempt_baseline_state(driver):
    """
    TC-17-03: Single Attempt Baseline State & Benchmark Callout (AC 4)
    Verifies that a student with exactly 1 completed take receives [data-testid='trends-single-baseline-state'],
    with baseline benchmark metrics (overall, speech, visual presence) and second take prompt.
    """
    email = "single_take_student@careerflow.test"
    user = create_user_in_db(email, "ValidPass2026!", role=User.Role.STUDENT, full_name="Single Take Student")

    # Create exactly 1 completed video
    create_sample_trend_video(
        user=user,
        filename="baseline_pitch_attempt.mp4",
        overall_score=74,
        speech_score=72,
        behavioral_score=76,
        wpm=138.0,
        eye_score=75,
        posture_score=78
    )

    login_student(driver, email, "ValidPass2026!")

    # Navigate to Score Trends
    driver.get(f"{FRONTEND_URL}/student/videos?tab=trends")
    wait = WebDriverWait(driver, 10)

    # Verify single baseline card
    baseline_state = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='trends-single-baseline-state']")))
    state_text_upper = baseline_state.text.upper()
    assert "BASELINE TAKE REGISTERED" in state_text_upper
    assert "74 / 100" in baseline_state.text
    assert "SPEECH DYNAMICS" in state_text_upper
    assert "VISUAL PRESENCE" in state_text_upper

    # Verify CTA button
    cta_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-upload-second-take-cta']")
    assert "Record Second Attempt to Unlock Trends" in cta_btn.text

    # Verify CTA click navigation to practice
    cta_btn.click()
    wait.until(EC.url_contains("/student/practice"))
    assert "/student/practice" in driver.current_url

    # Screenshot
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    driver.save_screenshot(os.path.join(SCREENSHOTS_DIR, "us17_03_single_attempt_baseline_state.png"))


@pytest.mark.django_db(transaction=True)
def test_tc17_04_multi_attempt_dashboard_and_summary(driver):
    """
    TC-17-04: Multi-Attempt Score Trends Dashboard & Summary Stats (AC 1, AC 3)
    Verifies that a student with 3 chronological attempts sees [data-testid='score-trends-dashboard'],
    with trajectory banner, total delta (+18%), summary stat widgets (Latest, Personal Best, Average, Baseline),
    and progress highlights.
    """
    email = "multi_trends_student@careerflow.test"
    user = create_user_in_db(email, "ValidPass2026!", role=User.Role.STUDENT, full_name="Multi Takes Student")

    # Attempt 1 (7 days ago): 70/100
    create_sample_trend_video(
        user=user,
        filename="attempt_1_initial.mp4",
        overall_score=70,
        speech_score=68,
        behavioral_score=72,
        eye_score=68,
        wpm=130.0,
        days_ago=7
    )
    # Attempt 2 (3 days ago): 78/100
    create_sample_trend_video(
        user=user,
        filename="attempt_2_mid.mp4",
        overall_score=78,
        speech_score=76,
        behavioral_score=80,
        eye_score=78,
        wpm=140.0,
        days_ago=3
    )
    # Attempt 3 (today): 88/100
    create_sample_trend_video(
        user=user,
        filename="attempt_3_final.mp4",
        overall_score=88,
        speech_score=86,
        behavioral_score=90,
        eye_score=88,
        wpm=146.0,
        days_ago=0
    )

    login_student(driver, email, "ValidPass2026!")

    # Navigate to Score Trends
    driver.get(f"{FRONTEND_URL}/student/videos?tab=trends")
    wait = WebDriverWait(driver, 10)

    # Asserts main dashboard mounts
    dashboard = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='score-trends-dashboard']")))
    assert "Performance Improvement Curve" in dashboard.text
    assert "Across 3 Recorded Attempts" in dashboard.text

    # Asserts Total Delta widget (+18%)
    assert "+18%" in dashboard.text

    # Asserts Summary Stats
    dash_text_upper = dashboard.text.upper()
    assert "LATEST TAKE" in dash_text_upper
    assert "88" in dashboard.text
    assert "PERSONAL BEST" in dash_text_upper
    assert "AVERAGE SCORE" in dash_text_upper
    assert "78.7" in dashboard.text
    assert "BASELINE TAKE" in dash_text_upper
    assert "70" in dashboard.text

    # Asserts progress highlight badge
    assert "Eye contact improved by +20%" in dashboard.text or "Overall presentation score improved by +18%" in dashboard.text

    # Screenshot
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    driver.save_screenshot(os.path.join(SCREENSHOTS_DIR, "us17_04_multi_attempt_dashboard_and_summary.png"))


@pytest.mark.django_db(transaction=True)
def test_tc17_05_chart_series_toggle_interaction(driver):
    """
    TC-17-05: Chart Series Toggles & Curve Switching (AC 1, AC 2)
    Verifies all series filter pills:
    - [data-testid='toggle-chart-overall']
    - [data-testid='toggle-chart-categories']
    - [data-testid='toggle-chart-speech']
    - [data-testid='toggle-chart-behavioral']
    - [data-testid='toggle-chart-all']
    and ensures the Recharts line graph container remains intact and responsive.
    """
    email = "chart_toggle_student@careerflow.test"
    user = create_user_in_db(email, "ValidPass2026!", role=User.Role.STUDENT, full_name="Chart Student")

    # Populate 3 takes
    create_sample_trend_video(user, "take1.mp4", overall_score=72, days_ago=4)
    create_sample_trend_video(user, "take2.mp4", overall_score=80, days_ago=2)
    create_sample_trend_video(user, "take3.mp4", overall_score=86, days_ago=0)

    login_student(driver, email, "ValidPass2026!")

    driver.get(f"{FRONTEND_URL}/student/videos?tab=trends")
    wait = WebDriverWait(driver, 10)

    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='score-trends-dashboard']")))
    chart_container = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='recharts-line-container']")))
    assert chart_container.is_displayed()

    # 1. Toggle Speech vs. Behavioral (Categories)
    btn_categories = driver.find_element(By.CSS_SELECTOR, "[data-testid='toggle-chart-categories']")
    btn_categories.click()
    time.sleep(0.5)
    assert "bg-[#253142]" in btn_categories.get_attribute("class")

    # 2. Toggle Vocal Dynamics (Speech breakdown)
    btn_speech = driver.find_element(By.CSS_SELECTOR, "[data-testid='toggle-chart-speech']")
    btn_speech.click()
    time.sleep(0.5)
    assert "bg-[#253142]" in btn_speech.get_attribute("class")

    # 3. Toggle Visual Presence (Behavioral breakdown)
    btn_behavioral = driver.find_element(By.CSS_SELECTOR, "[data-testid='toggle-chart-behavioral']")
    btn_behavioral.click()
    time.sleep(0.5)
    assert "bg-[#253142]" in btn_behavioral.get_attribute("class")

    # 4. Toggle All Curves
    btn_all = driver.find_element(By.CSS_SELECTOR, "[data-testid='toggle-chart-all']")
    btn_all.click()
    time.sleep(0.5)
    assert "bg-[#253142]" in btn_all.get_attribute("class")

    # 5. Return to Overall
    btn_overall = driver.find_element(By.CSS_SELECTOR, "[data-testid='toggle-chart-overall']")
    btn_overall.click()
    time.sleep(0.5)
    assert "bg-[#253142]" in btn_overall.get_attribute("class")

    # Screenshot
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    driver.save_screenshot(os.path.join(SCREENSHOTS_DIR, "us17_05_chart_series_toggle_interaction.png"))


@pytest.mark.django_db(transaction=True)
def test_tc17_06_milestone_cards_and_navigation(driver):
    """
    TC-17-06: Milestone Cards Navigation to Analysis Report (AC 3, AC 6)
    Verifies that historical milestone take cards render with baseline comparison badges,
    and clicking [data-testid='milestone-take-card-1'] opens the corresponding presentation report.
    """
    email = "milestone_nav_student@careerflow.test"
    user = create_user_in_db(email, "ValidPass2026!", role=User.Role.STUDENT, full_name="Milestone Student")

    v1 = create_sample_trend_video(user, "milestone_1.mp4", overall_score=70, days_ago=5)
    v2 = create_sample_trend_video(user, "milestone_2.mp4", overall_score=82, days_ago=2)

    login_student(driver, email, "ValidPass2026!")

    driver.get(f"{FRONTEND_URL}/student/videos?tab=trends")
    wait = WebDriverWait(driver, 10)

    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='score-trends-dashboard']")))

    card1 = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='milestone-take-card-1']")))
    card2 = driver.find_element(By.CSS_SELECTOR, "[data-testid='milestone-take-card-2']")

    assert "Take #1" in card1.text
    assert "Starting Baseline" in card1.text
    assert "Take #2" in card2.text
    assert "+12% vs baseline" in card2.text

    # Scroll card1 into view and click
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", card1)
    time.sleep(0.5)
    driver.execute_script("arguments[0].click();", card1)

    # In VideoHistory tab mode, onSelectAttempt opens the in-page analysis modal or navigates to report
    time.sleep(1.0)
    # Check that either analysis modal mounted or URL navigated to history
    has_modal = len(driver.find_elements(By.CSS_SELECTOR, "[data-testid='past-analysis-detail-modal']")) > 0
    has_url = f"/presentation/history/{v1.id}" in driver.current_url
    assert has_modal or has_url

    # Screenshot
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    driver.save_screenshot(os.path.join(SCREENSHOTS_DIR, "us17_06_milestone_cards_and_navigation.png"))


@pytest.mark.django_db(transaction=True)
def test_tc17_07_tenant_isolation_trend_privacy(driver):
    """
    TC-17-07: Strict Tenant Isolation on Score Trends (AC 5)
    Student Alice has 3 practice takes. Student Bob has 1 practice take.
    Verifies Bob only sees his baseline take and never accesses or views Alice's scores or takes.
    """
    alice_email = "alice_trends_secure@careerflow.test"
    bob_email = "bob_trends_secure@careerflow.test"

    alice = create_user_in_db(alice_email, "ValidPass2026!", role=User.Role.STUDENT, full_name="Alice Secret")
    bob = create_user_in_db(bob_email, "ValidPass2026!", role=User.Role.STUDENT, full_name="Bob Regular")

    # Alice has 3 takes
    create_sample_trend_video(alice, "alice_executive_take1.mp4", overall_score=75, days_ago=4)
    create_sample_trend_video(alice, "alice_executive_take2.mp4", overall_score=85, days_ago=2)
    create_sample_trend_video(alice, "alice_executive_take3.mp4", overall_score=94, days_ago=0)

    # Bob has 1 take (score 64)
    create_sample_trend_video(bob, "bob_beginner_take1.mp4", overall_score=64, days_ago=1)

    # Log in as Bob
    login_student(driver, bob_email, "ValidPass2026!")

    # Bob goes to score trends
    driver.get(f"{FRONTEND_URL}/student/videos?tab=trends")
    wait = WebDriverWait(driver, 10)

    # Bob should see Single Baseline State (since he has only 1 video)
    baseline_card = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='trends-single-baseline-state']")))
    assert "64 / 100" in baseline_card.text

    # Assert Alice's confidential scores and filenames are NEVER exposed
    page_text = driver.find_element(By.TAG_NAME, "body").text
    assert "alice_executive" not in page_text
    assert "94 / 100" not in page_text
    assert "Across 3 Recorded Attempts" not in page_text

    # Screenshot
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    driver.save_screenshot(os.path.join(SCREENSHOTS_DIR, "us17_07_tenant_isolation_trend_privacy.png"))


@pytest.mark.django_db(transaction=True)
def test_tc17_08_dynamic_curve_update_after_attempt(driver):
    """
    TC-17-08: Dynamic Curve Update After New Attempt (AC 6)
    Verifies that when a student with 1 baseline attempt uploads a second attempt,
    the UI seamlessly transitions from single baseline state to full multi-attempt dashboard.
    """
    email = "dynamic_trend_student@careerflow.test"
    user = create_user_in_db(email, "ValidPass2026!", role=User.Role.STUDENT, full_name="Dynamic Student")

    # Initial Attempt 1
    create_sample_trend_video(user, "dynamic_take1.mp4", overall_score=72, days_ago=3)

    login_student(driver, email, "ValidPass2026!")

    driver.get(f"{FRONTEND_URL}/student/videos?tab=trends")
    wait = WebDriverWait(driver, 10)

    # 1. First state: Single baseline state
    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='trends-single-baseline-state']")))

    # 2. Simulate completing Attempt 2 in database
    create_sample_trend_video(user, "dynamic_take2.mp4", overall_score=84, days_ago=0)

    # 3. Reload page to fetch updated trends
    driver.refresh()
    time.sleep(1.0)

    # 4. Second state: Score trends dashboard with multi-attempt curve
    dashboard = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='score-trends-dashboard']")))
    assert "Performance Improvement Curve" in dashboard.text
    assert "+12%" in dashboard.text
    assert "Across 2 Recorded Attempts" in dashboard.text

    # Screenshot
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    driver.save_screenshot(os.path.join(SCREENSHOTS_DIR, "us17_08_dynamic_curve_update_after_attempt.png"))
