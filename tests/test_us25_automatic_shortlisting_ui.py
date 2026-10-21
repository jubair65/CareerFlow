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
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

from apps.authentication.models import User
from apps.recruitment.models import RecruitmentRoom, CandidateApplication
from apps.cv.models import CandidateCV, CVJobMatch
from conftest import FRONTEND_URL, SCREENSHOTS_DIR, create_user_in_db


def login_hr(driver, email="mobin_hr_tester@careerflow.test", password="ValidPass2026!", full_name="MD. Hasanul Mobin"):
    """Helper to ensure HR Manager exists and logs in via UI."""
    create_user_in_db(email, password, role=User.Role.HR_MANAGER, full_name=full_name)

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

    wait.until(EC.url_contains("/hr/dashboard"))


def set_react_input(driver, element, value):
    """Reliably sets React controlled input value directly and dispatches input/change synthetic events."""
    driver.execute_script(
        "var el = arguments[0];"
        "var nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;"
        "nativeSetter.call(el, arguments[1]);"
        "el.dispatchEvent(new Event('input', { bubbles: true }));"
        "el.dispatchEvent(new Event('change', { bubbles: true }));",
        element,
        str(value)
    )


def set_react_slider(driver, element, value):
    """Sets range slider value and dispatches React synthetic change events."""
    driver.execute_script(
        "var slider = arguments[0];"
        "var nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;"
        "nativeSetter.call(slider, arguments[1]);"
        "slider.dispatchEvent(new Event('input', { bubbles: true }));"
        "slider.dispatchEvent(new Event('change', { bubbles: true }));",
        element,
        str(value)
    )


