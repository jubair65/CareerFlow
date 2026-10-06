# Sprint 4 UI Testing Report — Task US-18-T6

**Sprint:** Sprint 4 (Recruitment Rooms & Candidate Submission)  
**User Story:** US-18: Create Recruitment Room  
**Task:** US-18-T6 (UI Testing for Room Creation Flow)  
**Peer Tester:** Nafisa Tabassum Maria (System Architect)  
**Developer:** MD. Jubair Bin Hasan (Software Developer)  
**Date:** 2026-10-06  
**Framework:** Selenium WebDriver + pytest  
**Platform:** macOS | Python 3.14.2 | pytest 9.1.1  
**Environment:** Localhost (Frontend: `http://localhost:5173`, Backend: `http://127.0.0.1:8000`)  
**Browser:** Google Chrome (Headless)  

---

## 1. Executive Summary

| Metric | Result |
| :--- | :--- |
| **Total Automated UI Test Cases** | **4** |
| **Passed** | **4 (100%)** |
| **Failed** | **0 (0%)** |
| **Backend Unit Tests** | **11 / 11 Passed (100%)** (`backend/apps/recruitment/tests/test_room_management.py`) |
| **Execution Duration** | **30.52 seconds** |
| **Automated Suite Status** | 🟢 **PASSED & VERIFIED** |
| **Manual Verification Status** | 🟢 **PASSED & DEFECT RESOLVED** (See Section 4) |
| **Overall Recommendation** | 🟢 **APPROVED FOR MERGE INTO `develop`** |

---

## 2. Test Execution Matrix

| Test Case ID | Test Method Name | Description | Status | Execution Time |
| :--- | :--- | :--- | :---: | :---: |
| **TC-US18-01** | `test_tc_us18_01_create_room_modal_validation` | HR logs into workspace; navigates to `/hr/rooms` via sidebar link (`data-testid="nav-recruitment-rooms"`); opens Room Creation Modal; verifies validation feedback for blank title (`Job title is required.`), short title under 3 characters (`Job title must be at least 3 characters.`), and blank company name (`Company name is required.`), plus clean modal dismissal on cancel. | ✅ **PASSED** | ~8.1s |
| **TC-US18-02** | `test_tc_us18_02_create_room_success` | HR creates room with complete valid payload (Title: "Lead Full Stack Engineer", Company: "Google Cloud", Department, Description); verifies asynchronous submission, modal dismissal, and reactive rendering of room card in DOM with ACTIVE status and evaluation weights (CV 50% / Video 50%). | ✅ **PASSED** | ~7.9s |
| **TC-US18-03** | `test_tc_us18_03_room_list_status_toggle` | HR toggles room status between `ACTIVE` and `PAUSED` using the room card quick-action toggle button; verifies reactive badge color and text transitions without full page reload. | ✅ **PASSED** | ~7.2s |
| **TC-US18-04** | `test_tc_us18_04_copy_shareable_link` | HR clicks **[Copy Link]** on room card; verifies button label transitions to "Copied!" and shareable URL containing unique crypto token (`/apply/<share_token>`) is copied to clipboard with toast notification. | ✅ **PASSED** | ~7.3s |

---

## 3. Acceptance Criteria Verified

- ✅ **AC 1 — Room Creation for Opening:** HR Manager can create a Room successfully for a specific opening with title, company name, department, and description.
- ✅ **AC 2 — Input Validation:** Strict validation rules enforce non-empty title (min 3 chars) and non-empty company name with instant inline validation text before submitting.
- ✅ **AC 3 — Role-Based Access Control (RBAC):** `IsHRManager` permission restricts room management strictly to HR users. Student and Agency roles receive `403 Forbidden` (verified in unit tests).
- ✅ **AC 4 — HR Ownership Link:** Every created room is automatically associated with the authenticated HR user via `created_by`.
- ✅ **AC 5 — Room List & Status Toggle:** Rooms list renders created cards with metadata (department, company, creation date, CV/video weights) and allows immediate toggling between ACTIVE and PAUSED.
- ✅ **AC 6 — Secure Link Generation:** Every room is provisioned with a cryptographic `share_token` (16 bytes urlsafe) ready for applicant submissions (US-21 / US-22 foundation).

---

## 4. Defect Lifecycle & Resolution Report

