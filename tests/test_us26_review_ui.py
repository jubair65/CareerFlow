import os
import sys
import time
from datetime import timedelta
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

import pytest
from django.utils import timezone
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from apps.authentication.models import User
from apps.recruitment.models import RecruitmentRoom, CandidateApplication
from apps.cv.models import CandidateCV, CVJobMatch
from apps.presentation.models import PresentationVideo, PresentationScore
from apps.recruitment.services.review_service import AI_ADVISORY_DISCLAIMER
from conftest import FRONTEND_URL, SCREENSHOTS_DIR, create_user_in_db


def get_base_url():
    """Ensure reliable IPv4 localhost URL on Windows 11."""
    return os.environ.get("FRONTEND_URL", "http://127.0.0.1:5173")


def login_hr(driver, email="bonny_peer_tester@careerflow.test", password="ValidPass2026!", full_name="Farhana Tahsin Bonny"):
    """Helper to ensure HR Manager user exists and authenticates via UI."""
    create_user_in_db(email, password, role=User.Role.HR_MANAGER, full_name=full_name)

    base_url = get_base_url()
    driver.get(f"{base_url}/login")
    wait = WebDriverWait(driver, 10)
    email_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-login-email']")))
    pass_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-login-password']")
    submit_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-login']")

    email_input.clear()
    email_input.send_keys(email)
    pass_input.clear()
    pass_input.send_keys(password)
    submit_btn.click()

    wait.until(EC.url_contains("/hr/dashboard"))


def set_react_input(driver, element, value):
    """Reliably sets React controlled input/textarea value and dispatches input/change synthetic events."""
    driver.execute_script(
        "var el = arguments[0];"
        "var nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;"
        "nativeSetter.call(el, arguments[1]);"
        "el.dispatchEvent(new Event('input', { bubbles: true }));"
        "el.dispatchEvent(new Event('change', { bubbles: true }));",
        element,
        str(value)
    )