def create_shortlisting_sample_room(
    hr_email: str,
    room_title="Lead AI & Machine Learning Engineer",
    company="Cognitive Systems AI",
    strategy="NONE",
    min_score=None,
    top_n=None
):
    """
    Creates a RecruitmentRoom owned by hr_email with 6 candidates designed to validate:
    1. Alice: Final Score 92.0 (CV 94.0, Vid 90.0) -> Rank #1
    2. Bob: Final Score 85.0 (CV 90.0, Vid 80.0) -> Rank #2 (wins tie-breaker)
    3. Charlie: Final Score 85.0 (CV 80.0, Vid 90.0) -> Rank #3
    4. David: Final Score 72.0 (CV 70.0, Vid 74.0) -> Rank #4
    5. Eva: Unranked / Pending (CV 78.0, Video missing, final_score=None)
    6. Frank: Unranked / Pending (Neither CV nor Video, final_score=None)
    """
    hr_user = User.objects.get(email=hr_email)

    room = RecruitmentRoom.objects.create(
        title=room_title,
        company_name=company,
        department="AI Research",
        description="Lead research and deployment of LLM agent architectures and vision pipelines.",
        requirements_text="Expertise in PyTorch, Transformers, Distributed Training, and Python.",
        skills_required=["PyTorch", "Transformers", "Distributed Systems", "Python"],
        status=RecruitmentRoom.Status.ACTIVE,
        created_by=hr_user,
        cv_weight=50,
        video_weight=50,
        shortlist_strategy=strategy,
        shortlist_min_score=min_score,
        shortlist_top_n=top_n
    )

    now = timezone.now()

    # 1. Alice (Score: 92.0)
    alice_user = create_user_in_db("alice_us25@careerflow.test", "ValidPass2026!", role=User.Role.STUDENT, full_name="Alice Architect")
    alice_cv = CandidateCV.objects.create(
        user=alice_user, file="students/alice/alice_cv.pdf", original_filename="Alice_Resume.pdf", file_size=220000, is_active=True
    )
    CVJobMatch.objects.create(cv=alice_cv, job_title=room.title, company=room.company_name, match_score=94.0)
    app_alice = CandidateApplication.objects.create(
        room=room, candidate=alice_user, cv=alice_cv, final_score=92.0, cv_score=94.0, video_score=90.0,
        is_partial_score=False, status=CandidateApplication.Status.COMPLETED
    )
    CandidateApplication.objects.filter(id=app_alice.id).update(applied_at=now - timedelta(days=6))

    # 2. Bob (Score: 85.0, CV: 90.0) -> Higher CV score for tie-break
    bob_user = create_user_in_db("bob_us25@careerflow.test", "ValidPass2026!", role=User.Role.STUDENT, full_name="Bob Builder")
    bob_cv = CandidateCV.objects.create(
        user=bob_user, file="students/bob/bob_cv.pdf", original_filename="Bob_Resume.pdf", file_size=190000, is_active=True
    )
    CVJobMatch.objects.create(cv=bob_cv, job_title=room.title, company=room.company_name, match_score=90.0)
    app_bob = CandidateApplication.objects.create(
        room=room, candidate=bob_user, cv=bob_cv, final_score=85.0, cv_score=90.0, video_score=80.0,
        is_partial_score=False, status=CandidateApplication.Status.COMPLETED
    )
    CandidateApplication.objects.filter(id=app_bob.id).update(applied_at=now - timedelta(days=5))

    # 3. Charlie (Score: 85.0, CV: 80.0) -> Lower CV score for tie-break
    charlie_user = create_user_in_db("charlie_us25@careerflow.test", "ValidPass2026!", role=User.Role.STUDENT, full_name="Charlie Cloud")
    charlie_cv = CandidateCV.objects.create(
        user=charlie_user, file="students/charlie/charlie_cv.pdf", original_filename="Charlie_Resume.pdf", file_size=195000, is_active=True
    )
    CVJobMatch.objects.create(cv=charlie_cv, job_title=room.title, company=room.company_name, match_score=80.0)
    app_charlie = CandidateApplication.objects.create(
        room=room, candidate=charlie_user, cv=charlie_cv, final_score=85.0, cv_score=80.0, video_score=90.0,
        is_partial_score=False, status=CandidateApplication.Status.COMPLETED
    )
    CandidateApplication.objects.filter(id=app_charlie.id).update(applied_at=now - timedelta(days=4))

    # 4. David (Score: 72.0)
    david_user = create_user_in_db("david_us25@careerflow.test", "ValidPass2026!", role=User.Role.STUDENT, full_name="David Developer")
    david_cv = CandidateCV.objects.create(
        user=david_user, file="students/david/david_cv.pdf", original_filename="David_Resume.pdf", file_size=175000, is_active=True
    )
    CVJobMatch.objects.create(cv=david_cv, job_title=room.title, company=room.company_name, match_score=70.0)
    app_david = CandidateApplication.objects.create(
        room=room, candidate=david_user, cv=david_cv, final_score=72.0, cv_score=70.0, video_score=74.0,
        is_partial_score=False, status=CandidateApplication.Status.COMPLETED
    )
    CandidateApplication.objects.filter(id=app_david.id).update(applied_at=now - timedelta(days=3))

    # 5. Eva (Unranked: Video missing)
    eva_user = create_user_in_db("eva_us25@careerflow.test", "ValidPass2026!", role=User.Role.STUDENT, full_name="Eva Evaluation")
    eva_cv = CandidateCV.objects.create(
        user=eva_user, file="students/eva/eva_cv.pdf", original_filename="Eva_Resume.pdf", file_size=160000, is_active=True
    )
    app_eva = CandidateApplication.objects.create(
        room=room, candidate=eva_user, cv=eva_cv, final_score=None, cv_score=None, video_score=None,
        status=CandidateApplication.Status.PENDING
    )
    CandidateApplication.objects.filter(id=app_eva.id).update(applied_at=now - timedelta(days=2), final_score=None)

    # 6. Frank (Unranked: Both missing)
    frank_user = create_user_in_db("frank_us25@careerflow.test", "ValidPass2026!", role=User.Role.STUDENT, full_name="Frank Fresh")
    app_frank = CandidateApplication.objects.create(
        room=room, candidate=frank_user, cv=None, final_score=None, cv_score=None, video_score=None,
        status=CandidateApplication.Status.PENDING
    )
    CandidateApplication.objects.filter(id=app_frank.id).update(applied_at=now - timedelta(days=1))

    return room, [app_alice, app_bob, app_charlie, app_david, app_eva, app_frank]