### 🟢 Defect ID: BUG-US18-01 — Sidebar Link to Recruitment Rooms Does Not Navigate
* **Severity:** Medium (Navigation / UX Flow)
* **Component:** `frontend/src/components/layout/AppShell.tsx` (Line 130–144)
* **Status:** 🟢 **RESOLVED & VERIFIED** (Fixed in commit `157964a`)

#### Description & Discovery:
During Step 2 manual verification, clicking the **"Recruitment rooms"** item in the sidebar navigation (`[data-testid='nav-recruitment-rooms']`) did not navigate to `/hr/rooms`. Instead, a toast notification displayed: `"Sprint 2 feature: Full interactive workflow coming in next sprint!"` because `handleNavClick` in `AppShell.tsx` had not whitelisted `/hr/rooms`.

#### Defect Resolution:
Developer MD. Jubair Bin Hasan updated `frontend/src/components/layout/AppShell.tsx` in commit `157964a` to whitelist `/hr/rooms` and `/hr/dashboard`:
```tsx
  const handleNavClick = (targetPath: string, isOverview?: boolean) => {
    setMobileOpen(false);
    if (
      isOverview ||
      targetPath === '/hr/rooms' ||
      targetPath === '/hr/dashboard' ||
      targetPath === '/student/cv' ||
      targetPath === '/student/practice' ||
      targetPath === '/student/videos' ||
      targetPath === '/student/presentation'
    ) {
      setLocation(targetPath);
    } else {
      notify('Sprint 2 feature: Full interactive workflow coming in next sprint!', 'info');
    }
  };
```

#### Re-Test & Verification:
- Peer Tester pulled commit `157964a` via `git pull origin feat/us-18-create-room`.
- Re-ran automated navigation verification: clicking `data-testid="nav-recruitment-rooms"` now navigates directly to `http://localhost:5173/hr/rooms` cleanly.
- Defect verified resolved.

---

## 5. Test Environment & Artifacts

- **UI Test Suite:** [`tests/test_us18_room_creation_ui.py`](file:///Users/nafisatabassummaria/Study/3.2/Project/CareerFlow/tests/test_us18_room_creation_ui.py)
- **HTML Report:** [`tests/reports/sprint4_us18_report.html`](file:///Users/nafisatabassummaria/Study/3.2/Project/CareerFlow/tests/reports/sprint4_us18_report.html)
- **Backend Unit Tests:** [`backend/apps/recruitment/tests/test_room_management.py`](file:///Users/nafisatabassummaria/Study/3.2/Project/CareerFlow/backend/apps/recruitment/tests/test_room_management.py) (11/11 passed)
- **Screenshots:**
  - Validation: [`tests/reports/screenshots/us18_01_modal_validation.png`](file:///Users/nafisatabassummaria/Study/3.2/Project/CareerFlow/tests/reports/screenshots/us18_01_modal_validation.png)
  - Card Created: [`tests/reports/screenshots/us18_02_room_card_created.png`](file:///Users/nafisatabassummaria/Study/3.2/Project/CareerFlow/tests/reports/screenshots/us18_02_room_card_created.png)
  - Status Toggle: [`tests/reports/screenshots/us18_03_room_status_paused.png`](file:///Users/nafisatabassummaria/Study/3.2/Project/CareerFlow/tests/reports/screenshots/us18_03_room_status_paused.png)
  - Copy Link: [`tests/reports/screenshots/us18_04_copy_link_toast.png`](file:///Users/nafisatabassummaria/Study/3.2/Project/CareerFlow/tests/reports/screenshots/us18_04_copy_link_toast.png)
  - Initial Defect Evidence: [`tests/reports/screenshots/bug_us18_sidebar_navigation_failure.png`](file:///Users/nafisatabassummaria/Study/3.2/Project/CareerFlow/tests/reports/screenshots/bug_us18_sidebar_navigation_failure.png)
  - Resolution Evidence: [`tests/reports/screenshots/us18_05_sidebar_navigation_resolved.png`](file:///Users/nafisatabassummaria/Study/3.2/Project/CareerFlow/tests/reports/screenshots/us18_05_sidebar_navigation_resolved.png)
- **Report Location:** [`tests/reports/sprint4_us18_ui_testing_report.md`](file:///Users/nafisatabassummaria/Study/3.2/Project/CareerFlow/tests/reports/sprint4_us18_ui_testing_report.md)
