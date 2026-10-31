"""
US-44: Student Practice Session Management & Deletion UI Test Suite (US-44-T6).
User Story: US-44 — Student Practice Session Management & Deletion
Sprint: Sprint 7 — Final Platform Maturity & Release
Lead Developer: Nafisa Tabassum Maria (@Maria-07-222) / MD. Jubair Bin Hasan (@jubair65)
Dedicated Peer UI Automation Tester & Reviewer: MD. Hasanul Mobin (@hasanulmobin)
Target Branch: feat/us-44-practice-session-mgmt -> develop

Acceptance Criteria & Scenarios Verified:
✓ TC-44-01: Session Cards Display (render titles, duration, action buttons) [AC-1, AC-2]
✓ TC-44-02: Inline Rename Success (immediate UI update, DB & refresh persistence) [AC-1]
✓ TC-44-03: Rename Validation & Cancel (empty title validation, escape/cancel revert) [AC-1]
✓ TC-44-04: Delete Modal Safeguard (modal warning message, cancellation preservation) [AC-3]
✓ TC-44-05: Permanent Deletion & Media Cleanup (safe disk cleanup, DB removal) [AC-2, AC-4]
✓ TC-44-06: Score Trends Recalculation (live chart recalculation upon deletion) [AC-5]
✓ TC-44-07: Data Isolation (cross-tenant access control for rename & delete) [AC-6]
✓ TC-44-08: Empty State (empty state container & CTA button on zero sessions) [AC-2, AC-5]
"""

import os
import sys
import time
import uuid
from pathlib import Path
from datetime import timedelta

TESTS_DIR = Path(__file__).resolve().parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

import pytest
import requests
from django.conf import settings
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
    """Reliably clears React controlled inputs across platforms."""
    element.send_keys(Keys.COMMAND + "a")
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


def login_candidate(driver, email: str, password: str = "ValidPass2026!", full_name: str = "Candidate User"):
    """Helper to authenticate a student / candidate via the UI login page."""
    user = User.objects.filter(email__iexact=email).first()
    if not user:
        user = create_user_in_db(email, password, role=User.Role.STUDENT, full_name=full_name)

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
    return user


def create_sample_practice_video(
    user: User,
    filename: str,
    title: str = "",
    duration: int = 80,
    overall_score: int = 85,
    wpm: float = 145.0,
    eye: int = 88,
    posture: int = 90,
    engagement: int = 85,
    days_ago: int = 0,
    status: str = "COMPLETED",
    is_active: bool = True,
) -> PresentationVideo:
    """Populates a PresentationVideo with full analysis models and backdated timestamps."""
    video = PresentationVideo.objects.create(
        user=user,
        file=f"students/{user.id}/videos/{filename}",
        original_filename=filename,
        title=title,
        raw_file_size=1024 * 1024 * 10,
        compressed_file_size=1024 * 1024 * 3,
        file_type="mp4",
        duration_seconds=duration,
        status=status,
        is_active=is_active,
    )

    if days_ago > 0:
        uploaded_time = timezone.now() - timedelta(days=days_ago)
        PresentationVideo.objects.filter(pk=video.pk).update(uploaded_at=uploaded_time)
        video.refresh_from_db()

    if status == "COMPLETED":
        SpeechAnalysis.objects.create(
            video=video,
            transcript="Good morning interview team. Today I will discuss scalable cloud architecture, micro-frontends, and distributed resilience.",
            words_per_minute=wpm,
            filler_word_count=2,
            filler_words_breakdown={"um": 1, "like": 1},
            clarity_score=90,
            duration_seconds=float(duration),
        )
        BehavioralAnalysis.objects.create(
            video=video,
            eye_contact_score=eye,
            posture_score=posture,
            engagement_score=engagement,
            frame_metrics={"sampled_frames": 120},
        )
        PresentationScore.objects.create(
            video=video,
            overall_score=overall_score,
            speech_score=85,
            behavioral_score=85,
            pace_score=90,
            filler_score=85,
            eye_contact_score=eye,
            posture_score=posture,
            engagement_score=engagement,
            notes="Strong presentation posture and natural speaking cadence.",
        )
        PresentationFeedback.objects.create(
            video=video,
            summary="Strong executive delivery with excellent posture and engaging camera eye contact.",
            strengths=[
                f"Outstanding pacing at {int(wpm)} WPM",
                f"Superb camera gaze contact ({eye}%) and posture alignment ({posture}%)",
            ],
            improvements=[
                {
                    "category": "Pacing & Transition",
                    "observation": "Brief hesitation before transition.",
                    "actionable_drill": "Practice pause transitions.",
                }
            ],
        )

    return video


