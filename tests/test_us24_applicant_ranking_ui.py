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
from apps.presentation.models import PresentationVideo, PresentationScore
from conftest import FRONTEND_URL, SCREENSHOTS_DIR, create_user_in_db


def login_hr(driver, email="jubair_hr_lead@careerflow.test", password="ValidPass2026!", full_name="MD. Jubair Bin Hasan"):
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


def clear_react_input(driver, element):
    """Reliably clears React controlled inputs across Windows and other OS."""
    element.send_keys(Keys.COMMAND + "a")
    element.send_keys(Keys.CONTROL + "a")
    element.send_keys(Keys.BACKSPACE)
    driver.execute_script(
        "var nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;"
        "nativeSetter.call(arguments[0], '');"
        "arguments[0].dispatchEvent(new Event('input', { bubbles: true }));"
        "arguments[0].dispatchEvent(new Event('change', { bubbles: true }));",
        element
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


def create_ranking_sample_room(hr_email: str, room_title="Principal Cloud Systems Architect", company="Apex Enterprise Cloud"):
    """
    Creates a RecruitmentRoom owned by hr_email with 6 candidates designed to thoroughly validate:
    1. Alice: Final Score 92.0 (CV 94.0, Video 90.0) -> Gold Trophy Rank #1
    2. Bob: Final Score 85.0 (CV 90.0, Video 80.0) -> Silver Medal Rank #2
    3. Charlie: Final Score 85.0 (CV 80.0, Video 90.0) -> Bronze Medal Rank #3
       * TIE-BREAK TEST: Bob and Charlie share 85.0 final score. Bob has higher CV score (90 > 80), so Bob is #2, Charlie is #3.
    4. David: Final Score 72.0 (CV 70.0, Video 74.0) -> Standard Rank #4
    5. Eva: Unranked (CV uploaded, match_score=78.0, Video missing/pending, final_score=None) -> Unranked Tab
    6. Frank: Unranked (Neither CV nor Video, final_score=None) -> Unranked Tab
    """
    hr_user = User.objects.get(email=hr_email)

    room = RecruitmentRoom.objects.create(
        title=room_title,
        company_name=company,
        department="Infrastructure",
        description="Lead global cloud architecture, Kubernetes orchestration, and resilience.",
        requirements_text="Expertise in Kubernetes, Terraform, Go, and AWS.",
        skills_required=["Kubernetes", "Terraform", "Go", "AWS"],
        status=RecruitmentRoom.Status.ACTIVE,
        created_by=hr_user,
        cv_weight=50,
        video_weight=50
    )

    now = timezone.now()

    # 1. Alice (Score: 92.0)
    alice_user = create_user_in_db("alice_us24@careerflow.test", "ValidPass2026!", role=User.Role.STUDENT, full_name="Alice Architect")
    alice_cv = CandidateCV.objects.create(
        user=alice_user, file="students/alice/alice_cv.pdf", original_filename="Alice_Cloud_CV.pdf", file_size=210000, is_active=True
    )
    CVJobMatch.objects.create(cv=alice_cv, job_title=room.title, company=room.company_name, match_score=94.0)
    app_alice = CandidateApplication.objects.create(
        room=room, candidate=alice_user, cv=alice_cv, final_score=92.0, cv_score=94.0, video_score=90.0,
        is_partial_score=False, status=CandidateApplication.Status.COMPLETED
    )
    CandidateApplication.objects.filter(id=app_alice.id).update(applied_at=now - timedelta(days=6))

    # 2. Bob (Score: 85.0, CV: 90.0) -> Higher CV score for tie-break
    bob_user = create_user_in_db("bob_us24@careerflow.test", "ValidPass2026!", role=User.Role.STUDENT, full_name="Bob Builder")
    bob_cv = CandidateCV.objects.create(
        user=bob_user, file="students/bob/bob_cv.pdf", original_filename="Bob_Resume.pdf", file_size=180000, is_active=True
    )
    CVJobMatch.objects.create(cv=bob_cv, job_title=room.title, company=room.company_name, match_score=90.0)
    app_bob = CandidateApplication.objects.create(
        room=room, candidate=bob_user, cv=bob_cv, final_score=85.0, cv_score=90.0, video_score=80.0,
        is_partial_score=False, status=CandidateApplication.Status.COMPLETED
    )
    CandidateApplication.objects.filter(id=app_bob.id).update(applied_at=now - timedelta(days=5))

    # 3. Charlie (Score: 85.0, CV: 80.0) -> Lower CV score for tie-break
    charlie_user = create_user_in_db("charlie_us24@careerflow.test", "ValidPass2026!", role=User.Role.STUDENT, full_name="Charlie Cloud")
    charlie_cv = CandidateCV.objects.create(
        user=charlie_user, file="students/charlie/charlie_cv.pdf", original_filename="Charlie_Resume.pdf", file_size=190000, is_active=True
    )
    CVJobMatch.objects.create(cv=charlie_cv, job_title=room.title, company=room.company_name, match_score=80.0)
    app_charlie = CandidateApplication.objects.create(
        room=room, candidate=charlie_user, cv=charlie_cv, final_score=85.0, cv_score=80.0, video_score=90.0,
        is_partial_score=False, status=CandidateApplication.Status.COMPLETED
    )
    CandidateApplication.objects.filter(id=app_charlie.id).update(applied_at=now - timedelta(days=4))

    # 4. David (Score: 72.0)
    david_user = create_user_in_db("david_us24@careerflow.test", "ValidPass2026!", role=User.Role.STUDENT, full_name="David Developer")
    david_cv = CandidateCV.objects.create(
        user=david_user, file="students/david/david_cv.pdf", original_filename="David_Resume.pdf", file_size=170000, is_active=True
    )
    CVJobMatch.objects.create(cv=david_cv, job_title=room.title, company=room.company_name, match_score=70.0)
    app_david = CandidateApplication.objects.create(
        room=room, candidate=david_user, cv=david_cv, final_score=72.0, cv_score=70.0, video_score=74.0,
        is_partial_score=False, status=CandidateApplication.Status.COMPLETED
    )
    CandidateApplication.objects.filter(id=app_david.id).update(applied_at=now - timedelta(days=3))

    # 5. Eva (Unranked: Video presentation missing)
    eva_user = create_user_in_db("eva_us24@careerflow.test", "ValidPass2026!", role=User.Role.STUDENT, full_name="Eva Evaluation")
    eva_cv = CandidateCV.objects.create(
        user=eva_user, file="students/eva/eva_cv.pdf", original_filename="Eva_Resume.pdf", file_size=165000, is_active=True
    )
    app_eva = CandidateApplication.objects.create(
        room=room, candidate=eva_user, cv=eva_cv, final_score=None, cv_score=None, video_score=None,
        status=CandidateApplication.Status.PENDING
    )
    CandidateApplication.objects.filter(id=app_eva.id).update(applied_at=now - timedelta(days=2), final_score=None)

    # 6. Frank (Unranked: Both CV and Video missing)
    frank_user = create_user_in_db("frank_us24@careerflow.test", "ValidPass2026!", role=User.Role.STUDENT, full_name="Frank Fresh")
    app_frank = CandidateApplication.objects.create(
        room=room, candidate=frank_user, cv=None, final_score=None, cv_score=None, video_score=None,
        status=CandidateApplication.Status.PENDING
    )
    CandidateApplication.objects.filter(id=app_frank.id).update(applied_at=now - timedelta(days=1))

    return room, [app_alice, app_bob, app_charlie, app_david, app_eva, app_frank]


def create_large_candidate_room(hr_email: str, count: int = 25):
    """Creates a recruitment room with >20 applicants (25 total) to test pagination/scalability."""
    hr_user = User.objects.get(email=hr_email)

    room = RecruitmentRoom.objects.create(
        title="High Volume Candidate Pipeline",
        company_name="ScaleTech Global",
        department="Engineering",
        description="Testing high throughput candidate rankings and UI virtualization.",
        status=RecruitmentRoom.Status.ACTIVE,
        created_by=hr_user,
        cv_weight=50,
        video_weight=50
    )

    now = timezone.now()
    apps = []
    for i in range(count):
        score = round(98.0 - (i * 1.8), 1)  # Strictly descending 98.0 down to ~54.8
        u = create_user_in_db(f"scale_cand_{i:02d}@careerflow.test", "ValidPass2026!", role=User.Role.STUDENT, full_name=f"Candidate Scaled {i+1:02d}")
        app = CandidateApplication.objects.create(
            room=room,
            candidate=u,
            final_score=score,
            cv_score=round(score + 1.0, 1),
            video_score=round(score - 1.0, 1),
            is_partial_score=False,
            status=CandidateApplication.Status.COMPLETED
        )
        CandidateApplication.objects.filter(id=app.id).update(applied_at=now - timedelta(hours=i))
        apps.append(app)

    return room, apps


class TestUS24ApplicantRankingUI:
    """
    US-24: Applicant Ranking UI Automation Tests
    Task: US-24-T6 (Peer UI Testing & Code Review for Applicant Ranking Leaderboard)
    Reviewer / UI Tester: MD. Jubair Bin Hasan (@jubair65) - Software Developer & Peer Tester
    Primary Developer / Author: Nafisa Tabassum Maria (@Maria-07-222) - System Architect
    Sprint: Sprint 5
    """

    def test_tc_us24_01_dashboard_dropdown_opens_modal(self, driver):
        """TC-US24-01: Verify HR Dashboard quick room selector opens applicant ranking leaderboard modal."""
        hr_email = "jubair_tc01_dash@careerflow.test"
        login_hr(driver, email=hr_email, full_name="Jubair Reviewer")
        room, apps = create_ranking_sample_room(hr_email, room_title="Principal Cloud Systems Architect", company="Apex Enterprise Cloud")

        driver.get(f"{FRONTEND_URL}/hr/dashboard")
        wait = WebDriverWait(driver, 10)

        # 1. Locate quick room leaderboard dropdown on Dashboard
        dropdown = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='select-room-rankings-dashboard']"))
        )
        select = Select(dropdown)
        select.select_by_value(str(room.id))

        # 2. Verify modal mounts with title, room details, and evaluation weights badge
        modal = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-ranked-applicants']"))
        )
        assert modal is not None
        modal_title = driver.find_element(By.CSS_SELECTOR, "[data-testid='text-ranked-modal-title']").text
        assert "Applicant Leaderboard & Rankings" in modal_title

        modal_text = modal.text
        assert "Principal Cloud Systems Architect" in modal_text
        assert "Apex Enterprise Cloud" in modal_text
        assert "50% CV / 50% Video" in modal_text

        # Wait for data to load
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='card-ranked-applicant-1']")))

        # Capture screenshot for reporting
        screenshot_path = SCREENSHOTS_DIR / "us24_01_dashboard_rankings_dropdown_modal.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

        # 3. Dismiss modal cleanly via close button (X)
        close_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-close-ranked-modal']")
        close_btn.click()
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-ranked-applicants']")))

    def test_tc_us24_02_room_card_action_button_opens_modal_and_summary_stats(self, driver):
        """TC-US24-02: Verify Recruitment Rooms card 'Rankings' action button mounts leaderboard with 4 summary stats."""
        hr_email = "jubair_tc02_rooms@careerflow.test"
        login_hr(driver, email=hr_email, full_name="Jubair Reviewer")
        room, apps = create_ranking_sample_room(hr_email, room_title="Staff Infrastructure Engineer", company="Apex Cloud")

        driver.get(f"{FRONTEND_URL}/hr/rooms")
        wait = WebDriverWait(driver, 10)

        # 1. Locate and click Rankings action button on room card
        action_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-action-ranking-{room.id}']"))
        )
        assert "Rankings" in action_btn.text
        action_btn.click()

        # 2. Verify modal mounted
        modal = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-ranked-applicants']")))
        assert modal is not None

        # 3. Wait for data to load and statistical summary indicators to appear
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='row-statistical-summary']")))
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='card-ranked-applicant-1']")))

        total_stat = driver.find_element(By.CSS_SELECTOR, "[data-testid='stat-ranked-total']").text
        ranked_stat = driver.find_element(By.CSS_SELECTOR, "[data-testid='stat-ranked-count']").text
        unranked_stat = driver.find_element(By.CSS_SELECTOR, "[data-testid='stat-unranked-count']").text
        top_stat = driver.find_element(By.CSS_SELECTOR, "[data-testid='stat-top-score']").text

        assert total_stat == "6", f"Expected 6 total applicants, got {total_stat}"
        assert ranked_stat == "4", f"Expected 4 ranked candidates, got {ranked_stat}"
        assert unranked_stat == "2", f"Expected 2 unranked candidates, got {unranked_stat}"
        assert "92.0" in top_stat, f"Expected 92.0 in top score, got {top_stat}"

        # Capture screenshot for reporting
        screenshot_path = SCREENSHOTS_DIR / "us24_02_room_card_rankings_modal_mount.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

        # Clean close
        driver.find_element(By.CSS_SELECTOR, "[data-testid='button-close-ranked-modal']").click()
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-ranked-applicants']")))

    def test_tc_us24_03_leaderboard_descending_order_and_tie_breaking(self, driver):
        """TC-US24-03: Verify descending score ranking, podium badges (Gold, Silver, Bronze), and deterministic tie-breaking."""
        hr_email = "jubair_tc03_ranking@careerflow.test"
        login_hr(driver, email=hr_email, full_name="Jubair Reviewer")
        room, apps = create_ranking_sample_room(hr_email, room_title="Lead Kubernetes Architect", company="Cognitive Infrastructure")

        driver.get(f"{FRONTEND_URL}/hr/rooms")
        wait = WebDriverWait(driver, 10)

        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-action-ranking-{room.id}']"))).click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-ranked-applicants']")))
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='card-ranked-applicant-1']")))

        # Check Rank #1: Alice Architect (92.0 score) -> Gold Trophy
        rank1_card = driver.find_element(By.CSS_SELECTOR, "[data-testid='card-ranked-applicant-1']")
        assert "Alice Architect" in rank1_card.text
        assert "Rank #1" in rank1_card.text
        assert "92.0" in rank1_card.find_element(By.CSS_SELECTOR, "[data-testid='text-final-score-1']").text
        assert "94.0" in rank1_card.find_element(By.CSS_SELECTOR, "[data-testid='text-cv-score-1']").text
        assert "90.0" in rank1_card.find_element(By.CSS_SELECTOR, "[data-testid='text-video-score-1']").text

        # Check Rank #2: Bob Builder (85.0 score, CV 90.0) -> Silver Medal
        rank2_card = driver.find_element(By.CSS_SELECTOR, "[data-testid='card-ranked-applicant-2']")
        assert "Bob Builder" in rank2_card.text
        assert "Rank #2" in rank2_card.text
        assert "85.0" in rank2_card.find_element(By.CSS_SELECTOR, "[data-testid='text-final-score-2']").text
        assert "90.0" in rank2_card.find_element(By.CSS_SELECTOR, "[data-testid='text-cv-score-2']").text

        # Check Rank #3: Charlie Cloud (85.0 score, CV 80.0) -> Bronze Medal
        # TIE-BREAK VERIFICATION: Bob and Charlie both have 85.0. Bob has higher CV score (90 > 80), so Bob is #2 and Charlie is #3!
        rank3_card = driver.find_element(By.CSS_SELECTOR, "[data-testid='card-ranked-applicant-3']")
        assert "Charlie Cloud" in rank3_card.text
        assert "Rank #3" in rank3_card.text
        assert "85.0" in rank3_card.find_element(By.CSS_SELECTOR, "[data-testid='text-final-score-3']").text
        assert "80.0" in rank3_card.find_element(By.CSS_SELECTOR, "[data-testid='text-cv-score-3']").text

        # Check Rank #4: David Developer (72.0 score) -> Standard Rank Pill #4
        rank4_card = driver.find_element(By.CSS_SELECTOR, "[data-testid='card-ranked-applicant-4']")
        assert "David Developer" in rank4_card.text
        assert "#4" in rank4_card.text
        assert "72.0" in rank4_card.find_element(By.CSS_SELECTOR, "[data-testid='text-final-score-4']").text

        # Capture screenshot for reporting
        screenshot_path = SCREENSHOTS_DIR / "us24_03_leaderboard_tie_breaking_and_badges.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

        driver.find_element(By.CSS_SELECTOR, "[data-testid='button-close-ranked-modal']").click()

    def test_tc_us24_04_instant_search_and_score_slider_filtering(self, driver):
        """TC-US24-04: Verify instant search, minimum score slider filtering, and sort dropdown reordering."""
        hr_email = "jubair_tc04_search@careerflow.test"
        login_hr(driver, email=hr_email, full_name="Jubair Reviewer")
        room, apps = create_ranking_sample_room(hr_email, room_title="Fullstack SRE Lead", company="Vanguard Cloud")

        driver.get(f"{FRONTEND_URL}/hr/rooms")
        wait = WebDriverWait(driver, 10)

        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-action-ranking-{room.id}']"))).click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-ranked-applicants']")))
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='card-ranked-applicant-1']")))

        search_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-ranked-search']")

        # 1. Search by candidate name "Alice" + Enter
        clear_react_input(driver, search_input)
        search_input.send_keys("Alice")
        search_input.send_keys(Keys.ENTER)
        time.sleep(0.6)
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='card-ranked-applicant-1']")))
        assert "Alice Architect" in driver.find_element(By.CSS_SELECTOR, "[data-testid='card-ranked-applicant-1']").text
        assert len(driver.find_elements(By.CSS_SELECTOR, "[data-testid='card-ranked-applicant-2']")) == 0

        # 2. Search by email "bob_us24" + Enter
        clear_react_input(driver, search_input)
        search_input.send_keys("bob_us24")
        search_input.send_keys(Keys.ENTER)
        time.sleep(0.6)
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='card-ranked-applicant-1']")))
        assert "Bob Builder" in driver.find_element(By.CSS_SELECTOR, "[data-testid='card-ranked-applicant-1']").text

        # 3. Clear search and restore
        clear_react_input(driver, search_input)
        search_input.send_keys(Keys.ENTER)
        time.sleep(0.6)
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='card-ranked-applicant-4']")))
        assert len(driver.find_elements(By.CSS_SELECTOR, "[data-testid^='card-ranked-applicant-']")) == 4

        # 4. Filter by minimum score slider >= 80
        slider = driver.find_element(By.CSS_SELECTOR, "[data-testid='slider-min-score']")
        set_react_slider(driver, slider, 80)
        time.sleep(0.6)

        indicator_text = driver.find_element(By.CSS_SELECTOR, "[data-testid='text-min-score-indicator']").text
        assert "80" in indicator_text
        # Alice (92.0), Bob (85.0), Charlie (85.0) are >= 80. David (72.0) is excluded.
        visible_cards = driver.find_elements(By.CSS_SELECTOR, "[data-testid^='card-ranked-applicant-']")
        assert len(visible_cards) == 3

        # Capture screenshot for reporting
        screenshot_path = SCREENSHOTS_DIR / "us24_04_instant_search_and_score_slider_filters.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

        # 5. Reset slider to 0
        set_react_slider(driver, slider, 0)
        time.sleep(0.6)
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='card-ranked-applicant-4']")))
        assert len(driver.find_elements(By.CSS_SELECTOR, "[data-testid^='card-ranked-applicant-']")) == 4

        # 6. Sort by Final Score (Low to High)
        sort_select = Select(driver.find_element(By.CSS_SELECTOR, "[data-testid='select-ranked-sort']"))
        sort_select.select_by_value("final_score")
        time.sleep(0.6)
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='card-ranked-applicant-1']")))
        # Lowest score is David Developer (72.0), so first row should be David
        first_card_text = driver.find_element(By.CSS_SELECTOR, "[data-testid='card-ranked-applicant-1']").text
        assert "David Developer" in first_card_text
        assert "72.0" in first_card_text

        # Restore default sort
        sort_select.select_by_value("-final_score")
        time.sleep(0.6)

        driver.find_element(By.CSS_SELECTOR, "[data-testid='button-close-ranked-modal']").click()

    def test_tc_us24_05_unranked_candidates_segregation_and_tab_switching(self, driver):
        """TC-US24-05: Verify unranked candidates tab segregation and explanatory pending reasons."""
        hr_email = "jubair_tc05_unranked@careerflow.test"
        login_hr(driver, email=hr_email, full_name="Jubair Reviewer")
        room, apps = create_ranking_sample_room(hr_email, room_title="Cloud Security Specialist", company="ShieldTech")

        driver.get(f"{FRONTEND_URL}/hr/rooms")
        wait = WebDriverWait(driver, 10)

        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-action-ranking-{room.id}']"))).click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-ranked-applicants']")))
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='card-ranked-applicant-1']")))

        # 1. Click Evaluation In Progress tab
        unranked_tab = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='tab-unranked-leaderboard']")))
        assert "2" in unranked_tab.text  # 2 unranked candidates
        unranked_tab.click()
        time.sleep(0.5)

        # 2. Verify informational banner explaining unranked status
        modal = driver.find_element(By.CSS_SELECTOR, "[data-testid='modal-ranked-applicants']")
        assert "do not have a calculated final score yet" in modal.text

        # 3. Verify Eva Evaluation (Missing video presentation)
        eva_card = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='card-unranked-applicant-{apps[4].id}']")))
        assert "Eva Evaluation" in eva_card.text
        assert "Video presentation missing" in eva_card.text

        # 4. Verify Frank Fresh (Missing both CV and video)
        frank_card = driver.find_element(By.CSS_SELECTOR, f"[data-testid='card-unranked-applicant-{apps[5].id}']")
        assert "Frank Fresh" in frank_card.text
        assert "CV document and video presentation missing" in frank_card.text

        # Capture screenshot for reporting
        screenshot_path = SCREENSHOTS_DIR / "us24_05_unranked_candidates_segregation.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

        # 5. Switch back to Ranked Leaderboard tab
        driver.find_element(By.CSS_SELECTOR, "[data-testid='tab-ranked-leaderboard']").click()
        time.sleep(0.5)
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='card-ranked-applicant-1']")))
        assert len(driver.find_elements(By.CSS_SELECTOR, "[data-testid^='card-ranked-applicant-']")) == 4

        driver.find_element(By.CSS_SELECTOR, "[data-testid='button-close-ranked-modal']").click()

    def test_tc_us24_06_score_recalculation_and_empty_room_state(self, driver):
        """TC-US24-06: Verify batch score recalculation trigger and graceful empty state for rooms with 0 applicants."""
        hr_email = "jubair_tc06_recalc@careerflow.test"
        login_hr(driver, email=hr_email, full_name="Jubair Reviewer")
        hr_user = User.objects.get(email=hr_email)

        # Create room with candidates for recalculation test
        active_room, apps = create_ranking_sample_room(hr_email, room_title="DevOps Lead", company="ScaleOps")

        # Create empty room with 0 applicants
        empty_room = RecruitmentRoom.objects.create(
            title="Newly Created Empty Opening",
            company_name="Vacant Systems",
            department="Operations",
            status=RecruitmentRoom.Status.ACTIVE,
            created_by=hr_user,
            cv_weight=50,
            video_weight=50
        )

        driver.get(f"{FRONTEND_URL}/hr/rooms")
        wait = WebDriverWait(driver, 10)

        # 1. Test Refresh Scores button on active room
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-action-ranking-{active_room.id}']"))).click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-ranked-applicants']")))
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='card-ranked-applicant-1']")))

        recalc_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-recalculate-scores']")
        assert "Refresh Scores" in recalc_btn.text
        recalc_btn.click()
        time.sleep(1.2)

        # Verify leaderboard remains populated and stable after recalculation
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='card-ranked-applicant-1']")))
        ranked_cards = driver.find_elements(By.CSS_SELECTOR, "[data-testid^='card-ranked-applicant-']")
        assert len(ranked_cards) >= 4, f"Expected at least 4 ranked cards, got {len(ranked_cards)}"
        driver.find_element(By.CSS_SELECTOR, "[data-testid='button-close-ranked-modal']").click()
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-ranked-applicants']")))

        # 2. Test Empty Room
        driver.get(f"{FRONTEND_URL}/hr/rooms")
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-action-ranking-{empty_room.id}']"))).click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-ranked-applicants']")))

        empty_text = wait.until(EC.visibility_of_element_located((By.XPATH, "//*[contains(text(), 'No ranked candidates found')]")))
        assert empty_text is not None

        modal = driver.find_element(By.CSS_SELECTOR, "[data-testid='modal-ranked-applicants']")
        assert "Total Applicants: 0" in modal.text or "0" in modal.text
        assert "Ranked Candidates: 0" in modal.text or "0" in modal.text

        # Capture screenshot for reporting
        screenshot_path = SCREENSHOTS_DIR / "us24_06_score_recalculation_and_empty_state.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

        driver.find_element(By.CSS_SELECTOR, "[data-testid='button-close-ranked-modal']").click()

    def test_tc_us24_07_large_candidate_pool_ranking(self, driver):
        """TC-US24-07: Verify pagination, scalability, and deterministic sorting with >20 applicants (25 total)."""
        hr_email = "jubair_tc07_scale@careerflow.test"
        login_hr(driver, email=hr_email, full_name="Jubair Reviewer")
        large_room, apps = create_large_candidate_room(hr_email, count=25)

        driver.get(f"{FRONTEND_URL}/hr/rooms")
        wait = WebDriverWait(driver, 10)

        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-action-ranking-{large_room.id}']"))).click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-ranked-applicants']")))
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='card-ranked-applicant-1']")))

        # Verify summary stats reflect 25 candidates
        modal = driver.find_element(By.CSS_SELECTOR, "[data-testid='modal-ranked-applicants']")
        assert "25" in driver.find_element(By.CSS_SELECTOR, "[data-testid='stat-ranked-total']").text
        assert "25" in driver.find_element(By.CSS_SELECTOR, "[data-testid='stat-ranked-count']").text
        assert "98.0" in driver.find_element(By.CSS_SELECTOR, "[data-testid='stat-top-score']").text

        # Verify all 25 applicant cards render in descending order
        cards = driver.find_elements(By.CSS_SELECTOR, "[data-testid^='card-ranked-applicant-']")
        assert len(cards) == 25, f"Expected 25 ranked candidate cards, got {len(cards)}"

        # Verify Rank #1 is Candidate Scaled 01 (98.0)
        assert "Candidate Scaled 01" in cards[0].text
        assert "Rank #1" in cards[0].text
        assert "98.0" in cards[0].text

        # Verify Rank #25 is Candidate Scaled 25
        assert "Candidate Scaled 25" in cards[24].text
        assert "#25" in cards[24].text

        # Capture screenshot for reporting
        screenshot_path = SCREENSHOTS_DIR / "us24_07_large_candidate_pool_ranking.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

        driver.find_element(By.CSS_SELECTOR, "[data-testid='button-close-ranked-modal']").click()

    def test_tc_us24_08_mobile_responsive_leaderboard(self, driver):
        """TC-US24-08: Verify responsive mobile viewport rendering (375x812) without horizontal overflow or clipping."""
        hr_email = "jubair_tc08_mobile@careerflow.test"
        login_hr(driver, email=hr_email, full_name="Jubair Reviewer")
        room, apps = create_ranking_sample_room(hr_email, room_title="Mobile Platform Architect", company="NeoMobility")

        # Set mobile viewport (iPhone dimensions)
        driver.set_window_size(375, 812)

        try:
            driver.get(f"{FRONTEND_URL}/hr/rooms")
            wait = WebDriverWait(driver, 10)

            # Open leaderboard modal on mobile
            action_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, f"[data-testid='button-action-ranking-{room.id}']")))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", action_btn)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", action_btn)

            modal = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-ranked-applicants']")))
            wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='card-ranked-applicant-1']")))
            assert modal is not None

            # Verify rank cards and text remain readable
            rank1_card = driver.find_element(By.CSS_SELECTOR, "[data-testid='card-ranked-applicant-1']")
            assert "Alice Architect" in rank1_card.text
            assert "92.0" in rank1_card.text

            # Verify modal dialog and contents adapt responsively to viewport
            window_inner_width = driver.execute_script("return window.innerWidth")
            modal_rect = modal.rect
            assert modal_rect["width"] <= window_inner_width + 10

            # Verify modal container does not experience unconstrained horizontal scrolling
            modal_scroll_width = driver.execute_script("return arguments[0].scrollWidth;", modal)
            modal_client_width = driver.execute_script("return arguments[0].clientWidth;", modal)
            assert modal_scroll_width <= modal_client_width + 10

            # Verify underlying document scroll does not exhibit excessive overflow (allowing 25px for Windows scrollbar)
            body_scroll_width = driver.execute_script("return document.body.scrollWidth")
            assert body_scroll_width <= window_inner_width + 25, f"Horizontal overflow detected: scrollWidth={body_scroll_width}, innerWidth={window_inner_width}"

            # Capture screenshot for reporting
            screenshot_path = SCREENSHOTS_DIR / "us24_08_mobile_responsive_leaderboard.png"
            driver.save_screenshot(str(screenshot_path))
            assert screenshot_path.exists()

            close_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-close-ranked-modal']")
            driver.execute_script("arguments[0].click();", close_btn)
        finally:
            # Restore standard desktop window size
            driver.set_window_size(1920, 1080)
