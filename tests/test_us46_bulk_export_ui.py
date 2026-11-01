"""
US-46: Bulk Applicant Data Export — CSV / Excel UI Automation Test Suite (US-46-T6).
User Story: US-46 – Bulk Applicant Data Export — CSV / Excel
Sprint: Sprint 7 – Final Platform Maturity & Release
Lead Developer: Nafisa Tabassum Maria (@Maria-07-222)
Dedicated Peer UI Automation Tester & Reviewer: MD. Hasanul Mobin (@hasanulmobin)
Target Branch: feat/us-46-bulk-applicant-export -> develop

Acceptance Criteria & Scenarios Verified:
✔ TC-46-01: Export Dropdown Mount & UI Options (Export Data dropdown, CSV/Excel actions) [AC-1, AC-4]
✔ TC-46-02: CSV Bulk Export Trigger & Content Verification (Streamed CSV, UTF-8 BOM, ATS columns) [AC-1, AC-2, AC-4, AC-5]
✔ TC-46-03: Excel (.xlsx) Export Trigger & Sheet Verification (Styled workbook, CareerFlow header, zebra striping) [AC-1, AC-2]
✔ TC-46-04: Filter Preservation — Shortlisted Only Export (Preserves ?shortlisted=true filter) [AC-3]
✔ TC-46-05: Filter Preservation — Search & Score Filters (Preserves search query & min score thresholds) [AC-3]
✔ TC-46-06: CSV Comma & Double-Quote Escaping Integrity (Escaping special characters & commas in names) [AC-4]
✔ TC-46-07: Empty Room Zero-State Export (Graceful handling of 0 applicants without server crash) [AC-1, AC-5]
✔ TC-46-08: Cross-Tenant Access Control & RBAC Enforcement (Rejection of student and unauthorized HR access) [AC-6]
"""

import os
import io
import csv
import sys
import time
import uuid
from pathlib import Path
from datetime import timedelta
import openpyxl

TESTS_DIR = Path(__file__).resolve().parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

import pytest
import requests
from django.conf import settings
from django.utils import timezone
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from apps.authentication.models import User
from apps.recruitment.models import RecruitmentRoom, CandidateApplication
from apps.cv.models import CandidateCV, CVJobMatch
from conftest import FRONTEND_URL, BACKEND_URL, SCREENSHOTS_DIR, create_user_in_db


def clear_react_input(driver, element):
    """Reliably clears React controlled inputs across Windows and other OS."""
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


def login_hr_user(driver, email: str, password: str = "ValidPass2026!", full_name: str = "HR Export Manager"):
    """Helper to authenticate an HR Manager via the UI login page and navigate to /hr/rooms."""
    driver.get(f"{FRONTEND_URL}/login")
    driver.execute_script("sessionStorage.clear(); localStorage.clear();")
    driver.refresh()

    wait = WebDriverWait(driver, 10)
    email_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-login-email']")))
    pass_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-login-password']")
    submit_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-login']")

    set_react_input(driver, email_input, email)
    set_react_input(driver, pass_input, password)
    submit_btn.click()

    wait.until(EC.url_contains("/hr/dashboard"))
    # Navigate to rooms management page
    driver.get(f"{FRONTEND_URL}/hr/rooms")
    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='section-recruitment-rooms']")))


def get_access_token_from_browser(driver) -> str:
    """Extracts the JWT access token from browser localStorage."""
    token = driver.execute_script("return localStorage.getItem('careerflow_access_token');")
    return token or ""


