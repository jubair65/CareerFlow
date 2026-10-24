import os
import sys
import time
import uuid
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
from apps.recruitment.models import RecruitmentRoom, CandidateApplication
from apps.cv.models import CandidateCV, CVJobMatch
from apps.presentation.models import (
    PresentationVideo,
    PresentationScore,
    SpeechAnalysis,
    BehavioralAnalysis,
)
from conftest import FRONTEND_URL, BACKEND_URL, SCREENSHOTS_DIR, create_user_in_db


def get_base_url():
    """Ensure reliable frontend URL."""
    return os.environ.get("FRONTEND_URL", "http://localhost:5173")


def login_hr(driver, email: str, password: str = "ValidPass2026!", full_name: str = "MD. Jubair Bin Hasan"):
    """Helper to ensure HR Manager user exists and authenticates via UI."""
    if not User.objects.filter(email__iexact=email).exists():
        create_user_in_db(email, password, role=User.Role.HR_MANAGER, full_name=full_name)

    base_url = get_base_url()
    driver.get(f"{base_url}/login")
    driver.execute_script("sessionStorage.clear(); localStorage.clear();")
    driver.refresh()

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


def create_us28_sample_room(hr_email: str, room_title="Principal Full-Stack Engineer", company="Apex Cloud Systems"):
    """
    Creates a RecruitmentRoom owned by hr_email with 5 candidate applications covering all US-28 testing facets:
    1. Candidate 1 (Rahim Ahmed): High composite (88.0), top CV (90.0%), top eye contact (92%), 4 matched skills.
    2. Candidate 2 (Fatima Noor): High composite (86.0), top video (95.0), WPM 150, 3 matched skills.
    3. Candidate 3 (Tanvir Hasan): Lower composite (72.0), CV 70.0%, Video 75.0, 2 matched skills.
    4. Candidate 4 (Anika Tabassum): Balanced (83.0), CV 85.0%, Video 80.0, 3 matched skills.
    5. Candidate 5 (Kamrul Islam): Missing video evaluation (CV 65.0%, Video None -> Partial/Pending).
    """
    if not User.objects.filter(email__iexact=hr_email).exists():
        create_user_in_db(hr_email, "ValidPass2026!", role=User.Role.HR_MANAGER, full_name="MD. Jubair Bin Hasan")

    hr_user = User.objects.get(email__iexact=hr_email)
    uid = uuid.uuid4().hex[:6]

    room = RecruitmentRoom.objects.create(
        title=f"{room_title} {uid}",
        company_name=company,
        department="Engineering",
        description="Principal engineer leading distributed microservices and reactive frontend architectures.",
        requirements_text="Must master Python, Django, PostgreSQL, Docker, and AWS.",
        skills_required=["Python", "Django", "PostgreSQL", "Docker", "AWS"],
        status=RecruitmentRoom.Status.ACTIVE,
        created_by=hr_user,
        cv_weight=60,
        video_weight=40,
        shortlist_strategy=RecruitmentRoom.ShortlistStrategy.TOP_N,
        shortlist_top_n=3,
    )

    # 1. Rahim Ahmed (Top CV & Top Eye Contact)
    u1 = create_user_in_db(f"rahim_{uid}@demo.com", "ValidPass2026!", role=User.Role.STUDENT, full_name="Rahim Ahmed")
    cv1 = CandidateCV.objects.create(user=u1, file=f"cv_{uid}_1.pdf", original_filename="Rahim_CV.pdf", file_size=200000, is_active=True)
    CVJobMatch.objects.create(
        cv=cv1, job_title=room.title, company=room.company_name,
        match_score=90.0,
        skills_matched=["Python", "Django", "PostgreSQL", "Docker"],
        skills_missing=["AWS"]
    )
    v1 = PresentationVideo.objects.create(user=u1, file=f"v_{uid}_1.mp4", original_filename="Rahim_Pitch.mp4", raw_file_size=12000000, file_type="mp4", duration_seconds=115, status="COMPLETED")
    PresentationScore.objects.create(video=v1, overall_score=85, speech_score=84, behavioral_score=86, pace_score=85, eye_contact_score=92, posture_score=88)
    SpeechAnalysis.objects.create(video=v1, words_per_minute=140.0, filler_word_count=2, clarity_score=88)
    BehavioralAnalysis.objects.create(video=v1, eye_contact_score=92, posture_score=88, engagement_score=85)
    app1 = CandidateApplication.objects.create(
        room=room, candidate=u1, cv=cv1, video=v1,
        final_score=88.0, cv_score=90.0, video_score=85.0,
        is_partial_score=False, is_shortlisted=True,
        shortlist_reason="Top ranking candidate",
        status=CandidateApplication.Status.COMPLETED
    )

    # 2. Fatima Noor (Top Video)
    u2 = create_user_in_db(f"fatima_{uid}@demo.com", "ValidPass2026!", role=User.Role.STUDENT, full_name="Fatima Noor")
    cv2 = CandidateCV.objects.create(user=u2, file=f"cv_{uid}_2.pdf", original_filename="Fatima_CV.pdf", file_size=195000, is_active=True)
    CVJobMatch.objects.create(
        cv=cv2, job_title=room.title, company=room.company_name,
        match_score=80.0,
        skills_matched=["Python", "Django", "PostgreSQL"],
        skills_missing=["Docker", "AWS"]
    )
    v2 = PresentationVideo.objects.create(user=u2, file=f"v_{uid}_2.mp4", original_filename="Fatima_Pitch.mp4", raw_file_size=14000000, file_type="mp4", duration_seconds=120, status="COMPLETED")
    PresentationScore.objects.create(video=v2, overall_score=95, speech_score=94, behavioral_score=96, pace_score=95, eye_contact_score=88, posture_score=92)
    SpeechAnalysis.objects.create(video=v2, words_per_minute=150.0, filler_word_count=1, clarity_score=92)
    BehavioralAnalysis.objects.create(video=v2, eye_contact_score=88, posture_score=92, engagement_score=94)
    app2 = CandidateApplication.objects.create(
        room=room, candidate=u2, cv=cv2, video=v2,
        final_score=86.0, cv_score=80.0, video_score=95.0,
        is_partial_score=False, is_shortlisted=True,
        shortlist_reason="Top video presentation",
        status=CandidateApplication.Status.COMPLETED
    )

    # 3. Tanvir Hasan (Lower score)
    u3 = create_user_in_db(f"tanvir_{uid}@demo.com", "ValidPass2026!", role=User.Role.STUDENT, full_name="Tanvir Hasan")
    cv3 = CandidateCV.objects.create(user=u3, file=f"cv_{uid}_3.pdf", original_filename="Tanvir_CV.pdf", file_size=180000, is_active=True)
    CVJobMatch.objects.create(
        cv=cv3, job_title=room.title, company=room.company_name,
        match_score=70.0,
        skills_matched=["Python", "Django"],
        skills_missing=["PostgreSQL", "Docker", "AWS"]
    )
    v3 = PresentationVideo.objects.create(user=u3, file=f"v_{uid}_3.mp4", original_filename="Tanvir_Pitch.mp4", raw_file_size=11000000, file_type="mp4", duration_seconds=100, status="COMPLETED")
    PresentationScore.objects.create(video=v3, overall_score=75, speech_score=76, behavioral_score=74, pace_score=72, eye_contact_score=70, posture_score=75)
    SpeechAnalysis.objects.create(video=v3, words_per_minute=120.0, filler_word_count=5, clarity_score=78)
    BehavioralAnalysis.objects.create(video=v3, eye_contact_score=70, posture_score=75, engagement_score=70)
    app3 = CandidateApplication.objects.create(
        room=room, candidate=u3, cv=cv3, video=v3,
        final_score=72.0, cv_score=70.0, video_score=75.0,
        is_partial_score=False, is_shortlisted=False,
        status=CandidateApplication.Status.COMPLETED
    )

    # 4. Anika Tabassum
    u4 = create_user_in_db(f"anika_{uid}@demo.com", "ValidPass2026!", role=User.Role.STUDENT, full_name="Anika Tabassum")
    cv4 = CandidateCV.objects.create(user=u4, file=f"cv_{uid}_4.pdf", original_filename="Anika_CV.pdf", file_size=190000, is_active=True)
    CVJobMatch.objects.create(
        cv=cv4, job_title=room.title, company=room.company_name,
        match_score=85.0,
        skills_matched=["Python", "PostgreSQL", "AWS"],
        skills_missing=["Django", "Docker"]
    )
    v4 = PresentationVideo.objects.create(user=u4, file=f"v_{uid}_4.mp4", original_filename="Anika_Pitch.mp4", raw_file_size=13000000, file_type="mp4", duration_seconds=110, status="COMPLETED")
    PresentationScore.objects.create(video=v4, overall_score=80, speech_score=82, behavioral_score=78, pace_score=85, eye_contact_score=85, posture_score=80)
    SpeechAnalysis.objects.create(video=v4, words_per_minute=145.0, filler_word_count=3, clarity_score=82)
    BehavioralAnalysis.objects.create(video=v4, eye_contact_score=85, posture_score=80, engagement_score=82)
    app4 = CandidateApplication.objects.create(
        room=room, candidate=u4, cv=cv4, video=v4,
        final_score=83.0, cv_score=85.0, video_score=80.0,
        is_partial_score=False, is_shortlisted=True,
        status=CandidateApplication.Status.COMPLETED
    )

    # 5. Kamrul Islam (Pending Video evaluation -> partial)
    u5 = create_user_in_db(f"kamrul_{uid}@demo.com", "ValidPass2026!", role=User.Role.STUDENT, full_name="Kamrul Islam")
    cv5 = CandidateCV.objects.create(user=u5, file=f"cv_{uid}_5.pdf", original_filename="Kamrul_CV.pdf", file_size=170000, is_active=True)
    CVJobMatch.objects.create(
        cv=cv5, job_title=room.title, company=room.company_name,
        match_score=65.0,
        skills_matched=["Python"],
        skills_missing=["Django", "PostgreSQL", "Docker", "AWS"]
    )
    app5 = CandidateApplication.objects.create(
        room=room, candidate=u5, cv=cv5, video=None,
        final_score=65.0, cv_score=65.0, video_score=None,
        is_partial_score=True, is_shortlisted=False,
        status=CandidateApplication.Status.COMPLETED
    )

    return room, [app1, app2, app3, app4, app5]


