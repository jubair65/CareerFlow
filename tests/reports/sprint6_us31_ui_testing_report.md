# Sprint 6 UI Testing & Peer Review Report — Task US-31-T6

**Sprint:** Sprint 6 (Smart Recruitment Decisions: Scoring, Ranking, Shortlisting & Agency Management)  
**Epic:** Epic 7: Recruitment Agency Management  
**User Story:** US-31: Cross-Client Applicant View (Consolidated Agency Pipeline, Multi-Tenant Aggregation, Scores & Filtering)  
**Task:** US-31-T6 (Dedicated Peer UI Testing, Access Control Verification & Automated Selenium Test Suite)  
**Author / Developer:** Farhana Tahsin Bonny ([@tahsinbonnie98](https://github.com/tahsinbonnie98)) (Lead Developer)  
**Reviewer / Peer UI Tester:** MD. Hasanul Mobin ([@hasanulmobin1](https://github.com/hasanulmobin1)) (Project Manager & Full Stack Developer)  
**Source Branch:** `feat/us-31-cross-client-applicant-view`  
**Target Merge Branch:** `develop`  
**Date of Testing:** 2026-10-27  
**Test Framework:** Selenium WebDriver (`selenium 4.29.0`) + pytest (`pytest 9.1.1`) & Django REST Framework APITestCase  
**Platform:** Windows 11 (win32) | Python 3.14.2 | pytest 9.1.1 | selenium 4.29.0  
**Environment:** Localhost (Frontend: `http://127.0.0.1:5173`, Backend: `http://127.0.0.1:8000`, Database: MySQL `fahad`)  
**Browser:** Google Chrome Headless (`155.0.8059.85`)  

---

## 1. Executive Summary

| Metric | Result | Status |
| :--- | :--- | :---: |
| **Total Automated UI Test Cases** | **9 / 9 Passed (100%)** ([tests/test_us31_cross_client_pipeline_ui.py](file:///e:/sdeproject/CareerFlow/tests/test_us31_cross_client_pipeline_ui.py)) in 147.02s | 🟢 **PASSED** |
| **Backend Unit & Integration Tests** | **17 / 17 Passed (100%)** (`apps.recruitment.tests.test_us31_cross_client_applicants`) in 88.57s | 🟢 **PASSED** |
| **Frontend Production Build** | **Vite build succeeds with 0 errors** (`npm run build`, 2,401 modules) in 13.47s | 🟢 **PASSED** |
| **Acceptance Criteria Verified** | **All 6 ACs (AC#1 through AC#6) fully covered by test suite** | 🟢 **VERIFIED** |
| **Code Review Policy** | **Zero reviewer modifications to author's code; clean isolation** | 📌 **ADHERED** |
| **Overall Recommendation** | **ALL 9 UI TESTS & 17 BACKEND TESTS PASS — APPROVED FOR MERGE** | 🟢 **APPROVED** |

---

## 2. Acceptance Criteria Verification Matrix

| AC ID | Description | Automated UI Test Case | Status |
| :--- | :--- | :--- | :---: |
| **AC#1** | **Cross-Client Applicant Aggregation:** Consolidated pipeline view across all client companies of an agency. | `test_tc_us31_02_cross_client_aggregation_and_table_schema` | 🟢 **VERIFIED** |
| **AC#2** | **Required Fields & Details Modal:** Candidate info, client company, position, CV match score, video score, final weighted score badge, status badge, shortlist star indicator, and detail breakdown modal. | `test_tc_us31_02_cross_client_aggregation_and_table_schema`, `test_tc_us31_03_applicant_detail_modal_breakdown` | 🟢 **VERIFIED** |
| **AC#3** | **Filters & Real-Time Search (US-31-T4):** Client company selector, cascading Room selector, application status filter, shortlist toggle, ordering sort dropdown, and live text search. | `test_tc_us31_04_live_search_and_instant_filtering`, `test_tc_us31_05_client_and_cascading_room_filters`, `test_tc_us31_06_status_shortlist_and_sorting_controls` | 🟢 **VERIFIED** |
| **AC#4** | **Multi-Tenant Data Isolation (US-31-T5):** Agency A cannot view or retrieve Agency B's applications. Strict database and DOM boundaries enforced. | `test_tc_us31_08_multi_tenant_isolation_agency_boundaries` | 🟢 **VERIFIED** |
| **AC#5** | **Empty Pipeline Handling:** Informative empty state banner (`[data-testid='banner-empty-applicants']`) with guidance and filter reset CTA when no applications match criteria. | `test_tc_us31_07_empty_state_and_filter_reset` | 🟢 **VERIFIED** |
| **AC#6** | **High Performance & KPI Dashboard:** Sub-second queries with `select_related`, 4 KPI metric cards, and dashboard navigation via sidebar and review pipeline CTA. | `test_tc_us31_01_navigation_and_kpi_dashboard`, `test_tc_us31_06_status_shortlist_and_sorting_controls` | 🟢 **VERIFIED** |

---

## 3. Automated Selenium UI Test Suite Details (`tests/test_us31_cross_client_pipeline_ui.py`)

A comprehensive test suite of 9 automated test cases has been authored at [tests/test_us31_cross_client_pipeline_ui.py](file:///e:/sdeproject/CareerFlow/tests/test_us31_cross_client_pipeline_ui.py):

| Test Case ID | Test Method Name | Description | Acceptance Criteria |
| :--- | :--- | :--- | :---: |
| **TC-US31-01** | `test_tc_us31_01_navigation_and_kpi_dashboard` | Agency Admin navigates to `/agency/pipeline` via sidebar button `[data-testid='nav-pipeline']` and Dashboard "Review pipeline" `[data-testid='button-review-pipeline']`; verifies container `[data-testid='page-agency-applicants']` and 4 KPI metric cards (Total Applicants, Completed Analyses, Shortlisted Candidates, Average Final Score). | **AC#1, AC#6** |
| **TC-US31-02** | `test_tc_us31_02_cross_client_aggregation_and_table_schema` | Pre-seeds 2 Client Companies and 3 Candidate Applications; verifies consolidated cross-client table aggregation `[data-testid='container-applicant-table']`; asserts candidate name, email, client name, room position, CV score, video score, final score badge, status badge, and shortlist badge. | **AC#1, AC#2** |
| **TC-US31-03** | `test_tc_us31_03_applicant_detail_modal_breakdown` | Clicks "Details" button `[data-testid='button-view-applicant-{id}']`; verifies modal `[data-testid='modal-applicant-detail']` mounts; asserts evaluation breakdown (CV match %, Video %, final weighted score), shortlist reason, and HR review decision; tests modal dismissal. | **AC#2** |
| **TC-US31-04** | `test_tc_us31_04_live_search_and_instant_filtering` | Tests live debounced text search `[data-testid='input-search-applicants']` across candidate names and client companies; verifies instant row filtering and restoration upon clearing search. | **AC#3** |
| **TC-US31-05** | `test_tc_us31_05_client_and_cascading_room_filters` | Tests Client Company selector `[data-testid='select-filter-client']`; verifies table filters by client; verifies Room selector `[data-testid='select-filter-room']` cascades to only show the selected client's rooms; tests `[data-testid='button-reset-filters']`. | **AC#3** |
| **TC-US31-06** | `test_tc_us31_06_status_shortlist_and_sorting_controls` | Tests application status filter `[data-testid='select-filter-status']` (COMPLETED, ANALYZING), shortlist filter `[data-testid='select-filter-shortlist']` (Shortlisted Only), and sorting ordering dropdown `[data-testid='select-sort-ordering']` (-final_score). | **AC#3, AC#6** |
| **TC-US31-07** | `test_tc_us31_07_empty_state_and_filter_reset` | Tests empty applicant pipeline; verifies `[data-testid='banner-empty-applicants']` renders with clear user guidance and filter clear CTA. | **AC#5** |
| **TC-US31-08** | `test_tc_us31_08_multi_tenant_isolation_agency_boundaries` | Tests multi-tenant isolation across agencies; verifies Agency Admin 1 can only see Agency 1 applications; asserts Agency 2 applicants are strictly excluded from DOM and API responses. | **AC#4** |
| **TC-US31-09** | `test_tc_us31_09_rbac_protection_and_unauthorized_redirects` | Verifies strict RBAC access controls: Student candidates and unauthenticated visitors attempting to navigate to `/agency/pipeline` are blocked by `ProtectedRoute`. | Security & RBAC |

---

## 4. Backend Unit & Integration Tests (`apps.recruitment.tests.test_us31_cross_client_applicants`)

All 17 backend unit and integration tests authored by Bonny are verified and pass in 88.57s:

| Test Method Name | Description | Status |
| :--- | :--- | :---: |
| `test_agency_can_view_applicants_across_all_client_companies` | Consolidated applicant aggregation across client portfolio (AC#1) | ✅ **PASSED** |
| `test_applicant_list_contains_required_fields` | Response schema includes client, Room, scores, and status (AC#2) | ✅ **PASSED** |
| `test_filter_by_client_company` | Filter applicants by client company ID (AC#3) | ✅ **PASSED** |
| `test_filter_by_room` | Filter applicants by specific Room ID (AC#3) | ✅ **PASSED** |
| `test_filter_by_status` | Filter applicants by status (COMPLETED, ANALYZING, PENDING, FAILED) | ✅ **PASSED** |
| `test_filter_by_shortlisted_true` | Filter shortlisted candidates (`shortlisted=true`) | ✅ **PASSED** |
| `test_filter_by_shortlisted_false` | Filter non-shortlisted candidates (`shortlisted=false`) | ✅ **PASSED** |
| `test_filter_by_hr_decision` | Filter by HR review decision (CONFIRMED, REJECTED, OVERRIDDEN, ON_HOLD) | ✅ **PASSED** |
| `test_search_by_candidate_name` | Live search by candidate full name (AC#3) | ✅ **PASSED** |
| `test_search_by_candidate_email` | Live search by candidate email | ✅ **PASSED** |
| `test_search_by_room_title` | Live search by opening Room title | ✅ **PASSED** |
| `test_search_by_client_company_name` | Live search by client company name | ✅ **PASSED** |
| `test_multi_tenant_isolation_agency_boundaries` | Cross-agency isolation: Agency 1 cannot view Agency 2 applicants (AC#4) | ✅ **PASSED** |
| `test_multi_tenant_retrieve_detail_blocked_for_other_agency` | Detail retrieval across agency boundary returns HTTP 404 | ✅ **PASSED** |
| `test_empty_results_when_agency_has_no_applicants` | Empty pipeline returns HTTP 200 with empty array (AC#5) | ✅ **PASSED** |
| `test_sorting_and_ordering` | Sorting by score descending and date ascending (AC#6) | ✅ **PASSED** |
| `test_summary_stats_endpoint` | Pipeline summary KPI statistics endpoint | ✅ **PASSED** |

---

## 5. Screenshot Evidence Gallery

| Evidence ID | Description | File Path |
| :--- | :--- | :--- |
| **US31-01** | Agency Dashboard navigation & 4 KPI metric cards | [us31_01_navigation_dashboard.png](file:///e:/sdeproject/CareerFlow/tests/reports/screenshots/us31_01_navigation_dashboard.png) |
| **US31-02** | Cross-client applicant aggregation & schema table | [us31_02_cross_client_aggregation.png](file:///e:/sdeproject/CareerFlow/tests/reports/screenshots/us31_02_cross_client_aggregation.png) |
| **US31-03** | Applicant detail breakdown modal (weights, scores & HR decision) | [us31_03_detail_modal_breakdown.png](file:///e:/sdeproject/CareerFlow/tests/reports/screenshots/us31_03_detail_modal_breakdown.png) |
| **US31-04** | Real-time text search and candidate row filtering | [us31_04_search_filtering.png](file:///e:/sdeproject/CareerFlow/tests/reports/screenshots/us31_04_search_filtering.png) |
| **US31-05** | Client selector and cascading Room filter | [us31_05_client_room_filters.png](file:///e:/sdeproject/CareerFlow/tests/reports/screenshots/us31_05_client_room_filters.png) |
| **US31-06** | Status filter, shortlist toggle, and score sorting | [us31_06_status_shortlist_sorting.png](file:///e:/sdeproject/CareerFlow/tests/reports/screenshots/us31_06_status_shortlist_sorting.png) |
| **US31-07** | Empty pipeline state with user guidance and reset CTA | [us31_07_empty_state_handling.png](file:///e:/sdeproject/CareerFlow/tests/reports/screenshots/us31_07_empty_state_handling.png) |
| **US31-08** | Multi-tenant isolation: Agency 1 vs Agency 2 applicant separation | [us31_08_multi_tenant_isolation.png](file:///e:/sdeproject/CareerFlow/tests/reports/screenshots/us31_08_multi_tenant_isolation.png) |
| **US31-09** | Strict RBAC protection: Candidate/unauthenticated access blocked | [us31_09_rbac_protection.png](file:///e:/sdeproject/CareerFlow/tests/reports/screenshots/us31_09_rbac_protection.png) |

---

## 6. Architectural Review & Best Practice Recommendation for Farhana Tahsin Bonny

While all functional and visual acceptance criteria pass 100%, the following frontend architectural optimization is recommended for future refinement:

### 💡 Recommendation: Debounced Search State Pattern (`AgencyApplicantsPipelinePage.tsx`)
In `AgencyApplicantsPipelinePage.tsx` (lines 102–121), the search debounce effect directly invokes `apiGetAgencyCrossClientApplicants` after 250ms:
```tsx
useEffect(() => {
  const timer = setTimeout(() => {
    apiGetAgencyCrossClientApplicants({ ... }).then(...);
  }, 250);
  return () => clearTimeout(timer);
}, [searchQuery]);
```
- **Observation:** On component mount, both the main `useEffect` (for initial data loading) and this `searchQuery` effect execute simultaneously, generating **two network requests** on initial page mount.
- **Optimization:** Debounce `searchQuery` into a state `debouncedSearchQuery`, and include `debouncedSearchQuery` in `fetchData`'s dependency array:
```tsx
const [debouncedSearch, setDebouncedSearch] = useState('');

useEffect(() => {
  const timer = setTimeout(() => setDebouncedSearch(searchQuery), 250);
  return () => clearTimeout(timer);
}, [searchQuery]);

useEffect(() => {
  fetchData();
}, [selectedClientId, selectedRoomId, selectedStatus, selectedShortlist, selectedOrdering, debouncedSearch]);
```
This guarantees a single unified fetch on mount and prevents duplicate network traffic.

---

## 7. Conclusion & Sign-Off

The cross-client applicant pipeline feature (US-31) is exceptionally well-built, performant, and secure.
1. **17 / 17 Backend Unit & Integration Tests Passed (100%)**
2. **9 / 9 Automated Selenium UI Tests Passed (100%)**
3. **Vite Frontend Production Build Clean (0 errors)**
4. **All 6 Acceptance Criteria (AC#1 through AC#6) fully satisfied**

**Peer Reviewer:** MD. Hasanul Mobin ([@hasanulmobin1](https://github.com/hasanulmobin1)) (Project Manager & Full Stack Developer)  
**Final Status:** 🟢 **APPROVED FOR MERGE (Task US-31-T6 Completed)**
