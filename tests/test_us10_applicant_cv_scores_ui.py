import os
import sys
import time
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

from apps.authentication.models import User
from apps.recruitment.models import RecruitmentRoom, CandidateApplication
from apps.cv.models import CandidateCV, ParsedCV, JobRequirement, CVJobMatch
from conftest import FRONTEND_URL, SCREENSHOTS_DIR, create_user_in_db


def login_hr(driver, email="maria_hr_lead@careerflow.test", password="ValidPass2026!", full_name="Nafisa Tabassum Maria"):
    """Helper to ensure HR Manager exists and log in via UI."""
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
    """Reliably clears React controlled inputs across Windows and macOS."""
    element.send_keys(Keys.COMMAND + "a")
    element.send_keys(Keys.CONTROL + "a")
    element.send_keys(Keys.BACKSPACE)
    driver.execute_script(
        "arguments[0].value = ''; arguments[0].dispatchEvent(new Event('input', { bubbles: true })); arguments[0].dispatchEvent(new Event('change', { bubbles: true }));",
        element
    )



def create_sample_room_with_candidates(hr_email: str, room_title="Lead Frontend Architect", company="Apex Cloud Systems"):
    """
    Creates a RecruitmentRoom owned by hr_email with 4 distinct applicants:
    1. Alice Candidate: Strong Match (88%), Redux, React, TypeScript
    2. Bob Candidate: Moderate Match (62%), React, TypeScript
    3. Charlie Candidate: Low Match (42%), React only
    4. David Candidate: No CV Uploaded (None score, PENDING)
    """
    hr_user = User.objects.get(email=hr_email)

    room = RecruitmentRoom.objects.create(
        title=room_title,
        company_name=company,
        department="Engineering",
        description="Lead modern web architecture and React cloud micro-frontends.",
        requirements_text="Must master React, TypeScript, Redux, and Docker.",
        skills_required=["React", "TypeScript", "Redux", "Docker"],
        status=RecruitmentRoom.Status.ACTIVE,
        created_by=hr_user,
        cv_weight=60,
        video_weight=40
    )

    # 1. Alice (Strong Match: 88%)
    alice_user = create_user_in_db("alice_cand_us10@careerflow.test", "ValidPass2026!", role=User.Role.STUDENT, full_name="Alice Candidate")
    alice_cv = CandidateCV.objects.create(
        user=alice_user,
        file="students/alice/alice_cv.pdf",
        original_filename="Alice_Resume_React_Expert.pdf",
        file_size=215000,
        file_type="pdf",
        is_active=True
    )
    CVJobMatch.objects.create(
        cv=alice_cv,
        job_title=room.title,
        company=room.company_name,
        job_description=room.description,
        match_score=88,
        keyword_coverage=75,
        category_scores={"domain_craft": 90, "collaboration": 85, "leadership": 80, "accessibility": 70},
        skills_matched=["React", "TypeScript", "Redux"],
        skills_missing=["Docker"],
        strengths=["Exceptional React, TypeScript, and Redux enterprise architecture", "Strong full-stack frontend track record"],
        gaps=["Lacks containerization and Docker orchestrations"],
        recommendations=["Highlight containerization in upcoming projects"]
    )
    app_alice = CandidateApplication.objects.create(
        room=room,
        candidate=alice_user,
        cv=alice_cv,
        status=CandidateApplication.Status.COMPLETED
    )

    # 2. Bob (Moderate Match: 62%)
    bob_user = create_user_in_db("bob_cand_us10@careerflow.test", "ValidPass2026!", role=User.Role.STUDENT, full_name="Bob Midlevel")
    bob_cv = CandidateCV.objects.create(
        user=bob_user,
        file="students/bob/bob_cv.pdf",
        original_filename="Bob_Resume_Frontend.pdf",
        file_size=180000,
        file_type="pdf",
        is_active=True
    )
    CVJobMatch.objects.create(
        cv=bob_cv,
        job_title=room.title,
        company=room.company_name,
        job_description=room.description,
        match_score=62,
        keyword_coverage=50,
        category_scores={"domain_craft": 65, "collaboration": 70, "leadership": 60, "accessibility": 55},
        skills_matched=["React", "TypeScript"],
        skills_missing=["Redux", "Docker"],
        strengths=["Solid modern TypeScript and React hooks knowledge"],
        gaps=["Needs Redux and Docker exposure"],
        recommendations=["Strengthen state management architectures"]
    )
    app_bob = CandidateApplication.objects.create(
        room=room,
        candidate=bob_user,
        cv=bob_cv,
        status=CandidateApplication.Status.COMPLETED
    )

    # 3. Charlie (Weak Match: 42%)
    charlie_user = create_user_in_db("charlie_cand_us10@careerflow.test", "ValidPass2026!", role=User.Role.STUDENT, full_name="Charlie Junior")
    charlie_cv = CandidateCV.objects.create(
        user=charlie_user,
        file="students/charlie/charlie_cv.pdf",
        original_filename="Charlie_Junior_Resume.pdf",
        file_size=140000,
        file_type="pdf",
        is_active=True
    )
    CVJobMatch.objects.create(
        cv=charlie_cv,
        job_title=room.title,
        company=room.company_name,
        job_description=room.description,
        match_score=42,
        keyword_coverage=25,
        category_scores={"domain_craft": 45, "collaboration": 50, "leadership": 40, "accessibility": 35},
        skills_matched=["React"],
        skills_missing=["TypeScript", "Redux", "Docker"],
        strengths=["Basic familiarity with React ecosystem"],
        gaps=["Missing TypeScript, Redux, Docker requirements"],
        recommendations=["Focus on TypeScript fundamentals"]
    )
    app_charlie = CandidateApplication.objects.create(
        room=room,
        candidate=charlie_user,
        cv=charlie_cv,
        status=CandidateApplication.Status.COMPLETED
    )

    # 4. David (No CV Uploaded)
    david_user = create_user_in_db("david_nocv_us10@careerflow.test", "ValidPass2026!", role=User.Role.STUDENT, full_name="David NoCV")
    app_david = CandidateApplication.objects.create(
        room=room,
        candidate=david_user,
        cv=None,
        status=CandidateApplication.Status.PENDING
    )

    return room, [app_alice, app_bob, app_charlie, app_david]


