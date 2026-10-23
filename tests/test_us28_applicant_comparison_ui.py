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
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

from apps.authentication.models import User
from apps.recruitment.models import RecruitmentRoom, CandidateApplication
from apps.cv.models import CandidateCV, CVJobMatch
from apps.presentation.models import PresentationVideo, PresentationScore, SpeechAnalysis, BehavioralAnalysis
from conftest import FRONTEND_URL, SCREENSHOTS_DIR, create_user_in_db


def get_base_url():
    """Ensure reliable localhost URL."""
    return os.environ.get("FRONTEND_URL", "http://127.0.0.1:5173")


def login_hr(driver, email="jubair_tester_us28@careerflow.test", password="ValidPass2026!", full_name="MD. Jubair Bin Hasan"):
    """Helper to authenticate as HR Manager via UI."""
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


def create_us28_sample_room(hr_email: str, room_title="Lead Backend Architect", company="Nexus Innovations"):
    """
    Creates a RecruitmentRoom owned by hr_email with 5 candidate applications:
    1. Alice: Complete (Final 88.0, CV 90.0, Video 85.0, Eye 92%, WPM 140, Shortlisted)
    2. Bob: Complete (Final 86.0, CV 80.0, Video 95.0, Eye 88%, WPM 150, Shortlisted)
    3. Charlie: Complete (Final 83.0, CV 85.0, Video 80.0, Eye 85%, WPM 145, Pending Review)
    4. David: Complete (Final 72.0, CV 70.0, Video 75.0, Eye 70%, WPM 120, Pending Review)
    5. Eva: Incomplete (Final None, CV 75.0, Video None, Pending)
    """
    hr_user = User.objects.get(email=hr_email)

    room = RecruitmentRoom.objects.create(
        title=room_title,
        company_name=company,
        department="Engineering",
        description="Senior architecture role for high-throughput distributed systems.",
        requirements_text="Proficiency in Python, Django, PostgreSQL, Docker, AWS.",
        skills_required=["Python", "Django", "PostgreSQL", "Docker", "AWS"],
        status=RecruitmentRoom.Status.ACTIVE,
        created_by=hr_user,
        cv_weight=60,
        video_weight=40,
        shortlist_strategy=RecruitmentRoom.ShortlistStrategy.MIN_SCORE,
        shortlist_min_score=85.0
    )

    now = timezone.now()

    # 1. Alice
    alice_user = create_user_in_db(f"alice_us28_{room.id}@careerflow.test", "ValidPass2026!", role=User.Role.STUDENT, full_name="Alice Smith")
    alice_cv = CandidateCV.objects.create(user=alice_user, file="students/alice/cv.pdf", original_filename="Alice_CV.pdf", file_size=102400, is_active=True)
    CVJobMatch.objects.create(cv=alice_cv, job_title=room.title, company=room.company_name, match_score=90.0, skills_matched=["Python", "Django", "PostgreSQL", "Docker"], skills_missing=["AWS"])
    alice_vid = PresentationVideo.objects.create(user=alice_user, file="students/alice/vid.mp4", original_filename="Alice_Video.mp4", raw_file_size=500000, file_type="mp4", status="COMPLETED")
    PresentationScore.objects.create(video=alice_vid, overall_score=85, speech_score=86, behavioral_score=84, eye_contact_score=92, posture_score=88)
    SpeechAnalysis.objects.create(video=alice_vid, words_per_minute=140.0, filler_word_count=2)
    BehavioralAnalysis.objects.create(video=alice_vid, eye_contact_score=92, posture_score=88)
    app_alice = CandidateApplication.objects.create(room=room, candidate=alice_user, cv=alice_cv, video=alice_vid, final_score=88.0, cv_score=90.0, video_score=85.0, is_shortlisted=True, status=CandidateApplication.Status.COMPLETED)
    CandidateApplication.objects.filter(id=app_alice.id).update(applied_at=now - timedelta(days=5))

    # 2. Bob
    bob_user = create_user_in_db(f"bob_us28_{room.id}@careerflow.test", "ValidPass2026!", role=User.Role.STUDENT, full_name="Bob Jones")
    bob_cv = CandidateCV.objects.create(user=bob_user, file="students/bob/cv.pdf", original_filename="Bob_CV.pdf", file_size=102400, is_active=True)
    CVJobMatch.objects.create(cv=bob_cv, job_title=room.title, company=room.company_name, match_score=80.0, skills_matched=["Python", "Django", "AWS"], skills_missing=["PostgreSQL", "Docker"])
    bob_vid = PresentationVideo.objects.create(user=bob_user, file="students/bob/vid.mp4", original_filename="Bob_Video.mp4", raw_file_size=500000, file_type="mp4", status="COMPLETED")
    PresentationScore.objects.create(video=bob_vid, overall_score=95, speech_score=94, behavioral_score=96, eye_contact_score=88, posture_score=90)
    SpeechAnalysis.objects.create(video=bob_vid, words_per_minute=150.0, filler_word_count=1)
    BehavioralAnalysis.objects.create(video=bob_vid, eye_contact_score=88, posture_score=90)
    app_bob = CandidateApplication.objects.create(room=room, candidate=bob_user, cv=bob_cv, video=bob_vid, final_score=86.0, cv_score=80.0, video_score=95.0, is_shortlisted=True, status=CandidateApplication.Status.COMPLETED)
    CandidateApplication.objects.filter(id=app_bob.id).update(applied_at=now - timedelta(days=4))

    # 3. Charlie
    charlie_user = create_user_in_db(f"charlie_us28_{room.id}@careerflow.test", "ValidPass2026!", role=User.Role.STUDENT, full_name="Charlie Brown")
    charlie_cv = CandidateCV.objects.create(user=charlie_user, file="students/charlie/cv.pdf", original_filename="Charlie_CV.pdf", file_size=102400, is_active=True)
    CVJobMatch.objects.create(cv=charlie_cv, job_title=room.title, company=room.company_name, match_score=85.0, skills_matched=["Python", "Docker", "AWS"], skills_missing=["Django", "PostgreSQL"])
    charlie_vid = PresentationVideo.objects.create(user=charlie_user, file="students/charlie/vid.mp4", original_filename="Charlie_Video.mp4", raw_file_size=500000, file_type="mp4", status="COMPLETED")
    PresentationScore.objects.create(video=charlie_vid, overall_score=80, speech_score=80, behavioral_score=80, eye_contact_score=85, posture_score=82)
    SpeechAnalysis.objects.create(video=charlie_vid, words_per_minute=145.0, filler_word_count=3)
    BehavioralAnalysis.objects.create(video=charlie_vid, eye_contact_score=85, posture_score=82)
    app_charlie = CandidateApplication.objects.create(room=room, candidate=charlie_user, cv=charlie_cv, video=charlie_vid, final_score=83.0, cv_score=85.0, video_score=80.0, is_shortlisted=False, status=CandidateApplication.Status.COMPLETED)
    CandidateApplication.objects.filter(id=app_charlie.id).update(applied_at=now - timedelta(days=3))

    # 4. David
    david_user = create_user_in_db(f"david_us28_{room.id}@careerflow.test", "ValidPass2026!", role=User.Role.STUDENT, full_name="David Miller")
    david_cv = CandidateCV.objects.create(user=david_user, file="students/david/cv.pdf", original_filename="David_CV.pdf", file_size=102400, is_active=True)
    CVJobMatch.objects.create(cv=david_cv, job_title=room.title, company=room.company_name, match_score=70.0, skills_matched=["Python"], skills_missing=["Django", "PostgreSQL", "Docker", "AWS"])
    david_vid = PresentationVideo.objects.create(user=david_user, file="students/david/vid.mp4", original_filename="David_Video.mp4", raw_file_size=500000, file_type="mp4", status="COMPLETED")
    PresentationScore.objects.create(video=david_vid, overall_score=75, speech_score=74, behavioral_score=76, eye_contact_score=70, posture_score=75)
    SpeechAnalysis.objects.create(video=david_vid, words_per_minute=120.0, filler_word_count=5)
    BehavioralAnalysis.objects.create(video=david_vid, eye_contact_score=70, posture_score=75)
    app_david = CandidateApplication.objects.create(room=room, candidate=david_user, cv=david_cv, video=david_vid, final_score=72.0, cv_score=70.0, video_score=75.0, is_shortlisted=False, status=CandidateApplication.Status.COMPLETED)
    CandidateApplication.objects.filter(id=app_david.id).update(applied_at=now - timedelta(days=2))

    # 5. Eva (Incomplete: Missing video)
    eva_user = create_user_in_db(f"eva_us28_{room.id}@careerflow.test", "ValidPass2026!", role=User.Role.STUDENT, full_name="Eva Green")
    eva_cv = CandidateCV.objects.create(user=eva_user, file="students/eva/cv.pdf", original_filename="Eva_CV.pdf", file_size=102400, is_active=True)
    app_eva = CandidateApplication.objects.create(room=room, candidate=eva_user, cv=eva_cv, video=None, final_score=None, cv_score=75.0, video_score=None, is_shortlisted=False, status=CandidateApplication.Status.PENDING)
    CandidateApplication.objects.filter(id=app_eva.id).update(applied_at=now - timedelta(days=1))

    return room, [app_alice, app_bob, app_charlie, app_david, app_eva]