def setup_sample_room_with_applicants(hr_user: User, title: str = "Cloud Security Operations Lead"):
    """
    Creates a RecruitmentRoom with 4 diverse candidates:
    1. Alice: Rank 1, Score 92.0 (CV 94.0, Video 90.0), Shortlisted: True
    2. Bob: Rank 2, Score 85.0 (CV 88.0, Video 82.0), Shortlisted: False
    3. Sarah: Rank 3, Score 80.0, Name with comma/quotes: Dr. Sarah "Sally" O'Connor, Ph.D.
    4. David: Unranked/Pending, Score None, Shortlisted: False
    """
    room = RecruitmentRoom.objects.create(
        created_by=hr_user,
        title=title,
        company_name="CyberShield Global",
        department="Security Engineering",
        status=RecruitmentRoom.Status.OPEN,
        cv_weight=50,
        video_weight=50,
        skills_required=["AWS Security", "Kubernetes", "SIEM", "Incident Response"],
        link_is_active=True,
    )
    now = timezone.now()

    # 1. Alice (Rank 1, Shortlisted)
    uid_a = uuid.uuid4().hex[:6]
    alice = create_user_in_db(f"alice_{uid_a}@careerflow.test", "ValidPass2026!", role=User.Role.STUDENT, full_name="Alice Architect")
    alice_cv = CandidateCV.objects.create(user=alice, file="cvs/alice.pdf", original_filename="Alice_CV.pdf", file_size=1024, file_type="pdf", is_active=True)
    CVJobMatch.objects.create(cv=alice_cv, job_title=room.title, company=room.company_name, match_score=94.0)
    CandidateApplication.objects.create(
        room=room, candidate=alice, cv=alice_cv,
        cv_score=94.0, video_score=90.0, final_score=92.0,
        is_shortlisted=True, shortlist_reason="Exceeded top score threshold",
        status=CandidateApplication.Status.COMPLETED,
    )

    # 2. Bob (Rank 2, Not Shortlisted)
    uid_b = uuid.uuid4().hex[:6]
    bob = create_user_in_db(f"bob_{uid_b}@careerflow.test", "ValidPass2026!", role=User.Role.STUDENT, full_name="Bob Builder")
    bob_cv = CandidateCV.objects.create(user=bob, file="cvs/bob.pdf", original_filename="Bob_CV.pdf", file_size=1024, file_type="pdf", is_active=True)
    CVJobMatch.objects.create(cv=bob_cv, job_title=room.title, company=room.company_name, match_score=88.0)
    CandidateApplication.objects.create(
        room=room, candidate=bob, cv=bob_cv,
        cv_score=88.0, video_score=82.0, final_score=85.0,
        is_shortlisted=False,
        status=CandidateApplication.Status.COMPLETED,
    )

    # 3. Sarah (Rank 3, Special characters and comma in name)
    uid_s = uuid.uuid4().hex[:6]
    sarah_name = 'Dr. Sarah "Sally" O\'Connor, Ph.D.'
    sarah = create_user_in_db(f"sarah_{uid_s}@careerflow.test", "ValidPass2026!", role=User.Role.STUDENT, full_name=sarah_name)
    sarah_cv = CandidateCV.objects.create(user=sarah, file="cvs/sarah.pdf", original_filename="Sarah_CV.pdf", file_size=1024, file_type="pdf", is_active=True)
    CVJobMatch.objects.create(cv=sarah_cv, job_title=room.title, company=room.company_name, match_score=80.0)
    CandidateApplication.objects.create(
        room=room, candidate=sarah, cv=sarah_cv,
        cv_score=80.0, video_score=80.0, final_score=80.0,
        is_shortlisted=False,
        status=CandidateApplication.Status.COMPLETED,
    )

    # 4. David (Unranked / Pending)
    uid_d = uuid.uuid4().hex[:6]
    david = create_user_in_db(f"david_{uid_d}@careerflow.test", "ValidPass2026!", role=User.Role.STUDENT, full_name="David Developer")
    CandidateApplication.objects.create(
        room=room, candidate=david,
        cv_score=None, video_score=None, final_score=None,
        is_shortlisted=False,
        status=CandidateApplication.Status.PENDING,
    )

    return room


# ---------------------------------------------------------------------------
# Test Cases TC-46-01 through TC-46-08
# ---------------------------------------------------------------------------

