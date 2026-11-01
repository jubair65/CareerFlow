"""
US-47: Recruiter Evaluation Notes & Multi-Stage Interview Pipeline Progression UI Automation Test Suite (US-47-T6).
User Story: US-47 – Recruiter Evaluation Notes & Multi-Stage Interview Pipeline Progression
Sprint: Sprint 7 – System Enhancements & Platform Maturity
Lead Developer: MD. Hasanul Mobin (@hasanulmobin)
Dedicated Peer UI Automation Tester & Reviewer: MD. Jubair Bin Hasan (@jubair65)
Target Branch: feat/us-47-recruiter-notes-stages -> develop

Acceptance Criteria & Scenarios Verified:
✔ TC-47-01: Recruiter Notes Modal Mount & Applicant Context [AC-1, AC-2]
✔ TC-47-02: Recruiter Internal Note Creation & Real-Time Stream Mount [AC-1, AC-3]
✔ TC-47-03: Inline Note Editing & Edited Badge Display [AC-1, AC-3]
✔ TC-47-04: Note Deletion & Leaderboard Counter Badge Update [AC-1]
✔ TC-47-05: Multi-Stage Progression Transition & Chronological Audit History [AC-2, AC-3]
✔ TC-47-06: Candidate In-App Notification Dispatch on Stage Progression [AC-5]
✔ TC-47-07: Leaderboard Multi-Stage Filtering Pills [AC-6]
✔ TC-47-08: Candidate Role Privacy & Strict RBAC Enforcement [AC-4]
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
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

from apps.authentication.models import User
from apps.recruitment.models import (
    RecruitmentRoom,
    CandidateApplication,
    CandidateNote,
    CandidateStageHistory,
)
from apps.cv.models import CandidateCV, CVJobMatch
from apps.core.models import Notification
from conftest import FRONTEND_URL, BACKEND_URL, SCREENSHOTS_DIR, create_user_in_db


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


def login_hr_user(driver, email: str, password: str = "ValidPass2026!"):
    """Helper to authenticate an HR Manager via the UI login page and navigate to /hr/rooms."""
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

    wait.until(EC.url_contains("/hr/dashboard"))
    driver.get(f"{FRONTEND_URL}/hr/rooms")
    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='section-recruitment-rooms']")))


def login_candidate_user(driver, email: str, password: str = "ValidPass2026!"):
    """Helper to authenticate a Candidate (Student) via the UI login page."""
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

    wait.until(EC.url_contains("/student/dashboard"))


def get_access_token_from_browser(driver) -> str:
    """Extracts the JWT access token from browser localStorage."""
    token = driver.execute_script("return localStorage.getItem('careerflow_access_token');")
    return token or ""


def setup_sample_room_with_single_applicant(hr_user: User, title: str = "Principal Systems Architect"):
    """Creates a recruitment room with one ranked applicant."""
    room = RecruitmentRoom.objects.create(
        created_by=hr_user,
        title=title,
        company_name="CloudMatrix Dynamics",
        department="Platform Engineering",
        status=RecruitmentRoom.Status.OPEN,
        cv_weight=50,
        video_weight=50,
        skills_required=["Distributed Systems", "Kubernetes", "Rust", "Go"],
        link_is_active=True,
    )
    uid = uuid.uuid4().hex[:6]
    candidate = create_user_in_db(f"candidate_{uid}@careerflow.test", "ValidPass2026!", role=User.Role.STUDENT, full_name="Samantha Ray")
    candidate_cv = CandidateCV.objects.create(user=candidate, file="cvs/sam.pdf", original_filename="Sam_CV.pdf", file_size=1024, file_type="pdf", is_active=True)
    CVJobMatch.objects.create(cv=candidate_cv, job_title=room.title, company=room.company_name, match_score=92.0)
    app = CandidateApplication.objects.create(
        room=room,
        candidate=candidate,
        cv=candidate_cv,
        cv_score=92.0,
        video_score=88.0,
        final_score=90.0,
        is_shortlisted=True,
        shortlist_reason="Top tier architectural candidate",
        status=CandidateApplication.Status.COMPLETED,
        stage=CandidateApplication.Stage.APPLIED,
    )
    return room, app, candidate


def setup_multi_applicant_pipeline_room(hr_user: User, title: str = "DevOps Infrastructure Lead"):
    """Creates a room with multiple candidates in diverse pipeline stages."""
    room = RecruitmentRoom.objects.create(
        created_by=hr_user,
        title=title,
        company_name="Starlight Systems",
        department="Infrastructure",
        status=RecruitmentRoom.Status.OPEN,
        cv_weight=50,
        video_weight=50,
        skills_required=["Terraform", "CI/CD", "AWS", "Python"],
        link_is_active=True,
    )
    stages = [
        ("Alice Applied", CandidateApplication.Stage.APPLIED, 95.0),
        ("Bob UnderReview", CandidateApplication.Stage.UNDER_REVIEW, 90.0),
        ("Charlie Shortlisted", CandidateApplication.Stage.SHORTLISTED, 88.0),
        ("Diana RoundOne", CandidateApplication.Stage.INTERVIEW_ROUND_1, 85.0),
        ("Evan RoundTwo", CandidateApplication.Stage.INTERVIEW_ROUND_2, 82.0),
        ("Fiona Offered", CandidateApplication.Stage.OFFERED, 80.0),
        ("George Hired", CandidateApplication.Stage.HIRED, 78.0),
        ("Helen Rejected", CandidateApplication.Stage.REJECTED, 70.0),
    ]
    apps = []
    for name, stage, score in stages:
        uid = uuid.uuid4().hex[:6]
        c = create_user_in_db(f"cand_{uid}@careerflow.test", "ValidPass2026!", role=User.Role.STUDENT, full_name=name)
        cv = CandidateCV.objects.create(user=c, file=f"cvs/{uid}.pdf", original_filename=f"{name}_CV.pdf", file_size=1024, file_type="pdf", is_active=True)
        CVJobMatch.objects.create(cv=cv, job_title=room.title, company=room.company_name, match_score=score)
        a = CandidateApplication.objects.create(
            room=room,
            candidate=c,
            cv=cv,
            cv_score=score,
            video_score=score,
            final_score=score,
            is_shortlisted=(stage in [CandidateApplication.Stage.SHORTLISTED, CandidateApplication.Stage.INTERVIEW_ROUND_1, CandidateApplication.Stage.INTERVIEW_ROUND_2, CandidateApplication.Stage.OFFERED, CandidateApplication.Stage.HIRED]),
            status=CandidateApplication.Status.COMPLETED,
            stage=stage,
        )
        apps.append(a)
    return room, apps


# ---------------------------------------------------------------------------
# Test Cases TC-47-01 through TC-47-08
# ---------------------------------------------------------------------------

def test_tc47_01_recruiter_notes_modal_mount_and_context(driver):
    """
    TC-47-01: Recruiter Notes Modal Mount & Applicant Context (AC-1, AC-2)
    Scenario: Verify that clicking the 'Notes' trigger button on an applicant card
    in the room rankings modal opens the RecruiterNotesModal with candidate details,
    the 8-stage stepper, stage update dropdown, and notes stream section.
    """
    email = f"tc47_01_{uuid.uuid4().hex[:6]}@careerflow.test"
    hr_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.HR_MANAGER, full_name="Recruiter Lead")
    room, app, candidate = setup_sample_room_with_single_applicant(hr_user)

    login_hr_user(driver, email)
    wait = WebDriverWait(driver, 10)

    # Open rankings modal
    ranking_btn = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-action-ranking-{room.id}']"))
    )
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", ranking_btn)
    driver.execute_script("arguments[0].click();", ranking_btn)

    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-ranked-applicants']")))

    # Click the Notes button on the applicant card
    notes_trigger = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-open-notes-{app.id}']"))
    )
    driver.execute_script("arguments[0].click();", notes_trigger)

    # Verify modal mounts
    notes_modal = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-recruiter-notes']")))
    assert notes_modal.is_displayed()

    # Verify candidate name and position
    cand_name_elem = driver.find_element(By.CSS_SELECTOR, "[data-testid='text-modal-candidate-name']")
    assert candidate.full_name in cand_name_elem.text

    # Verify Stage progression section & Current Stage badge
    stage_section = driver.find_element(By.CSS_SELECTOR, "[data-testid='section-stage-progression']")
    assert stage_section.is_displayed()
    current_stage_badge = driver.find_element(By.CSS_SELECTOR, "[data-testid='badge-current-stage']")
    assert "Applied" in current_stage_badge.text

    # Verify Notes section is mounted
    notes_section = driver.find_element(By.CSS_SELECTOR, "[data-testid='section-recruiter-notes']")
    assert notes_section.is_displayed()

    driver.save_screenshot(str(SCREENSHOTS_DIR / "us47_01_recruiter_notes_modal_mounted.png"))


def test_tc47_02_recruiter_note_creation_and_stream_mount(driver):
    """
    TC-47-02: Recruiter Internal Note Creation & Real-Time Stream Mount (AC-1, AC-3)
    Scenario: HR types an internal evaluation note and clicks 'Post Note'.
    Verify the note is rendered in the stream with the author's name, timestamp,
    and text content, and is persisted in the database.
    """
    email = f"tc47_02_{uuid.uuid4().hex[:6]}@careerflow.test"
    hr_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.HR_MANAGER, full_name="Hiring Lead Alex")
    room, app, candidate = setup_sample_room_with_single_applicant(hr_user)

    login_hr_user(driver, email)
    wait = WebDriverWait(driver, 10)

    # Open rankings modal and notes modal
    ranking_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-action-ranking-{room.id}']")))
    driver.execute_script("arguments[0].click();", ranking_btn)

    notes_trigger = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-open-notes-{app.id}']")))
    driver.execute_script("arguments[0].click();", notes_trigger)

    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-recruiter-notes']")))

    # Type new note
    note_text = "Strong behavioral responses in system design; demonstrated clear communication."
    note_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-new-note'], [data-testid='textarea-new-note']")))
    set_react_input(driver, note_input, note_text)

    # Click Post Note
    post_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-add-note'], [data-testid='button-submit-note']")))
    driver.execute_script("arguments[0].click();", post_btn)

    # Wait for note card to appear in the stream
    wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "[data-testid^='card-recruiter-note-']")) > 0)
    note_card = driver.find_elements(By.CSS_SELECTOR, "[data-testid^='card-recruiter-note-']")[0]

    # Verify content and author
    assert note_text in note_card.text
    assert hr_user.full_name in note_card.text

    # Verify DB persistence
    time.sleep(0.5)
    db_note = CandidateNote.objects.filter(application=app).first()
    assert db_note is not None
    assert db_note.content == note_text
    assert db_note.author == hr_user
    assert db_note.is_edited is False

    driver.save_screenshot(str(SCREENSHOTS_DIR / "us47_02_note_added_to_stream.png"))


def test_tc47_03_note_inline_editing_and_edited_badge(driver):
    """
    TC-47-03: Inline Note Editing & Edited Badge Display (AC-1, AC-3)
    Scenario: Click edit button on existing note, modify content, click save.
    Verify note content updates in real-time and displays the '(edited)' badge.
    """
    email = f"tc47_03_{uuid.uuid4().hex[:6]}@careerflow.test"
    hr_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.HR_MANAGER, full_name="Editor Recruiter")
    room, app, candidate = setup_sample_room_with_single_applicant(hr_user)
    initial_note = CandidateNote.objects.create(
        application=app,
        author=hr_user,
        content="Candidate completed initial review.",
        is_edited=False,
    )

    login_hr_user(driver, email)
    wait = WebDriverWait(driver, 10)

    # Open rankings modal and notes modal
    ranking_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-action-ranking-{room.id}']")))
    driver.execute_script("arguments[0].click();", ranking_btn)

    notes_trigger = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-open-notes-{app.id}']")))
    driver.execute_script("arguments[0].click();", notes_trigger)

    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-recruiter-notes']")))

    # Click edit button
    edit_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-edit-note-{initial_note.id}']")))
    driver.execute_script("arguments[0].click();", edit_btn)

    # Wait for edit textarea and update text
    edit_textarea = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='input-edit-note-{initial_note.id}']")))
    updated_text = "Candidate completed initial review (Updated: Recommended for Round 2 Technical)."
    set_react_input(driver, edit_textarea, updated_text)

    # Click Save
    save_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-save-edit-note-{initial_note.id}']")))
    driver.execute_script("arguments[0].click();", save_btn)

    # Verify updated content is displayed
    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='text-note-content-{initial_note.id}']")))
    content_elem = driver.find_element(By.CSS_SELECTOR, f"[data-testid='text-note-content-{initial_note.id}']")
    assert updated_text in content_elem.text

    # Verify edited badge
    edited_badge = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='badge-note-edited-{initial_note.id}']")))
    assert "edited" in edited_badge.text.lower()

    # Verify DB state
    initial_note.refresh_from_db()
    assert initial_note.content == updated_text
    assert initial_note.is_edited is True

    driver.save_screenshot(str(SCREENSHOTS_DIR / "us47_03_note_inline_edited.png"))


def test_tc47_04_note_deletion_and_badge_counter_update(driver):
    """
    TC-47-04: Note Deletion & Leaderboard Counter Badge Update (AC-1)
    Scenario: Delete a note, confirm alert prompt, verify note is removed from DOM,
    and verify the notes counter badge on the leaderboard updates.
    """
    email = f"tc47_04_{uuid.uuid4().hex[:6]}@careerflow.test"
    hr_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.HR_MANAGER, full_name="Cleanup Recruiter")
    room, app, candidate = setup_sample_room_with_single_applicant(hr_user)
    note = CandidateNote.objects.create(
        application=app,
        author=hr_user,
        content="Temporary note to be deleted.",
    )

    login_hr_user(driver, email)
    wait = WebDriverWait(driver, 10)

    # Open rankings modal
    ranking_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-action-ranking-{room.id}']")))
    driver.execute_script("arguments[0].click();", ranking_btn)

    # Verify initial badge count shows 1
    badge_count = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='badge-notes-count-{app.id}']")))
    assert "1" in badge_count.text

    # Open notes modal
    notes_trigger = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-open-notes-{app.id}']")))
    driver.execute_script("arguments[0].click();", notes_trigger)

    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-recruiter-notes']")))

    # Auto-accept window.confirm
    driver.execute_script("window.confirm = () => true;")

    # Click delete button
    delete_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-delete-note-{note.id}']")))
    driver.execute_script("arguments[0].click();", delete_btn)

    # Wait for note card to disappear
    wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='card-recruiter-note-{note.id}']")))

    # Verify empty state or 0 notes in modal
    assert len(driver.find_elements(By.CSS_SELECTOR, f"[data-testid='card-recruiter-note-{note.id}']")) == 0

    # Close modal
    close_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-close-recruiter-notes'], [data-testid='button-modal-done']")))
    driver.execute_script("arguments[0].click();", close_btn)

    # Verify leaderboard notes badge is updated/hidden
    time.sleep(0.5)
    remaining_badges = driver.find_elements(By.CSS_SELECTOR, f"[data-testid='badge-notes-count-{app.id}']")
    assert len(remaining_badges) == 0 or "0" in remaining_badges[0].text

    # Verify DB
    assert CandidateNote.objects.filter(id=note.id).count() == 0

    driver.save_screenshot(str(SCREENSHOTS_DIR / "us47_04_note_deleted_and_badge_updated.png"))


def test_tc47_05_interview_stage_progression_and_audit_history(driver):
    """
    TC-47-05: Multi-Stage Progression Transition & Chronological Audit History (AC-2, AC-3)
    Scenario: Update candidate stage from APPLIED to INTERVIEW_ROUND_1 with rationale.
    Verify current stage badge updates, and view audit history accordion to verify
    the transition record with author and timestamp.
    """
    email = f"tc47_05_{uuid.uuid4().hex[:6]}@careerflow.test"
    hr_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.HR_MANAGER, full_name="Stage Transition Lead")
    room, app, candidate = setup_sample_room_with_single_applicant(hr_user)

    login_hr_user(driver, email)
    wait = WebDriverWait(driver, 10)

    # Open rankings and notes modal
    ranking_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-action-ranking-{room.id}']")))
    driver.execute_script("arguments[0].click();", ranking_btn)

    notes_trigger = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-open-notes-{app.id}']")))
    driver.execute_script("arguments[0].click();", notes_trigger)

    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-recruiter-notes']")))

    # Select INTERVIEW_ROUND_1 in the stage select dropdown
    stage_select_elem = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='select-candidate-stage']")))
    stage_select = Select(stage_select_elem)
    stage_select.select_by_value("INTERVIEW_ROUND_1")

    # Enter rationale note
    stage_note_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-stage-note']")
    rationale = "Passed preliminary CV and technical screen."
    set_react_input(driver, stage_note_input, rationale)

    # Click Update Stage
    update_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-update-stage']")))
    driver.execute_script("arguments[0].click();", update_btn)

    # Verify stage badge updates to Interview Round 1
    wait.until(lambda d: "Interview Round 1" in d.find_element(By.CSS_SELECTOR, "[data-testid='badge-current-stage']").text)

    # Expand audit history accordion
    toggle_history_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-toggle-stage-history']")))
    driver.execute_script("arguments[0].click();", toggle_history_btn)

    history_section = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='section-stage-history']")))
    assert "Interview Round 1" in history_section.text
    assert rationale in history_section.text

    # Verify DB records
    app.refresh_from_db()
    assert app.stage == CandidateApplication.Stage.INTERVIEW_ROUND_1

    history_record = CandidateStageHistory.objects.filter(application=app, to_stage="INTERVIEW_ROUND_1").first()
    assert history_record is not None
    assert history_record.notes == rationale
    assert history_record.updated_by == hr_user

    driver.save_screenshot(str(SCREENSHOTS_DIR / "us47_05_interview_stage_progression_history.png"))


def test_tc47_06_candidate_notification_on_stage_update(driver):
    """
    TC-47-06: Candidate In-App Notification Dispatch on Stage Progression (AC-5)
    Scenario: Ensure 'Notify candidate' checkbox is checked when transitioning stage.
    Verify candidate receives an in-app Notification record in DB.
    """
    email = f"tc47_06_{uuid.uuid4().hex[:6]}@careerflow.test"
    hr_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.HR_MANAGER, full_name="Notification Lead")
    room, app, candidate = setup_sample_room_with_single_applicant(hr_user)
    app.stage = CandidateApplication.Stage.INTERVIEW_ROUND_2
    app.save()

    login_hr_user(driver, email)
    wait = WebDriverWait(driver, 10)

    # Open rankings and notes modal
    ranking_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-action-ranking-{room.id}']")))
    driver.execute_script("arguments[0].click();", ranking_btn)

    notes_trigger = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-open-notes-{app.id}']")))
    driver.execute_script("arguments[0].click();", notes_trigger)

    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-recruiter-notes']")))

    # Transition to OFFERED
    stage_select_elem = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='select-candidate-stage']")))
    Select(stage_select_elem).select_by_value("OFFERED")

    # Ensure notify checkbox is checked
    notify_cb = driver.find_element(By.CSS_SELECTOR, "[data-testid='checkbox-notify-candidate']")
    if not notify_cb.is_selected():
        driver.execute_script("arguments[0].click();", notify_cb)

    rationale = "Formal employment offer extended."
    set_react_input(driver, driver.find_element(By.CSS_SELECTOR, "[data-testid='input-stage-note']"), rationale)

    # Submit
    update_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-update-stage']")))
    driver.execute_script("arguments[0].click();", update_btn)

    # Verify current stage badge updates
    wait.until(lambda d: "Offered" in d.find_element(By.CSS_SELECTOR, "[data-testid='badge-current-stage']").text)

    # Verify notification created in DB
    time.sleep(0.5)
    notif = Notification.objects.filter(
        user=candidate,
        notification_type=Notification.NotificationType.APPLICATION_STATUS,
    ).latest('created_at')
    assert notif is not None
    assert room.title in notif.title
    assert "Offered" in notif.message

    driver.save_screenshot(str(SCREENSHOTS_DIR / "us47_06_candidate_notification_dispatched.png"))


def test_tc47_07_leaderboard_stage_filter_pills(driver):
    """
    TC-47-07: Leaderboard Multi-Stage Filtering Pills (AC-6)
    Scenario: Verify stage filter pills (Applied, Under Review, Shortlisted, Round 1, Offered, All)
    filter candidates dynamically on the leaderboard.
    """
    email = f"tc47_07_{uuid.uuid4().hex[:6]}@careerflow.test"
    hr_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.HR_MANAGER, full_name="Pipeline Filter Lead")
    room, apps = setup_multi_applicant_pipeline_room(hr_user)

    login_hr_user(driver, email)
    wait = WebDriverWait(driver, 10)

    # Open rankings modal
    ranking_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-action-ranking-{room.id}']")))
    driver.execute_script("arguments[0].click();", ranking_btn)

    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-ranked-applicants']")))

    # Initial view has all candidates
    initial_cards = driver.find_elements(By.CSS_SELECTOR, "[data-testid^='card-ranked-applicant-']")
    assert len(initial_cards) > 0

    # 1. Filter by Offered
    offered_pill = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='filter-stage-offered']")))
    driver.execute_script("arguments[0].click();", offered_pill)
    time.sleep(0.5)

    offered_cards = driver.find_elements(By.CSS_SELECTOR, "[data-testid^='card-ranked-applicant-']")
    assert len(offered_cards) == 1
    assert "Fiona Offered" in offered_cards[0].text

    # 2. Filter by Round 1
    round1_pill = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='filter-stage-round1'], [data-testid='filter-stage-interview-round-1']")))
    driver.execute_script("arguments[0].click();", round1_pill)
    time.sleep(0.5)

    r1_cards = driver.find_elements(By.CSS_SELECTOR, "[data-testid^='card-ranked-applicant-']")
    assert len(r1_cards) == 1
    assert "Diana RoundOne" in r1_cards[0].text

    # 3. Filter by All Stages
    all_pill = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='filter-stage-all']")))
    driver.execute_script("arguments[0].click();", all_pill)
    time.sleep(0.5)

    restored_cards = driver.find_elements(By.CSS_SELECTOR, "[data-testid^='card-ranked-applicant-']")
    assert len(restored_cards) >= len(apps) - 1  # All ranked applicants restored

    driver.save_screenshot(str(SCREENSHOTS_DIR / "us47_07_leaderboard_stage_filter_pills.png"))


def test_tc47_08_candidate_privacy_and_rbac_isolation(driver):
    """
    TC-47-08: Candidate Role Privacy & Strict RBAC Enforcement (AC-4)
    Scenario: Candidate logs in; verify zero recruiter notes or evaluation UI are accessible.
    Assert direct API request to notes endpoint with candidate JWT returns HTTP 403 Forbidden.
    """
    email = f"tc47_08_hr_{uuid.uuid4().hex[:6]}@careerflow.test"
    hr_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.HR_MANAGER, full_name="Private HR")
    room, app, candidate = setup_sample_room_with_single_applicant(hr_user)
    CandidateNote.objects.create(
        application=app,
        author=hr_user,
        content="Confidential recruiter observation: candidate salary expectations are slightly high.",
    )

    # Log in as candidate (Student)
    login_candidate_user(driver, candidate.email)
    wait = WebDriverWait(driver, 10)

    # Check candidate views
    driver.get(f"{FRONTEND_URL}/student/applications")
    time.sleep(1)

    # Verify zero notes modal or notes elements in DOM
    assert len(driver.find_elements(By.CSS_SELECTOR, "[data-testid='modal-recruiter-notes']")) == 0
    assert len(driver.find_elements(By.CSS_SELECTOR, "[data-testid^='button-open-notes-']")) == 0
    assert "Confidential recruiter observation" not in driver.page_source

    driver.save_screenshot(str(SCREENSHOTS_DIR / "us47_08_candidate_privacy_zero_leakage.png"))

    # Direct API request verification
    token = get_access_token_from_browser(driver)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. GET notes -> 403 Forbidden
    res_get = requests.get(f"{BACKEND_URL}/api/recruitment/applications/{app.id}/notes/", headers=headers)
    assert res_get.status_code == 403

    # 2. POST notes -> 403 Forbidden
    res_post = requests.post(f"{BACKEND_URL}/api/recruitment/applications/{app.id}/notes/", headers=headers, json={"content": "Hacker note"})
    assert res_post.status_code == 403

    # 3. PATCH stage -> 403 Forbidden
    res_stage = requests.patch(f"{BACKEND_URL}/api/recruitment/applications/{app.id}/stage/", headers=headers, json={"stage": "HIRED"})
    assert res_stage.status_code == 403

    # 4. GET stage history -> 403 Forbidden
    res_hist = requests.get(f"{BACKEND_URL}/api/recruitment/applications/{app.id}/stage-history/", headers=headers)
    assert res_hist.status_code == 403

