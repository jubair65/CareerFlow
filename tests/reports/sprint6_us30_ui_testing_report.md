# Sprint 6 UI Testing & Peer Review Report — Task US-30-T6

**Sprint:** Sprint 6 (Smart Recruitment Decisions: Scoring, Ranking, Shortlisting & Agency Management)  
**Epic:** Epic 7: Recruitment Agency Management  
**User Story:** US-30: Agency Room Creation for Client Companies (Multi-Tenant Client Association, Reusable Criteria, Weights & Links)  
**Task:** US-30-T6 (Dedicated Peer UI Testing, Access Control Verification & Automated Selenium Test Suite)  
**Author / Developer:** Farhana Tahsin Bonny ([@tahsinbonnie98](https://github.com/tahsinbonnie98)) (Lead Developer)  
**Reviewer / Peer UI Tester:** MD. Hasanul Mobin ([@hasanulmobin1](https://github.com/hasanulmobin1)) (Project Manager & Full Stack Developer)  
**Source Branch:** `feat/us-30-agency-room-creation`  
**Target Merge Branch:** `develop`  
**Date of Testing:** 2026-10-26  
**Test Framework:** Selenium WebDriver (`selenium 4.29.0`) + pytest (`pytest 9.1.1`) & Django REST Framework APITestCase  
**Platform:** Windows 11 (win32) | Python 3.14.2 | pytest 9.1.1 | selenium 4.29.0  
**Environment:** Localhost (Frontend: `http://127.0.0.1:5173`, Backend: `http://127.0.0.1:8000`, Database: MySQL `fahad`)  
**Browser:** Google Chrome Headless (`155.0.8059.85`)  

---

## 1. Executive Summary

| Metric | Result | Status |
| :--- | :--- | :---: |
| **Total Automated UI Test Cases** | **9 / 9 Passed (100%)** (`tests/test_us30_agency_rooms_ui.py`) in 175.97s | 🟢 **PASSED** |
| **Backend Unit & Integration Tests** | **17 / 17 Passed (100%)** (`backend/apps/recruitment/tests/test_us30_agency_rooms.py`) in 38.44s | 🟢 **PASSED** |
| **Frontend Production Build** | **Vite build succeeds** (`npm run build`) | 🟢 **PASSED** |
| **Acceptance Criteria Verified** | **All 6 ACs (AC#1 to AC#6) fully covered by test suite** | 🟢 **VERIFIED** |
| **Peer Review Bugs Discovered** | **3 Code Defects Identified & Successfully Fixed by Author (commit `9e79835`)** | 🟢 **RESOLVED** |
| **Code Review Policy** | **Reviewer policy: Zero foreign code modifications; author fixed and pushed code** | 📌 **ADHERED** |
| **Overall Recommendation** | **ALL 9 UI TESTS & 17 BACKEND TESTS PASS — APPROVED FOR MERGE** | 🟢 **APPROVED** |

---

## 2. Peer Review Findings & Bug Resolutions (Commit `9e79835`)

During peer UI automation testing, 3 defects were reported to the author (@tahsinbonnie98). The author promptly resolved and pushed fixes in commit `9e79835ddf35aefbcdfc3304ef0ed6a30f884f06`, and all 3 were re-verified in the UI test suite:

### ✅ Bug 1: Sidebar Navigation Handler Missing `/agency/rooms` (RESOLVED)
- **Severity:** High (Functional Navigation Defect)
- **File:** `frontend/src/components/layout/AppShell.tsx`
- **Resolution:** Added `targetPath === '/agency/rooms'` to `handleNavClick`. Re-verified via `test_tc_us30_01_navigation_and_kpi_dashboard`. Status: 🟢 **VERIFIED FIXED**.

---

### ✅ Bug 2: Prop Mismatch in `WeightingConfigCard` Invocation (RESOLVED)
- **Severity:** Critical (JavaScript Runtime Crash)
- **File:** `frontend/src/pages/AgencyRoomsPage.tsx`
- **Resolution:** Updated `WeightingConfigCard` invocation to pass `room={weightingModalRoom}`, `onClose`, and `onWeightingSaved`. Re-verified via `test_tc_us30_06_reused_weighting_modal_configuration`. Status: 🟢 **VERIFIED FIXED**.

---

### ✅ Bug 3: `RecruitmentRoomViewSet` Permissions Reject Agency Admins (RESOLVED)
- **Severity:** High (API 403 Forbidden on Reused Endpoints)
- **File:** `backend/apps/recruitment/views.py`
- **Resolution:** Updated `RecruitmentRoomViewSet.permission_classes` to `[permissions.IsAuthenticated, IsHRManagerOrAgencyAdmin, IsRoomOwner]` and updated `get_queryset()` to permit `AGENCY_ADMIN`. Re-verified via `test_tc_us30_05_reused_criteria_modal_configuration` and `test_tc_us30_06_reused_weighting_modal_configuration`. Status: 🟢 **VERIFIED FIXED**.

### Detailed Resolution Log:

1. **Bug 1: Sidebar Navigation Handler Missing `/agency/rooms` (`AppShell.tsx`)**
   - **Fix:** Author updated `handleNavClick` in `frontend/src/components/layout/AppShell.tsx` to include `targetPath === '/agency/rooms'`.
   - **Verification:** `test_tc_us30_01_navigation_and_kpi_dashboard` clicked sidebar button `[data-testid='nav-rooms']` and successfully verified URL change to `/agency/rooms` and mounting of the Agency Rooms dashboard.

2. **Bug 2: Prop Mismatch in `WeightingConfigCard` Invocation (`AgencyRoomsPage.tsx`)**
   - **Fix:** Author updated `AgencyRoomsPage.tsx` to pass `room={weightingModalRoom}`, `onClose={() => setWeightingModalRoom(null)}`, and `onWeightingSaved={...}` to `WeightingConfigCard`.
   - **Verification:** `test_tc_us30_06_reused_weighting_modal_configuration` launched weighting modal, selected the 70% CV / 30% Video preset, saved configuration, and verified persistent room card badge updates without console runtime errors.

3. **Bug 3: `RecruitmentRoomViewSet` Permissions Reject Agency Admins (`views.py`)**
   - **Fix:** Author replaced `IsHRManager` with `IsHRManagerOrAgencyAdmin` in `RecruitmentRoomViewSet.permission_classes` and updated `get_queryset()` to permit `User.Role.AGENCY_ADMIN`.
   - **Verification:** Both criteria (`PATCH /api/recruitment/rooms/{id}/requirements/`) and weighting (`PATCH /api/recruitment/rooms/{id}/weighting/`) updates now return HTTP 200 OK for Agency Admins. Re-verified via `test_tc_us30_05` and `test_tc_us30_06`.

---

## 3. Automated Selenium UI Test Suite Matrix (`tests/test_us30_agency_rooms_ui.py`)

A comprehensive test suite of 9 automated test cases has been authored and committed at [tests/test_us30_agency_rooms_ui.py](file:///e:/sdeproject/CareerFlow/tests/test_us30_agency_rooms_ui.py):

| Test Case ID | Test Method Name | Description | Acceptance Criteria |
| :--- | :--- | :--- | :---: |
| **TC-US30-01** | `test_tc_us30_01_navigation_and_kpi_dashboard` | Agency Admin navigates to `/agency/rooms` via sidebar button `[data-testid='nav-rooms']` and Dashboard "New room" `[data-testid='button-agency-create-room']`; asserts target URL `/agency/rooms`; asserts page container `[data-testid='page-agency-rooms']`, Create Room button, and 4 KPI metric cards. | Navigation |
| **TC-US30-02** | `test_tc_us30_02_client_grouped_view_and_accordion` | Pre-seeds 2 clients and 3 rooms; asserts client grouped accordion cards `[data-testid='card-client-group-{id}']` mount with client badges, room counters `[data-testid='badge-rooms-count-{id}']`, and summary counter; verifies accordion collapse/expand toggle `[data-testid='button-toggle-collapse-{id}']`. | **AC#6** |
| **TC-US30-03** | `test_tc_us30_03_room_creation_modal_and_submission` | Clicks "+ Create Room", asserts modal `[data-testid='modal-agency-create-room']` mounts; selects client company `[data-testid='select-agency-client-company']`; asserts client info badge; fills Title, Department, Category, Level, Description, and weight slider; submits form; asserts modal dismisses and `RecruitmentRoom.company_name` auto-synchronizes with client company name. | **AC#1, AC#2** |
| **TC-US30-04** | `test_tc_us30_04_validation_and_inactive_client_protection` | Opens Create Room modal; submits empty and short title (< 3 chars); asserts error banner `[data-testid='alert-agency-create-room-error']`; asserts deactivated client companies (`is_active=False`) are excluded from selector; dismisses modal via Cancel button. | **AC#5** |
| **TC-US30-05** | `test_tc_us30_05_reused_criteria_modal_configuration` | Clicks "Criteria" button `[data-testid='button-config-reqs-{roomId}']` on room card; verifies `[data-testid='modal-job-requirements']` mounts with room title and client context; adds new skill tag; updates seniority level; submits and verifies persistence in DB and card. | **AC#3** |
| **TC-US30-06** | `test_tc_us30_06_reused_weighting_modal_configuration` | Clicks "Weights" button `[data-testid='button-config-weights-{roomId}']` on room card; verifies modal `[data-testid='modal-agency-weighting-config']` mounts; applies preset (70% CV / 30% Video); clicks Save; asserts room card badge `[data-testid='room-weights-{roomId}']` updates to "70% CV / 30% Video". | **AC#3** |
| **TC-US30-07** | `test_tc_us30_07_application_link_generation_and_lifecycle` | Asserts application link input `[data-testid='input-room-link-{roomId}']` contains valid `/apply/{share_token}`; clicks copy button with visual feedback; toggles link status button `[data-testid='button-toggle-link-{roomId}']` between "Active" and "Disabled", verifying database `link_is_active` synchronization. | **AC#4** |
| **TC-US30-08** | `test_tc_us30_08_filters_search_and_quick_status_change` | Tests Client filter dropdown `[data-testid='select-client-filter']`, Status filter dropdown `[data-testid='select-status-filter']`, search input `[data-testid='input-search-rooms']`, and quick status dropdown `[data-testid='select-room-status-{roomId}']` on room card (`ACTIVE` <-> `PAUSED`). | Controls & Filters |
| **TC-US30-09** | `test_tc_us30_09_multi_tenant_isolation_and_rbac` | Tests cross-agency isolation (Agency 1 cannot view Agency 2's client groups or rooms). Tests RBAC: Student candidates and unauthenticated visitors attempting to access `/agency/rooms` are blocked by `ProtectedRoute`. | **AC#5** |

---

## 4. Backend Unit & Integration Tests (`backend/apps/recruitment/tests/test_us30_agency_rooms.py`)

All 17 backend unit and integration tests authored by Bonny are verified and pass:

| Test Method Name | Description | Status |
| :--- | :--- | :---: |
| `test_model_clean_syncs_company_name_from_client_company` | Auto-sync `company_name` from `client_company` | ✅ **PASSED** |
| `test_model_clean_rejects_cross_agency_association` | Cross-agency client association rejected | ✅ **PASSED** |
| `test_model_clean_rejects_deactivated_client_for_new_room` | Deactivated client room creation rejected | ✅ **PASSED** |
| `test_agency_create_room_success` | Agency room creation via API (HTTP 201) | ✅ **PASSED** |
| `test_agency_create_room_missing_client_company_fails` | Missing client company returns HTTP 400 | ✅ **PASSED** |
| `test_agency_cannot_create_room_for_another_agency_client` | Prevent associating another agency's client | ✅ **PASSED** |
| `test_agency_cannot_create_room_for_deactivated_client` | Prevent creating room for inactive client | ✅ **PASSED** |
| `test_agency_multi_tenant_isolation_list` | Agency 1 only lists its own client rooms | ✅ **PASSED** |
| `test_agency_multi_tenant_isolation_retrieve_and_edit` | Agency 1 cannot get/patch Agency 2's room | ✅ **PASSED** |
| `test_hr_manager_cannot_access_agency_rooms_endpoint` | HR Manager blocked with HTTP 403 | ✅ **PASSED** |
| `test_student_cannot_access_agency_rooms_endpoint` | Student blocked with HTTP 403 | ✅ **PASSED** |
| `test_unauthenticated_cannot_access_agency_rooms_endpoint` | Unauthenticated blocked with HTTP 401 | ✅ **PASSED** |
| `test_agency_room_requirements_configuration` | Configure requirements & skills via PATCH | ✅ **PASSED** |
| `test_agency_room_weighting_configuration` | Configure CV vs Video weighting via PATCH | ✅ **PASSED** |
| `test_agency_room_link_retrieval_and_lifecycle` | Retrieve share token & toggle link status | ✅ **PASSED** |
| `test_grouped_by_client_endpoint` | Grouped rooms by client endpoint (AC#6) | ✅ **PASSED** |
| `test_agency_summary_stats_endpoint` | Summary KPI stats endpoint | ✅ **PASSED** |

---

## 5. Screenshot Evidence Gallery

| Evidence ID | Description | File Path |
| :--- | :--- | :--- |
| **US30-01** | Agency Dashboard navigation & 4 KPI metric cards | [us30_01_navigation_dashboard.png](file:///e:/sdeproject/CareerFlow/tests/reports/screenshots/us30_01_navigation_dashboard.png) |
| **US30-02** | Client grouped view with badges & accordion toggle | [us30_02_client_grouped_view.png](file:///e:/sdeproject/CareerFlow/tests/reports/screenshots/us30_02_client_grouped_view.png) |
| **US30-03** | Room creation modal with auto client name sync & slider | [us30_03_room_creation_success.png](file:///e:/sdeproject/CareerFlow/tests/reports/screenshots/us30_03_room_creation_success.png) |
| **US30-04** | Title validation and exclusion of deactivated clients | [us30_04_validation_inactive_client.png](file:///e:/sdeproject/CareerFlow/tests/reports/screenshots/us30_04_validation_inactive_client.png) |
| **US30-05** | Reused Job Requirements modal & skill configuration | [us30_05_criteria_modal.png](file:///e:/sdeproject/CareerFlow/tests/reports/screenshots/us30_05_criteria_modal.png) |
| **US30-06** | Reused Evaluation Weighting modal & preset selection | [us30_06_weighting_modal.png](file:///e:/sdeproject/CareerFlow/tests/reports/screenshots/us30_06_weighting_modal.png) |
| **US30-07** | Application link generation, copy & lifecycle toggle | [us30_07_link_generation.png](file:///e:/sdeproject/CareerFlow/tests/reports/screenshots/us30_07_link_generation.png) |
| **US30-08** | Client filter, status filter, search & quick status change | [us30_08_filters_and_search.png](file:///e:/sdeproject/CareerFlow/tests/reports/screenshots/us30_08_filters_and_search.png) |
| **US30-09** | Cross-agency multi-tenant isolation & RBAC protection | [us30_09_multi_tenant_isolation.png](file:///e:/sdeproject/CareerFlow/tests/reports/screenshots/us30_09_multi_tenant_isolation.png) |

---

## 6. Conclusion & Sign-Off
 
The architectural design, multi-tenant client association models, and frontend integration for US-30 are solid and production-ready.
 
All 3 code review findings were promptly and cleanly addressed by Farhana Tahsin Bonny in commit `9e79835`. Comprehensive end-to-end verification confirms:
1. **17 / 17 Backend Unit & Integration Tests Passed (100%)**
2. **9 / 9 Automated Selenium UI Tests Passed (100%)**
3. **Vite Frontend Production Build Clean (0 errors)**
4. **All 6 Acceptance Criteria (AC#1 through AC#6) fully satisfied**
 
**Peer Reviewer:** MD. Hasanul Mobin ([@hasanulmobin1](https://github.com/hasanulmobin1)) (Project Manager & Full Stack Developer)  
**Final Status:** 🟢 **APPROVED FOR MERGE (Task US-30-T6 Completed)**
