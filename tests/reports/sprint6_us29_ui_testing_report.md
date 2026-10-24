# Sprint 6 UI Testing Report — Task US-29-T6

**Sprint:** Sprint 6 (Smart Recruitment Decisions: Scoring, Ranking, Shortlisting & Agency Management)  
**Epic:** Epic 7: Recruitment Agency Management  
**User Story:** US-29: Manage Multiple Client Companies (Portfolio Organization, Client Lifecycle & Multi-Tenant Isolation)  
**Task:** US-29-T6 (Dedicated Peer UI Testing, Access Control Verification & Automated Selenium Test Suite)  
**Author / Lead Developer:** Nafisa Tabassum Maria ([@Maria-07-222](https://github.com/Maria-07-222)) (System Design / Architect)  
**Reviewer / Peer UI Tester:** MD. Jubair Bin Hasan ([@jubair65](https://github.com/jubair65)) (Lead Developer & Dedicated Peer Tester)  
**Source Branch:** `feat/us-29-agency-client-management`  
**Target Merge Branch:** `develop`  
**Date of Testing:** 2026-10-24  
**Test Framework:** Selenium WebDriver (`selenium 4.29.0`) + pytest (`pytest 9.1.1`) & Django REST Framework APITestCase  
**Platform:** Windows 11 (win32) | Python 3.14.0 (venv) | pytest 9.1.1 | selenium 4.29.0  
**Environment:** Localhost (Frontend: `http://localhost:5173`, Backend: `http://127.0.0.1:8000`, Database: MySQL `careerflow_db`)  
**Browser:** Google Chrome Headless (`155.0.8059.85`)  

---

## 1. Executive Summary

| Metric | Result | Status |
| :--- | :--- | :---: |
| **Total Automated UI Test Cases** | **8 / 8 Passed (100%)** (`tests/test_us29_agency_clients_ui.py`) in 162.99s | 🟢 **PASSED** |
| **Backend Unit & Security Tests** | **19 / 19 Passed (100%)** (`backend/apps/recruitment/tests/test_us29_agency_clients.py`) in 33.95s | 🟢 **PASSED** |
| **Frontend Production Build** | **Built in 14.76s with 0 errors** (`npm run build`, Vite v6.4.3) | 🟢 **PASSED** |
| **Acceptance Criteria Verified** | **6 / 6 ACs Fully Verified & Enforced** | 🟢 **PASSED** |
| **Multi-Tenant Isolation & Security** | **100% Enforced** (Strict `agency=request.user` partition, cross-agency foreign ID 404, RBAC 403) | 🛡️ **SECURE** |
| **Design System Harmonization** | **100% Light Mode Compliant** (`#f4f6ef` canvas, `#ffffff` cards, `#277254` emerald, `#253142` text) | 🎨 **POLISHED** |
| **UI Test Suite Duration** | **162.99 seconds (~2m 43s)** | ⏱️ **OPTIMAL** |
| **Overall Recommendation** | **APPROVED FOR SQUASH AND MERGE INTO `develop`** | 🚀 **READY** |

---

## 2. Test Execution Matrix

### A. Automated Selenium UI Tests (`tests/test_us29_agency_clients_ui.py`)

| Test Case ID | Test Method Name | Description | Status | Execution Time |
| :--- | :--- | :--- | :---: | :---: |
| **TC-29-01** | `test_tc29_01_navigation_and_kpi_dashboard` | Agency Admin logs in and lands on `/agency/dashboard`; navigates to Client Management via sidebar button `[data-testid='nav-clients']`; asserts deep-link URL `/agency/clients`; asserts portfolio header, Add Client CTA (`[data-testid='button-add-client']`), and 4 live KPI metric cards: Total Clients (`stat-total-clients`), Active Clients (`stat-active-clients`), Deactivated Clients (`stat-deactivated-clients`), and Associated Recruitment Rooms (`stat-associated-rooms`) (AC#1, AC#4). | ✅ **PASSED** | ~9.5s |
| **TC-29-02** | `test_tc29_02_client_creation_and_field_validation` | Clicks "Add client company", asserts modal `modal-client-form` mounts; submits empty form and asserts mandatory field validations: "Company name is required.", "Contact person name is required.", "Contact email is required."; inputs invalid email string and non-HTTP URL format; asserts format validations: "Please provide a valid email address.", "Website URL must begin with http:// or https://" (AC#1, AC#2). | ✅ **PASSED** | ~15.2s |
| **TC-29-03** | `test_tc29_03_create_client_company_success` | Fills complete client profile (Name: "TechNova Solutions", Industry: "Technology & Software", Contact: "Sarah Jenkins", Email: "sarah@technova.test", Phone: "+1 (555) 014-4900", Website: "https://technova.example.com", Notes: "Key enterprise client"); submits form; asserts modal unmounts, success toast displays, newly rendered card `client-card-{id}` appears with green "Active" status pill, contact details, phone, and website link; asserts KPI metrics increment (AC#1, AC#4). | ✅ **PASSED** | ~16.8s |
| **TC-29-04** | `test_tc29_04_duplicate_name_rejection_same_agency` | Opens Add Client modal and inputs company name identical to an existing client within the same agency portfolio ("TechNova Solutions"); enters valid contact details; submits form; verifies backend validation intercepts duplicate and displays inline error: `"A client company named 'TechNova Solutions' already exists in your agency portfolio."`; ensures modal remains intact without state corruption (AC#2, AC#6). | ✅ **PASSED** | ~14.6s |
| **TC-29-05** | `test_tc29_05_edit_client_details` | Clicks "Edit" action button `[data-testid='button-edit-client-{id}']` on client card; verifies modal opens with "Edit Client Company" header and pre-filled inputs; updates Contact Person to "Elena Rostova", Phone to "+1 (555) 998-8776", and notes; submits form; asserts modal dismisses and client card updates in real time with new representative and phone contact (AC#3). | ✅ **PASSED** | ~17.2s |
| **TC-29-06** | `test_tc29_06_search_and_filtering_controls` | Tests real-time search and filter controls: inputs "Vanguard" in `[data-testid='input-search-clients']`, asserts only matching card displays while others hide; clears search; selects "Healthcare & Biotech" in `select-filter-industry`, asserts only healthcare client renders; switches status tabs in `select-filter-status` between "All", "Active", and "Deactivated", asserting correct status-filtered cohorts (AC#1, AC#3). | ✅ **PASSED** | ~18.5s |
| **TC-29-07** | `test_tc29_07_deactivation_reactivation_lifecycle` | Clicks "Deactivate" trigger `[data-testid='button-toggle-client-{id}']` on active client; asserts confirmation modal `modal-confirm-toggle` mounts with warning explaining past candidate data and scores remain preserved; clicks confirm; verifies card shifts to deactivated styling (`border-[#ebd9d7]`, red "Deactivated" pill, "Reactivate" button); verifies KPI counters update; clicks "Reactivate" and confirms, verifying clean transition back to Active (AC#3). | ✅ **PASSED** | ~19.1s |
| **TC-29-08** | `test_tc29_08_rbac_and_multitenant_isolation` | Tests RBAC: Student and HR Manager users attempt direct navigation to `/agency/clients`; asserts `ProtectedRoute` blocks access and redirects to respective dashboards; tests multi-tenant isolation: Agency 1 registers confidential client; Agency 2 logs in and navigates to `/agency/clients`, asserting zero visibility of Agency 1's client; validates direct API GET to foreign client ID returns HTTP 404/403 (AC#5, AC#6). | ✅ **PASSED** | ~21.0s |

---

### B. Backend Security & Unit Tests (`backend/apps/recruitment/tests/test_us29_agency_clients.py`)

| Test Method Name | Description | Status | Duration |
| :--- | :--- | :---: | :---: |
| `test_client_company_model_str_and_defaults` | Validates model string representation and default `is_active=True`. | ✅ **PASSED** | ~1.6s |
| `test_client_company_deactivated_str` | Validates model string representation when `is_active=False`. | ✅ **PASSED** | ~1.5s |
| `test_different_agencies_can_have_same_company_name` | Validates two distinct agencies CAN register a client with identical name. | ✅ **PASSED** | ~1.8s |
| `test_unauthenticated_access_rejected` | Validates anonymous requests return HTTP 401 Unauthorized. | ✅ **PASSED** | ~1.4s |
| `test_student_role_forbidden` | Validates student users are rejected with HTTP 403 Forbidden. | ✅ **PASSED** | ~1.7s |
| `test_hr_manager_role_forbidden` | Validates HR Manager users are rejected with HTTP 403 Forbidden. | ✅ **PASSED** | ~1.6s |
| `test_agency_admin_role_authorized` | Validates Agency Admin users receive full HTTP 200 OK access. | ✅ **PASSED** | ~1.7s |
| `test_agency_admin_only_sees_own_clients_in_list` | Validates Agency 1 only receives its own clients in list endpoint. | ✅ **PASSED** | ~1.9s |
| `test_agency_admin_cannot_retrieve_other_agency_client` | Validates Agency 1 cannot retrieve Agency 2's client (HTTP 404). | ✅ **PASSED** | ~1.6s |
| `test_agency_admin_cannot_update_other_agency_client` | Validates Agency 1 cannot update Agency 2's client (HTTP 404). | ✅ **PASSED** | ~1.7s |
| `test_agency_admin_cannot_toggle_other_agency_client` | Validates Agency 1 cannot toggle active state of foreign client (HTTP 404). | ✅ **PASSED** | ~1.8s |
| `test_create_client_company_valid` | Validates creating a client with all fields returns HTTP 201 Created. | ✅ **PASSED** | ~1.9s |
| `test_create_client_company_duplicate_name_same_agency_rejected` | Validates duplicate company name within same agency returns HTTP 400. | ✅ **PASSED** | ~1.8s |
| `test_create_client_company_missing_required_fields` | Validates missing name, industry, or contact fields returns HTTP 400. | ✅ **PASSED** | ~1.7s |
| `test_create_client_company_invalid_email_format` | Validates malformed email returns HTTP 400 with field error. | ✅ **PASSED** | ~1.6s |
| `test_partial_update_client_company` | Validates PATCH request updates only specified fields cleanly. | ✅ **PASSED** | ~1.8s |
| `test_toggle_client_active_custom_action` | Validates `POST .../toggle-active/` switches status between active and inactive. | ✅ **PASSED** | ~1.9s |
| `test_summary_stats_calculation` | Validates KPI stats endpoint correctly counts total, active, and rooms. | ✅ **PASSED** | ~2.1s |
| `test_filter_clients_by_search_industry_and_status` | Validates backend query params (`?q=`, `?industry=`, `?status=`) filter correctly. | ✅ **PASSED** | ~2.2s |

---

## 3. Acceptance Criteria Verification

### ✅ AC#1: Agency Admin Can Create Client Companies
- **Verification:** On `AgencyClientManagementPage` (`/agency/clients`), clicking `[data-testid='button-add-client']` mounts the registration modal. Form fields capture Company Name, Industry Sector dropdown, Contact Person, Contact Email, Contact Phone, Website URL, and Internal Notes. Submitting creates the `ClientCompany` record in the database linked to the authenticated agency admin, adds the card to the grid, and updates summary KPI meters.
- **Evidence:** Verified in automated UI test `TC-29-03` and backend unit test `test_create_client_company_valid`.

### ✅ AC#2: Validated Inputs & Duplicate Prevention
- **Verification:** Form validates that Company Name, Industry, Contact Person, and Contact Email are non-empty. Contact Email enforces regex email formatting (`user@domain.com`), and Website URL requires `http://` or `https://` prefix. Submitting a company name already registered under the same agency admin returns HTTP 400 with message `"A client company named '<name>' already exists in your agency portfolio."` and renders below the input field.
- **Evidence:** Verified in automated UI tests `TC-29-02`, `TC-29-04` and backend unit tests `test_create_client_company_duplicate_name_same_agency_rejected`, `test_create_client_company_invalid_email_format`.

### ✅ AC#3: View, Edit, and Soft Deactivation / Reactivation Lifecycle
- **Verification:** Registered clients render as structured cards with full contact info, room counts, and an active/deactivated badge. Clicking "Edit" opens the modal with existing data pre-filled, saving updates back to the API. Clicking "Deactivate" triggers a confirmation dialog (`[data-testid='modal-confirm-toggle']`) detailing that candidate applications and scores remain safe. Upon confirmation, the company transitions to deactivated status, moves under the Deactivated filter tab, updates KPI counters, and presents a "Reactivate" button.
- **Evidence:** Verified in automated UI tests `TC-29-05`, `TC-29-06`, `TC-29-07` and backend unit tests `test_partial_update_client_company`, `test_toggle_client_active_custom_action`.

### ✅ AC#4: Client Records Linked to Owning Agency & Associated Rooms
- **Verification:** Every `ClientCompany` record is explicitly associated with the authenticated Agency Admin (`agency=request.user`) via `perform_create`. The `ClientCompanyViewSet.summary_stats` action dynamically calculates the number of `RecruitmentRoom` instances linked to the agency's clients via `RecruitmentRoom.objects.filter(client_company__agency=request.user).count()`, accurately displayed in the Associated Rooms KPI card.
- **Evidence:** Verified in automated UI tests `TC-29-01`, `TC-29-03` and backend unit test `test_summary_stats_calculation`.

### ✅ AC#5: RBAC Authorization Enforced
- **Verification:** Only authenticated users with `role=AGENCY_ADMIN` (`role === 'agency'`) can access client endpoints and pages. In the backend, `IsAgencyAdmin` permission class rejects non-agency users with `HTTP 403 Forbidden` and anonymous users with `HTTP 401 Unauthorized`. In the frontend, `ProtectedRoute allowedRoles={['agency']}` intercepts unauthorized visits from Students and HR Managers, redirecting them to `/student/dashboard` or `/hr/dashboard`.
- **Evidence:** Verified in automated UI test `TC-29-08` and backend unit tests `test_unauthenticated_access_rejected`, `test_student_role_forbidden`, `test_hr_manager_role_forbidden`, `test_agency_admin_role_authorized`.

### ✅ AC#6: Strict Multi-Tenant Query Isolation
- **Verification:** `ClientCompanyViewSet.get_queryset()` strictly filters by `agency=self.request.user`. Agency A cannot see, retrieve, update, or toggle Agency B's clients in lists or direct detail endpoints (`HTTP 404 Not Found`). Furthermore, the database constraint `unique_agency_client_company_name` scopes uniqueness exclusively to `(agency, name)`, permitting two separate agencies to independently register clients with identical names without conflict.
- **Evidence:** Verified in automated UI tests `TC-29-04`, `TC-29-08` and backend unit tests `test_different_agencies_can_have_same_company_name`, `test_agency_admin_only_sees_own_clients_in_list`, `test_agency_admin_cannot_retrieve_other_agency_client`, `test_agency_admin_cannot_update_other_agency_client`.

---

## 4. UI Testing Evidence & Screenshots

All 8 high-resolution screenshots were captured during live headless Chrome test execution and are archived in [`tests/reports/screenshots/`](screenshots/):

| Screenshot File | Description | Visual Verification Highlights |
| :--- | :--- | :--- |
| [`us29_01_navigation_and_kpi_dashboard.png`](screenshots/us29_01_navigation_and_kpi_dashboard.png) | Step 1: Navigation & Portfolio KPI Dashboard | Displays `/agency/clients` page heading, "Add client company" CTA, and 4 KPI cards: Total Clients (2), Active (1), Deactivated (1), and Associated Rooms (1). |
| [`us29_02_client_creation_and_field_validation.png`](screenshots/us29_02_client_creation_and_field_validation.png) | Step 2: Client Creation Modal & Field Validation | Demonstrates modal mount, mandatory field validation errors, and email/website format validation messages. |
| [`us29_03_create_client_company_success.png`](screenshots/us29_03_create_client_company_success.png) | Step 3: Client Company Registration Success | Shows newly created "TechNova Solutions" card with green "Active" pill, contact representative, email, phone, website link, and room counter. |
| [`us29_04_duplicate_name_rejection_same_agency.png`](screenshots/us29_04_duplicate_name_rejection_same_agency.png) | Step 4: Duplicate Company Name Rejection | Demonstrates inline backend error: `"A client company named 'TechNova Solutions' already exists in your agency portfolio."` |
| [`us29_05_edit_client_details.png`](screenshots/us29_05_edit_client_details.png) | Step 5: Edit Client Profile & Details | Demonstrates Edit modal saving updated representative ("Elena Rostova") and phone ("+1 (555) 998-8776") reflected immediately on card. |
| [`us29_06_search_and_filtering_controls.png`](screenshots/us29_06_search_and_filtering_controls.png) | Step 6: Search & Industry / Status Filters | Shows filtering by search query "Vanguard", industry dropdown "Healthcare & Biotech", and switching between Active and Deactivated tabs. |
| [`us29_07_deactivation_reactivation_lifecycle.png`](screenshots/us29_07_deactivation_reactivation_lifecycle.png) | Step 7: Soft Deactivation & Reactivation Dialog | Demonstrates deactivation confirmation modal with data safety notice, transition to red "Deactivated" card, and subsequent one-click reactivation. |
| [`us29_08_rbac_and_multitenant_isolation.png`](screenshots/us29_08_rbac_and_multitenant_isolation.png) | Step 8: Multi-Tenant Isolation & RBAC Guard | Verifies Agency 2 cannot view Agency 1's confidential client, and unauthorized student/HR users are blocked by route guards. |

---

## 5. Design Polish & CareerFlow Light Mode Harmonization

During dedicated peer testing (`US-29-T6`), the client management interface was reviewed and verified against CareerFlow's light theme design system:

1. **Light Mode Palette Compliance:**
   - Client cards use clean white cards (`#ffffff`) with subtle `#d9dbd1` borders for active clients and soft `#ebd9d7` borders with `#fdfbfb` background for deactivated clients.
   - Surface background matches CareerFlow's warm beige canvas (`#f5f1e6`, `#fbfaf5`).

2. **Typography & Hierarchy:**
   - Headings styled in deep slate navy (`#253142`), subtitles and descriptions in neutral slate (`#526072` and `#7b8490`).

3. **Status Badges & Tokens:**
   - **Active Status:** Emerald green badge (`bg-[#e2f0e9] text-[#277254]`) with pulsing indicator dot.
   - **Deactivated Status:** Coral red badge (`bg-[#f7e5e1] text-[#a33d35]`) with dot indicator.
   - **Primary Action Buttons:** Solid emerald green (`bg-[#277254] hover:bg-[#1f5b43] text-white`).

4. **HTML5 Form Validation Fix:**
   - Added `noValidate` to the modal `<form>` to prevent browser-native tooltips from suppressing React's custom inline validation errors and format warnings.

---

## 6. Architecture & Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    RECRUITMENT AGENCY CLIENT MANAGEMENT                     │
│                Multi-Tenant Organization & Portfolio Engine                 │
└─────────────────────────────────────────────────────────────────────────────┘
                             Agency Administrator Request
                                          │
                                          ▼
                      /api/recruitment/agency/clients/
                                          │
                        [RBAC & Permission Inspection]
                        ├── IsAuthenticated (401 if anonymous)
                        ├── IsAgencyAdmin (403 if Student or HR)
                        └── IsClientAgencyOwner (404/403 if foreign agency)
                                          │
                                          ▼
                      [Multi-Tenant Scoped Queryset]
                      └── ClientCompany.objects.filter(agency=request.user)
                                          │
               ┌──────────────────────────┴──────────────────────────┐
               ▼                                                     ▼
     POST /agency/clients/                                 POST .../toggle-active/
     ├── Validate name uniqueness                          ├── Invert is_active
     │   within agency scope                               ├── Save updated_at
     ├── Validate email & URL                              └── Return updated client
     └── Save with agency = request.user
                                          │
                                          ▼
                      Frontend AgencyClientManagementPage.tsx
                      ├── Real-time Search (?q=) & Clear action
                      ├── Industry dropdown filter
                      ├── Active / Deactivated cohort tabs
                      ├── Modal create/edit with inline validation
                      ├── Deactivation confirmation dialog
                      └── Associated room counter calculation
```

---

## 7. Definition of Done (DoD) Signoff Checklist

- [x] **Backend Unit & Security Tests:** 19/19 passed (`python manage.py test apps.recruitment.tests.test_us29_agency_clients`) in 33.95s
- [x] **Frontend Production Build:** Built with 0 TypeScript/ESLint errors in 14.76s (`npm run build`, Vite v6.4.3)
- [x] **Automated Selenium UI Tests:** 8/8 test cases passed in 162.99s (`pytest tests/test_us29_agency_clients_ui.py`)
- [x] **Acceptance Criteria Verification:** AC#1 through AC#6 fully verified and documented
- [x] **Multi-Tenant Isolation:** Verified strict agency-level partition; cross-agency foreign ID access blocked with 404
- [x] **RBAC Enforcement:** Verified unauthorized Student and HR roles are blocked with 403 / route redirection
- [x] **Data Safety:** Soft deactivation preserves past recruitment rooms, applicant submissions, and scores
- [x] **Design Polish:** 100% compliant with CareerFlow light mode palette
- [x] **Visual Evidence Captured:** 8 high-resolution screenshots archived in `tests/reports/screenshots/`

---

## 8. Peer Review Recommendation

> **Verdict:** 🟢 **APPROVED FOR SQUASH AND MERGE**  
> **Signoff Reviewer:** MD. Jubair Bin Hasan ([@jubair65](https://github.com/jubair65)) (Lead Developer & Dedicated Peer Tester)  
> **Lead Developer:** Nafisa Tabassum Maria ([@Maria-07-222](https://github.com/Maria-07-222)) (System Design / Architect)  
> **Target Branch:** `develop`  
> **Summary Statement:** Nafisa Tabassum Maria ([@Maria-07-222](https://github.com/Maria-07-222)) has delivered a production-grade, highly secure client company management suite for US-29. The multi-tenant isolation, unique name constraints per agency, lifecycle management (create, edit, soft deactivation with audit safety), and portfolio KPI analytics function flawlessly. All 19 backend unit tests and 8 automated Selenium UI tests execute with a 100% pass rate. The light-mode design perfectly harmonizes with the CareerFlow visual system. The feature is verified, signed off, and recommended for immediate merge into `develop`.