def create_us26_sample_room(hr_email: str, room_title="Senior AI Solutions Architect", company="CareerFlow Systems BD"):
    """
    Creates a RecruitmentRoom owned by hr_email with 3 candidates to thoroughly test US-26:
    1. Alice: Recommended for shortlist by AI (final_score=88.5, cv=92.0, video=85.0, is_shortlisted=True)
       Includes full CV skills and Video presentation telemetry for tab testing.
    2. Bob: Not recommended by AI (final_score=64.0, cv=68.0, video=60.0, is_shortlisted=False) -> Target for Override test
    3. Charlie: Pending review with complete signals (final_score=78.0, cv=76.0, video=80.0, hr_decision='UNDECIDED')
    """
    hr_user = User.objects.get(email=hr_email)

    room = RecruitmentRoom.objects.create(
        title=room_title,
        company_name=company,
        department="Engineering",
        description="Senior AI architect responsible for designing LLM pipelines and enterprise decision engines.",
        requirements_text="Proficiency in Python, PyTorch, Django, and Distributed Systems.",
        skills_required=["Python", "PyTorch", "Django", "Distributed Systems"],
        status=RecruitmentRoom.Status.ACTIVE,
        created_by=hr_user,
        cv_weight=50,
        video_weight=50
    )

    now = timezone.now()

    # 1. Alice (Recommended Shortlist)
    alice_user = create_user_in_db("alice_us26@careerflow.test", "ValidPass2026!", role=User.Role.STUDENT, full_name="Alice Candidate")
    alice_cv = CandidateCV.objects.create(
        user=alice_user,
        file="students/alice/alice_cv.pdf",
        original_filename="Alice_AI_Architect_CV.pdf",
        file_size=204800,
        is_active=True
    )
    CVJobMatch.objects.create(
        cv=alice_cv,
        job_title=room.title,
        company=room.company_name,
        match_score=92.0,
        skills_matched=["Python", "PyTorch", "Django"],
        skills_missing=["Distributed Systems"]
    )
    alice_video = PresentationVideo.objects.create(
        user=alice_user,
        file="students/alice/video.mp4",
        original_filename="Alice_Presentation.mp4",
        raw_file_size=15000000,
        file_type="mp4",
        duration_seconds=120,
        status="COMPLETED"
    )
    PresentationScore.objects.create(
        video=alice_video,
        overall_score=85,
        speech_score=88,
        behavioral_score=82
    )
    app_alice = CandidateApplication.objects.create(
        room=room,
        candidate=alice_user,
        cv=alice_cv,
        video=alice_video,
        final_score=88.5,
        cv_score=92.0,
        video_score=85.0,
        is_partial_score=False,
        is_shortlisted=True,
        shortlist_reason="Exceeded minimum score threshold of 80.0",
        shortlisted_at=now - timedelta(days=2),
        status=CandidateApplication.Status.COMPLETED,
        hr_decision=CandidateApplication.HrDecision.UNDECIDED
    )

    # 2. Bob (Not Recommended Shortlist -> For Override test)
    bob_user = create_user_in_db("bob_us26@careerflow.test", "ValidPass2026!", role=User.Role.STUDENT, full_name="Bob LowScore")
    bob_cv = CandidateCV.objects.create(
        user=bob_user,
        file="students/bob/bob_cv.pdf",
        original_filename="Bob_Junior_CV.pdf",
        file_size=190000,
        is_active=True
    )
    CVJobMatch.objects.create(
        cv=bob_cv,
        job_title=room.title,
        company=room.company_name,
        match_score=68.0,
        skills_matched=["Python"],
        skills_missing=["PyTorch", "Django", "Distributed Systems"]
    )
    app_bob = CandidateApplication.objects.create(
        room=room,
        candidate=bob_user,
        cv=bob_cv,
        final_score=64.0,
        cv_score=68.0,
        video_score=60.0,
        is_partial_score=False,
        is_shortlisted=False,
        shortlist_reason="Score below minimum threshold of 80.0",
        status=CandidateApplication.Status.COMPLETED,
        hr_decision=CandidateApplication.HrDecision.UNDECIDED
    )

    # 3. Charlie (Undecided candidate for general actions)
    charlie_user = create_user_in_db("charlie_us26@careerflow.test", "ValidPass2026!", role=User.Role.STUDENT, full_name="Charlie Reviewee")
    charlie_cv = CandidateCV.objects.create(
        user=charlie_user,
        file="students/charlie/charlie_cv.pdf",
        original_filename="Charlie_CV.pdf",
        file_size=185000,
        is_active=True
    )
    CVJobMatch.objects.create(
        cv=charlie_cv,
        job_title=room.title,
        company=room.company_name,
        match_score=76.0,
        skills_matched=["Python", "Django"],
        skills_missing=["PyTorch", "Distributed Systems"]
    )
    app_charlie = CandidateApplication.objects.create(
        room=room,
        candidate=charlie_user,
        cv=charlie_cv,
        final_score=78.0,
        cv_score=76.0,
        video_score=80.0,
        is_partial_score=False,
        is_shortlisted=False,
        shortlist_reason="Under general evaluation",
        status=CandidateApplication.Status.COMPLETED,
        hr_decision=CandidateApplication.HrDecision.UNDECIDED
    )

    return room, [app_alice, app_bob, app_charlie]


def open_candidate_review_modal(driver, wait, room_id, app_id, expected_name):
    """Helper to open shortlist modal, click review on candidate, and wait for candidate details to load."""
    base_url = get_base_url()
    driver.get(f"{base_url}/hr/rooms")

    shortlist_btn = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-action-shortlist-{room_id}']"))
    )
    shortlist_btn.click()

    wait.until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-shortlist-config']"))
    )

    review_btn = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='btn-review-applicant-{app_id}']"))
    )
    review_btn.click()

    modal = wait.until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-candidate-review']"))
    )
    wait.until(
        EC.text_to_be_present_in_element((By.CSS_SELECTOR, "[data-testid='heading-candidate-name']"), expected_name)
    )
    wait.until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='text-final-score']"))
    )
    return modal


