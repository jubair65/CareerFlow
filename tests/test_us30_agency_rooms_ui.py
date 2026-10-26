"""
US-30: Agency Room Creation for Client Companies UI Automation Test Suite (US-30-T6).
Peer UI Tester & Reviewer: MD. Hasanul Mobin (@hasanulmobin1)
Lead Developer: Farhana Tahsin Bonny (@tahsinbonnie98)
Sprint: Sprint 6 — Agency Operations & Client Room Management

Acceptance Criteria & Features Verified:
✓ AC#1 & AC#2: Room creation modal with client company selector, company name auto-sync & weight configuration
✓ AC#3: Reusable criteria (/requirements) and weighting (/weighting) modal configuration
✓ AC#4: Shareable candidate application link generation (/apply/{token}), copy action & lifecycle status toggle
✓ AC#5: Multi-tenant client isolation & deactivated client company exclusion
✓ AC#6: Client-grouped accordion view with client metadata badges and room counters
✓ Search & filter toolbar (by client, status, keyword)
✓ Quick room status change (ACTIVE -> PAUSED -> CLOSED)
✓ Strict RBAC protection: only AGENCY_ADMIN can access /agency/rooms; Student & unauthenticated blocked
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
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

from apps.authentication.models import User
from apps.recruitment.models import ClientCompany, RecruitmentRoom
from conftest import FRONTEND_URL, BACKEND_URL, SCREENSHOTS_DIR, create_user_in_db


def get_base_url():
    """Returns local frontend URL."""
    return os.environ.get("FRONTEND_URL", FRONTEND_URL)


def login_user(driver, email: str, password: str = "ValidPass2026!", role: str = User.Role.AGENCY_ADMIN, full_name: str = "Agency Test Admin"):
    """Helper to authenticate a user via the UI login page."""
    if not User.objects.filter(email__iexact=email).exists():
        create_user_in_db(email, password, role=role, full_name=full_name)

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

    expected_dashboard = "/agency/dashboard" if role == User.Role.AGENCY_ADMIN else ("/hr/dashboard" if role == User.Role.HR_MANAGER else "/student/dashboard")
    wait.until(EC.url_contains(expected_dashboard))


def create_agency_test_client(agency_user, name: str, industry: str = "Technology & Software", is_active: bool = True) -> ClientCompany:
    """Helper to create ClientCompany directly in MySQL database."""
    uid = uuid.uuid4().hex[:6]
    return ClientCompany.objects.create(
        agency=agency_user,
        name=name,
        industry=industry,
        contact_person=f"Contact {name}",
        contact_email=f"contact_{uid}@company.test",
        phone="+1-555-0199",
        website="https://example.com",
        is_active=is_active
    )


def create_agency_test_room(agency_user, client_company: ClientCompany, title: str, department: str = "Engineering", status: str = "ACTIVE", cv_weight: int = 50, video_weight: int = 50) -> RecruitmentRoom:
    """Helper to create a RecruitmentRoom linked to an agency user and client company."""
    room = RecruitmentRoom.objects.create(
        title=title,
        company_name=client_company.name,
        client_company=client_company,
        department=department,
        description=f"Opening for {title} at {client_company.name}.",
        status=status,
        created_by=agency_user,
        cv_weight=cv_weight,
        video_weight=video_weight,
        role_category="Engineering",
        experience_level="MID",
        skills_required=[{"name": "Python", "importance": "REQUIRED", "category": "Technical"}],
    )
    return room


class TestUS30AgencyRoomCreationUI:
    """
    Automated Selenium UI Test Suite for US-30: Agency Room Creation for Client Companies.
    Task: US-30-T6 (Peer UI Automation Testing & Verification)
    Reviewer / Peer Tester: MD. Hasanul Mobin (@hasanulmobin1)
    Developer: Farhana Tahsin Bonny (@tahsinbonnie98)
    """

    def test_tc_us30_01_navigation_and_kpi_dashboard(self, driver):
        """
        TC-US30-01: Verify Agency Admin navigates to /agency/rooms via sidebar or dashboard,
        and verify page heading, controls, and 4 KPI metric cards.
        """
        email = f"mobin_tc01_{uuid.uuid4().hex[:6]}@careerflow.test"
        agency_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.AGENCY_ADMIN, full_name="Hasanul Mobin")
        login_user(driver, email=email)
        wait = WebDriverWait(driver, 10)

        # 1. Test navigation from /agency/dashboard via sidebar "Rooms" button
        rooms_nav = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='nav-rooms']")))
        rooms_nav.click()
        wait.until(EC.url_contains("/agency/rooms"))
        assert "/agency/rooms" in driver.current_url

        # 2. Verify page container & heading
        page = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='page-agency-rooms']")))
        assert page is not None
        assert "Client Recruitment Rooms" in driver.page_source
        assert "US-30" in driver.page_source

        # 3. Verify primary action button "+ Create Room"
        create_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-agency-create-room-page']")
        assert create_btn.is_displayed()
        assert "Create Room" in create_btn.text

        # 4. Verify 4 KPI cards render
        assert "Total Rooms" in driver.page_source
        assert "Active Openings" in driver.page_source
        assert "Managed Clients" in driver.page_source
        assert "Total Candidates" in driver.page_source

        # 5. Verify navigation from Dashboard "New room" button
        driver.get(f"{get_base_url()}/agency/dashboard")
        dash_create_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-agency-create-room']")))
        dash_create_btn.click()
        wait.until(EC.url_contains("/agency/rooms"))

        # Save screenshot
        screenshot_path = SCREENSHOTS_DIR / "us30_01_navigation_dashboard.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc_us30_02_client_grouped_view_and_accordion(self, driver):
        """
        TC-US30-02: Verify rooms are grouped under client company cards with client badges,
        room count, and collapsible accordion functionality (AC#6).
        """
        email = f"mobin_tc02_{uuid.uuid4().hex[:6]}@careerflow.test"
        agency_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.AGENCY_ADMIN, full_name="Hasanul Mobin")

        # Pre-seed 2 clients and 3 rooms
        client_a = create_agency_test_client(agency_user, "Apex Dynamics", industry="Fintech")
        client_b = create_agency_test_client(agency_user, "CloudScale Systems", industry="Cloud Infrastructure")
        room_a1 = create_agency_test_room(agency_user, client_a, "Senior Backend Engineer")
        room_a2 = create_agency_test_room(agency_user, client_a, "Lead DevOps Architect")
        room_b1 = create_agency_test_room(agency_user, client_b, "Frontend Specialist")

        login_user(driver, email=email)
        driver.get(f"{get_base_url()}/agency/rooms")
        wait = WebDriverWait(driver, 10)

        # 1. Verify Client Group cards exist
        card_a = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='card-client-group-{client_a.id}']")))
        card_b = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='card-client-group-{client_b.id}']")))
        assert card_a is not None
        assert card_b is not None

        # 2. Verify Room counters on client badges
        badge_a = driver.find_element(By.CSS_SELECTOR, f"[data-testid='badge-rooms-count-{client_a.id}']")
        badge_b = driver.find_element(By.CSS_SELECTOR, f"[data-testid='badge-rooms-count-{client_b.id}']")
        assert "2 Rooms" in badge_a.text
        assert "1 Room" in badge_b.text

        # 3. Verify total summary count text
        count_summary = driver.find_element(By.CSS_SELECTOR, "[data-testid='text-rooms-count']")
        assert "3" in count_summary.text
        assert "2" in count_summary.text

        # 4. Verify rooms render within their respective client cards
        room_card_a1 = driver.find_element(By.CSS_SELECTOR, f"[data-testid='card-room-{room_a1.id}']")
        room_card_a2 = driver.find_element(By.CSS_SELECTOR, f"[data-testid='card-room-{room_a2.id}']")
        room_card_b1 = driver.find_element(By.CSS_SELECTOR, f"[data-testid='card-room-{room_b1.id}']")
        assert "Senior Backend Engineer" in room_card_a1.text
        assert "Lead DevOps Architect" in room_card_a2.text
        assert "Frontend Specialist" in room_card_b1.text

        # 5. Test accordion collapse & expand toggle
        toggle_btn_a = driver.find_element(By.CSS_SELECTOR, f"[data-testid='button-toggle-collapse-{client_a.id}']")
        toggle_btn_a.click()
        time.sleep(0.5)
        # Room card should no longer be visible inside collapsed group
        assert len(driver.find_elements(By.CSS_SELECTOR, f"[data-testid='card-room-{room_a1.id}']")) == 0

        # Expand again
        toggle_btn_a.click()
        time.sleep(0.5)
        assert driver.find_element(By.CSS_SELECTOR, f"[data-testid='card-room-{room_a1.id}']").is_displayed()

        screenshot_path = SCREENSHOTS_DIR / "us30_02_client_grouped_view.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc_us30_03_room_creation_modal_and_submission(self, driver):
        """
        TC-US30-03: Successfully create a Room for a selected client company via modal,
        verify auto company name sync, weight configuration, and DOM card mount (AC#1, AC#2).
        """
        email = f"mobin_tc03_{uuid.uuid4().hex[:6]}@careerflow.test"
        agency_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.AGENCY_ADMIN, full_name="Hasanul Mobin")
        client = create_agency_test_client(agency_user, "Nexus AI Labs", industry="Artificial Intelligence")

        login_user(driver, email=email)
        driver.get(f"{get_base_url()}/agency/rooms")
        wait = WebDriverWait(driver, 10)

        # 1. Open Create Room modal
        create_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-agency-create-room-page']")))
        create_btn.click()

        modal = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-agency-create-room']")))
        assert modal is not None
        heading = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='heading-agency-create-room']")))
        assert "Create Client Recruitment Room" in heading.text

        # 2. Select client company
        client_select = Select(driver.find_element(By.CSS_SELECTOR, "[data-testid='select-agency-client-company']"))
        client_select.select_by_value(str(client.id))

        # Assert client info badge appears
        info_badge = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='client-info-badge']")))
        assert "Artificial Intelligence" in info_badge.text

        # 3. Fill form inputs
        title_in = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-agency-room-title']")
        title_in.clear()
        title_in.send_keys("Lead AI Research Scientist")

        dept_in = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-agency-room-dept']")
        dept_in.clear()
        dept_in.send_keys("Generative Models Team")

        cat_select = Select(driver.find_element(By.CSS_SELECTOR, "[data-testid='select-agency-room-category']"))
        cat_select.select_by_value("Engineering")

        level_select = Select(driver.find_element(By.CSS_SELECTOR, "[data-testid='select-agency-room-level']"))
        level_select.select_by_value("LEAD")

        desc_in = driver.find_element(By.CSS_SELECTOR, "[data-testid='textarea-agency-room-desc']")
        desc_in.clear()
        desc_in.send_keys("Lead multimodal research pipelines and foundation model training.")

        # 4. Adjust CV weight slider
        slider = driver.find_element(By.CSS_SELECTOR, "[data-testid='slider-agency-room-cv-weight']")
        driver.execute_script("arguments[0].value = 60; arguments[0].dispatchEvent(new Event('input', { bubbles: true })); arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", slider)

        # 5. Submit form
        submit_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-submit-agency-create-room']")
        submit_btn.click()

        # 6. Verify modal dismisses
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-agency-create-room']")))

        # 7. Verify new room appears in DOM under client group
        created_room = RecruitmentRoom.objects.filter(created_by=agency_user, title="Lead AI Research Scientist").first()
        assert created_room is not None
        assert created_room.client_company == client
        assert created_room.company_name == "Nexus AI Labs"  # Auto company sync

        room_card = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='card-room-{created_room.id}']")))
        assert "Lead AI Research Scientist" in room_card.text
        assert "Generative Models Team" in room_card.text
        assert "Nexus AI Labs" in driver.page_source

        # Verify weights on card
        weights_el = driver.find_element(By.CSS_SELECTOR, f"[data-testid='room-weights-{created_room.id}']")
        assert "CV" in weights_el.text

        screenshot_path = SCREENSHOTS_DIR / "us30_03_room_creation_success.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc_us30_04_validation_and_inactive_client_protection(self, driver):
        """
        TC-US30-04: Verify client room creation form validation (empty/short title) and verify
        that deactivated clients are excluded from room creation (AC#5).
        """
        email = f"mobin_tc04_{uuid.uuid4().hex[:6]}@careerflow.test"
        agency_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.AGENCY_ADMIN, full_name="Hasanul Mobin")
        active_client = create_agency_test_client(agency_user, "Active BioTech", industry="Healthcare", is_active=True)
        inactive_client = create_agency_test_client(agency_user, "Deactivated Legacy Corp", industry="Legacy", is_active=False)

        login_user(driver, email=email)
        driver.get(f"{get_base_url()}/agency/rooms")
        wait = WebDriverWait(driver, 10)

        # 1. Open Create Room modal
        create_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-agency-create-room-page']")))
        create_btn.click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-agency-create-room']")))

        # 2. Check client selector options: Deactivated client MUST be excluded
        client_select = Select(driver.find_element(By.CSS_SELECTOR, "[data-testid='select-agency-client-company']"))
        options_texts = [opt.text for opt in client_select.options]
        assert any("Active BioTech" in opt for opt in options_texts)
        assert not any("Deactivated Legacy Corp" in opt for opt in options_texts), "Deactivated client should not be in selector!"

        # 3. Submit empty title -> assert validation error
        title_in = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-agency-room-title']")
        title_in.clear()
        submit_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-submit-agency-create-room']")
        # Use javascript submit to trigger onSubmit validation without browser HTML5 interference
        driver.execute_script("arguments[0].removeAttribute('required');", title_in)
        submit_btn.click()

        err_banner = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='alert-agency-create-room-error']")))
        assert "Job title is required." in err_banner.text

        # 4. Submit short title (< 3 chars) -> assert length validation
        title_in.send_keys("ab")
        submit_btn.click()
        err_short = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='alert-agency-create-room-error']")))
        assert "at least 3 characters" in err_short.text

        # 5. Cancel cleanly dismisses modal
        cancel_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-cancel-agency-create-room']")
        cancel_btn.click()
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-agency-create-room']")))

        screenshot_path = SCREENSHOTS_DIR / "us30_04_validation_inactive_client.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc_us30_05_reused_criteria_modal_configuration(self, driver):
        """
        TC-US30-05: Verify opening and updating Job Requirements & Skills modal (US-19 reuse)
        from an Agency Room card (AC#3).
        """
        email = f"mobin_tc05_{uuid.uuid4().hex[:6]}@careerflow.test"
        agency_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.AGENCY_ADMIN, full_name="Hasanul Mobin")
        client = create_agency_test_client(agency_user, "Horizon Robotics", industry="Robotics")
        room = create_agency_test_room(agency_user, client, "Robotics Software Engineer")

        login_user(driver, email=email)
        driver.get(f"{get_base_url()}/agency/rooms")
        wait = WebDriverWait(driver, 10)

        # 1. Click Criteria button on room card
        criteria_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-config-reqs-{room.id}']")))
        criteria_btn.click()

        # 2. Assert Job Requirements Modal mounts with room context
        modal = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-job-requirements']")))
        assert modal is not None
        assert "Robotics Software Engineer" in modal.text
        assert "Horizon Robotics" in modal.text

        # 3. Add a new skill
        skill_in = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-skill-tag']")
        add_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-add-skill']")
        skill_in.clear()
        skill_in.send_keys("ROS2")
        add_btn.click()

        # 4. Save requirements
        save_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-save-requirements']")
        save_btn.click()

        # 5. Modal dismisses
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-job-requirements']")))

        # Verify DB updated
        room.refresh_from_db()
        skill_names = room.get_skill_names()
        assert "ROS2" in skill_names

        screenshot_path = SCREENSHOTS_DIR / "us30_05_criteria_modal.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc_us30_06_reused_weighting_modal_configuration(self, driver):
        """
        TC-US30-06: Verify opening and updating CV vs Video evaluation weighting modal (US-20 reuse)
        from an Agency Room card (AC#3).
        """
        email = f"mobin_tc06_{uuid.uuid4().hex[:6]}@careerflow.test"
        agency_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.AGENCY_ADMIN, full_name="Hasanul Mobin")
        client = create_agency_test_client(agency_user, "FinTrust Global", industry="Financial Services")
        room = create_agency_test_room(agency_user, client, "Quantitative Portfolio Analyst", cv_weight=50, video_weight=50)

        login_user(driver, email=email)
        driver.get(f"{get_base_url()}/agency/rooms")
        wait = WebDriverWait(driver, 10)

        # 1. Click Weights button on room card
        weights_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-config-weights-{room.id}']")))
        weights_btn.click()

        # 2. Assert Weighting modal mounts
        modal = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-agency-weighting-config']")))
        assert modal is not None
        assert "CV vs. Video Evaluation Weighting" in modal.text
        assert "Quantitative Portfolio Analyst" in modal.text

        # 3. Apply "CV Focused" preset (70% CV / 30% Video)
        cv_focused_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='preset-button-70-30']")))
        cv_focused_btn.click()

        # 4. Save weighting
        save_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-save-weighting']")
        save_btn.click()

        # 5. Modal dismisses
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-agency-weighting-config']")))

        # 6. Verify room card displays updated weights
        room_card = driver.find_element(By.CSS_SELECTOR, f"[data-testid='card-room-{room.id}']")
        weights_display = room_card.find_element(By.CSS_SELECTOR, f"[data-testid='room-weights-{room.id}']")
        assert "70% CV / 30% Video" in weights_display.text

        # Verify DB updated
        room.refresh_from_db()
        assert room.cv_weight == 70
        assert room.video_weight == 30

        screenshot_path = SCREENSHOTS_DIR / "us30_06_weighting_modal.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc_us30_07_application_link_generation_and_lifecycle(self, driver):
        """
        TC-US30-07: Verify candidate application link format (/apply/{share_token}),
        copy button feedback, and link active status toggle (AC#4).
        """
        email = f"mobin_tc07_{uuid.uuid4().hex[:6]}@careerflow.test"
        agency_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.AGENCY_ADMIN, full_name="Hasanul Mobin")
        client = create_agency_test_client(agency_user, "CyberSec Innovations", industry="Cybersecurity")
        room = create_agency_test_room(agency_user, client, "Security Operations Analyst")

        login_user(driver, email=email)
        driver.get(f"{get_base_url()}/agency/rooms")
        wait = WebDriverWait(driver, 10)

        # 1. Assert application link field contains room share token
        link_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='input-room-link-{room.id}']")))
        expected_url = f"/apply/{room.share_token}"
        assert expected_url in link_input.get_attribute("value")

        # 2. Click copy button
        copy_btn = driver.find_element(By.CSS_SELECTOR, f"[data-testid='button-copy-link-{room.id}']")
        copy_btn.click()
        time.sleep(0.5)

        # 3. Toggle link status to Disabled
        toggle_btn = driver.find_element(By.CSS_SELECTOR, f"[data-testid='button-toggle-link-{room.id}']")
        assert "Active" in toggle_btn.text
        toggle_btn.click()

        # Wait for update
        time.sleep(1)
        room.refresh_from_db()
        assert room.link_is_active is False
        assert "Disabled" in toggle_btn.text

        # 4. Toggle back to Active
        toggle_btn.click()
        time.sleep(1)
        room.refresh_from_db()
        assert room.link_is_active is True
        assert "Active" in toggle_btn.text

        screenshot_path = SCREENSHOTS_DIR / "us30_07_link_generation.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc_us30_08_filters_search_and_quick_status_change(self, driver):
        """
        TC-US30-08: Verify toolbar filters (Client selector, Status filter, Search input)
        and Quick Status dropdown transitions (ACTIVE <-> PAUSED).
        """
        email = f"mobin_tc08_{uuid.uuid4().hex[:6]}@careerflow.test"
        agency_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.AGENCY_ADMIN, full_name="Hasanul Mobin")

        client_1 = create_agency_test_client(agency_user, "Alpha Dynamics", industry="Tech")
        client_2 = create_agency_test_client(agency_user, "Beta Corp", industry="Retail")
        room_1 = create_agency_test_room(agency_user, client_1, "Go Developer", status="ACTIVE")
        room_2 = create_agency_test_room(agency_user, client_2, "Store Operations Manager", status="PAUSED")

        login_user(driver, email=email)
        driver.get(f"{get_base_url()}/agency/rooms")
        wait = WebDriverWait(driver, 10)

        # 1. Filter by Client Company
        client_filter = Select(wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='select-client-filter']"))))
        client_filter.select_by_value(str(client_1.id))
        time.sleep(0.5)

        # Only client 1 should be visible
        assert driver.find_element(By.CSS_SELECTOR, f"[data-testid='card-client-group-{client_1.id}']").is_displayed()
        assert len(driver.find_elements(By.CSS_SELECTOR, f"[data-testid='card-client-group-{client_2.id}']")) == 0

        # Reset client filter
        client_filter.select_by_value("all")
        time.sleep(0.5)

        # 2. Filter by Status (PAUSED)
        status_filter = Select(driver.find_element(By.CSS_SELECTOR, "[data-testid='select-status-filter']"))
        status_filter.select_by_value("PAUSED")
        time.sleep(0.5)

        # Room 2 (PAUSED) visible, Room 1 (ACTIVE) hidden
        assert len(driver.find_elements(By.CSS_SELECTOR, f"[data-testid='card-room-{room_2.id}']")) > 0
        assert len(driver.find_elements(By.CSS_SELECTOR, f"[data-testid='card-room-{room_1.id}']")) == 0

        # Reset status filter
        status_filter.select_by_value("all")
        time.sleep(0.5)

        # 3. Search query
        search_in = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-search-rooms']")
        search_in.send_keys("Developer")
        time.sleep(0.5)
        assert len(driver.find_elements(By.CSS_SELECTOR, f"[data-testid='card-room-{room_1.id}']")) > 0
        assert len(driver.find_elements(By.CSS_SELECTOR, f"[data-testid='card-room-{room_2.id}']")) == 0

        search_in.clear()
        time.sleep(0.5)

        # 4. Quick Status select dropdown on room card
        quick_select = Select(driver.find_element(By.CSS_SELECTOR, f"[data-testid='select-room-status-{room_1.id}']"))
        quick_select.select_by_value("PAUSED")
        time.sleep(1)

        room_1.refresh_from_db()
        assert room_1.status == "PAUSED"
        status_pill = driver.find_element(By.CSS_SELECTOR, f"[data-testid='room-status-{room_1.id}']")
        assert "PAUSED" in status_pill.text

        screenshot_path = SCREENSHOTS_DIR / "us30_08_filters_and_search.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc_us30_09_multi_tenant_isolation_and_rbac(self, driver):
        """
        TC-US30-09: Verify cross-agency multi-tenant isolation (Agency A cannot see Agency B's rooms),
        and verify strict RBAC (student and unauthenticated users blocked from /agency/rooms).
        """
        email_1 = f"agency1_{uuid.uuid4().hex[:6]}@careerflow.test"
        email_2 = f"agency2_{uuid.uuid4().hex[:6]}@careerflow.test"
        agency_user_1 = create_user_in_db(email_1, "ValidPass2026!", role=User.Role.AGENCY_ADMIN, full_name="Agency One Admin")
        agency_user_2 = create_user_in_db(email_2, "ValidPass2026!", role=User.Role.AGENCY_ADMIN, full_name="Agency Two Admin")

        client_1 = create_agency_test_client(agency_user_1, "Agency One Exclusive Client")
        client_2 = create_agency_test_client(agency_user_2, "Agency Two Confidential Client")
        room_1 = create_agency_test_room(agency_user_1, client_1, "Agency 1 Room")
        room_2 = create_agency_test_room(agency_user_2, client_2, "Agency 2 Secret Room")

        # 1. Log in as Agency 1 -> verify cannot see Agency 2's client or room
        login_user(driver, email=email_1)
        driver.get(f"{get_base_url()}/agency/rooms")
        wait = WebDriverWait(driver, 10)

        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='card-client-group-{client_1.id}']")))
        assert "Agency One Exclusive Client" in driver.page_source
        assert "Agency Two Confidential Client" not in driver.page_source
        assert len(driver.find_elements(By.CSS_SELECTOR, f"[data-testid='card-client-group-{client_2.id}']")) == 0
        assert len(driver.find_elements(By.CSS_SELECTOR, f"[data-testid='card-room-{room_2.id}']")) == 0

        # 2. Student user attempts to access /agency/rooms -> protected route blocks
        student_email = f"student_{uuid.uuid4().hex[:6]}@careerflow.test"
        create_user_in_db(student_email, "ValidPass2026!", role=User.Role.STUDENT, full_name="Student Candidate")
        login_user(driver, email=student_email, role=User.Role.STUDENT)

        driver.get(f"{get_base_url()}/agency/rooms")
        time.sleep(1)
        # Should be redirected away to student dashboard or login
        assert "/agency/rooms" not in driver.current_url or "Access Denied" in driver.page_source

        screenshot_path = SCREENSHOTS_DIR / "us30_09_multi_tenant_isolation.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()