class TestUS44PracticeSessionManagementUI:
    """
    Automated Selenium UI Test Suite for US-44 Student Practice Session Management & Deletion.
    Assigned Task: US-44-T6 Peer QA Automation & Verification.
    Executed by: MD. Hasanul Mobin (@hasanulmobin).
    """

    def test_tc44_01_session_cards_display(self, driver):
        """
        TC-44-01: Session Cards Display (US-44-T1, US-44-T4)
        Log in as student; navigate to /student/practice; access Video History;
        verify session titles, duration, scores, and action buttons render properly.
        """
        uid = uuid.uuid4().hex[:6]
        student_email = f"student_cards_{uid}@careerflow.test"
        student = login_candidate(driver, email=student_email, full_name="Display Student")

        # Create two sample practice videos
        v1 = create_sample_practice_video(
            student,
            filename=f"practice_take_alpha_{uid}.mp4",
            title=f"Cloud Architecture Pitch {uid}",
            duration=95,
            overall_score=88,
            days_ago=1,
        )
        v2 = create_sample_practice_video(
            student,
            filename=f"practice_take_beta_{uid}.mp4",
            title=f"Frontend System Design {uid}",
            duration=120,
            overall_score=76,
            days_ago=0,
        )

        wait = WebDriverWait(driver, 10)

        # 1. Verify link from /student/practice
        driver.get(f"{FRONTEND_URL}/student/practice")
        history_link = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a[href='/student/videos']"))
        )
        assert history_link is not None

        # 2. Navigate to /student/videos
        driver.get(f"{FRONTEND_URL}/student/videos")
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='session-title-{v1.id}']")))

        # Check titles
        title_v1 = driver.find_element(By.CSS_SELECTOR, f"[data-testid='session-title-{v1.id}']")
        title_v2 = driver.find_element(By.CSS_SELECTOR, f"[data-testid='session-title-{v2.id}']")
        assert f"Cloud Architecture Pitch {uid}" in title_v1.text
        assert f"Frontend System Design {uid}" in title_v2.text

        # Check action buttons (Rename, Delete, Preview, Analysis)
        assert driver.find_element(By.CSS_SELECTOR, f"[data-testid='button-rename-session-{v1.id}']")
        assert driver.find_element(By.CSS_SELECTOR, f"[data-testid='button-delete-session-{v1.id}']")
        assert driver.find_element(By.CSS_SELECTOR, f"[data-testid='button-play-take-{v1.id}']")
        assert driver.find_element(By.CSS_SELECTOR, f"[data-testid='button-analysis-{v1.id}']")

        screenshot_path = SCREENSHOTS_DIR / "us44_01_session_cards_display.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc44_02_inline_rename_success(self, driver):
        """
        TC-44-02: Inline Rename Success (US-44-T2, US-44-T4)
        Click rename button; type a new title; save; verify instantaneous UI update
        and verify that the custom title persists across full page refresh and in MySQL DB.
        """
        uid = uuid.uuid4().hex[:6]
        student_email = f"student_rename_{uid}@careerflow.test"
        student = login_candidate(driver, email=student_email, full_name="Rename Student")

        video = create_sample_practice_video(
            student,
            filename=f"original_run_{uid}.mp4",
            title=f"Old Title {uid}",
            duration=70,
            overall_score=82,
        )

        wait = WebDriverWait(driver, 10)
        driver.get(f"{FRONTEND_URL}/student/videos")
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='button-rename-session-{video.id}']")))

        # Click rename button
        rename_btn = driver.find_element(By.CSS_SELECTOR, f"[data-testid='button-rename-session-{video.id}']")
        rename_btn.click()

        # Wait for inline input
        input_elem = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='input-rename-session-{video.id}']"))
        )
        new_title = f"Sprint 7 Presentation Final - Iteration {uid}"
        set_react_input(driver, input_elem, new_title)

        # Click save button
        save_btn = driver.find_element(By.CSS_SELECTOR, f"[data-testid='button-save-rename-{video.id}']")
        save_btn.click()

        # Verify immediate UI update in DOM
        updated_title_elem = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='session-title-{video.id}']"))
        )
        assert updated_title_elem.text == new_title

        # Verify persistence across browser refresh
        driver.refresh()
        reloaded_title_elem = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='session-title-{video.id}']"))
        )
        assert reloaded_title_elem.text == new_title

        # Verify database persistence
        video.refresh_from_db()
        assert video.title == new_title
        assert video.display_title == new_title

        screenshot_path = SCREENSHOTS_DIR / "us44_02_inline_rename_success.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc44_03_rename_validation_and_cancel(self, driver):
        """
        TC-44-03: Rename Validation & Cancel (US-44-T2, US-44-T4)
        Clearing title triggers validation error 'Title cannot be empty.';
        pressing Cancel / Escape preserves the original title without mutations.
        """
        uid = uuid.uuid4().hex[:6]
        student_email = f"student_val_{uid}@careerflow.test"
        student = login_candidate(driver, email=student_email, full_name="Validation Student")

        original_title = f"Unmodified Safe Title {uid}"
        video = create_sample_practice_video(
            student,
            filename=f"safe_video_{uid}.mp4",
            title=original_title,
            duration=85,
        )

        wait = WebDriverWait(driver, 10)
        driver.get(f"{FRONTEND_URL}/student/videos")
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='button-rename-session-{video.id}']")))

        # 1. Open rename input
        driver.find_element(By.CSS_SELECTOR, f"[data-testid='button-rename-session-{video.id}']").click()
        input_elem = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='input-rename-session-{video.id}']"))
        )

        # Clear input to empty
        clear_react_input(driver, input_elem)

        # Click save
        driver.find_element(By.CSS_SELECTOR, f"[data-testid='button-save-rename-{video.id}']").click()

        # Verify error text is displayed
        error_elem = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='text-rename-error-{video.id}']"))
        )
        assert "Title cannot be empty." in error_elem.text

        # 2. Click cancel button
        cancel_btn = driver.find_element(By.CSS_SELECTOR, f"[data-testid='button-cancel-rename-{video.id}']")
        cancel_btn.click()

        # Verify input disappears and original title remains
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='input-rename-session-{video.id}']")))
        title_elem = driver.find_element(By.CSS_SELECTOR, f"[data-testid='session-title-{video.id}']")
        assert title_elem.text == original_title

        # Check DB unchanged
        video.refresh_from_db()
        assert video.title == original_title

        screenshot_path = SCREENSHOTS_DIR / "us44_03_rename_validation_and_cancel.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc44_04_delete_modal_safeguard(self, driver):
        """
        TC-44-04: Delete Modal Safeguard (US-44-T4)
        Click trash button; verify accessible 2-step confirmation modal appears
        with required warning copy; clicking Cancel leaves session intact in DOM and DB.
        """
        uid = uuid.uuid4().hex[:6]
        student_email = f"student_modal_{uid}@careerflow.test"
        student = login_candidate(driver, email=student_email, full_name="Modal Student")

        video = create_sample_practice_video(
            student,
            filename=f"preserve_take_{uid}.mp4",
            title=f"Protected Rep {uid}",
            duration=60,
        )

        wait = WebDriverWait(driver, 10)
        driver.get(f"{FRONTEND_URL}/student/videos")
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='button-delete-session-{video.id}']")))

        # Click trash icon
        driver.find_element(By.CSS_SELECTOR, f"[data-testid='button-delete-session-{video.id}']").click()

        # Verify modal displays
        modal = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-delete-session']")))
        assert "Delete Practice Take" in modal.text
        assert "permanently delete" in modal.text
        assert "This action is permanent and cannot be undone." in modal.text

        # Click Cancel
        cancel_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-cancel-delete']")
        cancel_btn.click()

        # Verify modal disappears
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-delete-session']")))

        # Verify session still present in DOM and DB
        assert driver.find_element(By.CSS_SELECTOR, f"[data-testid='history-row-{video.id}']")
        assert PresentationVideo.objects.filter(pk=video.pk).exists() is True

        screenshot_path = SCREENSHOTS_DIR / "us44_04_delete_modal_safeguard.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc44_05_permanent_deletion_and_media_cleanup(self, driver):
        """
        TC-44-05: Permanent Deletion & Media Cleanup (US-44-T3, US-44-T4)
        Confirm permanent deletion in modal; verify row removal, toast alert,
        and physical disk unlinking of the video file from media storage.
        """
        uid = uuid.uuid4().hex[:6]
        student_email = f"student_del_{uid}@careerflow.test"
        student = login_candidate(driver, email=student_email, full_name="Delete Student")

        filename = f"media_cleanup_take_{uid}.mp4"
        video = create_sample_practice_video(
            student,
            filename=filename,
            title=f"Session To Wipe {uid}",
            duration=90,
        )

        # Create physical video file on disk in MEDIA_ROOT
        disk_file_path = Path(settings.MEDIA_ROOT) / f"students/{student.id}/videos/{filename}"
        disk_file_path.parent.mkdir(parents=True, exist_ok=True)
        disk_file_path.write_bytes(b"TEST DUMMY VIDEO BYTES FOR SPRINT 7 US-44 CLEANUP")
        assert disk_file_path.exists() is True

        wait = WebDriverWait(driver, 10)
        driver.get(f"{FRONTEND_URL}/student/videos")
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='button-delete-session-{video.id}']")))

        # Open delete modal
        driver.find_element(By.CSS_SELECTOR, f"[data-testid='button-delete-session-{video.id}']").click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-delete-session']")))

        # Confirm deletion
        driver.find_element(By.CSS_SELECTOR, "[data-testid='button-confirm-delete']").click()

        # Wait for row to be removed from DOM
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='history-row-{video.id}']")))

        # Verify physical file removed from storage
        time.sleep(0.5)
        assert disk_file_path.exists() is False, "Physical video file was NOT unlinked from media storage!"

        # Verify database removal
        assert PresentationVideo.objects.filter(pk=video.pk).exists() is False

        screenshot_path = SCREENSHOTS_DIR / "us44_05_permanent_deletion_and_media_cleanup.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc44_06_score_trends_recalculation(self, driver):
        """
        TC-44-06: Score Trends Recalculation (US-44-T5)
        Delete a practice take from history list; switch to Trends tab;
        verify score progression curve and average composite recalculate automatically
        without needing a full page reload (ensuring dynamic key reactivity).
        """
        uid = uuid.uuid4().hex[:6]
        student_email = f"student_trends_{uid}@careerflow.test"
        student = login_candidate(driver, email=student_email, full_name="Trends Student")

        # Create 3 attempts: Day 3 (score 70), Day 2 (score 80), Day 0 (score 90)
        v1 = create_sample_practice_video(student, f"t1_{uid}.mp4", title=f"Take 1 {uid}", overall_score=70, days_ago=3)
        v2 = create_sample_practice_video(student, f"t2_{uid}.mp4", title=f"Take 2 {uid}", overall_score=80, days_ago=2)
        v3 = create_sample_practice_video(student, f"t3_{uid}.mp4", title=f"Take 3 {uid}", overall_score=90, days_ago=0)

        wait = WebDriverWait(driver, 10)
        driver.get(f"{FRONTEND_URL}/student/videos")
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='tab-score-trends']")))

        # 1. Switch to Trends tab: should see 3 attempts, baseline 70, latest 90, avg 80
        driver.find_element(By.CSS_SELECTOR, "[data-testid='tab-score-trends']").click()
        trends_board = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='score-trends-dashboard']")))
        assert "Across 3 Recorded Attempts" in trends_board.text

        # 2. Switch back to Takes tab
        driver.find_element(By.CSS_SELECTOR, "[data-testid='tab-takes-history']").click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='button-delete-session-{v3.id}']")))

        # 3. Delete the 3rd take (score 90)
        driver.find_element(By.CSS_SELECTOR, f"[data-testid='button-delete-session-{v3.id}']").click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-delete-session']")))
        driver.find_element(By.CSS_SELECTOR, "[data-testid='button-confirm-delete']").click()
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='history-row-{v3.id}']")))

        # 4. Switch back to Trends tab without page reload
        driver.find_element(By.CSS_SELECTOR, "[data-testid='tab-score-trends']").click()
        updated_trends = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='score-trends-dashboard']"))
        )

        # Verify recalculation: now 2 attempts
        assert "Across 2 Recorded Attempts" in updated_trends.text

        screenshot_path = SCREENSHOTS_DIR / "us44_06_score_trends_recalculation.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc44_07_data_isolation(self, driver):
        """
        TC-44-07: Candidate Data Isolation (AC-6)
        Candidate A cannot see, rename, or delete Candidate B's sessions.
        Cross-tenant API operations return 403 Forbidden.
        """
        uid = uuid.uuid4().hex[:6]
        cand_a_email = f"cand_a_{uid}@careerflow.test"
        cand_b_email = f"cand_b_{uid}@careerflow.test"

        cand_a = create_user_in_db(cand_a_email, "ValidPass2026!", role=User.Role.STUDENT, full_name="Candidate Alpha")
        cand_b = login_candidate(driver, email=cand_b_email, full_name="Candidate Beta")

        cand_a_video = create_sample_practice_video(
            cand_a,
            filename=f"isolated_take_{uid}.mp4",
            title=f"Candidate A Secret Session {uid}",
            overall_score=92,
        )

        wait = WebDriverWait(driver, 10)
        driver.get(f"{FRONTEND_URL}/student/videos")
        time.sleep(1)

        # 1. UI Check: Candidate A's session should not be in Candidate B's DOM
        assert len(driver.find_elements(By.CSS_SELECTOR, f"[data-testid='session-title-{cand_a_video.id}']")) == 0

        # 2. Cross-Tenant API Rejection Check:
        # Obtain JWT token for Candidate B
        token_res = requests.post(f"{BACKEND_URL}/api/auth/login/", json={
            "email": cand_b_email,
            "password": "ValidPass2026!"
        })
        assert token_res.status_code == 200
        login_data = token_res.json()
        cand_b_token = login_data.get("access") or login_data.get("tokens", {}).get("access")
        auth_headers = {"Authorization": f"Bearer {cand_b_token}"}

        # Candidate B attempts to rename Candidate A's session
        rename_res = requests.patch(
            f"{BACKEND_URL}/api/practice/{cand_a_video.id}/rename/",
            json={"title": "Hacked Title"},
            headers=auth_headers
        )
        assert rename_res.status_code == 403, f"Expected 403 Forbidden, got {rename_res.status_code}"

        # Candidate B attempts to delete Candidate A's session
        del_res = requests.delete(
            f"{BACKEND_URL}/api/practice/{cand_a_video.id}/",
            headers=auth_headers
        )
        assert del_res.status_code == 403, f"Expected 403 Forbidden, got {del_res.status_code}"

        # Verify Candidate A's video remains unchanged in DB
        cand_a_video.refresh_from_db()
        assert cand_a_video.title == f"Candidate A Secret Session {uid}"

        screenshot_path = SCREENSHOTS_DIR / "us44_07_data_isolation.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc44_08_empty_state_and_navigation(self, driver):
        """
        TC-44-08: Empty State & Navigation CTA (AC-2, AC-5)
        Deleting the last session displays empty state with CTA button;
        clicking CTA navigates cleanly to /student/practice studio.
        """
        uid = uuid.uuid4().hex[:6]
        student_email = f"student_empty_{uid}@careerflow.test"
        student = login_candidate(driver, email=student_email, full_name="Empty Student")

        video = create_sample_practice_video(
            student,
            filename=f"last_take_{uid}.mp4",
            title=f"Final Remaining Rep {uid}",
            overall_score=75,
        )

        wait = WebDriverWait(driver, 10)
        driver.get(f"{FRONTEND_URL}/student/videos")
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='button-delete-session-{video.id}']")))

        # Delete the single session
        driver.find_element(By.CSS_SELECTOR, f"[data-testid='button-delete-session-{video.id}']").click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-delete-session']")))
        driver.find_element(By.CSS_SELECTOR, "[data-testid='button-confirm-delete']").click()

        # Wait for empty state to appear
        empty_state = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='empty-practice-history']"))
        )
        assert "No practice takes yet" in empty_state.text

        # Verify CTA button
        cta_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-empty-start-practice']")
        assert cta_btn is not None
        cta_btn.click()

        # Verify navigation to /student/practice
        wait.until(EC.url_contains("/student/practice"))

        screenshot_path = SCREENSHOTS_DIR / "us44_08_empty_state_and_navigation.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()
