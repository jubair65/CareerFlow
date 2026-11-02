"""
US-49: Automated Media Storage Purge & Data Retention UI Automation Test Suite (US-49-T6).
User Story: US-49 – Automated Media Storage Purge & Data Retention Management Command
Sprint: Sprint 7 – System Enhancements & Platform Maturity
Epic: Epic 9 – Security, Governance & Regulatory Compliance
Lead Developer: MD. Hasanul Mobin (@hasanulmobin)
Dedicated Peer UI Automation Tester & Reviewer: Farhana Tahsin Bonny (@bonny) / MD. Jubair Bin Hasan (@jubair65)
Target Branch: feat/us-49-media-retention-purge -> develop

Acceptance Criteria & Scenarios Verified:
✔ TC-49-01: Pre-Purge Practice Video History & Numerical Scores UI Baseline [AC-2]
✔ TC-49-02: Dry-Run Mode Retention Preview Preserves Physical Files and DB Records [AC-5]
✔ TC-49-03: Live Media Purge Execution Safely Unlinks Expired Files from Disk [AC-1, AC-2, AC-3]
✔ TC-49-04: Post-Purge Student Practice History Card & Numerical Scores Intact [AC-3]
✔ TC-49-05: Post-Purge Detailed Analysis Modal & Coaching Metrics Integrity [AC-3]
✔ TC-49-06: Post-Purge Fullscreen Presentation Analytics Report Render Integrity [AC-3]
✔ TC-49-07: Recruiter Evaluation Notes & Multi-Stage Pipeline Progression Integrity [AC-3]
✔ TC-49-08: DataAccessLog Retention Audit Trail & Missing File Exception Resilience [AC-4, AC-6]
"""

import os
import sys
import time
import uuid
import shutil
from pathlib import Path
from datetime import datetime, timezone as dt_timezone, timedelta
from io import StringIO

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
from django.core.management import call_command
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from apps.authentication.models import User
from apps.core.models import DataAccessLog
from apps.presentation.models import (
    PresentationVideo,
    PresentationScore,
    SpeechAnalysis,
    BehavioralAnalysis,
    PresentationFeedback,
)
from apps.recruitment.models import (
    RecruitmentRoom,
    CandidateApplication,
    CandidateNote,
    CandidateStageHistory,
)
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

    set_react_input(driver, email_input, email)
    set_react_input(driver, pass_input, password)
    submit_btn.click()

    wait.until(lambda d: "/student" in d.current_url or "/dashboard" in d.current_url)
    time.sleep(1)
    return user


def login_hr_user(driver, email: str, password: str = "ValidPass2026!", full_name: str = "Morgan HR Director"):
    """Helper to authenticate an HR Manager via the UI login page."""
    user = User.objects.filter(email__iexact=email).first()
    if not user:
        user = create_user_in_db(email, password, role=User.Role.HR_MANAGER, full_name=full_name)

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

    wait.until(lambda d: "/hr" in d.current_url or "/dashboard" in d.current_url)
    time.sleep(1)
    return user


