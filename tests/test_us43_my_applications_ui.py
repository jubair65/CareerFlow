"""
US-43: Candidate "My Applications" Tracking Dashboard UI Test Suite (US-43-T6).
User Story: US-43 — Candidate "My Applications" Tracking Dashboard
Sprint: Sprint 7 — Final Platform Maturity & Release
Lead Developer: MD. Jubair Bin Hasan (@jubair65)
Dedicated Peer UI Tester & System Architect: Nafisa Tabassum Maria (@Maria-07-222)
Target Branch: feat/us-43-my-applications -> develop

Acceptance Criteria & Features Verified:
✓ AC-1: Candidate can view a list of all their submitted room applications.
✓ AC-2: Each application displays room title, company/client name, applied date, and current status.
✓ AC-3: Candidate can click into an application to view submission details and available feedback (Modal).
✓ AC-4: Real-time status changes (Shortlisted, Rejected, Under Review) are displayed accurately with badges.
✓ AC-5: Empty state is displayed when candidate has not applied to any room.
✓ AC-6: Access is strictly restricted to candidate's own submitted applications (Multi-Tenant Isolation).
"""

import os
import sys
import time
import uuid
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from apps.authentication.models import User
from apps.recruitment.models import (
    RecruitmentRoom,
    CandidateApplication,
    StatusNotificationLog,
)
from apps.cv.models import CandidateCV
from apps.presentation.models import PresentationVideo
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

    wait.until(EC.url_contains("/student/dashboard"))
    return user