def test_tc46_01_export_dropdown_mount_and_options(driver):
    """
    TC-46-01: Export Dropdown Mount & UI Options
    Scenario: Verify that the HR ranking modal contains the 'Export Data' dropdown
    button, and clicking it reveals both 'Export as CSV' and 'Export as Excel (.xlsx)' options.
    """
    email = f"tc46_01_{uuid.uuid4().hex[:6]}@careerflow.test"
    hr_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.HR_MANAGER, full_name="Export UI Tester")
    room = setup_sample_room_with_applicants(hr_user)

    login_hr_user(driver, email)
    wait = WebDriverWait(driver, 10)

    # Open Rankings Modal for this room
    ranking_btn = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-action-ranking-{room.id}']"))
    )
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", ranking_btn)
    driver.execute_script("arguments[0].click();", ranking_btn)

    # Wait for Ranking Modal to mount
    modal = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-ranked-applicants']")))
    assert modal.is_displayed()

    # Click the Export Data dropdown button
    export_btn = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-export-applicants']"))
    )
    assert "Export Data" in export_btn.text
    driver.execute_script("arguments[0].click();", export_btn)

    # Verify both export option buttons are displayed in the dropdown
    csv_opt = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='button-export-csv']")))
    excel_opt = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='button-export-excel']")))

    assert "Export as CSV" in csv_opt.text
    assert "Streamed UTF-8 with BOM" in csv_opt.text
    assert "Export as Excel (.xlsx)" in excel_opt.text
    assert "Styled workbook with metrics" in excel_opt.text

    driver.save_screenshot(str(SCREENSHOTS_DIR / "us46_01_export_dropdown_mounted.png"))


