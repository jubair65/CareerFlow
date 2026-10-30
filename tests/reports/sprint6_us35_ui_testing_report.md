# Sprint 6 UI Testing Report — Task US-35-T6

**Sprint:** Sprint 6 (Epic 8: Analytics, Reports & Alerts)  
**User Story:** US-35: Applicant Application Status Notifications & Portal Navigation Fixes  
**Task:** US-35-T6 (Dedicated Peer UI Automation Testing, Portal Component Synchronization & Selenium Test Suite)  
**Lead Developer:** Maria ([@Maria-07-222](https://github.com/Maria-07-222))  
**Reviewer / UI Automation Tester:** Farhana Tahsin Bonny ([@tahsinbonnie98](https://github.com/tahsinbonnie98)) (Tester / QA Engineer & Dedicated Peer Tester)  
**Target Merge Branch:** `develop` (from `feat/us-35-applicant-status-notification`)  
**Date of Testing:** 2026-10-30  
**Test Framework:** Selenium WebDriver (`selenium 4.29.0`) + pytest (`pytest 9.1.1`) & Django REST Framework APITestCase  
**Platform:** macOS Darwin (arm64) | Python 3.14.2 | pytest 9.1.1 | selenium 4.29.0 | Vite 6.4.3 | React 18  
**Environment:** Localhost (Frontend: `http://localhost:5173`, Backend: `http://127.0.0.1:8000`, Database: MySQL `careerflow_db`)  
**Browser:** Google Chrome / Edge Headless (1920x1080)  

---

## 1. Executive Summary

| Metric | Result | Status |
| :--- | :--- | :---: |
| **Total Automated UI Test Cases** | **8 / 8 Passed (100%)** (`tests/test_us35_applicant_status_notifications_ui.py`) in 83.48s | 🟢 **PASSED** |
| **Backend Unit & Integration Tests** | **8 / 8 Passed (100%)** (`apps.recruitment.tests.test_us35_status_notifications`) in 10.07s | 🟢 **PASSED** |
| **Frontend Production Build** | **Built in 1.77s with 0 errors** (`npm run build`, Vite v6.4.3, 2,413 modules transformed) | 🟢 **PASSED** |
| **Acceptance Criteria Verified** | **All 6 ACs (AC#1 through AC#6) fully met and verified** | 🟢 **PASSED** |
| **Applicant Portal UI (/applications/my-status)** | **4-stage milestone tracker, score breakdown, hiring notes, audit accordion verified** | 🟢 **PASSED** |
| **Sidebar Navigation (HR & Agency Portals)** | **Dedicated views (/hr/applicants, /hr/shortlisted, /hr/reports, /agency/shortlisted, /agency/reports) render cleanly** | 🟢 **PASSED** |
| **Agency Forward Modal Render Trap** | **Eliminated unconditional mount; Backdrop click, ESC handling, candidate sync verified** | 🟢 **PASSED** |
| **Shortlist Rule Configuration** | **Rule configuration triggers on /agency/shortlisted and /agency/rooms open criteria modal** | 🟢 **PASSED** |
| **Multi-Tenant Candidate Isolation** | **100% Enforced** (Candidate Bob cannot view Candidate Alice's applications or decisions) | 🛡️ **SECURE** |
| **Overall Recommendation** | **APPROVED FOR SQUASH AND MERGE INTO `develop`** | 🚀 **READY** |

---

## 2. Test Execution Matrix

### A. Automated Selenium UI Tests (`tests/test_us35_applicant_status_notifications_ui.py`)

| Test Case ID | Test Method Name | Description | Status | Execution Time |
| :--- | :--- | :--- | :---: | :---: |
| **TC-35-01** | `test_tc35_01_applicant_status_page_milestones_and_shortlisted_badge` | Creates shortlisted candidate application with composite final score (93/100), CV skill match (91/100), Video presentation (95/100), and hiring note; logs in as candidate and navigates to `/applications/my-status`; verifies 4-stage milestone stepper (Submitted, AI Analysis, HR Review, Decision: Shortlisted); asserts shortlisted badge (`[data-testid='badge-status-shortlisted-<id>']`), score cards, and decision notes render properly. Captures screenshot `us35_01_applicant_status_stepper_shortlisted.png`. (AC#2, AC#3) | ✅ **PASSED** | ~11.8s |
| **TC-35-02** | `test_tc35_02_applicant_status_rejected_state_and_filter_tabs` | Seeds 3 applications in different states (Shortlisted, Not Selected with rejection note, and In Review); tests interactive status filter pills (`All Applications`, `Shortlisted`, `In Review`, `Not Selected`); verifies card filtering, badge counters, and rejected badge display (`[data-testid='badge-status-rejected-<id>']`). Captures screenshot `us35_02_applicant_status_rejected_and_filters.png`. (AC#2, AC#3) | ✅ **PASSED** | ~11.2s |
| **TC-35-03** | `test_tc35_03_notification_audit_log_accordion_toggle` | Seeds candidate application with 2 `StatusNotificationLog` records (`SHORTLISTED`, `CONFIRMED`); candidate opens portal; verifies accordion toggle displays event count (`Notification Audit Log (2 events)`); expands accordion and verifies container renders delivery timestamps, event types, and delivery indicators (`(Email delivered)`). Captures screenshot `us35_03_notification_audit_log_accordion.png`. (AC#6) | ✅ **PASSED** | ~10.4s |
| **TC-35-04** | `test_tc35_04_tenant_isolation_candidate_sees_only_own_applications` | Seeds confidential evaluation application for Candidate Alice; Candidate Bob (0 applications) logs in and inspects `/applications/my-status`; verifies clean empty state card (`[data-testid='empty-applications-state']`) with practice studio CTA; confirms Alice's application title, scores, and decision notes are 100% absent from Bob's DOM (zero data leakage). Captures screenshot `us35_04_tenant_isolation_empty_state.png`. (AC#4) | ✅ **PASSED** | ~9.8s |
| **TC-35-05** | `test_tc35_05_sidebar_navigation_to_status_portal` | Tests navigation into the applicant status portal from the candidate side nav bar button (`[data-testid='nav-applications']`) and dashboard metric card (`[data-testid='card-applications-status']`); verifies instant transition to `/applications/my-status`, active tab styling, and header rendering. Captures screenshot `us35_05_sidebar_navigation_to_status_portal.png`. (Sidebar Navigation) | ✅ **PASSED** | ~10.1s |
| **TC-35-06** | `test_tc35_06_hr_portal_sidebar_navigation_dedicated_views` | Logs in as HR Manager; clicks side nav bar items sequentially: Applicants (`/hr/applicants`), Shortlisted (`/hr/shortlisted`), and Reports (`/hr/reports`); asserts each dedicated view renders cleanly without route bouncing or unhandled exceptions. Captures screenshot `us35_06_hr_portal_navigation_dedicated_views.png`. (Sidebar Navigation) | ✅ **PASSED** | ~9.9s |
| **TC-35-07** | `test_tc35_07_agency_portal_sidebar_navigation_dedicated_views` | Logs in as Agency Admin; clicks side nav bar items: Shortlisted (`/agency/shortlisted`) and Reports (`/agency/reports`); confirms pages load cleanly and verifies `ForwardCandidatesModal` is NOT trapped or blocking the screen on initial mount. Captures screenshot `us35_07_agency_portal_navigation_dedicated_views.png`. (Modal Trap Fix) | ✅ **PASSED** | ~9.6s |
| **TC-35-08** | `test_tc35_08_agency_shortlisted_configure_rules_and_forward_modal` | Seeds Agency Client, Recruitment Room, and shortlisted candidate; on `/agency/shortlisted`, clicks "Configure Shortlist Rules" to verify criteria modal opens; closes modal; confirms "Forward to Client" button is initially disabled with 0 candidates; selects candidate checkbox and confirms button activates (`Forward to Client (1)`); opens `ForwardCandidatesModal`; verifies auto-populated client contact info; closes modal cleanly via Cancel. Captures screenshot `us35_08_agency_shortlist_config_and_forward_modal.png`. (Agency Portal Actions) | ✅ **PASSED** | ~10.6s |

---

### B. Backend Unit & Security Tests (`backend/apps/recruitment/tests/test_us35_status_notifications.py`)

| Test Method Name | Description | Status | Execution Time |
| :--- | :--- | :---: | :---: |
| `test_shortlist_transition_creates_in_app_notification_and_audit_log` | Verifies that updating an application to `is_shortlisted=True` triggers in-app notification creation with link `/applications/my-status` and creates a `StatusNotificationLog` audit record. | ✅ **PASSED** | ~1.2s |
| `test_rejection_transition_creates_in_app_notification_and_audit_log` | Verifies that setting `hr_decision='REJECTED'` creates an in-app rejection notification and logs `StatusType.REJECTED` in `StatusNotificationLog`. | ✅ **PASSED** | ~1.3s |
| `test_no_notification_if_status_remains_undecided` | Verifies signal idempotency: saving an application without changing shortlist status or HR decision does not generate redundant notifications. | ✅ **PASSED** | ~1.1s |
| `test_email_dispatch_handled_without_breaking_on_smtp_error` | Simulates an SMTP failure; verifies `StatusNotificationLog` records `email_sent=False` with error message, while the candidate's hiring decision persists safely without database rollback. | ✅ **PASSED** | ~1.3s |
| `test_email_template_contains_candidate_and_decision_details` | Validates rendered HTML transactional email templates (`application_shortlisted.html`, `application_rejected.html`) for proper branding, candidate name, room title, score, and decision note. | ✅ **PASSED** | ~1.2s |
| `test_candidate_my_status_api_enforces_tenant_isolation` | Verifies `GET /api/recruitment/applications/my-status/` scopes queries strictly to `request.user`, preventing access to other candidates' application records. | ✅ **PASSED** | ~1.3s |
| `test_candidate_detail_status_forbidden_for_other_candidates` | Verifies `GET /api/recruitment/applications/<id>/status/` returns `403 Forbidden` when Candidate B attempts to inspect Candidate A's application. | ✅ **PASSED** | ~1.2s |
| `test_hr_confirmed_decision_dispatches_notification` | Verifies that recording an explicit HR decision via `record_candidate_review_decision` triggers `dispatch_status_notification`. | ✅ **PASSED** | ~1.4s |

---

## 3. Acceptance Criteria Verification

### ✅ AC#1: Real-time Application Status Notification
- **Requirement:** Applicant receives a notification when their application status changes (shortlisted or rejected).
- **Verification:** Pre-save and post-save signals in `backend/apps/recruitment/signals.py` monitor state transitions on `CandidateApplication`. When `is_shortlisted` transitions from `False` to `True` or `hr_decision` updates to `'REJECTED'`, `'CONFIRMED'`, or `'OVERRIDDEN'`, the signal automatically triggers `dispatch_status_notification`.
- **Evidence:** Verified in automated UI tests `TC-35-01`, `TC-35-02` and backend tests `test_shortlist_transition_creates_in_app_notification_and_audit_log`, `test_rejection_transition_creates_in_app_notification_and_audit_log`.

### ✅ AC#2: Applicant Portal Status Page & 4-Stage Milestone Stepper
- **Requirement:** Notification is sent by email and displayed in applicant's application portal status page (`/applications/my-status`).
- **Verification:** Built `ApplicantStatusPage.tsx` at route `/applications/my-status`. Features an interactive 4-stage milestone stepper:
  1. **Stage 1 (Submitted):** Application CV and presentation video successfully received.
  2. **Stage 2 (AI Analysis):** Multi-modal CV skill matching and video delivery analysis completed.
  3. **Stage 3 (HR Review):** Hiring committee review of candidate dossier and score breakdown.
  4. **Stage 4 (Decision):** Outcome: Shortlisted, Not Selected, or On Hold.
- **Evidence:** Verified in automated UI tests `TC-35-01`, `TC-35-02`, `TC-35-05`.

### ✅ AC#3: HR Decision Reflection & Live Multi-Modal Score Breakdowns
- **Requirement:** Status shown matches the HR Manager's confirmed decision.
- **Verification:** `ApplicantApplicationStatusSerializer` exposes confirmed HR decisions (`CONFIRMED`, `REJECTED`, `OVERRIDDEN`, `ON_HOLD`), composite final scores (`final_score`), CV match scores (`cv_score`), and presentation video scores (`video_score`). The UI renders dedicated status badges and score cards reflecting real-time HR decisions.
- **Evidence:** Verified in automated UI tests `TC-35-01`, `TC-35-02` and backend test `test_hr_confirmed_decision_dispatches_notification`.

### ✅ AC#4: Strict Multi-Tenant Candidate Isolation & Privacy
- **Requirement:** Applicants can only see their own application status (strict candidate isolation).
- **Verification:** `ApplicantStatusListView` explicitly filters `CandidateApplication.objects.filter(candidate=request.user)`. `ApplicantStatusDetailView` checks `application.candidate != request.user` and returns `403 Forbidden` if unauthorized.
- **Evidence:** Verified in automated UI test `TC-35-04` (Candidate Bob sees 0 applications and 0 leakage of Alice's confidential dossier) and backend tests `test_candidate_my_status_api_enforces_tenant_isolation`, `test_candidate_detail_status_forbidden_for_other_candidates`.

### ✅ AC#5: Non-Blocking Fault Isolation for Email Dispatch
- **Requirement:** Failed email delivery is logged and handled gracefully without rolling back decision.
- **Verification:** `dispatch_status_notification` catches `smtplib.SMTPException` and general exceptions defensively. The error message is saved into `StatusNotificationLog` (`email_sent=False`, `error_message=str(e)`), ensuring that an external SMTP timeout never rolls back an HR hiring decision or causes a 500 server error.
- **Evidence:** Verified in backend unit test `test_email_dispatch_handled_without_breaking_on_smtp_error`.

### ✅ AC#6: Comprehensive Audit Logging in StatusNotificationLog
- **Requirement:** Sent notifications are stored in audit logs (`StatusNotificationLog`) for later reference.
- **Verification:** `StatusNotificationLog` records `application`, `recipient_email`, `status_type`, `email_sent`, `error_message`, and `dispatched_at`. The frontend renders an expandable accordion (`[data-testid='button-toggle-audit-logs-<id>']`) detailing dispatch events, timestamps, and delivery statuses.
- **Evidence:** Verified in automated UI test `TC-35-03` and backend test `test_shortlist_transition_creates_in_app_notification_and_audit_log`.

---

## 4. Sidebar Navigation & Portal Window Fixes

During Sprint 6 peer review and cross-testing, multiple navigation and portal interaction fixes were implemented and verified:

### 1. Dedicated HR Portal Navigation
- **Fixed:** Side navbar buttons previously pointed to generic paths or placeholder toasts.
- **Resolution:** Mapped dedicated views in [`AppShell.tsx`](file:///Users/nafisatabassummaria/Study/3.2/Project/CareerFlow/frontend/src/components/layout/AppShell.tsx) and [`App.tsx`](file:///Users/nafisatabassummaria/Study/3.2/Project/CareerFlow/frontend/src/App.tsx):
  - Applicants: `/hr/applicants` (`HrApplicantsPage.tsx`)
  - Shortlisted: `/hr/shortlisted` (`HrShortlistedPage.tsx`)
  - Reports: `/hr/reports` (`HrReportsPage.tsx`)
- **Verification:** Verified in `TC-35-06`.

### 2. Dedicated Agency Portal Navigation
- **Fixed:** Agency navbar buttons for Shortlisted and Reports had no dedicated views.
- **Resolution:** Mapped dedicated views:
  - Shortlisted: `/agency/shortlisted` (`AgencyShortlistedPage.tsx`)
  - Reports: `/agency/reports` (`AgencyReportsPage.tsx`)
- **Verification:** Verified in `TC-35-07`.

### 3. ForwardCandidatesModal Render Trap Elimination
- **Fixed:** In previous revisions, `ForwardCandidatesModal` was mounted unconditionally on page load with 0 candidates, causing a grey backdrop overlay that blocked user interaction.
- **Resolution:** Added conditional rendering (`if (isOpen === false) return null;`), backdrop click-to-close, ESC key listener, and synchronization of client company contact details.
- **Verification:** Verified in `TC-35-07` and `TC-35-08`.

### 4. Agency Room Shortlist Configuration
- **Enhancement:** Added the "Configure Shortlist Rules" button (`data-testid="button-agency-config-shortlist"`) to `/agency/shortlisted` and a "Shortlist" button (`data-testid="button-config-shortlist-<room.id>"`) to `/agency/rooms` so agency admins can easily configure and re-evaluate qualification criteria without manual URL manipulation.
- **Verification:** Verified in `TC-35-08`.

---

## 5. UI Testing Evidence & Screenshots

All 8 screenshots were captured during live Selenium execution and are archived in [`tests/reports/screenshots/`](screenshots/):

| Screenshot File | Step / Feature Verified | Visual Verification Highlights |
| :--- | :--- | :--- |
| [`us35_01_applicant_status_stepper_shortlisted.png`](screenshots/us35_01_applicant_status_stepper_shortlisted.png) | Step 1: 4-Stage Milestone Stepper & Shortlist Badge | Demonstrates 4-stage milestone tracker (all 4 stages completed), green "Shortlisted" badge, composite final score (93/100), multi-modal breakdown cards (CV: 91, Video: 95), and hiring committee feedback notes. |
| [`us35_02_applicant_status_rejected_and_filters.png`](screenshots/us35_02_applicant_status_rejected_and_filters.png) | Step 2: Status Filtering & Rejection State | Demonstrates interactive status filter pills (`All Applications`, `Shortlisted`, `In Review`, `Not Selected`); shows red "Not Selected" badge with hiring committee threshold feedback note. |
| [`us35_03_notification_audit_log_accordion.png`](screenshots/us35_03_notification_audit_log_accordion.png) | Step 3: Expandable Notification Audit Log | Demonstrates expanded audit log accordion displaying event counts (`2 events`), event categories (`Shortlisted`, `Confirmed`), email delivery status (`(Email delivered)`), and dispatch timestamps. |
| [`us35_04_tenant_isolation_empty_state.png`](screenshots/us35_04_tenant_isolation_empty_state.png) | Step 4: Candidate Tenant Isolation & Empty State | Demonstrates candidate tenant privacy: Candidate Bob sees a clean empty state card with CTA buttons ("Open Practice Studio", "Review CV Studio") and zero access to Candidate Alice's confidential dossier. |
| [`us35_05_sidebar_navigation_to_status_portal.png`](screenshots/us35_05_sidebar_navigation_to_status_portal.png) | Step 5: Candidate Side Nav Bar Integration | Demonstrates seamless transition into `/applications/my-status` via the side navbar "Applications" button and dashboard metric card, with active tab styling and breadcrumbs. |
| [`us35_06_hr_portal_navigation_dedicated_views.png`](screenshots/us35_06_hr_portal_navigation_dedicated_views.png) | Step 6: HR Portal Dedicated Navigation Views | Demonstrates clean navigation across HR Portal dedicated windows (`/hr/applicants`, `/hr/shortlisted`, `/hr/reports`) without route bouncing. |
| [`us35_07_agency_portal_navigation_dedicated_views.png`](screenshots/us35_07_agency_portal_navigation_dedicated_views.png) | Step 7: Agency Portal Navigation & Modal Trap Elimination | Demonstrates `/agency/shortlisted` and `/agency/reports` rendering with zero backdrop blocking, no trapped modals, and fully functional controls. |
| [`us35_08_agency_shortlist_config_and_forward_modal.png`](screenshots/us35_08_agency_shortlist_config_and_forward_modal.png) | Step 8: Shortlist Configuration & Forwarding Workflow | Demonstrates opening the shortlist criteria modal via "Configure Shortlist Rules", dynamic activation of "Forward to Client (1)", and opening `ForwardCandidatesModal` with auto-populated client contact details. |

---

## 6. Architectural Flow & Isolation Design

### Real-Time Status Notification Dispatch Flow

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        US-35 REAL-TIME NOTIFICATION DISPATCH FLOW                      │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│   HR Manager Decision / Auto-Shortlist Engine                                          │
│        │                                                                               │
│        ▼                                                                               │
│   CandidateApplication.save()                                                          │
│        │                                                                               │
│        ├──► pre_save Signal (captures previous is_shortlisted & hr_decision)           │
│        │                                                                               │
│        └──► post_save Signal (detects status transition)                               │
│                   │                                                                    │
│                   ▼                                                                    │
│             dispatch_status_notification(application, status_type)                     │
│                   │                                                                    │
│                   ├──► 1. In-App Notification (Notification.objects.create)           │
│                   │       └── Type: APPLICATION_STATUS                                 │
│                   │       └── Link: /applications/my-status                           │
│                   │                                                                    │
│                   ├──► 2. Transactional HTML Email (send_status_email)                 │
│                   │       ├── application_shortlisted.html / application_rejected.html │
│                   │       └── Defensive try/except (Fault Isolation)                  │
│                   │                                                                    │
│                   └──► 3. Audit Log (StatusNotificationLog.objects.create)             │
│                           └── Records recipient, status_type, email_sent, error        │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Multi-Tenant Candidate Isolation

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                          MULTI-TENANT CANDIDATE ISOLATION                              │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│   Candidate Alice (Student ID: 101)             Candidate Bob (Student ID: 102)        │
│          │                                             │                               │
│          ▼                                             ▼                               │
│   GET /api/recruitment/applications/my-status/  GET /api/recruitment/applications/my-status/ │
│          │                                             │                               │
│   CandidateApplication.objects.filter(          CandidateApplication.objects.filter(   │
│       candidate=request.user)                       candidate=request.user)            │
│          │                                             │                               │
│          ▼                                             ▼                               │
│   Alice's Private Dossier:                      Bob's Empty State:                     │
│   - Senior Cloud Architect (Score: 93/100)      - "No applications found"              │
│   - Status: Shortlisted                         - Zero data leakage of Alice's dossier │
│   - Hiring Committee Decision Note              - Alice's card IDs absent (404/empty)  │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Conclusion & Sign-Off

- **Task Status:** **US-35-T6 COMPLETED**
- **Automated UI Test Results:** **8 / 8 Passed (100%)** in 83.48s (`tests/test_us35_applicant_status_notifications_ui.py`)
- **Backend Test Results:** **8 / 8 Passed (100%)** in 10.07s (`apps.recruitment.tests.test_us35_status_notifications`)
- **Frontend Build:** **Vite v6.4.3 production bundle built in 1.77s with 0 errors**
- **Peer Tester Sign-Off:** Farhana Tahsin Bonny ([@tahsinbonnie98](https://github.com/tahsinbonnie98))  
- **Reviewer Recommendation:** All acceptance criteria verified, navigation fixes and modal traps resolved, zero merge blockers. **APPROVED FOR SQUASH AND MERGE INTO `develop`**.
