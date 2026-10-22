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
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from apps.authentication.models import User
from apps.recruitment.models import RecruitmentRoom, CandidateApplication
from apps.cv.models import CandidateCV, CVJobMatch
from apps.presentation.models import PresentationVideo, PresentationScore
from conftest import FRONTEND_URL, SCREENSHOTS_DIR, create_user_in_db


def get_base_url():
    """Ensure reliable IPv4 localhost URL on Windows 11."""
    return os.environ.get("FRONTEND_URL", "http://127.0.0.1:5173")


def login_hr(driver, email="mobin_peer_tester@careerflow.test", password="ValidPass2026!", full_name="MD. Hasanul Mobin"):
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


def create_us27_sample_room(hr_email: str, room_title="Senior AI Solutions Architect", company="TechCorp Global"):
    """
    Creates a RecruitmentRoom owned by hr_email with candidates to thoroughly test US-27:
    1. Alice: Complete multi-modal evaluation (final_score=88.5, cv=92.0, video=85.0, is_partial=False)
       Includes matched skills and video metrics for granular card inspection.
    2. Bob: Missing video submission (final_score=88.0, cv=88.0, video=None, is_partial=True)
       Target for graceful degradation and amber warning notice testing.
    3. Charlie: Complete evaluation (final_score=78.0, cv=80.0, video=76.0, is_partial=False)
    """
    hr_user = User.objects.get(email=hr_email)

    room = RecruitmentRoom.objects.create(
        title=room_title,
        company_name=company,
        department="Engineering",
        description="Senior AI architect responsible for designing enterprise decision engines and LLM systems.",
        requirements_text="Proficiency in Python, PyTorch, Django, and Distributed Systems.",
        skills_required=["Python", "PyTorch", "Django", "Distributed Systems"],
        status=RecruitmentRoom.Status.ACTIVE,
        created_by=hr_user,
        cv_weight=50,
        video_weight=50,
        shortlist_strategy=RecruitmentRoom.ShortlistStrategy.MIN_SCORE,
        shortlist_min_score=80.0
    )

    now = timezone.now()

    # 1. Alice (Complete signals)
    alice_user = create_user_in_db("alice_us27@careerflow.test", "ValidPass2026!", role=User.Role.STUDENT, full_name="Alice Candidate")
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
        status=CandidateApplication.Status.COMPLETED
    )

    # 2. Bob (Missing Video -> Partial score)
    bob_user = create_user_in_db("bob_us27@careerflow.test", "ValidPass2026!", role=User.Role.STUDENT, full_name="Bob MissingVideo")
    bob_cv = CandidateCV.objects.create(
        user=bob_user,
        file="students/bob/bob_cv.pdf",
        original_filename="Bob_Resume.pdf",
        file_size=190000,
        is_active=True
    )
    CVJobMatch.objects.create(
        cv=bob_cv,
        job_title=room.title,
        company=room.company_name,
        match_score=88.0,
        skills_matched=["Python", "Django"],
        skills_missing=["PyTorch", "Distributed Systems"]
    )
    app_bob = CandidateApplication.objects.create(
        room=room,
        candidate=bob_user,
        cv=bob_cv,
        final_score=88.0,
        cv_score=88.0,
        video_score=None,
        is_partial_score=True,
        is_shortlisted=True,
        shortlist_reason="Pro-rated based on CV score",
        status=CandidateApplication.Status.COMPLETED
    )

    # 3. Charlie (Complete signals)
    charlie_user = create_user_in_db("charlie_us27@careerflow.test", "ValidPass2026!", role=User.Role.STUDENT, full_name="Charlie Candidate")
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
        match_score=80.0,
        skills_matched=["Python"],
        skills_missing=["PyTorch", "Django", "Distributed Systems"]
    )
    charlie_video = PresentationVideo.objects.create(
        user=charlie_user,
        file="students/charlie/video.mp4",
        original_filename="Charlie_Presentation.mp4",
        raw_file_size=14000000,
        file_type="mp4",
        duration_seconds=110,
        status="COMPLETED"
    )
    PresentationScore.objects.create(
        video=charlie_video,
        overall_score=76,
        speech_score=78,
        behavioral_score=74
    )
    app_charlie = CandidateApplication.objects.create(
        room=room,
        candidate=charlie_user,
        cv=charlie_cv,
        video=charlie_video,
        final_score=78.0,
        cv_score=80.0,
        video_score=76.0,
        is_partial_score=False,
        is_shortlisted=False,
        shortlist_reason="Score below threshold",
        status=CandidateApplication.Status.COMPLETED
    )

    return room, [app_alice, app_bob, app_charlie]