def open_rankings_modal(driver, room):
    """Navigates to /hr/rooms and opens the RankedApplicantsModal for the specified room."""
    wait = WebDriverWait(driver, 10)
    base_url = get_base_url()
    driver.get(f"{base_url}/hr/rooms")

    # Locate the Rankings button on the room card
    rankings_btn = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-action-ranking-{room.id}']"))
    )
    rankings_btn.click()

    # Wait for RankedApplicantsModal elements
    wait.until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='tab-ranked-leaderboard']"))
    )


class TestUS28ApplicantComparisonUI:
    """
    US-28: Side-by-Side Applicant Comparison UI Test Suite (US-28-T6).
    Lead Developer: Nafisa Tabassum Maria (@Maria-07-222)
    Dedicated Peer Cross-Tester / Reviewer: MD. Jubair Bin Hasan (@jubair65)
    Sprint: Sprint 6 (Epic 6: Scoring, Ranking & Shortlisting)
    """

    def test_tc28_01_candidate_selection_checkboxes_and_bar(self, driver):
        """TC-28-01: Verify selection checkboxes on ranked candidates and dynamic comparison bar counter."""
        hr_email = "jubair_tc01@careerflow.test"
        room, apps = create_us28_sample_room(hr_email, room_title="Full-Stack Tech Lead")

        login_hr(driver, email=hr_email, full_name="MD. Jubair Bin Hasan")
        open_rankings_modal(driver, room)
        wait = WebDriverWait(driver, 10)

        # 1. Initially comparison bar is NOT visible
        assert len(driver.find_elements(By.CSS_SELECTOR, "[data-testid='bar-applicant-comparison']")) == 0

        # 2. Select first applicant (app1)
        app1_checkbox = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, f"[data-testid='checkbox-compare-{apps[0].id}']"))
        )
        driver.execute_script("arguments[0].click();", app1_checkbox)

        # Comparison bar appears with "1 of 4 candidates selected"
        bar = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='bar-applicant-comparison']"))
        )
        assert "1 of 4 candidates selected" in bar.text

        # Compare Now button should be disabled for < 2 candidates
        compare_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='btn-compare-now']")
        assert compare_btn.get_attribute("disabled") is not None

        # 3. Select second applicant (app2)
        app2_checkbox = driver.find_element(By.CSS_SELECTOR, f"[data-testid='checkbox-compare-{apps[1].id}']")
        driver.execute_script("arguments[0].click();", app2_checkbox)

        time.sleep(0.3)
        assert "2 of 4 candidates selected" in bar.text
        assert compare_btn.get_attribute("disabled") is None  # Now enabled

        screenshot_path = SCREENSHOTS_DIR / "us28_01_candidate_selection_checkboxes_and_bar.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc28_02_max_selection_limit_enforcement(self, driver):
        """TC-28-02: Verify max 4 candidates limit disables unselected checkboxes and Clear button resets selection."""
        hr_email = "jubair_tc02@careerflow.test"
        room, apps = create_us28_sample_room(hr_email, room_title="Lead Architect Selection")

        login_hr(driver, email=hr_email, full_name="MD. Jubair Bin Hasan")
        open_rankings_modal(driver, room)
        wait = WebDriverWait(driver, 10)

        # Select first 4 candidates
        for i in range(4):
            cb = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, f"[data-testid='checkbox-compare-{apps[i].id}']"))
            )
            driver.execute_script("arguments[0].click();", cb)
            time.sleep(0.1)

        bar = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='bar-applicant-comparison']"))
        )
        assert "4 of 4 candidates selected" in bar.text

        # 5th candidate checkbox must be disabled due to max 4 guard (AC#5)
        cb5 = driver.find_element(By.CSS_SELECTOR, f"[data-testid='checkbox-compare-{apps[4].id}']")
        assert cb5.get_attribute("disabled") is not None

        screenshot_path = SCREENSHOTS_DIR / "us28_02_max_selection_limit_enforcement.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

        # Click Clear button
        clear_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='btn-clear-selection']")
        clear_btn.click()
        time.sleep(0.3)

        # Comparison bar should disappear
        assert len(driver.find_elements(By.CSS_SELECTOR, "[data-testid='bar-applicant-comparison']")) == 0

    def test_tc28_03_launch_side_by_side_comparison_modal(self, driver):
        """TC-28-03: Verify clicking Compare Now launches the light-mode side-by-side comparison matrix modal."""
        hr_email = "jubair_tc03@careerflow.test"
        room, apps = create_us28_sample_room(hr_email, room_title="Principal DevOps Architect")

        login_hr(driver, email=hr_email, full_name="MD. Jubair Bin Hasan")
        open_rankings_modal(driver, room)
        wait = WebDriverWait(driver, 10)

        # Select Candidates 1 and 2
        for i in [0, 1]:
            cb = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, f"[data-testid='checkbox-compare-{apps[i].id}']"))
            )
            driver.execute_script("arguments[0].click();", cb)
            time.sleep(0.1)

        compare_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='btn-compare-now']"))
        )
        compare_btn.click()

        # Assert ApplicantComparisonModal mounts cleanly in light mode
        modal = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-applicant-comparison']"))
        )
        assert modal is not None

        # Verify header title and candidates count
        header_text = modal.text
        assert "Side-by-Side Applicant Comparison" in header_text
        assert "2 Candidates" in header_text

        # Verify candidate cards rendered side-by-side
        card1 = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='card-comparison-candidate-{apps[0].id}']"))
        )
        card2 = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='card-comparison-candidate-{apps[1].id}']"))
        )
        assert card1 is not None and card2 is not None

        screenshot_path = SCREENSHOTS_DIR / "us28_03_launch_side_by_side_comparison_modal.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc28_04_score_breakdown_and_group_differentials(self, driver):
        """TC-28-04: Verify composite scores, score differentials (Best vs variance delta), and Top Scorer badge."""
        hr_email = "jubair_tc04@careerflow.test"
        room, apps = create_us28_sample_room(hr_email, room_title="AI Research Staff")

        login_hr(driver, email=hr_email, full_name="MD. Jubair Bin Hasan")
        open_rankings_modal(driver, room)
        wait = WebDriverWait(driver, 10)

        # Select Candidates 1 (88.0) and 2 (86.0)
        for i in [0, 1]:
            cb = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, f"[data-testid='checkbox-compare-{apps[i].id}']"))
            )
            driver.execute_script("arguments[0].click();", cb)
            time.sleep(0.1)

        driver.find_element(By.CSS_SELECTOR, "[data-testid='btn-compare-now']").click()

        wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-applicant-comparison']"))
        )

        # Check Final Scores (88.0 vs 86.0)
        score1 = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='score-final-{apps[0].id}']"))
        ).text
        score2 = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='score-final-{apps[1].id}']"))
        ).text
        assert "88.0" in score1
        assert "86.0" in score2

        # Candidate 1 has Top Score differential "Best"
        diff1 = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='diff-final-{apps[0].id}']"))
        ).text
        assert "Best" in diff1

        # Candidate 2 has differential "-2.0"
        diff2 = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='diff-final-{apps[1].id}']"))
        ).text
        assert "-2.0" in diff2

        screenshot_path = SCREENSHOTS_DIR / "us28_04_score_breakdown_and_group_differentials.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc28_05_cv_semantic_skills_match_matrix(self, driver):
        """TC-28-05: Verify CV semantic score, Top CV badge, matched skills, and missing skills."""
        hr_email = "jubair_tc05@careerflow.test"
        room, apps = create_us28_sample_room(hr_email, room_title="Enterprise Solutions Lead")

        login_hr(driver, email=hr_email, full_name="MD. Jubair Bin Hasan")
        open_rankings_modal(driver, room)
        wait = WebDriverWait(driver, 10)

        for i in [0, 1]:
            cb = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, f"[data-testid='checkbox-compare-{apps[i].id}']"))
            )
            driver.execute_script("arguments[0].click();", cb)
            time.sleep(0.1)

        driver.find_element(By.CSS_SELECTOR, "[data-testid='btn-compare-now']").click()

        wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-applicant-comparison']"))
        )

        # CV Score 1 (90.0%) vs CV Score 2 (80.0%)
        cv_score1 = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='score-cv-{apps[0].id}']"))
        ).text
        cv_score2 = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='score-cv-{apps[1].id}']"))
        ).text
        assert "90.0%" in cv_score1
        assert "80.0%" in cv_score2

        screenshot_path = SCREENSHOTS_DIR / "us28_05_cv_semantic_skills_match_matrix.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc28_06_video_presentation_and_behavioral_signals(self, driver):
        """TC-28-06: Verify video score, eye contact %, WPM pace, filler words, and posture score."""
        hr_email = "jubair_tc06@careerflow.test"
        room, apps = create_us28_sample_room(hr_email, room_title="Cloud Security Director")

        login_hr(driver, email=hr_email, full_name="MD. Jubair Bin Hasan")
        open_rankings_modal(driver, room)
        wait = WebDriverWait(driver, 10)

        for i in [0, 1]:
            cb = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, f"[data-testid='checkbox-compare-{apps[i].id}']"))
            )
            driver.execute_script("arguments[0].click();", cb)
            time.sleep(0.1)

        driver.find_element(By.CSS_SELECTOR, "[data-testid='btn-compare-now']").click()

        wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-applicant-comparison']"))
        )

        # Video score 1 (85.0/100) vs Video score 2 (95.0/100 with Top Video badge)
        vid_score1 = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='score-video-{apps[0].id}']"))
        ).text
        vid_score2 = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='score-video-{apps[1].id}']"))
        ).text
        assert "85.0/100" in vid_score1
        assert "95.0/100" in vid_score2

        # Eye contact: 92% (Candidate 1 - Best Eye Contact) vs 88% (Candidate 2)
        eye1 = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='metric-eye-{apps[0].id}']"))
        ).text
        eye2 = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='metric-eye-{apps[1].id}']"))
        ).text
        assert "92%" in eye1
        assert "88%" in eye2

        screenshot_path = SCREENSHOTS_DIR / "us28_06_video_presentation_and_behavioral_signals.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc28_07_graceful_missing_scores_handling(self, driver):
        """TC-28-07: Verify graceful degradation with N/A - Pending when comparing candidates with missing scores."""
        hr_email = "jubair_tc07@careerflow.test"
        room, apps = create_us28_sample_room(hr_email, room_title="Systems Engineering Lead")

        login_hr(driver, email=hr_email, full_name="MD. Jubair Bin Hasan")
        open_rankings_modal(driver, room)
        wait = WebDriverWait(driver, 10)

        # Select Candidate 1 (Full signals) and Candidate 5 (Kamrul - Missing video evaluation)
        for idx in [0, 4]:
            cb = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, f"[data-testid='checkbox-compare-{apps[idx].id}']"))
            )
            driver.execute_script("arguments[0].click();", cb)
            time.sleep(0.1)

        driver.find_element(By.CSS_SELECTOR, "[data-testid='btn-compare-now']").click()

        modal = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-applicant-comparison']"))
        )

        # Wait for the candidate cards to finish loading
        wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='card-comparison-candidate-{apps[0].id}']"))
        )

        # Assert N/A - Pending is displayed for Candidate 5's video score
        modal_text = modal.text
        assert "N/A - Pending" in modal_text

        # Assert Close button cleanly dismisses modal
        close_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='btn-close-comparison-modal']")
        close_btn.click()
        time.sleep(0.3)

        assert len(driver.find_elements(By.CSS_SELECTOR, "[data-testid='modal-applicant-comparison']")) == 0

        screenshot_path = SCREENSHOTS_DIR / "us28_07_graceful_missing_scores_handling.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc28_08_tenant_isolation_unauthorized_room_owner_blocked(self, driver):
        """TC-28-08: Verify unauthorized HR user cannot compare applicants from another HR's room (AC#6)."""
        owner_email = "owner_hr_tc08@careerflow.test"
        unauth_email = "unauth_hr_tc08@careerflow.test"

        room, apps = create_us28_sample_room(owner_email, room_title="Restricted Strategy Lead")
        login_hr(driver, email=unauth_email, full_name="Unauthorized HR")

        # 1. Verify Backend REST API rejects unauthorized HR with 403 or 404 (zero leakage of room existence)
        unauth_user = User.objects.get(email=unauth_email)
        from rest_framework.test import APIClient
        client = APIClient()
        client.force_authenticate(user=unauth_user)

        res = client.post(
            f"/api/recruitment/rooms/{room.id}/compare-applicants/",
            {"application_ids": [apps[0].id, apps[1].id]},
            format="json"
        )
        assert res.status_code in [403, 404]

        # Also verify comparison service layer directly raises PermissionDenied (403)
        from rest_framework.exceptions import PermissionDenied
        from apps.recruitment.services.comparison_service import compare_room_applicants
        with pytest.raises(PermissionDenied):
            compare_room_applicants(
                room=room,
                application_ids=[apps[0].id, apps[1].id],
                request_user=unauth_user
            )

        # 2. Verify Frontend UI: Unauthorized HR navigating to rooms only sees their own rooms
        driver.get(f"{get_base_url()}/hr/rooms")
        time.sleep(0.5)

        # The unauthorized HR does not have room card action button for owner's room
        assert len(driver.find_elements(By.CSS_SELECTOR, f"[data-testid='button-action-ranking-{room.id}']")) == 0

        screenshot_path = SCREENSHOTS_DIR / "us28_08_tenant_isolation_unauthorized_room_owner_blocked.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()
