import os
import sys
import time
import uuid
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

import pytest
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from apps.authentication.models import User
from apps.recruitment.models import ClientCompany, RecruitmentRoom
from conftest import FRONTEND_URL, BACKEND_URL, SCREENSHOTS_DIR, create_user_in_db


def get_base_url():
    """Ensure reliable frontend URL."""
    return os.environ.get("FRONTEND_URL", "http://localhost:5173")


def login_user(driver, email: str, password: str = "ValidPass2026!", role: str = User.Role.AGENCY_ADMIN, full_name: str = "Agency Lead"):
    """Helper to ensure user exists and authenticates via UI."""
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


def navigate_to_agency_clients(driver):
    """Navigate to /agency/clients page via sidebar link or direct navigation and wait for page to mount."""
    wait = WebDriverWait(driver, 10)
    try:
        clients_link = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='nav-clients']")))
        clients_link.click()
    except Exception:
        base_url = get_base_url()
        driver.get(f"{base_url}/agency/clients")

    wait.until(EC.url_contains("/agency/clients"))
    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='button-add-client']")))


def create_agency_test_client(agency_user, name, industry="Technology & Software", contact_person="John Doe", contact_email=None, phone="+1-555-0100", website="https://example.com", notes="", is_active=True):
    """Helper to create a ClientCompany instance directly in the database."""
    if not contact_email:
        contact_email = f"contact_{uuid.uuid4().hex[:6]}@example.com"
    return ClientCompany.objects.create(
        agency=agency_user,
        name=name,
        industry=industry,
        contact_person=contact_person,
        contact_email=contact_email,
        phone=phone,
        website=website,
        notes=notes,
        is_active=is_active
    )