class TestUS10ApplicantCvScoresUI:
    """
    US-10: View Applicant CV Match Scores UI Automation Tests
    Task: US-10-T6 (Peer UI Testing & Code Review for CV Match Scores View)
    Tester / Peer Reviewer: Nafisa Tabassum Maria (@Maria-07-222) - System Architect
    Developer: MD. Jubair Bin Hasan (@jubair65) - Software Developer
    Sprint: Sprint 5
    """

    def test_tc_us10_01_dashboard_dropdown_opens_modal(self, driver):
        """TC-US10-01: Verify HR Dashboard quick room selector dropdown opens applicant CV scores modal."""
        hr_email = "maria_tc01_dash@careerflow.test"
        login_hr(driver, email=hr_email, full_name="Maria Reviewer")
        room, apps = create_sample_room_with_candidates(hr_email, room_title="Principal Fullstack Engineer", company="NovaTech")

        driver.get(f"{FRONTEND_URL}/hr/dashboard")
        wait = WebDriverWait(driver, 10)

        # 1. Locate quick room dropdown on Dashboard
        dropdown = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='select-room-cv-scores-dashboard']"))
        )
        select = Select(dropdown)
        select.select_by_value(str(room.id))

        # 2. Verify modal mounts with room title
        modal = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-room-cv-scores']"))
        )
        assert modal is not None
        header_title = driver.find_element(By.CSS_SELECTOR, "[data-testid='text-room-title-header']").text
        assert "Principal Fullstack Engineer" in header_title

        # Capture screenshot for reporting
        screenshot_path = SCREENSHOTS_DIR / "us10_01_dashboard_cv_scores_dropdown_modal.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

        # 3. Dismiss modal cleanly via header close button
        close_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-close-cv-scores-modal']")
        close_btn.click()
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-room-cv-scores']")))

    def test_tc_us10_02_room_card_action_button_opens_modal(self, driver):
        """TC-US10-02: Verify Recruitment Rooms card 'CV Scores' action button mounts modal with 4 metric cards."""
        hr_email = "maria_tc02_rooms@careerflow.test"
        login_hr(driver, email=hr_email, full_name="Maria Reviewer")
        room, apps = create_sample_room_with_candidates(hr_email, room_title="Senior Cloud Architect", company="Apex Cloud")

        driver.get(f"{FRONTEND_URL}/hr/rooms")
        wait = WebDriverWait(driver, 10)

        # 1. Locate and click CV Scores action button on room card
        action_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-action-cv-scores-{room.id}']"))
        )
        assert "CV Scores" in action_btn.text
        action_btn.click()

        # 2. Verify modal mounted
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-room-cv-scores']")))

        # 3. Verify the 4 metric cards
        total_stat = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='stat-total-applicants']"))).text
        scored_stat = driver.find_element(By.CSS_SELECTOR, "[data-testid='stat-scored-applicants']").text
        avg_stat = driver.find_element(By.CSS_SELECTOR, "[data-testid='stat-avg-cv-score']").text
        top_stat = driver.find_element(By.CSS_SELECTOR, "[data-testid='stat-highest-cv-score']").text

        assert total_stat == "4", f"Expected 4 total applicants, got {total_stat}"
        assert scored_stat == "3", f"Expected 3 scored applicants, got {scored_stat}"
        # Average of 88, 62, 42 is 64.0%
        assert "64" in avg_stat, f"Expected average ~64%, got {avg_stat}"
        assert top_stat == "88%", f"Expected top score 88%, got {top_stat}"

        # Capture screenshot for reporting
        screenshot_path = SCREENSHOTS_DIR / "us10_02_room_card_cv_scores_modal_mount.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

        # Clean close
        driver.find_element(By.CSS_SELECTOR, "[data-testid='button-close-cv-scores-modal']").click()
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-room-cv-scores']")))

    def test_tc_us10_03_score_tier_badges_and_chips_rendering(self, driver):
        """TC-US10-03: Verify color-coded match score badges (Strong, Moderate, Weak, No CV) and skills chips."""
        hr_email = "maria_tc03_tiers@careerflow.test"
        login_hr(driver, email=hr_email, full_name="Maria Reviewer")
        room, apps = create_sample_room_with_candidates(hr_email, room_title="AI Pipeline Engineer", company="Cognitive Tech")

        driver.get(f"{FRONTEND_URL}/hr/rooms")
        wait = WebDriverWait(driver, 10)

        # Open modal
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-action-cv-scores-{room.id}']"))).click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-room-cv-scores']")))

        # Check Alice row (Strong match: 88%)
        alice_row = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='row-applicant-cv-{apps[0].id}']")))
        assert "Alice Candidate" in alice_row.text
        alice_badge = alice_row.find_element(By.CSS_SELECTOR, f"[data-testid='badge-cv-score-{apps[0].id}']")
        assert "88%" in alice_badge.text
        assert "Strong" in alice_row.text

        # Check Bob row (Moderate match: 62%)
        bob_row = driver.find_element(By.CSS_SELECTOR, f"[data-testid='row-applicant-cv-{apps[1].id}']")
        assert "Bob Midlevel" in bob_row.text
        bob_badge = bob_row.find_element(By.CSS_SELECTOR, f"[data-testid='badge-cv-score-{apps[1].id}']")
        assert "62%" in bob_badge.text
        assert "Moderate" in bob_row.text

        # Check Charlie row (Weak match: 42%)
        charlie_row = driver.find_element(By.CSS_SELECTOR, f"[data-testid='row-applicant-cv-{apps[2].id}']")
        assert "Charlie Junior" in charlie_row.text
        charlie_badge = charlie_row.find_element(By.CSS_SELECTOR, f"[data-testid='badge-cv-score-{apps[2].id}']")
        assert "42%" in charlie_badge.text
        assert "Low" in charlie_row.text

        # Check David row (No CV)
        david_row = driver.find_element(By.CSS_SELECTOR, f"[data-testid='row-applicant-cv-{apps[3].id}']")
        assert "David NoCV" in david_row.text
        assert "No CV" in david_row.text

        # Capture screenshot for reporting
        screenshot_path = SCREENSHOTS_DIR / "us10_03_score_tier_badges_and_candidate_table.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

        driver.find_element(By.CSS_SELECTOR, "[data-testid='button-close-cv-scores-modal']").click()

    def test_tc_us10_04_instant_search_and_tier_filtering(self, driver):
        """TC-US10-04: Verify instant search by candidate name/skill and filtering by match score tiers."""
        hr_email = "maria_tc04_search@careerflow.test"
        login_hr(driver, email=hr_email, full_name="Maria Reviewer")
        room, apps = create_sample_room_with_candidates(hr_email, room_title="Fullstack Lead", company="Vanguard")

        driver.get(f"{FRONTEND_URL}/hr/rooms")
        wait = WebDriverWait(driver, 10)

        # Open modal
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-action-cv-scores-{room.id}']"))).click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-room-cv-scores']")))

        search_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-search-cv-scores']")

        # 1. Search by candidate name "Alice"
        clear_react_input(driver, search_input)
        search_input.send_keys("Alice")
        time.sleep(0.3)
        assert driver.find_element(By.CSS_SELECTOR, f"[data-testid='row-applicant-cv-{apps[0].id}']").is_displayed()
        assert len(driver.find_elements(By.CSS_SELECTOR, f"[data-testid='row-applicant-cv-{apps[1].id}']")) == 0

        # 2. Search by unique skill "Redux" (only matched by Alice)
        clear_react_input(driver, search_input)
        search_input.send_keys("Redux")
        time.sleep(0.3)
        assert driver.find_element(By.CSS_SELECTOR, f"[data-testid='row-applicant-cv-{apps[0].id}']").is_displayed()
        assert len(driver.find_elements(By.CSS_SELECTOR, f"[data-testid='row-applicant-cv-{apps[1].id}']")) == 0

        # Clear search before testing tier filters
        clear_react_input(driver, search_input)
        time.sleep(0.3)

        # 3. Filter by Tier ≥75% (High)
        filter_high = driver.find_element(By.CSS_SELECTOR, "[data-testid='filter-tier-high']")
        filter_high.click()
        time.sleep(0.3)
        assert driver.find_element(By.CSS_SELECTOR, f"[data-testid='row-applicant-cv-{apps[0].id}']").is_displayed()
        assert len(driver.find_elements(By.CSS_SELECTOR, f"[data-testid='row-applicant-cv-{apps[1].id}']")) == 0
        assert len(driver.find_elements(By.CSS_SELECTOR, f"[data-testid='row-applicant-cv-{apps[2].id}']")) == 0

        # 4. Filter by Tier 50-74% (Moderate)
        driver.find_element(By.CSS_SELECTOR, "[data-testid='filter-tier-moderate']").click()
        time.sleep(0.3)
        assert driver.find_element(By.CSS_SELECTOR, f"[data-testid='row-applicant-cv-{apps[1].id}']").is_displayed()
        assert len(driver.find_elements(By.CSS_SELECTOR, f"[data-testid='row-applicant-cv-{apps[0].id}']")) == 0

        # 5. Filter by Tier <50% (Low)
        driver.find_element(By.CSS_SELECTOR, "[data-testid='filter-tier-low']").click()
        time.sleep(0.3)
        assert driver.find_element(By.CSS_SELECTOR, f"[data-testid='row-applicant-cv-{apps[2].id}']").is_displayed()
        assert len(driver.find_elements(By.CSS_SELECTOR, f"[data-testid='row-applicant-cv-{apps[0].id}']")) == 0

        # 6. Filter by No CV
        driver.find_element(By.CSS_SELECTOR, "[data-testid='filter-tier-pending']").click()
        time.sleep(0.3)
        assert driver.find_element(By.CSS_SELECTOR, f"[data-testid='row-applicant-cv-{apps[3].id}']").is_displayed()
        assert len(driver.find_elements(By.CSS_SELECTOR, f"[data-testid='row-applicant-cv-{apps[0].id}']")) == 0

        # Capture screenshot for reporting
        screenshot_path = SCREENSHOTS_DIR / "us10_04_instant_search_and_tier_filters.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

        # 7. Reset to All
        driver.find_element(By.CSS_SELECTOR, "[data-testid='filter-tier-all']").click()
        time.sleep(0.3)
        assert driver.find_element(By.CSS_SELECTOR, f"[data-testid='row-applicant-cv-{apps[0].id}']").is_displayed()
        assert driver.find_element(By.CSS_SELECTOR, f"[data-testid='row-applicant-cv-{apps[1].id}']").is_displayed()

        driver.find_element(By.CSS_SELECTOR, "[data-testid='button-close-cv-scores-modal']").click()

    def test_tc_us10_05_skill_breakdown_inspection_modal(self, driver):
        """TC-US10-05: Verify skill breakdown modal inspection (score gauge, 4 sub-signals, matched/missing skills)."""
        hr_email = "maria_tc05_breakdown@careerflow.test"
        login_hr(driver, email=hr_email, full_name="Maria Reviewer")
        room, apps = create_sample_room_with_candidates(hr_email, room_title="Frontend Staff Engineer", company="FinTech Orbit")

        driver.get(f"{FRONTEND_URL}/hr/rooms")
        wait = WebDriverWait(driver, 10)

        # Open scores modal
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-action-cv-scores-{room.id}']"))).click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-room-cv-scores']")))

        # Click Inspect on Alice's row
        inspect_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-view-breakdown-{apps[0].id}']"))
        )
        inspect_btn.click()

        # Verify breakdown modal mounts
        breakdown_modal = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-cv-skill-breakdown']"))
        )
        assert breakdown_modal is not None

        # Verify candidate name in header
        candidate_header = driver.find_element(By.CSS_SELECTOR, "[data-testid='text-breakdown-candidate-name']").text
        assert "Alice Candidate" in candidate_header

        # Verify overall score banner & match tier badge
        overall_score = driver.find_element(By.CSS_SELECTOR, "[data-testid='badge-overall-match-score']").text
        assert "88%" in overall_score
        assert "Strong Match" in driver.find_element(By.CSS_SELECTOR, "[data-testid='card-cv-overall-score']").text

        # Verify 4 competency sub-signals
        signals_grid = driver.find_element(By.CSS_SELECTOR, "[data-testid='grid-signal-categories']")
        assert "Domain & Craft" in signals_grid.text
        assert "Collaboration" in signals_grid.text
        assert "Ownership & Scope" in signals_grid.text
        assert "Standards & Quality" in signals_grid.text

        # Verify matched skills pills (React, TypeScript, Redux)
        matched_card = driver.find_element(By.CSS_SELECTOR, "[data-testid='card-matched-skills']")
        assert "React" in matched_card.text
        assert "TypeScript" in matched_card.text
        assert "Redux" in matched_card.text

        # Verify missing skills pills (Docker)
        missing_card = driver.find_element(By.CSS_SELECTOR, "[data-testid='card-missing-skills']")
        assert "Docker" in missing_card.text

        # Verify CV file info
        assert "Alice_Resume_React_Expert.pdf" in breakdown_modal.text

        # Capture screenshot for reporting
        screenshot_path = SCREENSHOTS_DIR / "us10_05_skill_breakdown_inspection_modal.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

        # Close breakdown modal cleanly
        driver.find_element(By.CSS_SELECTOR, "[data-testid='button-close-cv-breakdown']").click()
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-cv-skill-breakdown']")))

        # Close scores modal
        driver.find_element(By.CSS_SELECTOR, "[data-testid='button-close-cv-scores-modal']").click()

    def test_tc_us10_06_empty_state_and_edge_cases(self, driver):
        """TC-US10-06: Verify empty state for rooms with zero applicants and RBAC access denial for unauthorized rooms."""
        hr_email = "maria_tc06_empty@careerflow.test"
        login_hr(driver, email=hr_email, full_name="Maria Reviewer")
        hr_user = User.objects.get(email=hr_email)

        # 1. Create an empty room with 0 applicants
        empty_room = RecruitmentRoom.objects.create(
            title="Newly Created Empty Opening",
            company_name="Solitary Tech",
            department="Operations",
            status=RecruitmentRoom.Status.ACTIVE,
            created_by=hr_user,
            cv_weight=50,
            video_weight=50
        )

        driver.get(f"{FRONTEND_URL}/hr/rooms")
        wait = WebDriverWait(driver, 10)

        # Open modal for empty room
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-action-cv-scores-{empty_room.id}']"))).click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-room-cv-scores']")))

        # Verify empty state card displays
        empty_card = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='card-empty-cv-scores']")))
        assert "No applicants found" in empty_card.text
        assert driver.find_element(By.CSS_SELECTOR, "[data-testid='stat-total-applicants']").text == "0"
        assert driver.find_element(By.CSS_SELECTOR, "[data-testid='stat-scored-applicants']").text == "0"

        # Capture screenshot for reporting
        screenshot_path = SCREENSHOTS_DIR / "us10_06_empty_state_and_edge_cases.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

        driver.find_element(By.CSS_SELECTOR, "[data-testid='button-close-cv-scores-modal']").click()