class TestUS26HRReviewUI:
    """
    US-26: HR Review of AI Results & Human Decision Audit Trail UI Automation Tests
    Task: US-26-T6 (Peer UI Testing & Code Review for HR Review Flow)
    Peer Tester / Reviewer: Farhana Tahsin Bonny (@tahsinbonnie98)
    Developer / Author: MD. Hasanul Mobin (@hasanulmobin1)
    Sprint: Sprint 5
    """

    def test_tc_us26_01_modal_mount_and_signals_display(self, driver):
        """TC-US26-01: Verify HR can open Candidate Review Modal from shortlist table and inspect composite signals."""
        hr_email = "bonny_tc01_mount@careerflow.test"
        login_hr(driver, email=hr_email, full_name="Farhana Tahsin Bonny")
        room, apps = create_us26_sample_room(hr_email, room_title="Lead AI Engineer", company="CareerFlow Systems")

        wait = WebDriverWait(driver, 10)
        app_alice = apps[0]
        modal = open_candidate_review_modal(driver, wait, room.id, app_alice.id, "Alice Candidate")
        assert modal is not None

        # Verify candidate heading, final score, CV score, and AI suggestion
        candidate_name = driver.find_element(By.CSS_SELECTOR, "[data-testid='heading-candidate-name']").text
        assert "Alice Candidate" in candidate_name

        final_score_el = driver.find_element(By.CSS_SELECTOR, "[data-testid='text-final-score']")
        assert "88.5" in final_score_el.text

        cv_score_el = driver.find_element(By.CSS_SELECTOR, "[data-testid='text-cv-score']")
        assert "92.0" in cv_score_el.text

        ai_rec_el = driver.find_element(By.CSS_SELECTOR, "[data-testid='badge-ai-recommendation']")
        assert "Shortlist" in ai_rec_el.text

        # Capture evidence screenshot
        screenshot_path = SCREENSHOTS_DIR / "us26_01_review_modal_mount.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

        # Clean dismissal
        close_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-close-review-modal']")
        close_btn.click()

    def test_tc_us26_02_ai_advisory_disclaimer_prominence(self, driver):
        """TC-US26-02: Verify prominent AI Advisory disclaimer banner is rendered verbatim (US-26 AC#5)."""
        hr_email = "bonny_tc02_disclaimer@careerflow.test"
        login_hr(driver, email=hr_email, full_name="Farhana Tahsin Bonny")
        room, apps = create_us26_sample_room(hr_email, room_title="Solutions Architect", company="CareerFlow Systems")

        wait = WebDriverWait(driver, 10)
        app_alice = apps[0]
        open_candidate_review_modal(driver, wait, room.id, app_alice.id, "Alice Candidate")

        # Verify AI Advisory Disclaimer banner
        disclaimer_banner = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='banner-ai-advisory-disclaimer']"))
        )
        assert disclaimer_banner.is_displayed()
        banner_text = disclaimer_banner.text
        assert "AI Advisory Disclaimer:" in banner_text
        assert "support, not replace, human hiring decisions" in banner_text

        # Capture evidence screenshot
        screenshot_path = SCREENSHOTS_DIR / "us26_02_ai_advisory_disclaimer.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

        close_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-close-review-modal']")
        close_btn.click()

    def test_tc_us26_03_confirm_shortlist_decision_flow(self, driver):
        """TC-US26-03: Verify HR Manager can record Confirm Shortlist decision with notes and audit log (AC#3)."""
        hr_email = "bonny_tc03_confirm@careerflow.test"
        login_hr(driver, email=hr_email, full_name="Farhana Tahsin Bonny")
        room, apps = create_us26_sample_room(hr_email, room_title="Principal Architect", company="CareerFlow Systems")

        wait = WebDriverWait(driver, 10)
        app_alice = apps[0]
        open_candidate_review_modal(driver, wait, room.id, app_alice.id, "Alice Candidate")

        # Click Confirm Shortlist button
        confirm_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='btn-decision-confirm']"))
        )
        confirm_btn.click()

        # Enter review notes
        notes_textarea = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-decision-notes']")
        set_react_input(driver, notes_textarea, "Strong technical portfolio with stellar interview performance. Shortlist confirmed.")

        # Submit Decision
        submit_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='btn-submit-decision']")
        submit_btn.click()

        # Verify success banner
        success_alert = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='alert-decision-success']"))
        )
        assert "recorded successfully" in success_alert.text.lower() or "confirmed" in success_alert.text.lower()

        # Verify DB audit state
        app_alice.refresh_from_db()
        assert app_alice.hr_decision == CandidateApplication.HrDecision.CONFIRMED
        assert app_alice.is_shortlisted is True
        assert app_alice.hr_decided_by.email == hr_email
        assert app_alice.hr_decided_at is not None
        assert "Strong technical portfolio" in app_alice.hr_decision_notes

        # Capture evidence screenshot
        screenshot_path = SCREENSHOTS_DIR / "us26_03_confirm_shortlist.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

        close_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-close-review-modal']")
        close_btn.click()

    def test_tc_us26_04_override_validation_mandatory_justification(self, driver):
        """TC-US26-04: Verify overriding AI recommendation strictly requires justification note (>= 5 chars) (AC#4)."""
        hr_email = "bonny_tc04_val@careerflow.test"
        login_hr(driver, email=hr_email, full_name="Farhana Tahsin Bonny")
        room, apps = create_us26_sample_room(hr_email, room_title="ML Infrastructure Lead", company="CareerFlow Systems")

        wait = WebDriverWait(driver, 10)
        app_bob = apps[1]
        open_candidate_review_modal(driver, wait, room.id, app_bob.id, "Bob LowScore")

        # Click Override AI
        override_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='btn-decision-override']"))
        )
        override_btn.click()

        # Verify Mandatory badge appears
        override_badge = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='badge-override-required']"))
        )
        assert override_badge.is_displayed()
        assert "Mandatory" in override_badge.text

        # Verify submit button is disabled when notes < 5 chars
        notes_textarea = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-decision-notes']")
        set_react_input(driver, notes_textarea, "No")

        submit_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='btn-submit-decision']")
        assert not submit_btn.is_enabled()

        # Capture evidence screenshot
        screenshot_path = SCREENSHOTS_DIR / "us26_04_override_validation_error.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

        close_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-close-review-modal']")
        close_btn.click()

    def test_tc_us26_05_override_successful_ai_inversion(self, driver):
        """TC-US26-05: Verify providing valid justification note permits override and inverts shortlist status (AC#4)."""
        hr_email = "bonny_tc05_over@careerflow.test"
        login_hr(driver, email=hr_email, full_name="Farhana Tahsin Bonny")
        room, apps = create_us26_sample_room(hr_email, room_title="ML Operations Lead", company="CareerFlow Systems")

        wait = WebDriverWait(driver, 10)
        app_bob = apps[1]
        assert app_bob.is_shortlisted is False

        open_candidate_review_modal(driver, wait, room.id, app_bob.id, "Bob LowScore")

        override_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='btn-decision-override']"))
        )
        override_btn.click()

        # Provide comprehensive justification note
        justification = "Candidate has exceptional niche production ML deployment experience compensating for lower CV score."
        notes_textarea = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-decision-notes']")
        set_react_input(driver, notes_textarea, justification)

        submit_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='btn-submit-decision']")
        assert submit_btn.is_enabled()
        submit_btn.click()

        # Verify success alert
        success_alert = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='alert-decision-success']"))
        )
        assert success_alert.is_displayed()

        # Verify DB audit: shortlist status INVERTED to True with OVERRIDDEN decision choice
        app_bob.refresh_from_db()
        assert app_bob.hr_decision == CandidateApplication.HrDecision.OVERRIDDEN
        assert app_bob.is_shortlisted is True
        assert app_bob.hr_decided_by.email == hr_email
        assert justification in app_bob.hr_decision_notes

        # Capture evidence screenshot
        screenshot_path = SCREENSHOTS_DIR / "us26_05_override_success_audit.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

        close_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-close-review-modal']")
        close_btn.click()

    def test_tc_us26_06_reject_and_hold_decision_recording(self, driver):
        """TC-US26-06: Verify Reject Candidate and Put On Hold decisions persist with audit log."""
        hr_email = "bonny_tc06_actions@careerflow.test"
        login_hr(driver, email=hr_email, full_name="Farhana Tahsin Bonny")
        room, apps = create_us26_sample_room(hr_email, room_title="Staff Backend Engineer", company="CareerFlow Systems")

        wait = WebDriverWait(driver, 10)
        app_charlie = apps[2]
        open_candidate_review_modal(driver, wait, room.id, app_charlie.id, "Charlie Reviewee")

        # Test Reject Decision
        reject_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='btn-decision-reject']"))
        )
        reject_btn.click()

        notes_textarea = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-decision-notes']")
        set_react_input(driver, notes_textarea, "Applicant does not meet mandatory backend system requirements.")

        submit_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='btn-submit-decision']")
        submit_btn.click()

        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='alert-decision-success']")))

        app_charlie.refresh_from_db()
        assert app_charlie.hr_decision == CandidateApplication.HrDecision.REJECTED
        assert app_charlie.is_shortlisted is False

        # Test Put On Hold
        hold_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='btn-decision-hold']"))
        )
        hold_btn.click()

        set_react_input(driver, notes_textarea, "Awaiting departmental headcount review before advancing.")
        submit_btn.click()

        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='alert-decision-success']")))

        app_charlie.refresh_from_db()
        assert app_charlie.hr_decision == CandidateApplication.HrDecision.ON_HOLD

        # Capture evidence screenshot
        screenshot_path = SCREENSHOTS_DIR / "us26_06_reject_and_hold_decisions.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

        close_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-close-review-modal']")
        close_btn.click()

    def test_tc_us26_07_tab_switching_cv_skills_and_video_metrics(self, driver):
        """TC-US26-07: Verify tab switching between Signal Overview, CV Skills Match, and Video Presentation Metrics."""
        hr_email = "bonny_tc07_tabs@careerflow.test"
        login_hr(driver, email=hr_email, full_name="Farhana Tahsin Bonny")
        room, apps = create_us26_sample_room(hr_email, room_title="Full Stack Architect", company="CareerFlow Systems")

        wait = WebDriverWait(driver, 10)
        app_alice = apps[0]
        open_candidate_review_modal(driver, wait, room.id, app_alice.id, "Alice Candidate")

        # Switch to CV Skills Tab
        cv_tab = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='tab-review-cv']"))
        )
        cv_tab.click()

        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='skill-matched-0']")))
        cv_tab_content = driver.find_element(By.CSS_SELECTOR, "[data-testid='modal-candidate-review']").text
        assert "Skills Match Analysis" in cv_tab_content
        assert "Matched Required Skills" in cv_tab_content

        # Switch to Video Details Tab
        video_tab = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='tab-review-video']"))
        )
        video_tab.click()

        video_tab_content = driver.find_element(By.CSS_SELECTOR, "[data-testid='modal-candidate-review']").text
        assert "Speech & Behavioral Signal Metrics" in video_tab_content

        # Switch back to Overview Tab
        overview_tab = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='tab-review-overview']"))
        )
        overview_tab.click()

        overview_content = driver.find_element(By.CSS_SELECTOR, "[data-testid='modal-candidate-review']").text
        assert "Human Decision Audit Trail" in overview_content

        # Capture evidence screenshot
        screenshot_path = SCREENSHOTS_DIR / "us26_07_cv_skills_and_video_tabs.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

        close_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-close-review-modal']")
        close_btn.click()

    def test_tc_us26_08_modal_dismissal_and_parent_table_sync(self, driver):
        """TC-US26-08: Verify closing review modal cleanly returns to shortlist list and updates state."""
        hr_email = "bonny_tc08_sync@careerflow.test"
        login_hr(driver, email=hr_email, full_name="Farhana Tahsin Bonny")
        room, apps = create_us26_sample_room(hr_email, room_title="Enterprise AI Lead", company="CareerFlow Systems")

        wait = WebDriverWait(driver, 10)
        app_alice = apps[0]
        open_candidate_review_modal(driver, wait, room.id, app_alice.id, "Alice Candidate")

        # Close Review modal
        close_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-close-review-modal']")
        close_btn.click()

        # Assert Review modal unmounts
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-candidate-review']")))

        # Assert Parent Shortlist Modal remains active
        parent_modal = driver.find_element(By.CSS_SELECTOR, "[data-testid='modal-shortlist-config']")
        assert parent_modal.is_displayed()

        # Capture evidence screenshot
        screenshot_path = SCREENSHOTS_DIR / "us26_08_modal_dismissal_and_table_sync.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()