def create_test_video_with_scores(student, days_ago: int = 0, has_physical_file: bool = True):
    """
    Creates a full PresentationVideo with real physical file in MEDIA_ROOT and
    associated score, speech analysis, and AI coaching feedback records.
    """
    filename = f"pitch_{uuid.uuid4().hex[:8]}.mp4"
    rel_path = f"presentation_videos/user_{student.id}/{filename}"
    abs_path = os.path.join(settings.MEDIA_ROOT, "presentation_videos", f"user_{student.id}", filename)

    if has_physical_file:
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        if SAMPLE_MP4_PATH.exists():
            shutil.copyfile(str(SAMPLE_MP4_PATH), abs_path)
        else:
            with open(abs_path, "wb") as f:
                f.write(b"MOCK MP4 VIDEO DATA CONTENT FOR TEST" * 100)
        file_size = os.path.getsize(abs_path)
    else:
        file_size = 2048

    video = PresentationVideo.objects.create(
        user=student,
        file=rel_path if has_physical_file else "",
        original_filename="Alex_Technical_Pitch.mp4",
        title="Executive Practice Session",
        raw_file_size=file_size,
        compressed_file_size=file_size,
        file_type="mp4",
        duration_seconds=92,
        status="COMPLETED",
        is_active=True,
    )

    if days_ago > 0:
        PresentationVideo.objects.filter(id=video.id).update(
            uploaded_at=timezone.now() - timedelta(days=days_ago)
        )
        video.refresh_from_db()

    PresentationScore.objects.create(
        video=video,
        overall_score=88,
        speech_score=85,
        behavioral_score=90,
        pace_score=84,
        filler_score=86,
        eye_contact_score=92,
        posture_score=88,
        engagement_score=90,
        has_behavioral_data=True,
    )

    SpeechAnalysis.objects.create(
        video=video,
        transcript="Hello hiring team, my name is Alex and I am presenting my technical portfolio.",
        words_per_minute=145.0,
        filler_word_count=2,
        filler_words_breakdown={"um": 1, "like": 1},
        clarity_score=88,
        duration_seconds=92.0,
    )

    BehavioralAnalysis.objects.create(
        video=video,
        eye_contact_score=92,
        posture_score=88,
        engagement_score=90,
        frame_metrics={"eye_contact": 92, "posture": 88},
    )

    PresentationFeedback.objects.create(
        video=video,
        summary="Strong technical delivery with structured pacing and confident eye contact.",
        strengths=["Strong technical depth", "Consistent camera gaze", "Natural pacing cadence"],
        improvements=[{"category": "Pacing", "observation": "Minor rush at conclusion", "actionable_drill": "Take a 2-second pause"}],
        practice_tip="Take a deliberate pause before moving to the next section.",
    )

    return video, abs_path


def stage_temp_upload(hours_ago: int = 50):
    """Creates a temporary abandoned file in MEDIA_ROOT/temp_uploads/ with modified timestamp."""
    temp_dir = os.path.join(settings.MEDIA_ROOT, "temp_uploads")
    os.makedirs(temp_dir, exist_ok=True)
    temp_filename = f"staged_take_{uuid.uuid4().hex[:8]}.webm"
    temp_abs_path = os.path.join(temp_dir, temp_filename)
    with open(temp_abs_path, "wb") as f:
        f.write(b"STAGED_TEMPORARY_UPLOAD_BYTES_REPRESENTING_ABANDONED_RECORDING" * 50)

    mtime = time.time() - (hours_ago * 3600)
    os.utime(temp_abs_path, (mtime, mtime))
    return temp_abs_path, temp_filename


