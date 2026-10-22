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
from selenium.webdriver.support.ui import WebDriverWait, Select
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


def login_student(driver, email: str, password: str = "ValidPass2026!", full_name: str = "Maria Candidate"):
    """Helper to ensure student exists and logs in via UI."""
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


def create_sample_presentation_video(
    user: User,
    filename: str,
    duration: int = 75,
    overall_score: int = 85,
    wpm: float = 145.0,
    eye: int = 88,
    posture: int = 90,
    engagement: int = 85,
    days_ago: int = 0,
    status: str = 'COMPLETED'
) -> PresentationVideo:
    """Populates a PresentationVideo with full analysis models and backdated timestamps."""
    video = PresentationVideo.objects.create(
        user=user,
        file=f"students/{user.id}/videos/{filename}",
        original_filename=filename,
        raw_file_size=1024 * 1024 * 12,
        compressed_file_size=1024 * 1024 * 4,
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
            transcript="Good morning interview team. Today I will discuss scalable cloud architecture, micro-frontends, and distributed resilience.",
            words_per_minute=wpm,
            filler_word_count=2,
            filler_words_breakdown={"um": 1, "like": 1},
            clarity_score=92,
            duration_seconds=float(duration)
        )
        BehavioralAnalysis.objects.create(
            video=video,
            eye_contact_score=eye,
            posture_score=posture,
            engagement_score=engagement,
            frame_metrics={"sampled_frames": 150}
        )
        PresentationScore.objects.create(
            video=video,
            overall_score=overall_score,
            speech_score=88,
            behavioral_score=87,
            pace_score=90,
            filler_score=85,
            eye_contact_score=eye,
            posture_score=posture,
            engagement_score=engagement,
            has_behavioral_data=True
        )
        PresentationFeedback.objects.create(
            video=video,
            summary="Strong executive delivery with excellent posture and engaging camera eye contact.",
            strengths=[
                f"Outstanding pacing at {int(wpm)} WPM",
                f"Superb camera gaze contact ({eye}%) and posture alignment ({posture}%)"
            ],
            improvements=[
                {
                    "category": "Pacing & Transition",
                    "observation": "Brief hesitation before transition to technical trade-offs.",
                    "actionable_drill": "Practice deliberate transitional phrasing between topic points."
                }
            ],
            practice_tip="Maintain measured, steady diaphragmatic breathing during key technical points."
        )

    return video