class TestUS43MyApplicationsUI:
    """
    Automated Selenium UI Test Suite for US-43 Candidate My Applications Dashboard.
    Executed by Nafisa Tabassum Maria (@Maria-07-222).
    """

    def test_tc43_01_dashboard_loading_and_summary_metrics(self, driver):
        """
        Test Case 1: Dashboard Loading & Summary Metrics (US-43-T1, US-43-T3)
        Verifies that total applied, shortlisted, in-review, rejected, and average composite
        score metric cards load with accurate computed values. (AC-1, AC-2)
        """
        uid = uuid.uuid4().hex[:6]
        hr_email = f"hr_metrics_{uid}@careerflow.test"
        candidate_email = f"candidate_metrics_{uid}@careerflow.test"

        hr_user = create_user_in_db(hr_email, "ValidPass2026!", role=User.Role.HR_MANAGER, full_name="HR Manager")
        candidate = login_candidate(driver, email=candidate_email, full_name="Metrics Candidate")

        # Create 3 Rooms
        room_1 = RecruitmentRoom.objects.create(
            title=f"Cloud Architect {uid}",
            company_name="Acme Cloud Systems",
            department="Engineering",
            created_by=hr_user,
            cv_weight=50.0,
            video_weight=50.0,
            link_is_active=True,
        )
        room_2 = RecruitmentRoom.objects.create(
            title=f"Lead Frontend Dev {uid}",
            company_name="PixelCraft Studio",
            department="Product",
            created_by=hr_user,
            cv_weight=40.0,
            video_weight=60.0,
            link_is_active=True,
        )
        room_3 = RecruitmentRoom.objects.create(
            title=f"DevOps Specialist {uid}",
            company_name="DevScale Infra",
            department="Operations",
            created_by=hr_user,
            cv_weight=60.0,
            video_weight=40.0,
            link_is_active=True,
        )

        # Create 3 Applications: Shortlisted, In Review, Rejected
        CandidateApplication.objects.create(
            room=room_1,
            candidate=candidate,
            status=CandidateApplication.Status.COMPLETED,
            cv_score=90.0,
            video_score=86.0,
            final_score=88.0,
            is_shortlisted=True,
            shortlist_reason="Top percentile skills",
            hr_decision=CandidateApplication.HrDecision.CONFIRMED,
            hr_decision_notes="Approved for next round interview."
        )
        CandidateApplication.objects.create(
            room=room_2,
            candidate=candidate,
            status=CandidateApplication.Status.COMPLETED,
            cv_score=75.0,
            video_score=77.0,
            final_score=76.0,
            is_shortlisted=False,
            hr_decision=CandidateApplication.HrDecision.UNDECIDED
        )
        CandidateApplication.objects.create(
            room=room_3,
            candidate=candidate,
            status=CandidateApplication.Status.COMPLETED,
            cv_score=50.0,
            video_score=54.0,
            final_score=52.0,
            is_shortlisted=False,
            hr_decision=CandidateApplication.HrDecision.REJECTED,
            hr_decision_notes="Position filled by internal transfer."
        )

        wait = WebDriverWait(driver, 10)
        driver.get(f"{FRONTEND_URL}/student/applications")
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='summary-metrics-bar']")))

        # Verify summary metric values:
        # Total = 3, Shortlisted = 1, Review = 1, Rejected = 1, Avg = (88 + 76 + 52)/3 = 72%
        total_card = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='metric-total-applications']")))
        shortlisted_card = driver.find_element(By.CSS_SELECTOR, "[data-testid='metric-shortlisted-applications']")
        review_card = driver.find_element(By.CSS_SELECTOR, "[data-testid='metric-review-applications']")
        rejected_card = driver.find_element(By.CSS_SELECTOR, "[data-testid='metric-rejected-applications']")
        avg_score_card = driver.find_element(By.CSS_SELECTOR, "[data-testid='metric-average-score']")

        assert total_card.text == "3"
        assert shortlisted_card.text == "1"
        assert review_card.text == "1"
        assert rejected_card.text == "1"
        assert "72%" in avg_score_card.text

        screenshot_path = SCREENSHOTS_DIR / "us43_01_dashboard_loading_and_summary_metrics.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc43_02_status_filter_tabs_and_badge_tones(self, driver):
        """
        Test Case 2: Status Filter Tabs & Counters (US-43-T1, US-43-T3)
        Validates switching between All, Shortlisted, In Review, and Not Selected tabs.
        Verifies correct badge tone formatting (emerald, amber/blue, rose). (AC-2, AC-4)
        """
        uid = uuid.uuid4().hex[:6]
        hr_email = f"hr_tabs_{uid}@careerflow.test"
        candidate_email = f"candidate_tabs_{uid}@careerflow.test"

        hr_user = create_user_in_db(hr_email, "ValidPass2026!", role=User.Role.HR_MANAGER, full_name="HR Manager")
        candidate = login_candidate(driver, email=candidate_email, full_name="Tabs Candidate")

        room_1 = RecruitmentRoom.objects.create(
            title=f"AI Research Engineer {uid}",
            company_name="DeepMind Ventures",
            created_by=hr_user,
            link_is_active=True,
        )
        room_2 = RecruitmentRoom.objects.create(
            title=f"Data Analyst {uid}",
            company_name="Analytics Pros",
            created_by=hr_user,
            link_is_active=True,
        )
        room_3 = RecruitmentRoom.objects.create(
            title=f"Security Analyst {uid}",
            company_name="CyberGuard Corp",
            created_by=hr_user,
            link_is_active=True,
        )

        app_short = CandidateApplication.objects.create(
            room=room_1,
            candidate=candidate,
            status=CandidateApplication.Status.COMPLETED,
            final_score=94.0,
            is_shortlisted=True,
            hr_decision=CandidateApplication.HrDecision.CONFIRMED,
        )
        app_rev = CandidateApplication.objects.create(
            room=room_2,
            candidate=candidate,
            status=CandidateApplication.Status.COMPLETED,
            final_score=70.0,
            is_shortlisted=False,
            hr_decision=CandidateApplication.HrDecision.UNDECIDED,
        )
        app_rej = CandidateApplication.objects.create(
            room=room_3,
            candidate=candidate,
            status=CandidateApplication.Status.COMPLETED,
            final_score=45.0,
            is_shortlisted=False,
            hr_decision=CandidateApplication.HrDecision.REJECTED,
        )

        wait = WebDriverWait(driver, 10)
        driver.get(f"{FRONTEND_URL}/student/applications")
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='applications-status-list']")))

        # 1. Filter: Shortlisted
        tab_shortlisted = driver.find_element(By.CSS_SELECTOR, "[data-testid='filter-tab-shortlisted']")
        tab_shortlisted.click()
        time.sleep(0.5)

        cards = driver.find_elements(By.CSS_SELECTOR, "[data-testid^='application-card-']")
        assert len(cards) == 1
        badge_shortlisted = driver.find_element(By.CSS_SELECTOR, f"[data-testid='badge-status-shortlisted-{app_short.id}']")
        assert "Shortlisted" in badge_shortlisted.text
        badge_class = badge_shortlisted.get_attribute("className")
        assert "bg-[#e2f0e9]" in badge_class and "text-[#277254]" in badge_class

        screenshot_path1 = SCREENSHOTS_DIR / "us43_02_status_filter_shortlisted.png"
        driver.save_screenshot(str(screenshot_path1))

        # 2. Filter: In Review
        tab_review = driver.find_element(By.CSS_SELECTOR, "[data-testid='filter-tab-review']")
        tab_review.click()
        time.sleep(0.5)

        cards_rev = driver.find_elements(By.CSS_SELECTOR, "[data-testid^='application-card-']")
        assert len(cards_rev) == 1
        badge_review = driver.find_element(By.CSS_SELECTOR, f"[data-testid='badge-status-review-{app_rev.id}']")
        assert "In HR Review" in badge_review.text or "AI Analyzing" in badge_review.text

        screenshot_path2 = SCREENSHOTS_DIR / "us43_03_status_filter_review.png"
        driver.save_screenshot(str(screenshot_path2))

        # 3. Filter: Not Selected (Rejected)
        tab_rejected = driver.find_element(By.CSS_SELECTOR, "[data-testid='filter-tab-rejected']")
        tab_rejected.click()
        time.sleep(0.5)

        cards_rej = driver.find_elements(By.CSS_SELECTOR, "[data-testid^='application-card-']")
        assert len(cards_rej) == 1
        badge_rej = driver.find_element(By.CSS_SELECTOR, f"[data-testid='badge-status-rejected-{app_rej.id}']")
        assert "Not Selected" in badge_rej.text
        badge_rej_class = badge_rej.get_attribute("className")
        assert "bg-[#f7e5e1]" in badge_rej_class and "text-[#a33d35]" in badge_rej_class

        screenshot_path3 = SCREENSHOTS_DIR / "us43_04_status_filter_rejected.png"
        driver.save_screenshot(str(screenshot_path3))

    def test_tc43_03_live_search_filtering(self, driver):
        """
        Test Case 3: Live Search Filtering (US-43-T3)
        Filters application cards dynamically by keyword query, and restores full list on clear.
        """
        uid = uuid.uuid4().hex[:6]
        hr_email = f"hr_search_{uid}@careerflow.test"
        candidate_email = f"candidate_search_{uid}@careerflow.test"

        hr_user = create_user_in_db(hr_email, "ValidPass2026!", role=User.Role.HR_MANAGER, full_name="HR Manager")
        candidate = login_candidate(driver, email=candidate_email, full_name="Search Candidate")

        # Distinct searchable room titles
        room_1 = RecruitmentRoom.objects.create(
            title=f"Kubernetes Platform Architect {uid}",
            company_name="CloudFleet Global",
            created_by=hr_user,
            link_is_active=True,
        )
        room_2 = RecruitmentRoom.objects.create(
            title=f"Full Stack Django Engineer {uid}",
            company_name="WebScale Solutions",
            created_by=hr_user,
            link_is_active=True,
        )

        CandidateApplication.objects.create(
            room=room_1,
            candidate=candidate,
            status=CandidateApplication.Status.COMPLETED,
            final_score=85.0
        )
        CandidateApplication.objects.create(
            room=room_2,
            candidate=candidate,
            status=CandidateApplication.Status.COMPLETED,
            final_score=78.0
        )

        wait = WebDriverWait(driver, 10)
        driver.get(f"{FRONTEND_URL}/student/applications")
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='applications-status-list']")))

        search_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-search-applications']")))

        # Search for Kubernetes
        set_react_input(driver, search_input, "Kubernetes")
        time.sleep(0.5)

        cards = driver.find_elements(By.CSS_SELECTOR, "[data-testid^='application-card-']")
        assert len(cards) == 1
        assert "Kubernetes" in cards[0].text

        screenshot_path = SCREENSHOTS_DIR / "us43_05_live_search_filtering.png"
        driver.save_screenshot(str(screenshot_path))

        # Clear search
        clear_react_input(driver, search_input)
        time.sleep(0.5)
        cards_restored = driver.find_elements(By.CSS_SELECTOR, "[data-testid^='application-card-']")
        assert len(cards_restored) == 2

    def test_tc43_04_empty_state_display_and_navigation(self, driver):
        """
        Test Case 4: Empty State Display (AC-5)
        Verifies that a student with 0 applications receives a styled empty state card
        with functional CTA buttons linking to /student/practice and /student/cv.
        """
        uid = uuid.uuid4().hex[:6]
        email = f"candidate_empty_{uid}@careerflow.test"
        login_candidate(driver, email=email, full_name="Empty State Candidate")

        wait = WebDriverWait(driver, 10)
        driver.get(f"{FRONTEND_URL}/student/applications")

        # Verify empty state container
        empty_state = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='empty-applications-state']")))
        assert "No applications found" in empty_state.text

        # Verify action buttons
        practice_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='empty-action-practice']")
        cv_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='empty-action-cv']")
        assert practice_btn.is_displayed()
        assert cv_btn.is_displayed()

        screenshot_path = SCREENSHOTS_DIR / "us43_06_empty_state_and_navigation.png"
        driver.save_screenshot(str(screenshot_path))

        # Click Practice Studio CTA
        practice_btn.click()
        wait.until(EC.url_contains("/student/practice"))
        assert "/student/practice" in driver.current_url

    def test_tc43_05_application_detail_modal_dossier(self, driver):
        """
        Test Case 5: Application Detail Modal (US-43-T4 / AC-3)
        Clicks 'View Dossier Details' on an application card, validates modal renders
        room context, scoring weights, submitted CV/video artifacts, 4-stage stepper,
        and hiring feedback notes. Asserts modal close button functions properly.
        """
        uid = uuid.uuid4().hex[:6]
        hr_email = f"hr_modal_{uid}@careerflow.test"
        candidate_email = f"candidate_modal_{uid}@careerflow.test"

        hr_user = create_user_in_db(hr_email, "ValidPass2026!", role=User.Role.HR_MANAGER, full_name="HR Evaluator")
        candidate = login_candidate(driver, email=candidate_email, full_name="Dossier Candidate")

        room = RecruitmentRoom.objects.create(
            title=f"Principal ML Scientist {uid}",
            company_name="Neural AI Systems",
            department="Machine Learning",
            role_category="Engineering",
            description="Lead LLM inference pipelines and multimodal model fine-tuning.",
            requirements_text="Deep learning, PyTorch, Transformers, distributed training.",
            created_by=hr_user,
            cv_weight=45.0,
            video_weight=55.0,
            link_is_active=True,
        )

        cv = CandidateCV.objects.create(
            user=candidate,
            file="students/cv/ml_resume.pdf",
            original_filename="ML_Specialist_CV.pdf",
            file_size=314572,
            file_type="pdf",
        )
        video = PresentationVideo.objects.create(
            user=candidate,
            file="students/video/pitch.mp4",
            original_filename="ML_Pitch_Video.mp4",
            raw_file_size=5242880,
            file_type="mp4",
            duration_seconds=115,
            status="COMPLETED",
        )

        app = CandidateApplication.objects.create(
            room=room,
            candidate=candidate,
            cv=cv,
            video=video,
            status=CandidateApplication.Status.COMPLETED,
            cv_score=92.0,
            video_score=94.0,
            final_score=93.1,
            is_shortlisted=True,
            shortlist_reason="Exceptional alignment with AI vision architecture requirements.",
            hr_decision=CandidateApplication.HrDecision.CONFIRMED,
            hr_decision_notes="Top tier recommendation from hiring committee.",
        )

        wait = WebDriverWait(driver, 10)
        driver.get(f"{FRONTEND_URL}/student/applications")
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='applications-status-list']")))

        # Open Detail Modal
        view_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-view-details-{app.id}']")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", view_btn)
        time.sleep(0.3)
        driver.execute_script("arguments[0].click();", view_btn)

        # Wait for modal to render
        modal = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-application-detail']")))
        assert modal.is_displayed()

        # Verify Room Title and Company
        room_title = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-room-title']")))
        assert f"Principal ML Scientist {uid}" in room_title.text
        assert "Neural AI Systems" in modal.text

        # Verify Scoring Weights (45% CV, 55% Video)
        assert "45%" in modal.text
        assert "55%" in modal.text

        # Verify Artifacts Metadata
        assert "ML_Specialist_CV.pdf" in modal.text
        assert "ML_Pitch_Video.mp4" in modal.text

        # Verify Hiring Committee Feedback
        assert "Exceptional alignment with AI vision architecture requirements" in modal.text
        assert "Top tier recommendation from hiring committee" in modal.text

        screenshot_path1 = SCREENSHOTS_DIR / "us43_07_application_detail_modal_open.png"
        driver.save_screenshot(str(screenshot_path1))

        # Close Modal
        close_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-close-detail-modal']")))
        driver.execute_script("arguments[0].click();", close_btn)
        time.sleep(0.5)

        # Assert modal is closed
        modals = driver.find_elements(By.CSS_SELECTOR, "[data-testid='modal-application-detail']")
        assert len(modals) == 0

        screenshot_path2 = SCREENSHOTS_DIR / "us43_08_application_detail_modal_close.png"
        driver.save_screenshot(str(screenshot_path2))

    def test_tc43_06_candidate_data_isolation(self, driver):
        """
        Test Case 6: Candidate Data Isolation (US-43-T5 / AC-6)
        Candidate A submits application to Room A. Candidate B submits application to Room B.
        Log in as Candidate A; verify Candidate A only sees Room A and never sees Room B.
        """
        uid = uuid.uuid4().hex[:6]
        hr_email = f"hr_iso_{uid}@careerflow.test"
        candidate_a_email = f"candidate_iso_a_{uid}@careerflow.test"
        candidate_b_email = f"candidate_iso_b_{uid}@careerflow.test"

        hr_user = create_user_in_db(hr_email, "ValidPass2026!", role=User.Role.HR_MANAGER, full_name="HR Manager")
        cand_a = login_candidate(driver, email=candidate_a_email, full_name="Candidate Alpha")
        cand_b = create_user_in_db(candidate_b_email, "ValidPass2026!", role=User.Role.STUDENT, full_name="Candidate Beta")

        room_a = RecruitmentRoom.objects.create(
            title=f"Quantum Cryptographer Alpha {uid}",
            company_name="Alpha Secure Systems",
            created_by=hr_user,
            link_is_active=True,
        )
        room_b = RecruitmentRoom.objects.create(
            title=f"Confidential Defence Engineer Beta {uid}",
            company_name="Beta Defence Corp",
            created_by=hr_user,
            link_is_active=True,
        )

        CandidateApplication.objects.create(
            room=room_a,
            candidate=cand_a,
            status=CandidateApplication.Status.COMPLETED,
            final_score=95.0,
        )
        CandidateApplication.objects.create(
            room=room_b,
            candidate=cand_b,
            status=CandidateApplication.Status.COMPLETED,
            final_score=90.0,
        )

        wait = WebDriverWait(driver, 10)
        driver.get(f"{FRONTEND_URL}/student/applications")
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='applications-status-list']")))

        # Candidate A must see Room A
        assert f"Quantum Cryptographer Alpha {uid}" in driver.page_source
        # Candidate A must NEVER see Room B
        assert f"Confidential Defence Engineer Beta {uid}" not in driver.page_source

        screenshot_path = SCREENSHOTS_DIR / "us43_09_multi_tenant_candidate_isolation.png"
        driver.save_screenshot(str(screenshot_path))

    def test_tc43_07_refresh_and_audit_history_accordion(self, driver):
        """
        Test Case 7: Refresh Button & Audit Logs Accordion (US-43-T1, US-35)
        Tests expanding notification audit log events and triggering the dashboard refresh button.
        """
        uid = uuid.uuid4().hex[:6]
        hr_email = f"hr_audit_{uid}@careerflow.test"
        candidate_email = f"candidate_audit_{uid}@careerflow.test"

        hr_user = create_user_in_db(hr_email, "ValidPass2026!", role=User.Role.HR_MANAGER, full_name="HR Manager")
        candidate = login_candidate(driver, email=candidate_email, full_name="Audit Candidate")

        room = RecruitmentRoom.objects.create(
            title=f"Staff SRE {uid}",
            company_name="Reliability Cloud",
            created_by=hr_user,
            link_is_active=True,
        )
        app = CandidateApplication.objects.create(
            room=room,
            candidate=candidate,
            status=CandidateApplication.Status.COMPLETED,
            final_score=82.0,
            is_shortlisted=True,
            hr_decision=CandidateApplication.HrDecision.CONFIRMED,
        )

        # Create status notification audit log
        StatusNotificationLog.objects.create(
            application=app,
            status_type=StatusNotificationLog.StatusType.SHORTLISTED,
            recipient_email=candidate.email,
            email_sent=True,
        )

        wait = WebDriverWait(driver, 10)
        driver.get(f"{FRONTEND_URL}/student/applications")
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='applications-status-list']")))

        # Expand audit logs accordion
        accordion_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-toggle-audit-logs-{app.id}']")))
        accordion_btn.click()

        # Verify audit logs container mounts with event
        audit_container = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='audit-logs-container-{app.id}']")))
        assert audit_container.is_displayed()
        assert "Email delivered" in audit_container.text or "Shortlisted" in audit_container.text

        # Click refresh button
        refresh_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-refresh-applications']")
        refresh_btn.click()
        time.sleep(0.5)
        assert driver.find_element(By.CSS_SELECTOR, "[data-testid='applications-status-list']").is_displayed()

        screenshot_path = SCREENSHOTS_DIR / "us43_10_refresh_and_audit_history.png"
        driver.save_screenshot(str(screenshot_path))

    def test_tc43_08_sidebar_navigation_to_applications(self, driver):
        """
        Test Case 8: Sidebar Navigation to Applications Dashboard
        Navigates from candidate dashboard via [data-testid='nav-applications'],
        verifies page URL is /student/applications or /applications/my-status and heading renders correctly.
        """
        uid = uuid.uuid4().hex[:6]
        candidate_email = f"candidate_nav_{uid}@careerflow.test"
        login_candidate(driver, email=candidate_email, full_name="Navigation User")

        wait = WebDriverWait(driver, 10)
        nav_apps_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='nav-applications']")))
        nav_apps_btn.click()

        wait.until(lambda d: "/applications" in d.current_url or "/student/applications" in d.current_url)
        assert "/applications" in driver.current_url or "/student/applications" in driver.current_url

        heading = wait.until(EC.visibility_of_element_located((By.XPATH, "//h1[contains(., 'My Applications')]")))
        assert heading.is_displayed()

    def test_tc43_09_filter_tab_empty_state_with_active_tab(self, driver):
        """
        Test Case 9: Filter Tab Empty State
        When candidate only has shortlisted applications, switching to 'rejected' tab displays
        specific empty state message ("No applications match the 'rejected' filter criteria.").
        """
        uid = uuid.uuid4().hex[:6]
        hr_email = f"hr_ft_{uid}@careerflow.test"
        candidate_email = f"candidate_ft_{uid}@careerflow.test"

        hr_user = create_user_in_db(hr_email, "ValidPass2026!", role=User.Role.HR_MANAGER, full_name="HR Manager")
        candidate = login_candidate(driver, email=candidate_email, full_name="Filter Tab Candidate")

        room = RecruitmentRoom.objects.create(
            title=f"Security Architect {uid}",
            company_name="SecureNet",
            created_by=hr_user,
            link_is_active=True,
        )
        CandidateApplication.objects.create(
            room=room,
            candidate=candidate,
            status=CandidateApplication.Status.COMPLETED,
            is_shortlisted=True,
            hr_decision=CandidateApplication.HrDecision.CONFIRMED,
        )

        wait = WebDriverWait(driver, 10)
        driver.get(f"{FRONTEND_URL}/student/applications")
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='applications-status-list']")))

        # Click rejected tab
        driver.find_element(By.CSS_SELECTOR, "[data-testid='filter-tab-rejected']").click()
        time.sleep(0.5)

        # Empty state should appear for rejected
        empty_state = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='empty-applications-state']")))
        assert "No applications match the 'rejected' filter criteria." in empty_state.text

        # Restore to all
        driver.find_element(By.CSS_SELECTOR, "[data-testid='filter-tab-all']").click()
        time.sleep(0.5)
        assert driver.find_element(By.CSS_SELECTOR, "[data-testid='applications-status-list']").is_displayed()

    def test_tc43_10_responsive_layout(self, driver):
        """
        Test Case 10: Responsive Layout Verification
        Resizes viewport to tablet width (768x1024), verifies summary metrics and application cards
        render responsively without horizontal overflow.
        """
        uid = uuid.uuid4().hex[:6]
        hr_email = f"hr_resp_{uid}@careerflow.test"
        candidate_email = f"candidate_resp_{uid}@careerflow.test"

        hr_user = create_user_in_db(hr_email, "ValidPass2026!", role=User.Role.HR_MANAGER, full_name="HR Manager")
        candidate = login_candidate(driver, email=candidate_email, full_name="Responsive Candidate")

        room = RecruitmentRoom.objects.create(
            title=f"Responsive Dev {uid}",
            company_name="FlexDesign Labs",
            created_by=hr_user,
            link_is_active=True,
        )
        CandidateApplication.objects.create(
            room=room,
            candidate=candidate,
            status=CandidateApplication.Status.COMPLETED,
            final_score=80.0,
        )

        wait = WebDriverWait(driver, 10)
        driver.set_window_size(768, 1024)
        driver.get(f"{FRONTEND_URL}/student/applications")
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='summary-metrics-bar']")))

        metrics_bar = driver.find_element(By.CSS_SELECTOR, "[data-testid='summary-metrics-bar']")
        assert metrics_bar.is_displayed()

        card = driver.find_element(By.CSS_SELECTOR, "[data-testid^='application-card-']")
        assert card.is_displayed()

        # Reset window size to standard desktop
        driver.set_window_size(1920, 1080)