class TestUS27ScoreBreakdownUI:
    """
    US-27: Explainable Applicant Score Breakdown & Transparency UI Test Suite
    Task: US-27-T6 (Peer UI Testing & Code Review for Score Breakdown Display)
    Developer / Author: Farhana Tahsin Bonny (@tahsinbonnie98)
    Assigned Peer Tester: MD. Hasanul Mobin (@hasanulmobin1) [reassigned due to Mona's illness]
    Sprint: Sprint 5
    """

    def test_tc_us27_01_breakdown_modal_mount_from_leaderboard(self, driver):
        """TC-US27-01: Verify HR can launch Score Breakdown Modal from Applicant Leaderboard (RankedApplicantsModal)."""
        hr_email = "mobin_tc01_mount@careerflow.test"
        login_hr(driver, email=hr_email, full_name="MD. Hasanul Mobin")
        room, apps = create_us27_sample_room(hr_email, room_title="AI Research Lead", company="TechCorp Global")

        wait = WebDriverWait(driver, 10)
        base_url = get_base_url()
        driver.get(f"{base_url}/hr/dashboard")

        # Open Ranked Applicants Leaderboard modal via quick dropdown
        from selenium.webdriver.support.ui import Select
        room_select = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='select-room-rankings-dashboard']"))
        )
        Select(room_select).select_by_value(str(room.id))

        # Wait for RankedApplicantsModal elements
        wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='tab-ranked-leaderboard']"))
        )

        app_alice = apps[0]
        breakdown_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='btn-score-breakdown-{app_alice.id}']"))
        )
        breakdown_btn.click()

        # Assert Score Breakdown Modal mounts cleanly
        modal = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-score-breakdown']"))
        )
        assert modal is not None

        # Verify Candidate Name, US-27 Badge, and Room Title in Header
        candidate_header = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='text-breakdown-candidate-name']"))
        ).text
        assert "Alice Candidate" in candidate_header

        # Verify composite final score element
        final_score_el = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='text-composite-final-score']"))
        )
        assert "88.5" in final_score_el.text

        screenshot_path = SCREENSHOTS_DIR / "us27_01_leaderboard_breakdown_mount.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc_us27_02_breakdown_modal_mount_from_shortlist(self, driver):
        """TC-US27-02: Verify HR can launch Score Breakdown Modal from Shortlist Config Table (ShortlistConfigModal)."""
        hr_email = "mobin_tc02_shortlist@careerflow.test"
        login_hr(driver, email=hr_email, full_name="MD. Hasanul Mobin")
        room, apps = create_us27_sample_room(hr_email, room_title="Staff ML Engineer", company="TechCorp Global")

        wait = WebDriverWait(driver, 10)
        base_url = get_base_url()
        driver.get(f"{base_url}/hr/rooms")

        shortlist_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-action-shortlist-{room.id}']"))
        )
        shortlist_btn.click()

        wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-shortlist-config']"))
        )

        app_alice = apps[0]
        breakdown_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='btn-breakdown-applicant-{app_alice.id}']"))
        )
        breakdown_btn.click()

        modal = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-score-breakdown']"))
        )
        assert modal is not None

        candidate_header = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='text-breakdown-candidate-name']"))
        ).text
        assert "Alice Candidate" in candidate_header

        screenshot_path = SCREENSHOTS_DIR / "us27_02_shortlist_breakdown_mount.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc_us27_03_mathematical_points_and_weights_display(self, driver):
        """TC-US27-03: Verify configured weights split, exact points contributed, and final score badges (AC#1, AC#2)."""
        hr_email = "mobin_tc03_weights@careerflow.test"
        login_hr(driver, email=hr_email, full_name="MD. Hasanul Mobin")
        room, apps = create_us27_sample_room(hr_email, room_title="Principal Architect", company="TechCorp Global")

        wait = WebDriverWait(driver, 10)
        base_url = get_base_url()
        driver.get(f"{base_url}/hr/rooms")

        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-action-shortlist-{room.id}']"))).click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-shortlist-config']")))

        app_alice = apps[0]
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='btn-breakdown-applicant-{app_alice.id}']"))).click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-score-breakdown']")))

        # 1. Assert Weights (50% / 50%)
        cv_weight_el = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='text-cv-weight']")))
        assert "50%" in cv_weight_el.text

        video_weight_el = driver.find_element(By.CSS_SELECTOR, "[data-testid='text-video-weight']")
        assert "50%" in video_weight_el.text

        # 2. Assert Points Summary (+46.0 pts CV, +42.5 pts Video)
        cv_points_el = driver.find_element(By.CSS_SELECTOR, "[data-testid='text-cv-points-summary']")
        assert "+46.0" in cv_points_el.text

        video_points_el = driver.find_element(By.CSS_SELECTOR, "[data-testid='text-video-points-summary']")
        assert "+42.5" in video_points_el.text

        # 3. Assert Composite Final Score (88.5 / 100)
        final_score_el = driver.find_element(By.CSS_SELECTOR, "[data-testid='text-composite-final-score']")
        assert "88.5" in final_score_el.text

        screenshot_path = SCREENSHOTS_DIR / "us27_03_weights_and_points_display.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc_us27_04_visual_segmented_contribution_bar(self, driver):
        """TC-US27-04: Verify the visual segmented contribution bar scales correctly across 0-100 points."""
        hr_email = "mobin_tc04_bar@careerflow.test"
        login_hr(driver, email=hr_email, full_name="MD. Hasanul Mobin")
        room, apps = create_us27_sample_room(hr_email, room_title="Lead Data Scientist", company="TechCorp Global")

        wait = WebDriverWait(driver, 10)
        base_url = get_base_url()
        driver.get(f"{base_url}/hr/rooms")

        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-action-shortlist-{room.id}']"))).click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-shortlist-config']")))

        app_alice = apps[0]
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='btn-breakdown-applicant-{app_alice.id}']"))).click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-score-breakdown']")))

        # Verify Segmented Bar Container
        split_bar = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='bar-contribution-split']")))
        assert split_bar is not None

        # Verify bar text contents
        bar_text = split_bar.text
        assert "CV +46.0" in bar_text
        assert "Video +42.5" in bar_text

        screenshot_path = SCREENSHOTS_DIR / "us27_04_segmented_split_bar.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc_us27_05_arithmetic_formula_derivation_box(self, driver):
        """TC-US27-05: Verify mathematical formula box renders exact arithmetic derivation (AC#1, AC#5)."""
        hr_email = "mobin_tc05_formula@careerflow.test"
        login_hr(driver, email=hr_email, full_name="MD. Hasanul Mobin")
        room, apps = create_us27_sample_room(hr_email, room_title="DevOps Lead", company="TechCorp Global")

        wait = WebDriverWait(driver, 10)
        base_url = get_base_url()
        driver.get(f"{base_url}/hr/rooms")

        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-action-shortlist-{room.id}']"))).click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-shortlist-config']")))

        app_alice = apps[0]
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='btn-breakdown-applicant-{app_alice.id}']"))).click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-score-breakdown']")))

        formula_box = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='box-formula-display']")))
        formula_text = formula_box.text

        # Verify arithmetic formula: (50% × 92.0) + (50% × 85.0) = 46.0 + 42.5 = 88.5 / 100
        assert "50%" in formula_text
        assert "92.0" in formula_text
        assert "85.0" in formula_text
        assert "46.0 + 42.5" in formula_text
        assert "88.5" in formula_text

        screenshot_path = SCREENSHOTS_DIR / "us27_05_arithmetic_formula_display.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc_us27_06_side_by_side_signals_and_submetrics(self, driver):
        """TC-US27-06: Verify side-by-side component breakdown cards for CV Semantic Match and Video Analysis (AC#3)."""
        hr_email = "mobin_tc06_signals@careerflow.test"
        login_hr(driver, email=hr_email, full_name="MD. Hasanul Mobin")
        room, apps = create_us27_sample_room(hr_email, room_title="Full Stack Lead", company="TechCorp Global")

        wait = WebDriverWait(driver, 10)
        base_url = get_base_url()
        driver.get(f"{base_url}/hr/rooms")

        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-action-shortlist-{room.id}']"))).click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-shortlist-config']")))

        app_alice = apps[0]
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='btn-breakdown-applicant-{app_alice.id}']"))).click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-score-breakdown']")))

        # 1. Inspect CV Breakdown Card
        cv_card = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='card-cv-breakdown']")))
        cv_raw_score = cv_card.find_element(By.CSS_SELECTOR, "[data-testid='text-cv-raw-score']").text
        assert "92.0" in cv_raw_score

        cv_points = cv_card.find_element(By.CSS_SELECTOR, "[data-testid='text-cv-points-contributed']").text
        assert "+46.0" in cv_points

        # Assert matched skills pills
        assert "✓ Python" in cv_card.text
        assert "✓ PyTorch" in cv_card.text
        assert "✓ Django" in cv_card.text

        # 2. Inspect Video Breakdown Card
        video_card = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='card-video-breakdown']")))
        video_raw_score = video_card.find_element(By.CSS_SELECTOR, "[data-testid='text-video-raw-score']").text
        assert "85.0" in video_raw_score

        video_points = video_card.find_element(By.CSS_SELECTOR, "[data-testid='text-video-points-contributed']").text
        assert "+42.5" in video_points

        screenshot_path = SCREENSHOTS_DIR / "us27_06_side_by_side_signals.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc_us27_07_graceful_degradation_missing_component_alert(self, driver):
        """TC-US27-07: Verify graceful degradation banner & pro-rated notice when video is missing (AC#4)."""
        hr_email = "mobin_tc07_degrade@careerflow.test"
        login_hr(driver, email=hr_email, full_name="MD. Hasanul Mobin")
        room, apps = create_us27_sample_room(hr_email, room_title="Systems Engineer", company="TechCorp Global")

        wait = WebDriverWait(driver, 10)
        base_url = get_base_url()
        driver.get(f"{base_url}/hr/rooms")

        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-action-shortlist-{room.id}']"))).click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-shortlist-config']")))

        # Bob has missing video
        app_bob = apps[1]
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='btn-breakdown-applicant-{app_bob.id}']"))).click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-score-breakdown']")))

        # 1. Assert Partial Score Badge
        partial_badge = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='badge-partial-score']")))
        assert "Partial (Pro-rated)" in partial_badge.text

        # 2. Assert Missing Components Alert Banner
        alert_box = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='alert-missing-components']")))
        assert "Video submission or analysis is missing" in alert_box.text
        assert "pro-rated" in alert_box.text.lower()

        # 3. Assert Video Card shows Missing status
        video_card = driver.find_element(By.CSS_SELECTOR, "[data-testid='card-video-breakdown']")
        assert "Missing" in video_card.text
        assert "0.0 pts" in video_card.text

        screenshot_path = SCREENSHOTS_DIR / "us27_07_missing_component_degradation.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc_us27_08_modal_dismissal_and_mobile_responsiveness(self, driver):
        """TC-US27-08: Verify modal close button and mobile viewport responsiveness (375x812)."""
        hr_email = "mobin_tc08_mobile@careerflow.test"
        login_hr(driver, email=hr_email, full_name="MD. Hasanul Mobin")
        room, apps = create_us27_sample_room(hr_email, room_title="Mobile Architect", company="TechCorp Global")

        # Set mobile viewport
        driver.set_window_size(375, 812)
        wait = WebDriverWait(driver, 10)
        base_url = get_base_url()
        driver.get(f"{base_url}/hr/rooms")

        shortlist_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, f"[data-testid='button-action-shortlist-{room.id}']")))
        driver.execute_script("arguments[0].scrollIntoView(true);", shortlist_btn)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", shortlist_btn)

        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-shortlist-config']")))

        app_alice = apps[0]
        breakdown_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, f"[data-testid='btn-breakdown-applicant-{app_alice.id}']")))
        driver.execute_script("arguments[0].scrollIntoView(true);", breakdown_btn)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", breakdown_btn)

        modal = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-score-breakdown']")))
        assert modal is not None

        # Verify no severe horizontal overflow
        modal_width = driver.execute_script("return arguments[0].getBoundingClientRect().width;", modal)
        window_width = driver.execute_script("return window.innerWidth;")
        assert modal_width <= window_width + 20

        screenshot_path = SCREENSHOTS_DIR / "us27_08_mobile_responsive_breakdown.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

        # Test Close button dismissal
        close_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='btn-close-breakdown-modal']")))
        close_btn.click()

        # Assert breakdown modal unmounts
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-score-breakdown']")))

        # Restore desktop window size
        driver.set_window_size(1920, 1080)