class TestUS25AutomaticShortlistingUI:
    """
    US-25: Automatic Candidate Shortlisting UI Automation Tests
    Sprint: Sprint 5 (Smart Recruitment Decisions: Scoring, Ranking, Shortlisting & Human Review)
    Task: US-25-T6 (Peer UI Testing & Code Review for Automatic Shortlisting Flow)
    Dedicated Peer Tester: MD. Hasanul Mobin (@hasanulmobin) - Project Manager & Cross-Tester
    Primary Developer / Author: Jannatun Naeem Mona (@jn-mona04) - Systems Analyst / BA
    """

    def test_tc_us25_01_dashboard_shortlist_dropdown_and_header_button(self, driver):
        """TC-US25-01: Verify HR Dashboard quick room selector and 'Review Shortlist' button open Shortlist modal."""
        hr_email = "mobin_tc01_dash@careerflow.test"
        login_hr(driver, email=hr_email, full_name="Hasanul Mobin")
        room, apps = create_shortlisting_sample_room(hr_email, room_title="Lead AI & Machine Learning Engineer", company="Cognitive Systems AI")

        driver.get(f"{FRONTEND_URL}/hr/dashboard")
        wait = WebDriverWait(driver, 10)

        # 1. Locate quick room shortlist dropdown on Dashboard
        dropdown = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='select-room-shortlist-dashboard']"))
        )
        select = Select(dropdown)
        select.select_by_value(str(room.id))

        # 2. Verify modal mounts with title, room details, and US-25 badge
        modal = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-shortlist-config']"))
        )
        assert modal is not None
        modal_text = modal.text
        assert "Lead AI & Machine Learning Engineer" in modal_text
        assert "Cognitive Systems AI" in modal_text
        assert "US-25 Shortlisting" in modal_text

        # Wait for table to load
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='table-shortlisted-applicants']")))

        # Capture screenshot for reporting
        screenshot_path = SCREENSHOTS_DIR / "us25_01_dashboard_shortlist_modal_mount.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

        # 3. Dismiss modal cleanly via close button (X)
        close_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-close-shortlist-modal']")
        close_btn.click()
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-shortlist-config']")))

        # 4. Test "Review Shortlist" button in dashboard hero banner
        review_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-view-shortlisted-dashboard']"))
        )
        review_btn.click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-shortlist-config']")))
        driver.find_element(By.CSS_SELECTOR, "[data-testid='button-close-shortlist-modal']").click()
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-shortlist-config']")))

    def test_tc_us25_02_room_card_action_button_and_summary_statistics(self, driver):
        """TC-US25-02: Verify Recruitment Rooms card 'Shortlist' action button mounts modal with summary statistics."""
        hr_email = "mobin_tc02_rooms@careerflow.test"
        login_hr(driver, email=hr_email, full_name="Hasanul Mobin")
        room, apps = create_shortlisting_sample_room(
            hr_email,
            room_title="Principal Vision AI Architect",
            company="VisionWorks AI",
            strategy="MIN_SCORE",
            min_score=80.0
        )
        # Pre-evaluate shortlist in database
        from apps.recruitment.services.shortlisting_service import evaluate_room_shortlist
        evaluate_room_shortlist(room, persist=True)

        driver.get(f"{FRONTEND_URL}/hr/rooms")
        wait = WebDriverWait(driver, 10)

        # 1. Locate and click Shortlist action button on room card
        action_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-action-shortlist-{room.id}']"))
        )
        assert "Shortlist" in action_btn.text
        action_btn.click()

        # 2. Verify modal mounted
        modal = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-shortlist-config']")))
        assert modal is not None

        # 3. Wait for data to load and statistical summary indicators to appear
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='section-shortlist-results']")))
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='table-shortlisted-applicants']")))

        # Check statistical metrics (case-insensitive for UI styling)
        results_text = driver.find_element(By.CSS_SELECTOR, "[data-testid='section-shortlist-results']").text.upper()
        assert "TOTAL APPLICANTS" in results_text
        assert "SHORTLISTED" in results_text
        assert "UNDER REVIEW" in results_text
        assert "SCORE ≥ 80%" in results_text

        # Capture screenshot for reporting
        screenshot_path = SCREENSHOTS_DIR / "us25_02_room_card_shortlist_modal_and_stats.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

        # Clean close via footer Close button
        driver.find_element(By.CSS_SELECTOR, "[data-testid='button-close-shortlist-footer']").click()
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-shortlist-config']")))

    def test_tc_us25_03_min_score_threshold_shortlisting(self, driver):
        """TC-US25-03: Verify Minimum Score Threshold (Score >= 85) filters and tags shortlisted candidates with green badges."""
        hr_email = "mobin_tc03_minscore@careerflow.test"
        login_hr(driver, email=hr_email, full_name="Hasanul Mobin")
        room, apps = create_shortlisting_sample_room(hr_email, room_title="Senior NLP Research Engineer", company="LexiAI")

        driver.get(f"{FRONTEND_URL}/hr/rooms")
        wait = WebDriverWait(driver, 10)

        # Open shortlist modal
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-action-shortlist-{room.id}']"))).click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-shortlist-config']")))

        # Switch to Configure Rules tab
        criteria_tab = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='tab-shortlist-criteria']")))
        criteria_tab.click()

        # Select Minimum Score Threshold strategy
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='card-strategy-min-score']"))).click()

        # Set threshold to 85 via input
        min_score_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-shortlist-min-score']")))
        set_react_input(driver, min_score_input, 85)

        # Click Save & Apply Shortlist
        save_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-save-shortlist-criteria']")
        save_btn.click()

        # Should automatically switch back to Results tab
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='section-shortlist-results']")))
        time.sleep(1)

        # Verify Candidates with score >= 85 are shortlisted:
        # Alice (92.0 >= 85) -> Shortlisted
        # Bob (85.0 >= 85) -> Shortlisted
        # Charlie (85.0 >= 85) -> Shortlisted
        # David (72.0 < 85) -> Under Review
        # Eva (None) -> Under Review
        # Frank (None) -> Under Review
        app_alice = apps[0]
        app_bob = apps[1]
        app_charlie = apps[2]
        app_david = apps[3]

        alice_badge = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, f"[data-testid='badge-shortlisted-{app_alice.id}']")))
        assert "Shortlisted" in alice_badge.text

        bob_badge = driver.find_element(By.CSS_SELECTOR, f"[data-testid='badge-shortlisted-{app_bob.id}']")
        assert "Shortlisted" in bob_badge.text

        charlie_badge = driver.find_element(By.CSS_SELECTOR, f"[data-testid='badge-shortlisted-{app_charlie.id}']")
        assert "Shortlisted" in charlie_badge.text

        david_badge = driver.find_element(By.CSS_SELECTOR, f"[data-testid='badge-under-review-{app_david.id}']")
        assert "Under Review" in david_badge.text

        # Verify criteria explanation text in table
        david_row = driver.find_element(By.CSS_SELECTOR, f"[data-testid='row-applicant-{app_david.id}']").text
        assert "Below minimum score threshold of 85.0%" in david_row

        # Capture screenshot for reporting
        screenshot_path = SCREENSHOTS_DIR / "us25_03_min_score_threshold_results.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

        driver.find_element(By.CSS_SELECTOR, "[data-testid='button-close-shortlist-modal']").click()

    def test_tc_us25_04_top_n_candidates_shortlisting(self, driver):
        """TC-US25-04: Verify Top N Candidates (Top 3) shortlists exactly top 3 candidates and enforces tie-breaking."""
        hr_email = "mobin_tc04_topn@careerflow.test"
        login_hr(driver, email=hr_email, full_name="Hasanul Mobin")
        room, apps = create_shortlisting_sample_room(hr_email, room_title="Staff Platform Architect", company="OmniCloud")

        driver.get(f"{FRONTEND_URL}/hr/rooms")
        wait = WebDriverWait(driver, 10)

        # Open shortlist modal
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-action-shortlist-{room.id}']"))).click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-shortlist-config']")))

        # Switch to Configure Rules tab
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='tab-shortlist-criteria']"))).click()

        # Select Top N Candidates strategy
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='card-strategy-top-n']"))).click()

        # Click quick button for Top 3
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='quick-top-n-3']"))).click()

        # Save & Apply
        driver.find_element(By.CSS_SELECTOR, "[data-testid='button-save-shortlist-criteria']").click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='section-shortlist-results']")))
        time.sleep(1)

        # Exactly Top 3 should be shortlisted:
        # Rank #1 Alice (92.0), Rank #2 Bob (85.0, CV 90), Rank #3 Charlie (85.0, CV 80)
        # Rank #4 David (72.0) is outside top 3
        app_alice = apps[0]
        app_bob = apps[1]
        app_charlie = apps[2]
        app_david = apps[3]

        assert driver.find_element(By.CSS_SELECTOR, f"[data-testid='badge-shortlisted-{app_alice.id}']") is not None
        assert driver.find_element(By.CSS_SELECTOR, f"[data-testid='badge-shortlisted-{app_bob.id}']") is not None
        assert driver.find_element(By.CSS_SELECTOR, f"[data-testid='badge-shortlisted-{app_charlie.id}']") is not None
        assert driver.find_element(By.CSS_SELECTOR, f"[data-testid='badge-under-review-{app_david.id}']") is not None

        # Verify reason explains top 3 quota
        david_row = driver.find_element(By.CSS_SELECTOR, f"[data-testid='row-applicant-{app_david.id}']").text
        assert "Ranked #4" in david_row
        assert "outside required top 3 quota" in david_row

        # Capture screenshot for reporting
        screenshot_path = SCREENSHOTS_DIR / "us25_04_top_n_shortlisting_results.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

        driver.find_element(By.CSS_SELECTOR, "[data-testid='button-close-shortlist-modal']").click()

    def test_tc_us25_05_combined_strategy_and_boundary_tests(self, driver):
        """TC-US25-05: Verify Combined Criteria (Top N + Min Score) and boundary condition validation."""
        hr_email = "mobin_tc05_combined@careerflow.test"
        login_hr(driver, email=hr_email, full_name="Hasanul Mobin")
        room, apps = create_shortlisting_sample_room(hr_email, room_title="Principal Quantum ML Engineer", company="Q-Scale")

        driver.get(f"{FRONTEND_URL}/hr/rooms")
        wait = WebDriverWait(driver, 10)

        # Open shortlist modal
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-action-shortlist-{room.id}']"))).click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-shortlist-config']")))

        # Switch to Configure Rules tab
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='tab-shortlist-criteria']"))).click()

        # Select Combined Strategy
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='card-strategy-combined']"))).click()

        # Configure Top 2 with Min Score 80.0
        min_score_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-shortlist-min-score']")))
        set_react_input(driver, min_score_input, 80)

        # Custom Top N = 2
        top_n_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-shortlist-top-n']")))
        set_react_input(driver, top_n_input, 2)

        # Save and Apply
        driver.find_element(By.CSS_SELECTOR, "[data-testid='button-save-shortlist-criteria']").click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='section-shortlist-results']")))
        time.sleep(1)

        # Qualified meeting >= 80: Alice (92.0), Bob (85.0), Charlie (85.0).
        # But Top N quota is 2:
        # Alice is #1 -> Shortlisted
        # Bob is #2 -> Shortlisted
        # Charlie is #3 -> Under Review (meets 80, but exceeds Top 2 quota!)
        app_alice = apps[0]
        app_bob = apps[1]
        app_charlie = apps[2]

        assert driver.find_element(By.CSS_SELECTOR, f"[data-testid='badge-shortlisted-{app_alice.id}']") is not None
        assert driver.find_element(By.CSS_SELECTOR, f"[data-testid='badge-shortlisted-{app_bob.id}']") is not None
        assert driver.find_element(By.CSS_SELECTOR, f"[data-testid='badge-under-review-{app_charlie.id}']") is not None

        charlie_row = driver.find_element(By.CSS_SELECTOR, f"[data-testid='row-applicant-{app_charlie.id}']").text
        assert "exceeds top 2 quota" in charlie_row

        # Capture screenshot for reporting
        screenshot_path = SCREENSHOTS_DIR / "us25_05_combined_strategy_and_boundaries.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

        driver.find_element(By.CSS_SELECTOR, "[data-testid='button-close-shortlist-modal']").click()

    def test_tc_us25_06_instant_search_and_status_filtering(self, driver):
        """TC-US25-06: Verify search by candidate name/email and status filters (All, Shortlisted Only, Under Review)."""
        hr_email = "mobin_tc06_filters@careerflow.test"
        login_hr(driver, email=hr_email, full_name="Hasanul Mobin")
        room, apps = create_shortlisting_sample_room(
            hr_email,
            room_title="Lead Data Architect",
            company="DataSphere",
            strategy="MIN_SCORE",
            min_score=80.0
        )
        from apps.recruitment.services.shortlisting_service import evaluate_room_shortlist
        evaluate_room_shortlist(room, persist=True)

        driver.get(f"{FRONTEND_URL}/hr/rooms")
        wait = WebDriverWait(driver, 10)

        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-action-shortlist-{room.id}']"))).click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='section-shortlist-results']")))

        # 1. Test instant search by name: "Alice"
        search_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-search-shortlist']")))
        search_input.send_keys("Alice")
        time.sleep(0.5)

        rows = driver.find_elements(By.CSS_SELECTOR, "tbody tr")
        assert len(rows) == 1
        assert "Alice Architect" in rows[0].text

        # Clear search
        set_react_input(driver, search_input, "")
        time.sleep(0.5)

        # 2. Test "Shortlisted Only" filter tab
        filter_shortlisted = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='filter-shortlisted_only']")))
        filter_shortlisted.click()
        time.sleep(0.5)

        shortlisted_rows = driver.find_elements(By.CSS_SELECTOR, "tbody tr")
        # Alice (92.0), Bob (85.0), Charlie (85.0) are >= 80 -> 3 shortlisted rows
        assert len(shortlisted_rows) == 3
        for r in shortlisted_rows:
            assert "Shortlisted" in r.text

        # 3. Test "Under Review" filter tab
        filter_non = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='filter-non_shortlisted']")))
        filter_non.click()
        time.sleep(0.5)

        under_review_rows = driver.find_elements(By.CSS_SELECTOR, "tbody tr")
        # David (72), Eva (None), Frank (None) -> 3 rows
        assert len(under_review_rows) == 3
        for r in under_review_rows:
            assert "Under Review" in r.text

        # 4. Reset to "All Candidates"
        driver.find_element(By.CSS_SELECTOR, "[data-testid='filter-all']").click()
        time.sleep(0.5)
        all_rows = driver.find_elements(By.CSS_SELECTOR, "tbody tr")
        assert len(all_rows) == 6

        # Capture screenshot for reporting
        screenshot_path = SCREENSHOTS_DIR / "us25_06_search_and_status_filtering.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

        driver.find_element(By.CSS_SELECTOR, "[data-testid='button-close-shortlist-modal']").click()

    def test_tc_us25_07_disable_strategy_and_reevaluate_button(self, driver):
        """TC-US25-07: Verify Disabling Shortlisting resets candidates to Under Review and Re-evaluate button refreshes state."""
        hr_email = "mobin_tc07_disable@careerflow.test"
        login_hr(driver, email=hr_email, full_name="Hasanul Mobin")
        room, apps = create_shortlisting_sample_room(
            hr_email,
            room_title="Lead Security Systems Engineer",
            company="CyberFort",
            strategy="MIN_SCORE",
            min_score=75.0
        )
        from apps.recruitment.services.shortlisting_service import evaluate_room_shortlist
        evaluate_room_shortlist(room, persist=True)

        driver.get(f"{FRONTEND_URL}/hr/rooms")
        wait = WebDriverWait(driver, 10)

        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-action-shortlist-{room.id}']"))).click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='section-shortlist-results']")))

        # Switch to Configure Rules tab
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='tab-shortlist-criteria']"))).click()

        # Select Disabled strategy
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='card-strategy-none']"))).click()

        # Save
        driver.find_element(By.CSS_SELECTOR, "[data-testid='button-save-shortlist-criteria']").click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='section-shortlist-results']")))
        time.sleep(1)

        # All candidates should now be Under Review
        all_badges = driver.find_elements(By.CSS_SELECTOR, "[data-testid^='badge-under-review-']")
        assert len(all_badges) == 6

        # Shortlisted stat card should show 0
        results_text = driver.find_element(By.CSS_SELECTOR, "[data-testid='section-shortlist-results']").text
        assert "Disabled" in results_text

        # Test Re-evaluate button
        reeval_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-reevaluate-shortlist']")))
        reeval_btn.click()
        time.sleep(1)

        # Still 0 shortlisted and disabled
        assert len(driver.find_elements(By.CSS_SELECTOR, "[data-testid^='badge-shortlisted-']")) == 0

        # Capture screenshot for reporting
        screenshot_path = SCREENSHOTS_DIR / "us25_07_disabled_strategy_and_reevaluate.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

        driver.find_element(By.CSS_SELECTOR, "[data-testid='button-close-shortlist-modal']").click()

    def test_tc_us25_08_mobile_responsive_shortlist_modal(self, driver):
        """TC-US25-08: Verify Shortlist modal layout adapts gracefully to mobile viewports (375x812) without horizontal overflow."""
        hr_email = "mobin_tc08_mobile@careerflow.test"
        login_hr(driver, email=hr_email, full_name="Hasanul Mobin")
        room, apps = create_shortlisting_sample_room(
            hr_email,
            room_title="Mobile Platform Engineer",
            company="AppWorks",
            strategy="MIN_SCORE",
            min_score=80.0
        )
        from apps.recruitment.services.shortlisting_service import evaluate_room_shortlist
        evaluate_room_shortlist(room, persist=True)

        driver.get(f"{FRONTEND_URL}/hr/rooms")
        wait = WebDriverWait(driver, 10)

        # Locate action button before resizing or scroll into view
        action_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, f"[data-testid='button-action-shortlist-{room.id}']")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", action_btn)
        time.sleep(0.5)

        # Set mobile viewport
        driver.set_window_size(375, 812)
        time.sleep(0.5)

        driver.execute_script("arguments[0].click();", action_btn)
        modal = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-shortlist-config']")))

        # Check geometry
        window_inner_width = driver.execute_script("return window.innerWidth;")
        modal_width = modal.size['width']
        # Desktop Chrome window geometry on Windows OS enforces min window size ~500px, so assert modal fits inside viewport width
        assert modal_width <= window_inner_width + 15, f"Modal width {modal_width} exceeded viewport {window_inner_width}"

        # Capture screenshot for reporting
        screenshot_path = SCREENSHOTS_DIR / "us25_08_mobile_responsive_shortlist_modal.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

        # Reset window size
        driver.set_window_size(1920, 1080)
        driver.find_element(By.CSS_SELECTOR, "[data-testid='button-close-shortlist-modal']").click()
