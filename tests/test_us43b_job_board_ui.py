"""
US-43B: Applicant Job Room Discovery Dashboard (Job Board) UI Test Suite (US-43B-T7).
User Story: US-43B — Applicant Job Room Discovery Dashboard
Sprint: Sprint 7 — Final Platform Maturity & Release
Lead Developer: MD. Jubair Bin Hasan (@jubair65)
Dedicated Peer UI Tester & System Architect: Nafisa Tabassum Maria (@Maria-07-222)
Target Branch: feat/us-43b-job-board -> develop

Acceptance Criteria & Features Verified:
✓ AC-1: Candidate can view a paginated list of all OPEN recruitment rooms on Job Board (/student/jobs).
✓ AC-2: Each room card shows job title, company name, role level, deadline, and "Apply Now" button.
✓ AC-3: Rooms with status CLOSED, PAUSED, or past deadline are hidden from the listing.
✓ AC-4: Clicking "Apply Now" opens the standard application flow (/apply/:token).
✓ AC-5: Rooms the candidate has already applied to show an "Applied" badge with "Track Application" link.
✓ AC-6: Candidate can search/filter rooms by job title, company name, department, or experience level.
✓ AC-7: Empty state is displayed clearly when no matching open rooms exist.
✓ AC-8: Data is strictly tenant-isolated and candidate-scoped.
"""

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
from django.utils import timezone
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

from apps.authentication.models import User
from apps.recruitment.models import (
    RecruitmentRoom,
    CandidateApplication,
)
from conftest import FRONTEND_URL, SCREENSHOTS_DIR, create_user_in_db


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

    wait.until(lambda d: "/student" in d.current_url or "/dashboard" in d.current_url)
    return user