class TestUS28ApplicantComparisonUI:
    """
    US-28: Side-by-Side Applicant Comparison UI Tests (Task US-28-T6)
    Cross-Tester: MD. Jubair Bin Hasan (@jubair65)
    Lead Developer: Nafisa Tabassum Maria (@Maria-07-222)
    """

    def test_tc_us28_01_checkboxes_rendered_for_ranked_applicants(self, driver):
        """TC-US28-01: Verify checkboxes are rendered on each ranked candidate card."""
        hr_email = "jubair_tc01@careerflow.test"
        login_hr(driver, email=hr_email, full_name="MD. Jubair Bin Hasan")
        room, apps = create_us28_sample_room(hr_email, "Lead Backend Architect", "Nexus Innovations")

        driver.get(f"{FRONTEND_URL}/hr/dashboard")
        wait = WebDriverWait(driver, 10)

        # Open Leaderboard Modal via dashboard dropdown
        dropdown = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='select-room-rankings-dashboard']")))
        Select(dropdown).select_by_value(str(room.id))

        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-ranked-applicants']")))

        # Verify checkboxes for ranked candidates
        cb_alice = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, f"[data-testid='checkbox-compare-{apps[0].id}']")))
        cb_bob = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, f"[data-testid='checkbox-compare-{apps[1].id}']")))
        assert cb_alice is not None
        assert cb_bob is not None
        assert not cb_alice.is_selected()

    def test_tc_us28_02_floating_bar_and_selection_count(self, driver):
        """TC-US28-02: Verify sticky floating comparison bar appears when candidates are checked."""
        hr_email = "jubair_tc02@careerflow.test"
        login_hr(driver, email=hr_email, full_name="MD. Jubair Bin Hasan")
        room, apps = create_us28_sample_room(hr_email)

        driver.get(f"{FRONTEND_URL}/hr/dashboard")
        wait = WebDriverWait(driver, 10)
        dropdown = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='select-room-rankings-dashboard']")))
        Select(dropdown).select_by_value(str(room.id))

        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-ranked-applicants']")))

        # Check candidate 1
        cb_1 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='checkbox-compare-{apps[0].id}']")))
        cb_1.click()

        # Floating bar should be visible
        bar = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='bar-applicant-comparison']")))
        assert bar is not None
        assert "1 of 4 candidates selected" in bar.text

        # Compare button should be disabled for 1 candidate (<2 boundary)
        btn_compare = driver.find_element(By.CSS_SELECTOR, "[data-testid='btn-compare-now']")
        assert not btn_compare.is_enabled()

    def test_tc_us28_03_max_four_limit_enforced(self, driver):
        """TC-US28-03: Verify maximum 4 candidates limit is enforced by disabling remaining checkboxes."""
        hr_email = "jubair_tc03@careerflow.test"
        login_hr(driver, email=hr_email, full_name="MD. Jubair Bin Hasan")
        room, apps = create_us28_sample_room(hr_email)

        driver.get(f"{FRONTEND_URL}/hr/dashboard")
        wait = WebDriverWait(driver, 10)
        dropdown = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='select-room-rankings-dashboard']")))
        Select(dropdown).select_by_value(str(room.id))

        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-ranked-applicants']")))

        # Select 4 candidates
        for i in range(4):
            cb = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='checkbox-compare-{apps[i].id}']")))
            cb.click()

        bar = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='bar-applicant-comparison']")))
        assert "4 of 4 candidates selected" in bar.text

        btn_compare = driver.find_element(By.CSS_SELECTOR, "[data-testid='btn-compare-now']")
        assert btn_compare.is_enabled()

    def test_tc_us28_04_clear_selection_button(self, driver):
        """TC-US28-04: Verify Clear button resets all selections and hides floating bar."""
        hr_email = "jubair_tc04@careerflow.test"
        login_hr(driver, email=hr_email, full_name="MD. Jubair Bin Hasan")
        room, apps = create_us28_sample_room(hr_email)

        driver.get(f"{FRONTEND_URL}/hr/dashboard")
        wait = WebDriverWait(driver, 10)
        dropdown = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='select-room-rankings-dashboard']")))
        Select(dropdown).select_by_value(str(room.id))

        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-ranked-applicants']")))

        # Check candidate 1 & 2
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='checkbox-compare-{apps[0].id}']"))).click()
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='checkbox-compare-{apps[1].id}']"))).click()

        # Click Clear button
        btn_clear = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='btn-clear-selection']")))
        btn_clear.click()

        # Verify bar disappears
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='bar-applicant-comparison']")))

    def test_tc_us28_05_side_by_side_modal_layout_and_differentials(self, driver):
        """TC-US28-05: Verify opening comparison modal shows side-by-side columns, scores, and differentials."""
        hr_email = "jubair_tc05@careerflow.test"
        login_hr(driver, email=hr_email, full_name="MD. Jubair Bin Hasan")
        room, apps = create_us28_sample_room(hr_email)

        driver.get(f"{FRONTEND_URL}/hr/dashboard")
        wait = WebDriverWait(driver, 10)
        dropdown = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='select-room-rankings-dashboard']")))
        Select(dropdown).select_by_value(str(room.id))

        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-ranked-applicants']")))

        # Select Alice (88.0) and Bob (86.0)
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='checkbox-compare-{apps[0].id}']"))).click()
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='checkbox-compare-{apps[1].id}']"))).click()

        # Click Compare Now
        btn_compare = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='btn-compare-now']")))
        btn_compare.click()

        # Verify Comparison Modal opens
        comp_modal = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-applicant-comparison']")))
        assert comp_modal is not None

        # Verify candidate cards
        name_alice = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, f"[data-testid='text-candidate-name-{apps[0].id}']"))).text
        name_bob = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, f"[data-testid='text-candidate-name-{apps[1].id}']"))).text
        assert "Alice Smith" in name_alice
        assert "Bob Jones" in name_bob

        # Verify scores and differentials
        score_alice = driver.find_element(By.CSS_SELECTOR, f"[data-testid='score-final-{apps[0].id}']").text
        score_bob = driver.find_element(By.CSS_SELECTOR, f"[data-testid='score-final-{apps[1].id}']").text
        assert "88.0" in score_alice
        assert "86.0" in score_bob

        diff_alice = driver.find_element(By.CSS_SELECTOR, f"[data-testid='diff-final-{apps[0].id}']").text
        diff_bob = driver.find_element(By.CSS_SELECTOR, f"[data-testid='diff-final-{apps[1].id}']").text
        assert "Best" in diff_alice
        assert "-2.0" in diff_bob

        # Verify close modal button
        btn_close = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='btn-close-comparison-modal']")))
        btn_close.click()

        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-applicant-comparison']")))