class TestUS29AgencyClientManagementUI:
    """
    Automated Selenium UI Test Suite for US-29: Manage Multiple Client Companies (US-29-T6).
    Dedicated Peer Cross-Tester: MD. Jubair Bin Hasan (@jubair65).
    Lead Developer: Nafisa Tabassum Maria (@Maria-07-222).
    """

    def test_tc29_01_navigation_and_kpi_dashboard(self, driver):
        """
        TC-29-01: Verify navigation to /agency/clients from dashboard/sidebar and
        assert high-level portfolio KPI cards (Total, Active, Deactivated, Associated Rooms).
        """
        email = f"agency_tc01_{uuid.uuid4().hex[:6]}@careerflow.test"
        agency_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.AGENCY_ADMIN, full_name="MD. Jubair Bin Hasan")

        # Pre-seed 2 clients: 1 active, 1 deactivated
        client1 = create_agency_test_client(agency_user, "Apex Cloud Systems", industry="Technology & Software", is_active=True)
        create_agency_test_client(agency_user, "Legacy Retailers", industry="E-Commerce & Retail", is_active=False)

        # Seed 1 room associated with client1
        RecruitmentRoom.objects.create(
            title="Senior DevOps Engineer",
            company_name=client1.name,
            client_company=client1,
            created_by=agency_user,
            status=RecruitmentRoom.Status.ACTIVE
        )

        login_user(driver, email, role=User.Role.AGENCY_ADMIN, full_name="MD. Jubair Bin Hasan")

        wait = WebDriverWait(driver, 10)
        # Navigate from dashboard via sidebar nav
        nav_link = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='nav-clients']")))
        nav_link.click()

        wait.until(EC.url_contains("/agency/clients"))
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='button-add-client']")))

        time.sleep(1)  # Allow stats and list to resolve

        # Assert KPI Cards
        total_card = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='stat-total-clients']")))
        active_card = driver.find_element(By.CSS_SELECTOR, "[data-testid='stat-active-clients']")
        deact_card = driver.find_element(By.CSS_SELECTOR, "[data-testid='stat-deactivated-clients']")
        rooms_card = driver.find_element(By.CSS_SELECTOR, "[data-testid='stat-associated-rooms']")

        assert "2" in total_card.text
        assert "1" in active_card.text
        assert "1" in deact_card.text
        assert "1" in rooms_card.text

        screenshot_path = SCREENSHOTS_DIR / "us29_01_navigation_and_kpi_dashboard.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc29_02_client_creation_and_field_validation(self, driver):
        """
        TC-29-02: Verify Add Client Modal opens, enforces mandatory field validation
        (Company Name, Contact Person, Email), and rejects invalid email/website format.
        """
        email = f"agency_tc02_{uuid.uuid4().hex[:6]}@careerflow.test"
        create_user_in_db(email, "ValidPass2026!", role=User.Role.AGENCY_ADMIN, full_name="MD. Jubair Bin Hasan")

        login_user(driver, email, role=User.Role.AGENCY_ADMIN, full_name="MD. Jubair Bin Hasan")
        navigate_to_agency_clients(driver)

        wait = WebDriverWait(driver, 10)
        add_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-add-client']")))
        add_btn.click()

        modal = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-client-form']")))
        assert modal.is_displayed()

        # Submit empty form to trigger mandatory validations
        submit_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-submit-client']")
        submit_btn.click()
        time.sleep(0.4)

        modal_text = modal.text
        assert "Company name is required." in modal_text
        assert "Contact person name is required." in modal_text
        assert "Contact email is required." in modal_text

        name_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-client-name']")
        contact_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-client-contact-person']")
        email_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-client-contact-email']")
        website_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-client-website']")

        name_input.clear()
        name_input.send_keys("Validation Test Corp")
        contact_input.clear()
        contact_input.send_keys("Test Rep")
        email_input.clear()
        email_input.send_keys("invalid-email-format")
        website_input.clear()
        website_input.send_keys("ftp://not-supported-format")

        driver.find_element(By.CSS_SELECTOR, "[data-testid='button-submit-client']").click()
        time.sleep(0.5)

        modal_text = driver.find_element(By.CSS_SELECTOR, "[data-testid='modal-client-form']").text
        assert "Please provide a valid email address." in modal_text
        assert "Website URL must begin with http:// or https://" in modal_text

        screenshot_path = SCREENSHOTS_DIR / "us29_02_client_creation_and_field_validation.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

        # Close modal
        cancel_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-cancel-client']")
        cancel_btn.click()
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-client-form']")))

    def test_tc29_03_create_client_company_success(self, driver):
        """
        TC-29-03: Successfully register a new client company via the modal and
        verify real-time card mounting, details rendering, and KPI increments.
        """
        email = f"agency_tc03_{uuid.uuid4().hex[:6]}@careerflow.test"
        create_user_in_db(email, "ValidPass2026!", role=User.Role.AGENCY_ADMIN, full_name="MD. Jubair Bin Hasan")

        login_user(driver, email, role=User.Role.AGENCY_ADMIN, full_name="MD. Jubair Bin Hasan")
        navigate_to_agency_clients(driver)

        wait = WebDriverWait(driver, 10)
        add_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-add-client']")))
        add_btn.click()

        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-client-form']")))

        name_val = "TechNova Solutions"
        contact_val = "Sarah Jenkins"
        email_val = "sarah@technova.test"
        phone_val = "+1 (555) 014-4900"
        web_val = "https://technova.example.com"
        notes_val = "Key strategic partner for senior engineering pipelines."

        driver.find_element(By.CSS_SELECTOR, "[data-testid='input-client-name']").send_keys(name_val)
        driver.find_element(By.CSS_SELECTOR, "[data-testid='input-client-contact-person']").send_keys(contact_val)
        driver.find_element(By.CSS_SELECTOR, "[data-testid='input-client-contact-email']").send_keys(email_val)
        driver.find_element(By.CSS_SELECTOR, "[data-testid='input-client-phone']").send_keys(phone_val)
        driver.find_element(By.CSS_SELECTOR, "[data-testid='input-client-website']").send_keys(web_val)
        driver.find_element(By.CSS_SELECTOR, "[data-testid='input-client-notes']").send_keys(notes_val)

        driver.find_element(By.CSS_SELECTOR, "[data-testid='button-submit-client']").click()

        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-client-form']")))
        time.sleep(0.8)

        # Assert created client card
        created_client = ClientCompany.objects.get(name=name_val)
        card = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='client-card-{created_client.id}']")))

        assert name_val in card.text
        assert contact_val in card.text
        assert email_val in card.text
        assert "Active" in card.text
        assert "rooms" in card.text

        screenshot_path = SCREENSHOTS_DIR / "us29_03_create_client_company_success.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc29_04_duplicate_name_rejection_same_agency(self, driver):
        """
        TC-29-04: Verify attempting to register a client with a duplicate name within
        the same agency is rejected with an inline backend validation error.
        """
        email = f"agency_tc04_{uuid.uuid4().hex[:6]}@careerflow.test"
        agency_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.AGENCY_ADMIN, full_name="MD. Jubair Bin Hasan")

        # Pre-seed "TechNova Solutions"
        create_agency_test_client(agency_user, "TechNova Solutions", contact_email="tech@example.com")

        login_user(driver, email, role=User.Role.AGENCY_ADMIN, full_name="MD. Jubair Bin Hasan")
        navigate_to_agency_clients(driver)

        wait = WebDriverWait(driver, 10)
        add_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-add-client']")))
        add_btn.click()

        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-client-form']")))

        # Fill with identical company name
        driver.find_element(By.CSS_SELECTOR, "[data-testid='input-client-name']").send_keys("TechNova Solutions")
        driver.find_element(By.CSS_SELECTOR, "[data-testid='input-client-contact-person']").send_keys("Dave Rogers")
        driver.find_element(By.CSS_SELECTOR, "[data-testid='input-client-contact-email']").send_keys("dave@different.test")

        driver.find_element(By.CSS_SELECTOR, "[data-testid='button-submit-client']").click()
        time.sleep(0.8)

        modal = driver.find_element(By.CSS_SELECTOR, "[data-testid='modal-client-form']")
        assert "already exists in your agency portfolio" in modal.text

        screenshot_path = SCREENSHOTS_DIR / "us29_04_duplicate_name_rejection_same_agency.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

        driver.find_element(By.CSS_SELECTOR, "[data-testid='button-cancel-client']").click()
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-client-form']")))

    def test_tc29_05_edit_client_details(self, driver):
        """
        TC-29-05: Verify opening Edit modal on an existing client pre-fills data,
        persists modifications to database, and reflects in UI card.
        """
        email = f"agency_tc05_{uuid.uuid4().hex[:6]}@careerflow.test"
        agency_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.AGENCY_ADMIN, full_name="MD. Jubair Bin Hasan")

        client = create_agency_test_client(
            agency_user,
            "Apex Innovators",
            industry="Technology & Software",
            contact_person="Initial Rep",
            contact_email="initial@apex.test",
            phone="+1-555-0101"
        )

        login_user(driver, email, role=User.Role.AGENCY_ADMIN, full_name="MD. Jubair Bin Hasan")
        navigate_to_agency_clients(driver)

        wait = WebDriverWait(driver, 10)
        edit_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-edit-client-{client.id}']")))
        edit_btn.click()

        modal = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-client-form']")))
        assert "Edit Client Company" in modal.text

        # Update contact person and phone number
        contact_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-client-contact-person']")
        phone_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-client-phone']")
        notes_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-client-notes']")

        contact_input.clear()
        contact_input.send_keys("Elena Rostova")
        phone_input.clear()
        phone_input.send_keys("+1 (555) 998-8776")
        notes_input.clear()
        notes_input.send_keys("Priority SLA: candidate shortlist delivery within 48h.")

        driver.find_element(By.CSS_SELECTOR, "[data-testid='button-submit-client']").click()
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-client-form']")))
        time.sleep(0.8)

        card = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='client-card-{client.id}']")))
        assert "Elena Rostova" in card.text
        assert "+1 (555) 998-8776" in card.text

        screenshot_path = SCREENSHOTS_DIR / "us29_05_edit_client_details.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc29_06_search_and_filtering_controls(self, driver):
        """
        TC-29-06: Verify real-time client search by keyword, industry dropdown filter,
        and Active/Deactivated status tab switching.
        """
        email = f"agency_tc06_{uuid.uuid4().hex[:6]}@careerflow.test"
        agency_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.AGENCY_ADMIN, full_name="MD. Jubair Bin Hasan")

        c1 = create_agency_test_client(agency_user, "BioHealth Labs", industry="Healthcare & Biotech", is_active=True)
        c2 = create_agency_test_client(agency_user, "Vanguard Capital", industry="Finance & Banking", is_active=True)
        c3 = create_agency_test_client(agency_user, "OmniMedia Productions", industry="Media & Entertainment", is_active=False)

        login_user(driver, email, role=User.Role.AGENCY_ADMIN, full_name="MD. Jubair Bin Hasan")
        navigate_to_agency_clients(driver)

        wait = WebDriverWait(driver, 10)
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='client-card-{c1.id}']")))

        # 1. Test Search Box
        search_box = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-search-clients']")
        search_box.clear()
        search_box.send_keys("Vanguard")
        time.sleep(0.5)

        assert driver.find_element(By.CSS_SELECTOR, f"[data-testid='client-card-{c2.id}']").is_displayed()
        driver.implicitly_wait(0)
        try:
            assert len(driver.find_elements(By.CSS_SELECTOR, f"[data-testid='client-card-{c1.id}']")) == 0
            assert len(driver.find_elements(By.CSS_SELECTOR, f"[data-testid='client-card-{c3.id}']")) == 0
        finally:
            driver.implicitly_wait(10)

        # Clear search via Clear button or dispatch event
        clear_btns = driver.find_elements(By.XPATH, "//button[contains(text(), 'Clear')]")
        if clear_btns:
            clear_btns[0].click()
        else:
            driver.execute_script("arguments[0].value = ''; arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", search_box)
        time.sleep(0.5)

        # 2. Test Industry Filter
        industry_select = driver.find_element(By.CSS_SELECTOR, "[data-testid='select-filter-industry']")
        industry_select.click()
        for opt in industry_select.find_elements(By.TAG_NAME, "option"):
            if "Healthcare & Biotech" in opt.text:
                opt.click()
                break
        time.sleep(0.5)

        assert driver.find_element(By.CSS_SELECTOR, f"[data-testid='client-card-{c1.id}']").is_displayed()
        driver.implicitly_wait(0)
        try:
            assert len(driver.find_elements(By.CSS_SELECTOR, f"[data-testid='client-card-{c2.id}']")) == 0
        finally:
            driver.implicitly_wait(10)

        # Reset industry
        for opt in industry_select.find_elements(By.TAG_NAME, "option"):
            if "All Industries" in opt.text:
                opt.click()
                break
        time.sleep(0.5)

        # 3. Test Status Tabs (Active vs Deactivated)
        status_bar = driver.find_element(By.CSS_SELECTOR, "[data-testid='select-filter-status']")
        deactivated_tab = status_bar.find_element(By.XPATH, ".//button[contains(text(), 'Deactivated')]")
        deactivated_tab.click()
        time.sleep(0.5)

        assert driver.find_element(By.CSS_SELECTOR, f"[data-testid='client-card-{c3.id}']").is_displayed()
        driver.implicitly_wait(0)
        try:
            assert len(driver.find_elements(By.CSS_SELECTOR, f"[data-testid='client-card-{c1.id}']")) == 0
        finally:
            driver.implicitly_wait(10)

        screenshot_path = SCREENSHOTS_DIR / "us29_06_search_and_filtering_controls.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc29_07_deactivation_reactivation_lifecycle(self, driver):
        """
        TC-29-07: Verify soft deactivation lifecycle: confirmation modal with safety warning,
        status change to Deactivated (red pill), and subsequent one-click reactivation.
        """
        email = f"agency_tc07_{uuid.uuid4().hex[:6]}@careerflow.test"
        agency_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.AGENCY_ADMIN, full_name="MD. Jubair Bin Hasan")

        client = create_agency_test_client(agency_user, "Solaris Clean Energy", industry="Consulting & Services", is_active=True)

        login_user(driver, email, role=User.Role.AGENCY_ADMIN, full_name="MD. Jubair Bin Hasan")
        navigate_to_agency_clients(driver)

        wait = WebDriverWait(driver, 10)
        card = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='client-card-{client.id}']")))
        assert "Active" in card.text

        # Click Deactivate
        toggle_btn = driver.find_element(By.CSS_SELECTOR, f"[data-testid='button-toggle-client-{client.id}']")
        toggle_btn.click()

        # Confirmation modal check
        confirm_modal = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-confirm-toggle']")))
        assert "Deactivate Client Company?" in confirm_modal.text
        assert "preserving all past candidate applications" in confirm_modal.text

        confirm_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-confirm-toggle']")
        confirm_btn.click()
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-confirm-toggle']")))
        time.sleep(0.8)

        # Card now shows Deactivated
        card = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='client-card-{client.id}']")))
        assert "Deactivated" in card.text
        assert "Reactivate" in card.text

        # Now Reactivate
        reactivate_btn = driver.find_element(By.CSS_SELECTOR, f"[data-testid='button-toggle-client-{client.id}']")
        reactivate_btn.click()

        confirm_modal = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-confirm-toggle']")))
        assert "Reactivate Client Company?" in confirm_modal.text

        driver.find_element(By.CSS_SELECTOR, "[data-testid='button-confirm-toggle']").click()
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-confirm-toggle']")))
        time.sleep(0.8)

        card = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"[data-testid='client-card-{client.id}']")))
        assert "Active" in card.text
        assert "Deactivate" in card.text

        screenshot_path = SCREENSHOTS_DIR / "us29_07_deactivation_reactivation_lifecycle.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()

    def test_tc29_08_rbac_and_multitenant_isolation(self, driver):
        """
        TC-29-08: Verify RBAC (unauthorized Student and HR users cannot access /agency/clients)
        and strict multi-tenant query isolation (Agency 2 cannot view or access Agency 1 clients).
        """
        # 1. Setup Agency 1 with confidential client
        agency1_email = f"agency1_{uuid.uuid4().hex[:6]}@careerflow.test"
        agency1_user = create_user_in_db(agency1_email, "ValidPass2026!", role=User.Role.AGENCY_ADMIN, full_name="Agency One Admin")
        client_a1 = create_agency_test_client(agency1_user, "Confidential Tech Agency1", contact_email="a1@secret.test")

        # 2. Setup Agency 2
        agency2_email = f"agency2_{uuid.uuid4().hex[:6]}@careerflow.test"
        agency2_user = create_user_in_db(agency2_email, "ValidPass2026!", role=User.Role.AGENCY_ADMIN, full_name="Agency Two Admin")

        # 3. Setup unauthorized Student & HR
        student_email = f"student_{uuid.uuid4().hex[:6]}@careerflow.test"
        create_user_in_db(student_email, "ValidPass2026!", role=User.Role.STUDENT, full_name="Student Bob")

        hr_email = f"hr_{uuid.uuid4().hex[:6]}@careerflow.test"
        create_user_in_db(hr_email, "ValidPass2026!", role=User.Role.HR_MANAGER, full_name="HR Alice")

        # Test RBAC for Student
        login_user(driver, student_email, role=User.Role.STUDENT, full_name="Student Bob")
        driver.get(f"{get_base_url()}/agency/clients")
        time.sleep(1)
        # ProtectedRoute should redirect student to student dashboard
        assert "/student/dashboard" in driver.current_url or "/agency/clients" not in driver.current_url

        # Test RBAC for HR Manager
        login_user(driver, hr_email, role=User.Role.HR_MANAGER, full_name="HR Alice")
        driver.get(f"{get_base_url()}/agency/clients")
        time.sleep(1)
        assert "/hr/dashboard" in driver.current_url or "/agency/clients" not in driver.current_url

        # Test Multi-Tenant Isolation for Agency 2
        login_user(driver, agency2_email, role=User.Role.AGENCY_ADMIN, full_name="Agency Two Admin")
        navigate_to_agency_clients(driver)
        time.sleep(1)

        # Agency 2 must NOT see Agency 1's client
        body_text = driver.find_element(By.TAG_NAME, "body").text
        assert "Confidential Tech Agency1" not in body_text

        # Backend API validation of tenant isolation
        session = requests.Session()
        res = session.get(f"{BACKEND_URL}/api/recruitment/agency/clients/{client_a1.id}/")
        assert res.status_code in [401, 403, 404]

        screenshot_path = SCREENSHOTS_DIR / "us29_08_rbac_and_multitenant_isolation.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.exists()