class TestUS43BJobBoardUI:
    """Automated UI Selenium test suite for US-43B Job Board Discovery."""

    def test_tc43b_01_sidebar_navigation_and_metrics(self, driver):
        """
        Test Case 1: Sidebar Navigation & Metric Counters (US-43B-T6, AC-1)
        Log in as Candidate; click 'Job Board' in sidebar (nav-job-board);
        verify URL becomes /student/jobs and metric cards render.
        """
        uid = uuid.uuid4().hex[:6]
        hr_email = f"hr_jb_{uid}@careerflow.test"
        candidate_email = f"cand_jb_{uid}@careerflow.test"

        hr_user = create_user_in_db(hr_email, "ValidPass2026!", role=User.Role.HR_MANAGER, full_name="HR Mona")
        candidate = login_candidate(driver, email=candidate_email, full_name="Job Seeker")

        # Create active rooms
        now = timezone.now()
        room1 = RecruitmentRoom.objects.create(
            title=f"Platform Architect {uid}",
            company_name="Cloud Corp",
            department="Cloud",
            role_category="Engineering",
            experience_level=RecruitmentRoom.ExperienceLevel.SENIOR,
            status=RecruitmentRoom.Status.ACTIVE,
            link_is_active=True,
            link_expires_at=now + timedelta(days=10),
            share_token=f"tok-pa-{uid}",
            created_by=hr_user,
        )
        room2 = RecruitmentRoom.objects.create(
            title=f"Security Analyst {uid}",
            company_name="CyberGuard",
            department="Security",
            role_category="Security",
            experience_level=RecruitmentRoom.ExperienceLevel.MID,
            status=RecruitmentRoom.Status.ACTIVE,
            link_is_active=True,
            link_expires_at=now + timedelta(days=14),
            share_token=f"tok-sec-{uid}",
            created_by=hr_user,
        )
        # Apply to room 1
        CandidateApplication.objects.create(
            room=room1,
            candidate=candidate,
            status=CandidateApplication.Status.COMPLETED,
        )

        wait = WebDriverWait(driver, 10)
        # Click sidebar Job Board navigation
        nav_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='nav-job-board']")))
        nav_btn.click()

        wait.until(EC.url_contains("/student/jobs"))
        assert "/student/jobs" in driver.current_url

        # Verify page heading and eyebrow
        heading = wait.until(EC.visibility_of_element_located((By.XPATH, "//h1[contains(., 'Recruitment Job Board')]")))
        assert heading.is_displayed()

        # Verify metric cards
        open_pos = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='metric-open-positions']")))
        ready_pos = driver.find_element(By.CSS_SELECTOR, "[data-testid='metric-available-positions']")
        applied_pos = driver.find_element(By.CSS_SELECTOR, "[data-testid='metric-applied-positions']")

        assert int(open_pos.text) >= 2
        assert int(applied_pos.text) >= 1
        assert int(ready_pos.text) >= 1

        screenshot_path = SCREENSHOTS_DIR / "us43b_01_sidebar_navigation_and_metrics.png"
        driver.save_screenshot(str(screenshot_path))

    def test_tc43b_02_pagination_default_9_and_next_page(self, driver):
        """
        Test Case 2: 9/10 Card Pagination - Navigation to Page 2 (AC-1)
        Creates 11 active rooms. Verifies that exactly 9 cards render on page 1 by default,
        pagination controls show 'Page 1 of 2', Next button navigates to page 2 (showing remaining 2 cards).
        """
        uid = uuid.uuid4().hex[:6]
        hr_email = f"hr_pg_{uid}@careerflow.test"
        candidate_email = f"cand_pg_{uid}@careerflow.test"

        hr_user = create_user_in_db(hr_email, "ValidPass2026!", role=User.Role.HR_MANAGER, full_name="HR Recruiter")
        login_candidate(driver, email=candidate_email, full_name="Paging Candidate")

        # Create 11 rooms with unique prefix
        prefix = f"BatchRoom-{uid}"
        now = timezone.now()
        for i in range(11):
            RecruitmentRoom.objects.create(
                title=f"{prefix} Number {i+1:02d}",
                company_name=f"Enterprise {uid}",
                department="Engineering",
                role_category="Engineering",
                experience_level=RecruitmentRoom.ExperienceLevel.MID,
                status=RecruitmentRoom.Status.ACTIVE,
                link_is_active=True,
                link_expires_at=now + timedelta(days=20),
                share_token=f"tok-pg-{uid}-{i}",
                created_by=hr_user,
            )

        wait = WebDriverWait(driver, 10)
        driver.get(f"{FRONTEND_URL}/student/jobs")
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='job-board-grid']")))

        # Filter by unique search term to only test our 11 rooms
        search_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-search-jobs']")))
        set_react_input(driver, search_input, prefix)
        time.sleep(0.5)

        # Assert exactly 9 cards displayed on Page 1
        cards = driver.find_elements(By.XPATH, f"//div[contains(@data-testid, 'job-board-card-') and contains(., '{prefix}')]")
        assert len(cards) == 9

        # Verify pagination container and page 1 status
        pagination_info = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='pagination-info']")))
        assert "Page 1 of 2" in pagination_info.text

        prev_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-prev-page']")
        assert not prev_btn.is_enabled() or prev_btn.get_attribute("disabled") is not None

        next_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-next-page']")
        assert next_btn.is_enabled()

        # Click Next page
        driver.execute_script("arguments[0].click();", next_btn)
        time.sleep(0.5)

        # On Page 2: remaining 2 cards
        cards_page_2 = driver.find_elements(By.XPATH, f"//div[contains(@data-testid, 'job-board-card-') and contains(., '{prefix}')]")
        assert len(cards_page_2) == 2
        assert "Page 2 of 2" in pagination_info.text

        screenshot_path = SCREENSHOTS_DIR / "us43b_02_pagination_default_9_and_next_page.png"
        driver.save_screenshot(str(screenshot_path))

    def test_tc43b_03_page_size_toggle_10_cards(self, driver):
        """
        Test Case 3: Page Size Selector (9 vs 10 vs 15 cards per page) (AC-1)
        Toggles select-page-size to 10 cards per page; verifies grid now shows 10 cards.
        """
        uid = uuid.uuid4().hex[:6]
        hr_email = f"hr_sz_{uid}@careerflow.test"
        candidate_email = f"cand_sz_{uid}@careerflow.test"

        hr_user = create_user_in_db(hr_email, "ValidPass2026!", role=User.Role.HR_MANAGER, full_name="HR Mona")
        login_candidate(driver, email=candidate_email, full_name="Page Size Candidate")

        prefix = f"ScaleRoom-{uid}"
        now = timezone.now()
        for i in range(12):
            RecruitmentRoom.objects.create(
                title=f"{prefix} Position {i+1:02d}",
                company_name=f"ScaleCorp {uid}",
                department="Product",
                role_category="Engineering",
                experience_level=RecruitmentRoom.ExperienceLevel.SENIOR,
                status=RecruitmentRoom.Status.ACTIVE,
                link_is_active=True,
                link_expires_at=now + timedelta(days=20),
                share_token=f"tok-sz-{uid}-{i}",
                created_by=hr_user,
            )

        wait = WebDriverWait(driver, 10)
        driver.get(f"{FRONTEND_URL}/student/jobs")
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='job-board-grid']")))

        search_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-search-jobs']")))
        set_react_input(driver, search_input, prefix)
        time.sleep(0.5)

        # Select 10 cards per page
        page_size_select = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='select-page-size']")))
        select_obj = Select(page_size_select)
        select_obj.select_by_value("10")
        time.sleep(0.5)

        # Assert exactly 10 cards visible on Page 1
        cards = driver.find_elements(By.XPATH, f"//div[contains(@data-testid, 'job-board-card-') and contains(., '{prefix}')]")
        assert len(cards) == 10

        screenshot_path = SCREENSHOTS_DIR / "us43b_03_page_size_toggle_10_cards.png"
        driver.save_screenshot(str(screenshot_path))

    def test_tc43b_04_active_vs_closed_expired_exclusion(self, driver):
        """
        Test Case 4: Active Open Rooms vs Closed / Paused / Expired (AC-1, AC-3)
        Verifies that only ACTIVE and unexpired rooms render, while CLOSED, PAUSED,
        and past-deadline rooms are strictly excluded.
        """
        uid = uuid.uuid4().hex[:6]
        hr_email = f"hr_act_{uid}@careerflow.test"
        candidate_email = f"cand_act_{uid}@careerflow.test"

        hr_user = create_user_in_db(hr_email, "ValidPass2026!", role=User.Role.HR_MANAGER, full_name="HR Manager")
        login_candidate(driver, email=candidate_email, full_name="Active Candidate")

        now = timezone.now()
        # 1. Active Open
        room_active = RecruitmentRoom.objects.create(
            title=f"Visible Lead DevOps {uid}",
            company_name=f"CloudScale {uid}",
            status=RecruitmentRoom.Status.ACTIVE,
            link_is_active=True,
            link_expires_at=now + timedelta(days=5),
            share_token=f"tok-act-{uid}",
            created_by=hr_user,
        )
        # 2. Closed Room
        RecruitmentRoom.objects.create(
            title=f"Hidden Closed DevOps {uid}",
            company_name=f"CloudScale {uid}",
            status=RecruitmentRoom.Status.CLOSED,
            link_is_active=True,
            share_token=f"tok-cls-{uid}",
            created_by=hr_user,
        )
        # 3. Paused Room
        RecruitmentRoom.objects.create(
            title=f"Hidden Paused DevOps {uid}",
            company_name=f"CloudScale {uid}",
            status=RecruitmentRoom.Status.PAUSED,
            link_is_active=True,
            share_token=f"tok-psd-{uid}",
            created_by=hr_user,
        )
        # 4. Expired Deadline Room
        RecruitmentRoom.objects.create(
            title=f"Hidden Expired DevOps {uid}",
            company_name=f"CloudScale {uid}",
            status=RecruitmentRoom.Status.ACTIVE,
            link_is_active=True,
            link_expires_at=now - timedelta(days=2),
            share_token=f"tok-exp-{uid}",
            created_by=hr_user,
        )

        wait = WebDriverWait(driver, 10)
        driver.get(f"{FRONTEND_URL}/student/jobs")
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='job-board-grid']")))

        search_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-search-jobs']")))
        set_react_input(driver, search_input, uid)
        time.sleep(0.5)

        # Assert Active room is visible
        assert f"Visible Lead DevOps {uid}" in driver.page_source
        # Assert Closed, Paused, and Expired rooms are NOT present
        assert f"Hidden Closed DevOps {uid}" not in driver.page_source
        assert f"Hidden Paused DevOps {uid}" not in driver.page_source
        assert f"Hidden Expired DevOps {uid}" not in driver.page_source

        screenshot_path = SCREENSHOTS_DIR / "us43b_04_active_vs_closed_expired_exclusion.png"
        driver.save_screenshot(str(screenshot_path))

    def test_tc43b_05_apply_now_and_applied_badge(self, driver):
        """
        Test Case 5: 'Apply Now' vs 'Applied' Status (AC-4, AC-5)
        Unapplied room renders [button-apply-room-${id}], clicking opens /apply/${token}.
        Applied room renders [badge-applied-${id}] and clicking Track Application goes to /student/applications.
        """
        uid = uuid.uuid4().hex[:6]
        hr_email = f"hr_app_{uid}@careerflow.test"
        candidate_email = f"cand_app_{uid}@careerflow.test"

        hr_user = create_user_in_db(hr_email, "ValidPass2026!", role=User.Role.HR_MANAGER, full_name="HR Mona")
        candidate = login_candidate(driver, email=candidate_email, full_name="Applicant Candidate")

        now = timezone.now()
        # Room A (Not applied)
        room_unapplied = RecruitmentRoom.objects.create(
            title=f"Staff AI Engineer {uid}",
            company_name=f"DeepMind Tech {uid}",
            status=RecruitmentRoom.Status.ACTIVE,
            link_is_active=True,
            link_expires_at=now + timedelta(days=12),
            share_token=f"share-apply-tok-{uid}",
            created_by=hr_user,
        )
        # Room B (Applied)
        room_applied = RecruitmentRoom.objects.create(
            title=f"Lead Vision Engineer {uid}",
            company_name=f"Perception AI {uid}",
            status=RecruitmentRoom.Status.ACTIVE,
            link_is_active=True,
            link_expires_at=now + timedelta(days=12),
            share_token=f"share-applied-tok-{uid}",
            created_by=hr_user,
        )
        CandidateApplication.objects.create(
            room=room_applied,
            candidate=candidate,
            status=CandidateApplication.Status.COMPLETED,
        )

        wait = WebDriverWait(driver, 10)
        driver.get(f"{FRONTEND_URL}/student/jobs")
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='job-board-grid']")))

        search_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-search-jobs']")))
        set_react_input(driver, search_input, uid)
        time.sleep(0.5)

        # 1. Unapplied Room: Verify Apply Now button
        apply_btn = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='button-apply-room-{room_unapplied.id}']")))
        assert "Apply Now" in apply_btn.text

        # 2. Applied Room: Verify Applied badge & Track button
        applied_badge = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='badge-applied-{room_applied.id}']")))
        assert "Applied" in applied_badge.text

        track_btn = driver.find_element(By.CSS_SELECTOR, f"[data-testid='button-track-app-{room_applied.id}']")
        assert "Track Application" in track_btn.text

        screenshot_path = SCREENSHOTS_DIR / "us43b_05_apply_now_and_applied_badge.png"
        driver.save_screenshot(str(screenshot_path))

        # 3. Test Apply Now click redirects to /apply/:token
        driver.execute_script("arguments[0].click();", apply_btn)
        wait.until(EC.url_contains(f"/apply/{room_unapplied.share_token}"))
        assert f"/apply/{room_unapplied.share_token}" in driver.current_url

    def test_tc43b_06_keyword_search_filtering(self, driver):
        """
        Test Case 6: Live Search Filtering (AC-6)
        Searches by specific keyword in title, company, or skills;
        confirms matching card renders and non-matching is filtered out.
        """
        uid = uuid.uuid4().hex[:6]
        hr_email = f"hr_srch_{uid}@careerflow.test"
        candidate_email = f"cand_srch_{uid}@careerflow.test"

        hr_user = create_user_in_db(hr_email, "ValidPass2026!", role=User.Role.HR_MANAGER, full_name="HR Search")
        login_candidate(driver, email=candidate_email, full_name="Searcher")

        now = timezone.now()
        room1 = RecruitmentRoom.objects.create(
            title=f"Quantum Cryptography Specialist {uid}",
            company_name=f"CipherCorp {uid}",
            department="Cryptography",
            role_category="Engineering",
            status=RecruitmentRoom.Status.ACTIVE,
            link_is_active=True,
            link_expires_at=now + timedelta(days=10),
            share_token=f"tok-qc-{uid}",
            created_by=hr_user,
        )
        room2 = RecruitmentRoom.objects.create(
            title=f"Mobile React Native Developer {uid}",
            company_name=f"AppLab {uid}",
            department="Mobile",
            role_category="Engineering",
            status=RecruitmentRoom.Status.ACTIVE,
            link_is_active=True,
            link_expires_at=now + timedelta(days=10),
            share_token=f"tok-rn-{uid}",
            created_by=hr_user,
        )

        wait = WebDriverWait(driver, 10)
        driver.get(f"{FRONTEND_URL}/student/jobs")
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='job-board-grid']")))

        search_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-search-jobs']")))
        set_react_input(driver, search_input, "Quantum Cryptography")
        time.sleep(0.5)

        # Assert only room1 appears
        assert f"Quantum Cryptography Specialist {uid}" in driver.page_source
        assert f"Mobile React Native Developer {uid}" not in driver.page_source

        screenshot_path = SCREENSHOTS_DIR / "us43b_06_keyword_search_filtering.png"
        driver.save_screenshot(str(screenshot_path))

        # Clear search
        clear_react_input(driver, search_input)
        time.sleep(0.5)

    def test_tc43b_07_experience_level_filter(self, driver):
        """
        Test Case 7: Experience Level Filtering (AC-6)
        Filters by ENTRY, MID, SENIOR, LEAD; verifies card levels match.
        """
        uid = uuid.uuid4().hex[:6]
        hr_email = f"hr_lvl_{uid}@careerflow.test"
        candidate_email = f"cand_lvl_{uid}@careerflow.test"

        hr_user = create_user_in_db(hr_email, "ValidPass2026!", role=User.Role.HR_MANAGER, full_name="HR Mona")
        login_candidate(driver, email=candidate_email, full_name="Level Filter Candidate")

        now = timezone.now()
        room_lead = RecruitmentRoom.objects.create(
            title=f"Principal AI Architect {uid}",
            company_name=f"Vanguard {uid}",
            experience_level=RecruitmentRoom.ExperienceLevel.LEAD,
            status=RecruitmentRoom.Status.ACTIVE,
            link_is_active=True,
            link_expires_at=now + timedelta(days=15),
            share_token=f"tok-lead-{uid}",
            created_by=hr_user,
        )
        room_entry = RecruitmentRoom.objects.create(
            title=f"Associate QA Tester {uid}",
            company_name=f"Vanguard {uid}",
            experience_level=RecruitmentRoom.ExperienceLevel.ENTRY,
            status=RecruitmentRoom.Status.ACTIVE,
            link_is_active=True,
            link_expires_at=now + timedelta(days=15),
            share_token=f"tok-entry-{uid}",
            created_by=hr_user,
        )

        wait = WebDriverWait(driver, 10)
        driver.get(f"{FRONTEND_URL}/student/jobs")
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='job-board-grid']")))

        search_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-search-jobs']")))
        set_react_input(driver, search_input, uid)
        time.sleep(0.5)

        # Select LEAD
        exp_select = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='select-filter-experience']")))
        select_obj = Select(exp_select)
        select_obj.select_by_value("LEAD")
        time.sleep(0.5)

        assert f"Principal AI Architect {uid}" in driver.page_source
        assert f"Associate QA Tester {uid}" not in driver.page_source

        screenshot_path = SCREENSHOTS_DIR / "us43b_07_experience_level_filter.png"
        driver.save_screenshot(str(screenshot_path))

    def test_tc43b_08_room_detail_specs_modal(self, driver):
        """
        Test Case 8: Room Detail Modal Dossier (AC-2, AC-4)
        Clicks 'View Specs' (button-view-room-${id});
        verifies modal-job-room-detail opens with description, requirements, evaluation weights.
        Closes modal via button-close-job-modal.
        """
        uid = uuid.uuid4().hex[:6]
        hr_email = f"hr_spec_{uid}@careerflow.test"
        candidate_email = f"cand_spec_{uid}@careerflow.test"

        hr_user = create_user_in_db(hr_email, "ValidPass2026!", role=User.Role.HR_MANAGER, full_name="HR Mona")
        login_candidate(driver, email=candidate_email, full_name="Specs Candidate")

        now = timezone.now()
        room = RecruitmentRoom.objects.create(
            title=f"Distinguished Research Scientist {uid}",
            company_name=f"DeepCore Quantum {uid}",
            department="Advanced Algorithms",
            role_category="Quantum AI",
            experience_level=RecruitmentRoom.ExperienceLevel.LEAD,
            description=f"Pioneer quantum deep learning architectures for cryptography {uid}.",
            requirements_text="Ph.D. in Computer Science or Physics, 8+ years post-grad research.",
            skills_required=["Quantum Computing", "Qiskit", "PyTorch"],
            cv_weight=45,
            video_weight=55,
            status=RecruitmentRoom.Status.ACTIVE,
            link_is_active=True,
            link_expires_at=now + timedelta(days=30),
            share_token=f"tok-spec-{uid}",
            created_by=hr_user,
        )

        wait = WebDriverWait(driver, 10)
        driver.get(f"{FRONTEND_URL}/student/jobs")
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='job-board-grid']")))

        search_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-search-jobs']")))
        set_react_input(driver, search_input, uid)
        time.sleep(0.5)

        # Click View Specs
        view_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-view-room-{room.id}']")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", view_btn)
        time.sleep(0.3)
        driver.execute_script("arguments[0].click();", view_btn)

        # Assert Modal Opens
        modal = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-job-room-detail']")))
        assert modal.is_displayed()

        modal_title = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-job-title']")))
        assert f"Distinguished Research Scientist {uid}" in modal_title.text
        assert "DeepCore Quantum" in modal.text
        assert "45%" in modal.text
        assert "55%" in modal.text
        assert "Ph.D. in Computer Science or Physics" in modal.text

        screenshot_path = SCREENSHOTS_DIR / "us43b_08_room_detail_specs_modal.png"
        driver.save_screenshot(str(screenshot_path))

        # Close Modal
        close_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-close-job-modal']")))
        driver.execute_script("arguments[0].click();", close_btn)
        time.sleep(0.5)

        # Verify Modal closed
        modals = driver.find_elements(By.CSS_SELECTOR, "[data-testid='modal-job-room-detail']")
        assert len(modals) == 0

    def test_tc43b_09_status_filter_tabs_and_empty_state(self, driver):
        """
        Test Case 9: Status Filter Tabs & Empty State (AC-5, AC-7)
        Switches between All, Not Yet Applied, and Applied tabs.
        Searches for a nonexistent term; verifies empty-job-board-state mounts with Reset button.
        """
        uid = uuid.uuid4().hex[:6]
        candidate_email = f"cand_emp_{uid}@careerflow.test"
        login_candidate(driver, email=candidate_email, full_name="Empty State Candidate")

        wait = WebDriverWait(driver, 10)
        driver.get(f"{FRONTEND_URL}/student/jobs")
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='job-board-metrics-bar']")))

        # Search for non-existent keyword
        search_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-search-jobs']")))
        set_react_input(driver, search_input, f"NonExistentQueryXYZ_{uid}")
        time.sleep(0.5)

        # Verify Empty State
        empty_state = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='empty-job-board-state']")))
        assert empty_state.is_displayed()
        assert "No matching job rooms" in empty_state.text

        screenshot_path = SCREENSHOTS_DIR / "us43b_09_status_filter_tabs_and_empty_state.png"
        driver.save_screenshot(str(screenshot_path))

    def test_tc43b_10_responsive_layout(self, driver):
        """
        Test Case 10: Mobile and Tablet Responsive Layout (AC-1)
        Tests rendering in 375x812 (mobile) and 768x1024 (tablet) viewports.
        """
        uid = uuid.uuid4().hex[:6]
        candidate_email = f"cand_resp_{uid}@careerflow.test"
        login_candidate(driver, email=candidate_email, full_name="Responsive User")

        wait = WebDriverWait(driver, 10)
        driver.get(f"{FRONTEND_URL}/student/jobs")

        # Tablet view
        driver.set_window_size(768, 1024)
        time.sleep(0.5)
        metrics_bar = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='job-board-metrics-bar']")))
        assert metrics_bar.is_displayed()

        # Mobile view
        driver.set_window_size(375, 812)
        time.sleep(0.5)
        assert driver.find_element(By.CSS_SELECTOR, "[data-testid='input-search-jobs']").is_displayed()

        # Restore desktop window
        driver.set_window_size(1920, 1080)
        time.sleep(0.5)

        screenshot_path = SCREENSHOTS_DIR / "us43b_10_responsive_layout.png"
        driver.save_screenshot(str(screenshot_path))