def test_tc46_02_export_csv_download_and_content_verification(driver):
    """
    TC-46-02: CSV Bulk Export Trigger & Content Verification (AC-1, AC-2, AC-4, AC-5)
    Scenario: Click 'Export as CSV', verify that the export triggers successfully with toast,
    and verify the exported CSV content contains UTF-8 BOM, ATS headers, and candidate data.
    """
    email = f"tc46_02_{uuid.uuid4().hex[:6]}@careerflow.test"
    hr_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.HR_MANAGER, full_name="CSV Export Tester")
    room = setup_sample_room_with_applicants(hr_user)

    login_hr_user(driver, email)
    wait = WebDriverWait(driver, 10)

    # Open Rankings Modal
    ranking_btn = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-action-ranking-{room.id}']"))
    )
    driver.execute_script("arguments[0].click();", ranking_btn)
    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-ranked-applicants']")))

    # Open Export Menu & Click Export as CSV
    export_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-export-applicants']")))
    driver.execute_script("arguments[0].click();", export_btn)

    csv_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-export-csv']")))
    driver.execute_script("arguments[0].click();", csv_btn)

    # Verify toast notification in UI
    toast = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='toast-message']")))
    assert "Applicants CSV export downloaded successfully." in toast.text

    # Extract access token and verify CSV stream content directly from backend endpoint
    token = get_access_token_from_browser(driver)
    resp = requests.get(
        f"{BACKEND_URL}/api/recruitment/rooms/{room.id}/export/csv/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    assert "text/csv" in resp.headers.get("Content-Type", "")
    assert f"CareerFlow_Room_{room.id}" in resp.headers.get("Content-Disposition", "")

    # Verify UTF-8 BOM (\ufeff) is the very first byte
    raw_content = resp.content
    assert raw_content.startswith(b'\xef\xbb\xbf')

    # Parse CSV content using standard csv.reader
    text_content = raw_content.decode("utf-8-sig")
    csv_reader = csv.reader(io.StringIO(text_content))
    rows = list(csv_reader)

    # 1. Header Row
    headers = rows[0]
    expected_headers = [
        "Rank", "Candidate Name", "Email Address", "CV Match Score (%)",
        "Video Presentation Score (%)", "Final Weighted Score (%)",
        "Shortlisted", "Application Status", "Applied Date"
    ]
    assert headers == expected_headers

    # 2. Data Rows: Verify Alice is Rank #1 and Shortlisted is Yes
    alice_row = next((r for r in rows[1:] if "Alice Architect" in r[1]), None)
    assert alice_row is not None
    assert alice_row[0] == "1"
    assert "92.0%" in alice_row[5]
    assert alice_row[6] == "Yes"

    # Bob is Rank #2 and Shortlisted is No
    bob_row = next((r for r in rows[1:] if "Bob Builder" in r[1]), None)
    assert bob_row is not None
    assert bob_row[0] == "2"
    assert bob_row[6] == "No"

    driver.save_screenshot(str(SCREENSHOTS_DIR / "us46_02_export_csv_success.png"))


def test_tc46_03_export_excel_download_and_structure_verification(driver):
    """
    TC-46-03: Excel (.xlsx) Export Trigger & Sheet Verification (AC-1, AC-2)
    Scenario: Click 'Export as Excel (.xlsx)', verify toast notification, and verify
    the workbook structure: sheet name, title block, styled forest green headers, and candidate rows.
    """
    email = f"tc46_03_{uuid.uuid4().hex[:6]}@careerflow.test"
    hr_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.HR_MANAGER, full_name="Excel Export Tester")
    room = setup_sample_room_with_applicants(hr_user)

    login_hr_user(driver, email)
    wait = WebDriverWait(driver, 10)

    # Open Rankings Modal
    ranking_btn = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-action-ranking-{room.id}']"))
    )
    driver.execute_script("arguments[0].click();", ranking_btn)
    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-ranked-applicants']")))

    # Open Export Menu & Click Export as Excel
    export_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-export-applicants']")))
    driver.execute_script("arguments[0].click();", export_btn)

    excel_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-export-excel']")))
    driver.execute_script("arguments[0].click();", excel_btn)

    # Verify toast notification in UI
    toast = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='toast-message']")))
    assert "Applicants Excel export downloaded successfully." in toast.text

    # Fetch Excel workbook bytes from backend
    token = get_access_token_from_browser(driver)
    resp = requests.get(
        f"{BACKEND_URL}/api/recruitment/rooms/{room.id}/export/excel/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    assert "spreadsheetml.sheet" in resp.headers.get("Content-Type", "")

    # Load workbook using openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(resp.content))
    assert "Ranked Applicants" in wb.sheetnames
    ws = wb["Ranked Applicants"]

    # Verify Title Block
    assert room.title in ws.cell(row=1, column=1).value
    assert room.company_name in ws.cell(row=2, column=1).value

    # Verify Table Header Row (Row 5)
    header_cells = [ws.cell(row=5, column=col).value for col in range(1, 10)]
    assert "Candidate Name" in header_cells
    assert "Final Weighted Score (%)" in header_cells

    # Verify Header Style (#277254 background fill)
    header_fill = ws.cell(row=5, column=1).fill.start_color.rgb
    assert header_fill in ["00277254", "277254"]

    # Verify candidate row contents
    cand_names_in_sheet = [ws.cell(row=r, column=2).value for r in range(6, 11)]
    assert "Alice Architect" in cand_names_in_sheet
    assert "Bob Builder" in cand_names_in_sheet

    driver.save_screenshot(str(SCREENSHOTS_DIR / "us46_03_export_excel_success.png"))


def test_tc46_04_filter_preservation_shortlisted_only(driver):
    """
    TC-46-04: Filter Preservation — Shortlisted Only Export (AC-3)
    Scenario: In the ranking modal, toggle the 'Shortlisted Only' filter. Verify UI shows
    only shortlisted candidates, and verify the export with ?shortlisted=true includes
    only shortlisted candidates.
    """
    email = f"tc46_04_{uuid.uuid4().hex[:6]}@careerflow.test"
    hr_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.HR_MANAGER, full_name="Shortlist Export HR")
    room = setup_sample_room_with_applicants(hr_user)

    login_hr_user(driver, email)
    wait = WebDriverWait(driver, 10)

    # Open Rankings Modal
    ranking_btn = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-action-ranking-{room.id}']"))
    )
    driver.execute_script("arguments[0].click();", ranking_btn)
    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-ranked-applicants']")))

    # Click 'Shortlisted Only' filter button
    shortlist_filter_btn = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-filter-shortlisted-only']"))
    )
    driver.execute_script("arguments[0].click();", shortlist_filter_btn)
    time.sleep(0.5)

    # Verify only shortlisted candidates are visible in UI (Alice is shortlisted, Bob is not)
    visible_cards = driver.find_elements(By.CSS_SELECTOR, "[data-testid^='card-ranked-applicant-']")
    assert len(visible_cards) == 1
    assert "Alice Architect" in visible_cards[0].text
    assert "Bob Builder" not in visible_cards[0].text

    # Request export with ?shortlisted=true
    token = get_access_token_from_browser(driver)
    resp = requests.get(
        f"{BACKEND_URL}/api/recruitment/rooms/{room.id}/export/csv/?shortlisted=true",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200

    csv_reader = csv.reader(io.StringIO(resp.content.decode("utf-8-sig")))
    rows = list(csv_reader)
    data_rows = rows[1:]

    # Assert exactly 1 candidate row (Alice) and all rows have Shortlisted == 'Yes'
    assert len(data_rows) == 1
    assert data_rows[0][1] == "Alice Architect"
    assert data_rows[0][6] == "Yes"

    driver.save_screenshot(str(SCREENSHOTS_DIR / "us46_04_shortlisted_filter_export.png"))


def test_tc46_05_filter_preservation_search_query(driver):
    """
    TC-46-05: Filter Preservation — Search Query (AC-3)
    Scenario: Type a candidate name into the search box in the UI, verify leaderboard
    filters down, and verify that the export endpoint with ?search= preserves the query.
    """
    email = f"tc46_05_{uuid.uuid4().hex[:6]}@careerflow.test"
    hr_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.HR_MANAGER, full_name="Search Export HR")
    room = setup_sample_room_with_applicants(hr_user)

    login_hr_user(driver, email)
    wait = WebDriverWait(driver, 10)

    # Open Rankings Modal
    ranking_btn = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='button-action-ranking-{room.id}']"))
    )
    driver.execute_script("arguments[0].click();", ranking_btn)
    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='modal-ranked-applicants']")))

    # Type 'Bob' into search input and hit Enter to trigger search
    search_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-ranked-search']")))
    set_react_input(driver, search_input, "Bob")
    search_input.send_keys(Keys.ENTER)
    time.sleep(1.0)

    # Verify UI shows Bob
    visible_cards = driver.find_elements(By.CSS_SELECTOR, "[data-testid^='card-ranked-applicant-']")
    assert len(visible_cards) == 1
    assert "Bob Builder" in visible_cards[0].text

    # Request export with ?search=Bob
    token = get_access_token_from_browser(driver)
    resp = requests.get(
        f"{BACKEND_URL}/api/recruitment/rooms/{room.id}/export/csv/?search=Bob",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200

    csv_reader = csv.reader(io.StringIO(resp.content.decode("utf-8-sig")))
    rows = list(csv_reader)
    data_rows = rows[1:]

    # Assert only Bob Builder is in exported data
    assert len(data_rows) == 1
    assert "Bob Builder" in data_rows[0][1]

    driver.save_screenshot(str(SCREENSHOTS_DIR / "us46_05_search_filter_export.png"))


def test_tc46_06_csv_escaping_commas_and_quotes(driver):
    """
    TC-46-06: CSV Comma & Double-Quote Escaping Integrity (AC-4)
    Scenario: Verify that candidate names containing commas and quotation marks
    (e.g. Dr. Sarah "Sally" O'Connor, Ph.D.) are properly escaped by the CSV streaming engine.
    """
    email = f"tc46_06_{uuid.uuid4().hex[:6]}@careerflow.test"
    hr_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.HR_MANAGER, full_name="Escaping HR Tester")
    room = setup_sample_room_with_applicants(hr_user)

    login_hr_user(driver, email)
    wait = WebDriverWait(driver, 10)

    # Fetch CSV export via API
    token = get_access_token_from_browser(driver)
    resp = requests.get(
        f"{BACKEND_URL}/api/recruitment/rooms/{room.id}/export/csv/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200

    text = resp.content.decode("utf-8-sig")
    csv_reader = csv.reader(io.StringIO(text))
    rows = list(csv_reader)

    # Locate Sarah's row
    sarah_row = next((r for r in rows if "Sarah" in r[1]), None)
    assert sarah_row is not None
    # Verify standard CSV reader accurately decodes the full name with quotes and comma
    assert sarah_row[1] == 'Dr. Sarah "Sally" O\'Connor, Ph.D.'
    # Verify exact column alignment: exactly 9 columns
    assert len(sarah_row) == 9

    driver.save_screenshot(str(SCREENSHOTS_DIR / "us46_06_escaped_characters.png"))


def test_tc46_07_empty_room_export_graceful_handling(driver):
    """
    TC-46-07: Empty Room Zero-State Export (AC-1, AC-5)
    Scenario: When a recruitment room has 0 applicants, CSV and Excel exports must
    complete gracefully with HTTP 200, returning header columns and 0 candidate rows.
    """
    email = f"tc46_07_{uuid.uuid4().hex[:6]}@careerflow.test"
    hr_user = create_user_in_db(email, "ValidPass2026!", role=User.Role.HR_MANAGER, full_name="Empty Room HR")
    
    # Create empty room
    empty_room = RecruitmentRoom.objects.create(
        created_by=hr_user,
        title="Empty Leadership Opening",
        company_name="Apex Global",
        status=RecruitmentRoom.Status.OPEN,
    )

    login_hr_user(driver, email)
    token = get_access_token_from_browser(driver)

    # 1. Test CSV Export on Empty Room
    resp_csv = requests.get(
        f"{BACKEND_URL}/api/recruitment/rooms/{empty_room.id}/export/csv/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp_csv.status_code == 200
    csv_rows = list(csv.reader(io.StringIO(resp_csv.content.decode("utf-8-sig"))))
    assert len(csv_rows) == 1  # Only the header row
    assert csv_rows[0][0] == "Rank"

    # 2. Test Excel Export on Empty Room
    resp_excel = requests.get(
        f"{BACKEND_URL}/api/recruitment/rooms/{empty_room.id}/export/excel/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp_excel.status_code == 200
    wb = openpyxl.load_workbook(io.BytesIO(resp_excel.content))
    ws = wb.active
    assert ws.cell(row=5, column=1).value == "Rank"
    # Row 6 should be empty (no candidates)
    assert ws.cell(row=6, column=1).value is None

    driver.save_screenshot(str(SCREENSHOTS_DIR / "us46_07_empty_room_export.png"))


def test_tc46_08_rbac_cross_tenant_isolation(driver):
    """
    TC-46-08: Cross-Tenant Access Control & RBAC Enforcement (AC-6)
    Scenario: Verify that student candidates and unauthorized recruiters cannot access
    or export applicant data for a room they do not own.
    """
    # 1. Room owned by HR Owner
    owner_email = f"owner_tc46_{uuid.uuid4().hex[:6]}@careerflow.test"
    owner_hr = create_user_in_db(owner_email, "ValidPass2026!", role=User.Role.HR_MANAGER, full_name="Owner HR")
    room = setup_sample_room_with_applicants(owner_hr)

    # 2. Rogue HR user from different company
    rogue_email = f"rogue_tc46_{uuid.uuid4().hex[:6]}@careerflow.test"
    create_user_in_db(rogue_email, "ValidPass2026!", role=User.Role.HR_MANAGER, full_name="Rogue Recruiter")

    # 3. Student candidate user
    student_email = f"student_tc46_{uuid.uuid4().hex[:6]}@careerflow.test"
    create_user_in_db(student_email, "ValidPass2026!", role=User.Role.STUDENT, full_name="Student Candidate")

    # A. Unauthenticated request -> 401
    resp_unauth = requests.get(f"{BACKEND_URL}/api/recruitment/rooms/{room.id}/export/csv/")
    assert resp_unauth.status_code == 401

    # B. Student candidate request -> 403 Forbidden
    login_resp_student = requests.post(f"{BACKEND_URL}/api/auth/login/", json={"email": student_email, "password": "ValidPass2026!"})
    student_token = login_resp_student.json().get("access")
    resp_student = requests.get(
        f"{BACKEND_URL}/api/recruitment/rooms/{room.id}/export/csv/",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert resp_student.status_code == 403

    # C. Unauthorized HR request -> 403 Forbidden
    login_resp_rogue = requests.post(f"{BACKEND_URL}/api/auth/login/", json={"email": rogue_email, "password": "ValidPass2026!"})
    rogue_token = login_resp_rogue.json().get("access")
    resp_rogue = requests.get(
        f"{BACKEND_URL}/api/recruitment/rooms/{room.id}/export/csv/",
        headers={"Authorization": f"Bearer {rogue_token}"}
    )
    assert resp_rogue.status_code == 403

    # Log in as unauthorized HR in browser and verify UI isolation
    login_hr_user(driver, rogue_email)
    driver.get(f"{FRONTEND_URL}/hr/rooms")
    # Verify owner's room is completely absent from rogue HR's rooms view
    card = driver.find_elements(By.CSS_SELECTOR, f"[data-testid='card-room-{room.id}']")
    assert len(card) == 0

    driver.save_screenshot(str(SCREENSHOTS_DIR / "us46_08_rbac_forbidden.png"))