class TestUS16PresentationHistoryUI:
    """
    US-16: View Previous Presentation Analysis Results
    Sprint: Sprint 6 (Epic 4: Video Presentation & AI)
    Reviewer / QA: Nafisa Tabassum Maria (@Maria-07-222)

    Acceptance Criteria Coverage:
    - AC 1: Student can view a list of their past presentation analyses
    - AC 2: Student can open any past analysis to view composite score, speech metrics, behavioral signals, and AI suggestions
    - AC 3: Results are listed chronologically, newest first (-uploaded_at)
    - AC 4: Strict tenant isolation: Students can only view their own presentation analyses (403 Forbidden on foreign access)
    - AC 5: Empty state displays a clear, welcoming graphic and call-to-action button linking to /student/practice
    - AC 6: High performance response time (<1.2s under standard network)
    """

    def test_tc16_01_empty_history_renders_welcoming_state_and_cta(self, driver):
        """TC-16-01: When student has no past takes, renders welcoming empty state and CTA to practice (AC 5)."""
        email = "maria_cand_empty@careerflow.test"
        login_student(driver, email=email, full_name="Maria Empty Take")

        # Navigate to Video History
        driver.get(f"{FRONTEND_URL}/student/videos")
        wait = WebDriverWait(driver, 10)

        # Verify page titles and eyebrow
        eyebrow = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='heading-eyebrow']")))
        assert "PRESENTATION HISTORY" in eyebrow.text.upper()

        heading = driver.find_element(By.CSS_SELECTOR, "[data-testid='heading-title']")
        assert "Your reps, in one place." in heading.text

        # Verify AC 5 Empty State Card
        empty_state = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='history-empty-state']")))
        assert empty_state.is_displayed()
        assert "No practice takes yet" in empty_state.text
        assert "Record or upload your first 1 to 3 minute presentation" in empty_state.text

        # Capture screenshot for reporting
        screenshot_path = SCREENSHOTS_DIR / "us16_01_empty_history_welcoming_state.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

        # Click CTA and verify navigation to /student/practice
        cta_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-empty-start-practice']")
        cta_btn.click()
        wait.until(EC.url_contains("/student/practice"))
        assert "/student/practice" in driver.current_url

    def test_tc16_02_video_history_table_and_trajectory_metrics(self, driver):
        """TC-16-02: Renders trajectory metrics (Reps, Avg Score, Best Score, Pace) and table rows (AC 1 & AC 2)."""
        email = "maria_cand_history@careerflow.test"
        user = create_user_in_db(email, "ValidPass2026!", role=User.Role.STUDENT, full_name="Maria Presenter")

        # Create 3 takes with varying scores and metrics
        create_sample_presentation_video(user, "cloud_pitch_take1.mp4", duration=70, overall_score=88, wpm=145.0, eye=90, posture=92, days_ago=2)
        create_sample_presentation_video(user, "system_design_take2.mp4", duration=85, overall_score=78, wpm=138.0, eye=80, posture=84, days_ago=1)
        create_sample_presentation_video(user, "lead_arch_take3.mp4", duration=60, overall_score=92, wpm=150.0, eye=94, posture=95, days_ago=0)

        login_student(driver, email=email, full_name="Maria Presenter")
        driver.get(f"{FRONTEND_URL}/student/videos")
        wait = WebDriverWait(driver, 10)

        # Verify Trajectory Metric Cards
        total_reps = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='stat-total-takes']")))
        assert total_reps.text == "3"

        best_score = driver.find_element(By.CSS_SELECTOR, "[data-testid='stat-best-score']")
        assert "92/100" in best_score.text

        avg_score = driver.find_element(By.CSS_SELECTOR, "[data-testid='stat-avg-score']")
        assert "86/100" in avg_score.text  # (88 + 78 + 92) / 3 = 86

        avg_pace = driver.find_element(By.CSS_SELECTOR, "[data-testid='stat-avg-pace']")
        assert "144 WPM" in avg_pace.text  # (145 + 138 + 150) / 3 = 144.3

        # Verify all 3 video rows are displayed in the table
        rows = driver.find_elements(By.XPATH, "//div[starts-with(@data-testid, 'history-row-')]")
        assert len(rows) == 3

        # Verify title and AI metric badges on row
        assert "lead_arch_take3" in driver.page_source
        assert "cloud_pitch_take1" in driver.page_source
        assert "system_design_take2" in driver.page_source

        # Capture screenshot for reporting
        screenshot_path = SCREENSHOTS_DIR / "us16_02_video_history_table_and_trajectory_metrics.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc16_03_chronological_ordering_and_sorting(self, driver):
        """TC-16-03: Videos are ordered newest first (-uploaded_at) by default; tests interactive sorting (AC 3)."""
        email = "maria_cand_chronological@careerflow.test"
        user = create_user_in_db(email, "ValidPass2026!", role=User.Role.STUDENT, full_name="Maria Chrono")

        v_old = create_sample_presentation_video(user, "first_take_2026_old.mp4", duration=60, overall_score=70, days_ago=3)
        v_mid = create_sample_presentation_video(user, "second_take_2026_mid.mp4", duration=80, overall_score=85, days_ago=1)
        v_new = create_sample_presentation_video(user, "latest_take_2026_new.mp4", duration=90, overall_score=95, days_ago=0)

        login_student(driver, email=email, full_name="Maria Chrono")
        driver.get(f"{FRONTEND_URL}/student/videos")
        wait = WebDriverWait(driver, 10)

        # 1. Assert default chronological ordering: newest take is the first row
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='history-row-{v_new.id}']")))
        rows = driver.find_elements(By.XPATH, "//div[starts-with(@data-testid, 'history-row-')]")
        assert rows[0].get_attribute("data-testid") == f"history-row-{v_new.id}"
        assert rows[2].get_attribute("data-testid") == f"history-row-{v_old.id}"

        # 2. Test interactive sort: "Oldest First"
        sort_select = Select(driver.find_element(By.CSS_SELECTOR, "[data-testid='select-history-sort']"))
        sort_select.select_by_value("OLDEST")
        time.sleep(0.3)
        rows_sorted = driver.find_elements(By.XPATH, "//div[starts-with(@data-testid, 'history-row-')]")
        assert rows_sorted[0].get_attribute("data-testid") == f"history-row-{v_old.id}"

        # 3. Test interactive sort: "Highest Score"
        sort_select.select_by_value("SCORE_HIGH")
        time.sleep(0.3)
        rows_by_score = driver.find_elements(By.XPATH, "//div[starts-with(@data-testid, 'history-row-')]")
        assert rows_by_score[0].get_attribute("data-testid") == f"history-row-{v_new.id}"

        # Capture screenshot of sorting and chronological ordering
        screenshot_path = SCREENSHOTS_DIR / "us16_03_chronological_ordering_and_sorting.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc16_04_instant_search_and_status_filtering(self, driver):
        """TC-16-04: Instant search by filename and status dropdown filtering (AC 1 & AC 3)."""
        email = "maria_cand_search@careerflow.test"
        user = create_user_in_db(email, "ValidPass2026!", role=User.Role.STUDENT, full_name="Maria Searcher")

        v1 = create_sample_presentation_video(user, "executive_ai_pitch.mp4", duration=75, overall_score=90)
        v2 = create_sample_presentation_video(user, "devops_interview_drill.mp4", duration=65, overall_score=82)
        v3 = create_sample_presentation_video(user, "failed_take_sample.mp4", duration=40, status='FAILED')

        login_student(driver, email=email, full_name="Maria Searcher")
        driver.get(f"{FRONTEND_URL}/student/videos")
        wait = WebDriverWait(driver, 10)

        # 1. Search by filename substring
        search_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-history-search']")))
        clear_react_input(driver, search_input)
        search_input.send_keys("executive")
        time.sleep(0.3)

        visible_rows = driver.find_elements(By.XPATH, "//div[starts-with(@data-testid, 'history-row-')]")
        assert len(visible_rows) == 1
        assert f"history-row-{v1.id}" in visible_rows[0].get_attribute("data-testid")

        # Clear search
        clear_react_input(driver, search_input)
        time.sleep(0.3)
        assert len(driver.find_elements(By.XPATH, "//div[starts-with(@data-testid, 'history-row-')]")) == 3

        # 2. Filter by Status: "Failed"
        status_select = Select(driver.find_element(By.CSS_SELECTOR, "[data-testid='select-history-status']"))
        status_select.select_by_value("FAILED")
        time.sleep(0.3)
        failed_rows = driver.find_elements(By.XPATH, "//div[starts-with(@data-testid, 'history-row-')]")
        assert len(failed_rows) == 1
        assert f"history-row-{v3.id}" in failed_rows[0].get_attribute("data-testid")

        # Capture screenshot of search and status filtering
        screenshot_path = SCREENSHOTS_DIR / "us16_04_instant_search_and_status_filtering.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc16_05_in_page_analysis_modal_composite_score_and_breakdown(self, driver):
        """TC-16-05: Opening past analysis modal displays composite score, speech breakdown, vision signals & AI tips (AC 2)."""
        email = "maria_cand_modal@careerflow.test"
        user = create_user_in_db(email, "ValidPass2026!", role=User.Role.STUDENT, full_name="Maria Modal")

        v = create_sample_presentation_video(user, "keynote_presentation.mp4", duration=80, overall_score=89, wpm=146.0, eye=91, posture=93, engagement=87)

        login_student(driver, email=email, full_name="Maria Modal")
        driver.get(f"{FRONTEND_URL}/student/videos")
        wait = WebDriverWait(driver, 10)

        # Click Sparkles action button to open analysis modal
        analysis_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-analysis-{v.id}']")))
        analysis_btn.click()

        # Verify modal mounts
        modal = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='past-analysis-detail-modal']")))
        assert modal.is_displayed()

        # Assert title and composite score display
        assert "keynote_presentation" in modal.text
        assert "89" in modal.text

        # Assert Speech & Articulation breakdown (146 WPM)
        assert "146" in modal.text
        assert "WPM" in modal.text

        # Assert Behavioral Vision signals (Eye contact 91%, Posture 93%)
        assert "91%" in modal.text or "91" in modal.text
        assert "93%" in modal.text or "93" in modal.text

        # Assert AI Coaching Suggestions
        assert "Strong executive delivery" in modal.text

        # Assert Speech Transcript is rendered
        assert "distributed resilience" in modal.text

        # Capture screenshot of in-page analysis modal
        screenshot_path = SCREENSHOTS_DIR / "us16_05_in_page_analysis_modal_composite_score.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

        # Dismiss modal via close button
        close_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-close-analysis-modal']")
        close_btn.click()
        time.sleep(0.3)
        assert len(driver.find_elements(By.CSS_SELECTOR, "[data-testid='past-analysis-detail-modal']")) == 0

    def test_tc16_06_video_preview_player_modal(self, driver):
        """TC-16-06: Clicking play button opens preview playback modal with formatted specs and mirror controls."""
        email = "maria_cand_player@careerflow.test"
        user = create_user_in_db(email, "ValidPass2026!", role=User.Role.STUDENT, full_name="Maria Player")
        v = create_sample_presentation_video(user, "playback_drill.mp4", duration=75, overall_score=85)

        login_student(driver, email=email, full_name="Maria Player")
        driver.get(f"{FRONTEND_URL}/student/videos")
        wait = WebDriverWait(driver, 10)

        # Click play button
        play_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-play-take-{v.id}']")))
        play_btn.click()

        # Verify preview modal mounts
        playback_player = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='history-modal-playback']")))
        assert playback_player.is_displayed()

        # Verify specs banner
        assert "01:15" in driver.page_source

        # Capture screenshot of video preview modal
        screenshot_path = SCREENSHOTS_DIR / "us16_06_video_preview_player_modal.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc16_07_dedicated_standalone_report_page(self, driver):
        """TC-16-07: Fullscreen standalone report page (/presentation/history/:id) with copyable transcript (AC 2)."""
        email = "maria_cand_standalone@careerflow.test"
        user = create_user_in_db(email, "ValidPass2026!", role=User.Role.STUDENT, full_name="Maria Standalone")
        v = create_sample_presentation_video(user, "comprehensive_report.mp4", duration=90, overall_score=94, wpm=148.0, eye=92, posture=95)

        login_student(driver, email=email, full_name="Maria Standalone")

        # Navigate directly to dedicated report URL
        driver.get(f"{FRONTEND_URL}/presentation/history/{v.id}")
        wait = WebDriverWait(driver, 10)

        # Verify dedicated standalone page mounted
        title = wait.until(EC.visibility_of_element_located((By.XPATH, "//h1[contains(text(), 'comprehensive_report')]")))
        assert title.is_displayed()

        # Assert composite score gauge
        assert "94" in driver.page_source

        # Verify 1-click transcript copy button
        copy_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(., 'Copy') or @data-testid='button-copy-transcript']")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", copy_btn)
        time.sleep(0.3)
        assert copy_btn.is_displayed()
        driver.execute_script("arguments[0].click();", copy_btn)

        # Capture screenshot of standalone report page
        screenshot_path = SCREENSHOTS_DIR / "us16_07_dedicated_standalone_report_page.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

        # Verify back navigation button returns to /student/videos
        back_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(., 'Back to') or @data-testid='button-back-to-history']")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", back_btn)
        assert back_btn.is_displayed()
        driver.execute_script("arguments[0].click();", back_btn)

        wait.until(EC.url_contains("/student/videos"))
        assert "/student/videos" in driver.current_url

    def test_tc16_08_strict_tenant_isolation_403_forbidden(self, driver):
        """TC-16-08: Cross-student tenant isolation: Students cannot see or access foreign presentation videos (AC 4)."""
        # Student Alice creates a private take
        alice = create_user_in_db("alice_private_cand@careerflow.test", "ValidPass2026!", role=User.Role.STUDENT, full_name="Alice Owner")
        v_alice = create_sample_presentation_video(alice, "alice_confidential_pitch.mp4", overall_score=95)

        # Student Bob logs in
        bob = create_user_in_db("bob_intruder_cand@careerflow.test", "ValidPass2026!", role=User.Role.STUDENT, full_name="Bob Intruder")
        login_student(driver, email="bob_intruder_cand@careerflow.test", full_name="Bob Intruder")

        # 1. Bob views /student/videos -> Alice's video is NOT listed in Bob's history
        driver.get(f"{FRONTEND_URL}/student/videos")
        wait = WebDriverWait(driver, 10)
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='history-empty-state']")))
        assert "alice_confidential_pitch" not in driver.page_source

        # 2. Bob directly navigates to Alice's presentation report URL (/presentation/history/{v_alice.id})
        driver.get(f"{FRONTEND_URL}/presentation/history/{v_alice.id}")

        # Assert 403 Forbidden Access Denied warning is displayed
        forbidden_alert = wait.until(EC.visibility_of_element_located((By.XPATH, "//*[contains(text(), 'Access Denied')]")))
        assert forbidden_alert.is_displayed()
        assert "You do not have permission to view another student’s presentation analysis" in driver.page_source

        # Assert Alice's confidential presentation title, transcript, and AI feedback are NOT exposed
        assert "alice_confidential_pitch" not in driver.page_source
        assert "distributed resilience" not in driver.page_source
        assert len(driver.find_elements(By.CSS_SELECTOR, "[data-testid='button-copy-transcript']")) == 0

        # Capture screenshot of 403 Forbidden access barrier
        screenshot_path = SCREENSHOTS_DIR / "us16_08_tenant_isolation_foreign_access_blocked.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc16_09_high_performance_endpoint_latency(self):
        """TC-16-09: Endpoint latency test confirms history endpoint responds well under 1.2s (<400ms) (AC 6)."""
        email = "maria_perf_student@careerflow.test"
        password = "ValidPass2026!"
        user = create_user_in_db(email, password, role=User.Role.STUDENT)

        # Create multiple takes to verify prefetch performance
        for i in range(5):
            create_sample_presentation_video(user, f"perf_take_{i}.mp4", overall_score=80 + i)

        # Authenticate via JWT
        login_resp = requests.post(f"{BACKEND_URL}/api/auth/login/", json={"email": email, "password": password})
        assert login_resp.status_code == 200
        token = login_resp.json()["access"]
        headers = {"Authorization": f"Bearer {token}"}

        # Measure GET /api/presentation/history/ latency
        start_time = time.perf_counter()
        resp = requests.get(f"{BACKEND_URL}/api/presentation/history/", headers=headers)
        elapsed_time = time.perf_counter() - start_time

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 5

        # AC 6: Latency must be < 1.2 seconds (typically < 0.25s)
        assert elapsed_time < 1.2, f"Latency {elapsed_time:.3f}s exceeded 1.2s threshold!"
        print(f"\n[Performance Benchmark]: History API response time = {elapsed_time * 1000:.1f}ms (< 1200ms limit)")