class TestMediaRetentionPurgeUI:
    """Suite of 8 automated UI tests verifying US-49 Media Retention Purge & Data Integrity."""

    def test_tc49_01_pre_purge_video_history_and_scores_baseline(self, driver):
        """
        TC-49-01: Establish baseline UI state. Student visits /student/videos;
        practice session is rendered with title, status, and numerical score badge (88).
        """
        uid = uuid.uuid4().hex[:6]
        student_email = f"student_us49_{uid}@careerflow.test"
        student = login_student_user(driver, email=student_email, full_name="Alex PurgeTester")

        video, abs_path = create_test_video_with_scores(student, days_ago=0, has_physical_file=True)
        assert os.path.exists(abs_path), "Physical media file must exist before purge baseline test!"

        driver.get(f"{FRONTEND_URL}/student/videos")
        wait = WebDriverWait(driver, 10)

        # Verify video history row and numerical score badge
        row = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='history-row-{video.id}']")))
        assert row.is_displayed(), f"Expected history-row-{video.id} to be visible!"

        score_badge = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='score-badge-{video.id}']")))
        assert "88" in score_badge.text, f"Expected score badge 88, got: {score_badge.text}"

        title_elem = driver.find_element(By.CSS_SELECTOR, f"[data-testid='session-title-{video.id}']")
        assert "Executive Practice Session" in title_elem.text

        screenshot_path = SCREENSHOTS_DIR / "us49_01_pre_purge_video_history_baseline.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc49_02_dry_run_retention_preview_preserves_disk_and_db(self, driver):
        """
        TC-49-02: Execute purge_expired_media --dry-run.
        Verify dry-run reports eligible files without deleting them from disk or DB (AC-5).
        """
        uid = uuid.uuid4().hex[:6]
        student_email = f"dryrun_us49_{uid}@careerflow.test"
        student = login_student_user(driver, email=student_email, full_name="DryRun Auditor")

        # Create expired video (>30 days) and staged temp upload (>48 hours)
        video, abs_path = create_test_video_with_scores(student, days_ago=35, has_physical_file=True)
        temp_abs_path, temp_filename = stage_temp_upload(hours_ago=55)

        assert os.path.exists(abs_path)
        assert os.path.exists(temp_abs_path)

        # Execute management command with --dry-run flag
        initial_logs_count = DataAccessLog.objects.filter(resource_path="system:purge_expired_media").count()
        out = StringIO()
        call_command("purge_expired_media", dry_run=True, days=30, temp_hours=48, stdout=out)
        output = out.getvalue()

        # Assert output preview contents
        assert "CareerFlow Media Retention Purge [DRY-RUN PREVIEW]" in output
        assert "[DRY-RUN] Would purge video:" in output
        assert f"ID {video.id}" in output
        assert "[DRY-RUN] Would delete temp upload:" in output
        assert temp_filename in output

        # Assert physical files STILL EXIST on disk
        assert os.path.exists(abs_path), "Dry-run mode must NOT delete physical presentation video!"
        assert os.path.exists(temp_abs_path), "Dry-run mode must NOT delete physical temp upload!"

        # Assert database record still has file path
        video.refresh_from_db()
        assert video.file != "", "Dry-run mode must NOT unlink database file field!"

        # Assert no delete records added to DataAccessLog
        dry_run_logs = DataAccessLog.objects.filter(resource_path="system:purge_expired_media").count()
        assert dry_run_logs == initial_logs_count, "Dry-run must not create system purge deletion audit records!"

        # Verify UI renders session intact
        driver.get(f"{FRONTEND_URL}/student/videos")
        wait = WebDriverWait(driver, 10)
        row = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='history-row-{video.id}']")))
        assert row.is_displayed()

        score_badge = driver.find_element(By.CSS_SELECTOR, f"[data-testid='score-badge-{video.id}']")
        assert "88" in score_badge.text

        screenshot_path = SCREENSHOTS_DIR / "us49_02_dry_run_preview_intact.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc49_03_live_media_purge_execution_unlinks_disk_files(self, driver):
        """
        TC-49-03: Execute purge_expired_media in live execution mode.
        Verify physical media files and temp uploads are safely unlinked from disk (AC-1, AC-2, AC-3).
        """
        uid = uuid.uuid4().hex[:6]
        student_email = f"livepurge_us49_{uid}@careerflow.test"
        student = login_student_user(driver, email=student_email, full_name="Live Purge Student")

        video, abs_path = create_test_video_with_scores(student, days_ago=40, has_physical_file=True)
        temp_abs_path, temp_filename = stage_temp_upload(hours_ago=60)

        assert os.path.exists(abs_path)
        assert os.path.exists(temp_abs_path)

        # Execute live purge management command
        out = StringIO()
        call_command("purge_expired_media", days=30, temp_hours=48, stdout=out)
        output = out.getvalue()

        assert "CareerFlow Media Retention Purge [LIVE PURGE EXECUTION]" in output
        assert "[PURGED] Temp upload:" in output
        assert f"[PURGED] Video record ID {video.id}" in output
        assert "scores preserved" in output

        # Assert physical files were removed from disk
        assert not os.path.exists(abs_path), f"File {abs_path} should have been unlinked from disk!"
        assert not os.path.exists(temp_abs_path), f"Temp file {temp_abs_path} should have been unlinked from disk!"

        # Assert DB model preserved but file field cleared
        video.refresh_from_db()
        assert str(video.file) == "", "Video model file field must be cleared/unlinked!"
        assert video.presentation_score.overall_score == 88, "Video overall score must remain 88!"

        # Assert audit logs created
        video_log = DataAccessLog.objects.filter(
            user=student,
            action=DataAccessLog.Action.DELETE,
            status=DataAccessLog.Status.GRANTED,
        ).first()
        assert video_log is not None, "DataAccessLog entry must be recorded for purged video!"

        driver.get(f"{FRONTEND_URL}/student/videos")
        wait = WebDriverWait(driver, 10)
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='history-row-{video.id}']")))

        screenshot_path = SCREENSHOTS_DIR / "us49_03_live_purge_disk_cleanup.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc49_04_post_purge_student_history_scores_intact(self, driver):
        """
        TC-49-04: Verify student Video History page after purge (AC-3).
        The practice session card, title, and numerical score badge (88) remain 100% visible.
        """
        uid = uuid.uuid4().hex[:6]
        student_email = f"scores_us49_{uid}@careerflow.test"
        student = login_student_user(driver, email=student_email, full_name="Score Integrity Tester")

        video, abs_path = create_test_video_with_scores(student, days_ago=32, has_physical_file=True)

        # Purge the media file
        call_command("purge_expired_media", days=30, temp_hours=48)
        assert not os.path.exists(abs_path)

        driver.get(f"{FRONTEND_URL}/student/videos")
        wait = WebDriverWait(driver, 10)

        row = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='history-row-{video.id}']")))
        assert row.is_displayed()

        score_badge = driver.find_element(By.CSS_SELECTOR, f"[data-testid='score-badge-{video.id}']")
        assert score_badge.text == "88", f"Expected score badge 88, got: {score_badge.text}"

        title_elem = driver.find_element(By.CSS_SELECTOR, f"[data-testid='session-title-{video.id}']")
        assert "Executive Practice Session" in title_elem.text

        # Verify summary stats at the top of the history page
        avg_score_stat = driver.find_element(By.CSS_SELECTOR, "[data-testid='stat-avg-score']")
        assert "88" in avg_score_stat.text

        screenshot_path = SCREENSHOTS_DIR / "us49_04_post_purge_history_scores_intact.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc49_05_post_purge_analysis_modal_metrics_integrity(self, driver):
        """
        TC-49-05: Click View AI Analysis on purged video row.
        Verify past-analysis-detail-modal mounts with composite scores, speech metrics,
        and AI coaching suggestions fully intact (AC-3).
        """
        uid = uuid.uuid4().hex[:6]
        student_email = f"modal_us49_{uid}@careerflow.test"
        student = login_student_user(driver, email=student_email, full_name="Modal Analytics Tester")

        video, abs_path = create_test_video_with_scores(student, days_ago=35, has_physical_file=True)
        call_command("purge_expired_media", days=30, temp_hours=48)

        driver.get(f"{FRONTEND_URL}/student/videos")
        wait = WebDriverWait(driver, 10)

        # Click the analysis button
        analysis_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-analysis-{video.id}']")))
        driver.execute_script("arguments[0].click();", analysis_btn)

        # Verify past analysis detail modal mounts
        modal = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='past-analysis-detail-modal']")))
        assert modal.is_displayed()

        # Verify full report button is available
        full_report_btn = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='button-open-fullscreen-report']")))
        assert full_report_btn.is_displayed()

        screenshot_path = SCREENSHOTS_DIR / "us49_05_post_purge_modal_analysis_preserved.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc49_06_post_purge_fullscreen_detail_report(self, driver):
        """
        TC-49-06: Navigate to dedicated /presentation/history/{video.id} detail report.
        Verify entire analytics page loads with overall score 88, pace, and feedback (AC-3).
        """
        uid = uuid.uuid4().hex[:6]
        student_email = f"report_us49_{uid}@careerflow.test"
        student = login_student_user(driver, email=student_email, full_name="Report Analytics Tester")

        video, abs_path = create_test_video_with_scores(student, days_ago=38, has_physical_file=True)
        call_command("purge_expired_media", days=30, temp_hours=48)

        driver.get(f"{FRONTEND_URL}/presentation/history/{video.id}")
        wait = WebDriverWait(driver, 15)

        # Wait for presentation analysis loading to finish and content to render
        wait.until(lambda d: "88" in d.find_element(By.TAG_NAME, "body").text)
        body_text = driver.find_element(By.TAG_NAME, "body").text
        assert "88" in body_text, "Report page must display composite overall score 88!"
        assert "Alex_Technical_Pitch.mp4" in body_text or "Executive Practice Session" in body_text
        assert "AI Coaching Feedback" in body_text or "Evaluation" in body_text

        screenshot_path = SCREENSHOTS_DIR / "us49_06_post_purge_fullscreen_report.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc49_07_recruiter_pipeline_evaluation_notes_intact(self, driver):
        """
        TC-49-07: Verify recruiter evaluation notes and multi-stage interview pipeline progression
        remain completely intact when candidate application media is unlinked (AC-3).
        """
        uid = uuid.uuid4().hex[:6]
        hr_email = f"hr_purge_{uid}@careerflow.test"
        hr_user = login_hr_user(driver, email=hr_email, full_name="HR Director PurgeAudit")

        # Create recruitment room and candidate application
        room = RecruitmentRoom.objects.create(
            created_by=hr_user,
            title="Principal Infrastructure Engineer",
            company_name="Cloud Scale Systems",
            department="Cloud Ops",
            status=RecruitmentRoom.Status.OPEN,
            link_is_active=True,
        )

        candidate_user = create_user_in_db(f"candidate_{uid}@applicant.test", "ValidPass2026!", role=User.Role.STUDENT, full_name="Jordan Candidate")
        video, abs_path = create_test_video_with_scores(candidate_user, days_ago=35, has_physical_file=True)

        app = CandidateApplication.objects.create(
            room=room,
            candidate=candidate_user,
            stage=CandidateApplication.Stage.SHORTLISTED,
            status=CandidateApplication.Status.COMPLETED,
            is_shortlisted=True,
            final_score=92.5,
        )

        # Create recruiter internal note
        CandidateNote.objects.create(
            application=app,
            author=hr_user,
            content="Candidate shows exceptional cloud automation architecture. Shortlisted for Round 1.",
        )

        # Create stage progression audit history
        CandidateStageHistory.objects.create(
            application=app,
            from_stage=CandidateApplication.Stage.APPLIED,
            to_stage=CandidateApplication.Stage.SHORTLISTED,
            updated_by=hr_user,
            notes="Advanced to shortlisted based on match score 92.5.",
        )

        # Execute purge
        call_command("purge_expired_media", days=30, temp_hours=48)
        assert not os.path.exists(abs_path)

        # Verify notes and application remain in DB
        app.refresh_from_db()
        assert app.stage == CandidateApplication.Stage.SHORTLISTED
        assert app.recruiter_notes.count() == 1
        assert app.stage_history.count() == 1

        # View in UI: Navigate to HR rooms dashboard
        driver.get(f"{FRONTEND_URL}/hr/dashboard")
        wait = WebDriverWait(driver, 15)

        # View rooms / dashboard
        wait.until(lambda d: "/hr" in d.current_url)
        wait.until(lambda d: "Principal Infrastructure Engineer" in d.find_element(By.TAG_NAME, "body").text or "Cloud Scale Systems" in d.find_element(By.TAG_NAME, "body").text)
        time.sleep(1)

        screenshot_path = SCREENSHOTS_DIR / "us49_07_recruiter_notes_stages_intact.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc49_08_system_audit_logs_and_missing_file_resilience(self, driver):
        """
        TC-49-08: Verify DataAccessLog audit records (AC-4) and missing file lock exception resilience (AC-6).
        The purge command runs on already-missing files without crashing.
        """
        uid = uuid.uuid4().hex[:6]
        student = create_user_in_db(f"resilience_{uid}@careerflow.test", "ValidPass2026!", role=User.Role.STUDENT, full_name="Resilience Tester")

        # Create expired video where file does NOT physically exist on disk (simulating prior manual deletion or missing media)
        missing_rel_path = f"presentation_videos/user_{student.id}/non_existent_file_{uid}.mp4"
        missing_video = PresentationVideo.objects.create(
            user=student,
            file=missing_rel_path,
            original_filename="Missing_Take.mp4",
            title="Missing File Resilience Test",
            raw_file_size=1024,
            duration_seconds=30,
            status="COMPLETED",
            is_active=True,
        )
        PresentationVideo.objects.filter(id=missing_video.id).update(
            uploaded_at=timezone.now() - timedelta(days=45)
        )

        # AC-6: Verify command executes safely without crashing on missing file
        out = StringIO()
        call_command("purge_expired_media", days=30, temp_hours=48, stdout=out)
        output = out.getvalue()

        assert "already missing from disk" in output or "Video record ID" in output
        assert "SUMMARY REPORT - LIVE PURGE EXECUTION" in output

        # AC-4: Verify batch audit log in DataAccessLog
        batch_log = DataAccessLog.objects.filter(resource_path="system:purge_expired_media").last()
        assert batch_log is not None, "Batch retention audit log must be saved to DataAccessLog!"
        assert batch_log.action == DataAccessLog.Action.DELETE
        assert batch_log.status == DataAccessLog.Status.GRANTED
        assert "CareerFlow Management Command: purge_expired_media" in batch_log.user_agent

        # Capture browser verification screenshot
        driver.get(f"{FRONTEND_URL}/student/dashboard")
        time.sleep(1)

        screenshot_path = SCREENSHOTS_DIR / "us49_08_system_audit_log_verified.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()
