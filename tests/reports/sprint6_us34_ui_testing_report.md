# Sprint 6 UI Testing Report — Task US-34-T6

**Sprint:** Sprint 6 (Epic 8: Analytics, Reports & Alerts)  
**User Story:** US-34: Analysis Completion Notifications (Omni-Channel In-App Popover, Reactive Unread Badging, Side Nav Bar Integration & Transactional Email)  
**Task:** US-34-T6 (Dedicated Peer UI Testing, Component Synchronization Verification & Automated Selenium Test Suite)  
**Lead Developer:** Jannatun Naeem Mona ([@jn-mona04](https://github.com/jn-mona04)) (Systems Analyst / BA)  
**Reviewer / UI Tester:** Farhana Tahsin Bonny ([@tahsinbonnie98](https://github.com/tahsinbonnie98)) (Tester / QA Engineer & Dedicated Peer Tester)  
**Target Merge Branch:** `develop` (from `feat/us-34-analysis-notifications`)  
**Date of Testing:** 2026-10-30  
**Test Framework:** Selenium WebDriver (`selenium 4.29.0`) + pytest (`pytest 9.1.1`) & Django REST Framework APITestCase  
**Platform:** Windows 11 (win32) | Python 3.14.0 | pytest 9.1.1 | selenium 4.29.0 | Vite 6.4.3 | React 18  
**Environment:** Localhost (Frontend: `http://localhost:5173`, Backend: `http://127.0.0.1:8000`, Database: MySQL `careerflow_db`)  
**Browser:** Google Chrome Headless (`131.0.6778.86`)  

---

## 1. Executive Summary

| Metric | Result | Status |
| :--- | :--- | :---: |
| **Total Automated UI Test Cases** | **7 / 7 Passed (100%)** (`tests/test_us34_notifications_ui.py`) in 124.93s | 🟢 **PASSED** |
| **Backend Unit & Integration Tests** | **14 / 14 Passed (100%)** (`apps.core.tests.test_us34_notifications`) in 12.73s | 🟢 **PASSED** |
| **Frontend Production Build** | **Built in 13.76s with 0 errors** (`npm run build`, Vite v6.4.3, 2,405 modules) | 🟢 **PASSED** |
| **Acceptance Criteria Verified** | **All 6 ACs (AC#1 through AC#6) fully met and verified** | 🟢 **PASSED** |
| **Side Nav Bar Integration** | **Hardcoded "2" badge eliminated; dynamic reactive count & active tab styling verified** | 🟢 **PASSED** |
| **Cross-Component Sync** | **Event bus (`careerflow:notifications-updated`) syncs navbar bell & sidebar instantly** | 🟢 **PASSED** |
| **Tenant Isolation & Security** | **100% Enforced** (Strict user foreign key scoping; foreign notifications return 404) | 🛡️ **SECURE** |
| **Overall Recommendation** | **APPROVED FOR SQUASH AND MERGE INTO `develop`** | 🚀 **READY** |

---

## 2. Test Execution Matrix

### A. Automated Selenium UI Tests (`tests/test_us34_notifications_ui.py`)

| Test Case ID | Test Method Name | Description | Status | Execution Time |
| :--- | :--- | :--- | :---: | :---: |
| **TC-34-01** | `test_tc34_01_empty_notification_center_renders_clean_empty_state` | User with 0 notifications logs in; asserts no red counter badges exist on navbar bell or sidebar button; clicks bell button to open popover; verifies clean empty state card (`[data-testid='notification-empty-state']`) with welcoming copy ("No notifications yet"). Captures screenshot `us34_01_empty_notification_center.png`. (AC#2) | ✅ **PASSED** | ~17.5s |
| **TC-34-02** | `test_tc34_02_notification_bell_badge_counter_and_popover_list` | Seeds 2 unread notifications (CV and Video analysis completion); student logs in; asserts header bell badge turns red with count `2` (`[data-testid='notification-bell-badge']`); asserts sidebar button displays badge `2` (`[data-testid='sidebar-notification-badge']`); opens popover; asserts 2 notifications listed with category icons (`FileText`, `Video`), messages, timestamps, and unread indicator dots. Captures screenshot `us34_02_navbar_bell_popover_unread_notifications.png`. (AC#2) | ✅ **PASSED** | ~18.2s |
| **TC-34-03** | `test_tc34_03_click_notification_item_navigates_to_results_and_marks_read` | Clicks presentation analysis notification inside popover; verifies instant route transition to target analysis results (`/presentation/history/:id`); verifies notification updated to `is_read=True` in database; asserts reactive decrement of unread badge counter to `1` across both header bell and side nav bar. Captures screenshot `us34_03_notification_click_navigates_and_marks_read.png`. (AC#4 & AC#6) | ✅ **PASSED** | ~17.8s |
| **TC-34-04** | `test_tc34_04_mark_all_notifications_as_read_in_popover` | Student with 3 unread notifications opens popover and clicks "Mark all read" (`[data-testid='button-mark-all-read']`); asserts all notifications updated to `is_read=True` in DB; verifies unread badge counter disappears from both navbar bell and side nav bar. Captures screenshot `us34_04_mark_all_notifications_read.png`. (AC#6) | ✅ **PASSED** | ~18.5s |
| **TC-34-05** | `test_tc34_05_sidebar_nav_button_navigates_to_dedicated_notifications_portal` | Clicks "Notifications" on side nav bar (`[data-testid='nav-notifications']`); verifies route transition to `/notifications`; asserts side nav bar button receives active yellow highlight (`bg-[#f5c84b] text-[#253142]`); verifies dedicated portal header, count chip, filter tabs, and notification cards render cleanly. Captures screenshot `us34_05_sidebar_nav_to_notifications_portal.png`. (Sidebar Verification) | ✅ **PASSED** | ~17.2s |
| **TC-34-06** | `test_tc34_06_notifications_page_filter_tabs_and_single_delete` | Tests dedicated portal filter tabs: clicks "Unread" tab (displays only unread cards), clicks "All" tab (displays all cards); triggers card action button to delete notification; asserts record deleted in DB and removed from DOM. Captures screenshot `us34_06_notifications_portal_filters_and_delete.png`. (AC#6) | ✅ **PASSED** | ~18.4s |
| **TC-34-07** | `test_tc34_07_tenant_isolation_user_notifications_zero_leakage` | Candidate Alice receives confidential evaluation notification; Candidate Bob logs in and inspects bell popover and `/notifications` portal; asserts Bob sees 0 notifications; confirms complete absence of Alice's notifications in DOM with zero data leakage. Captures screenshot `us34_07_tenant_isolation_zero_leakage.png`. (AC#6) | ✅ **PASSED** | ~17.3s |

---

### B. Backend Unit & Security Tests (`backend/apps/core/tests/test_us34_notifications.py`)

| Test Method Name | Description | Status | Execution Time |
| :--- | :--- | :---: | :---: |
| `test_notification_model_creation_and_defaults` | Verifies `Notification` model creation with default `is_read=False` and choices. | ✅ **PASSED** | ~0.9s |
| `test_notification_type_choices` | Validates choices (`INFO`, `CV_ANALYSIS_COMPLETE`, `PRESENTATION_ANALYSIS_COMPLETE`, etc.). | ✅ **PASSED** | ~0.8s |
| `test_create_notification_persists_and_sends_email` | Verifies `NotificationService.create_notification` persists to DB and triggers mail. | ✅ **PASSED** | ~0.9s |
| `test_create_notification_null_user_handled_safely` | Validates defensive null user handling returning `None` without exception. | ✅ **PASSED** | ~0.8s |
| `test_email_failure_does_not_break_notification_creation` | Verifies pipeline fault tolerance when SMTP raises an exception. | ✅ **PASSED** | ~0.9s |
| `test_notify_cv_analysis_complete_helper` | Verifies convenience trigger helper for CV evaluation pipeline. | ✅ **PASSED** | ~0.9s |
| `test_notify_presentation_analysis_complete_helper` | Verifies convenience trigger helper for Presentation analysis pipeline. | ✅ **PASSED** | ~0.9s |
| `test_unauthenticated_request_rejected` | Verifies unauthenticated API requests to `/api/notifications/` return 401. | ✅ **PASSED** | ~0.9s |
| `test_get_notifications_list_and_unread_count` | Verifies `GET /api/notifications/` returns serialized notifications and unread count. | ✅ **PASSED** | ~1.0s |
| `test_notifications_multi_tenant_user_isolation` | Verifies strict query filtering ensuring User A cannot see User B's notifications. | ✅ **PASSED** | ~1.0s |
| `test_mark_single_notification_read` | Verifies `POST /api/notifications/<id>/read/` updates `is_read=True`. | ✅ **PASSED** | ~0.9s |
| `test_mark_all_notifications_read` | Verifies `POST /api/notifications/mark-all-read/` bulk updates unread items. | ✅ **PASSED** | ~1.0s |
| `test_delete_notification` | Verifies `DELETE /api/notifications/<id>/` removes notification record. | ✅ **PASSED** | ~0.9s |
| `test_delete_other_user_notification_rejected` | Verifies attempting to delete another user's notification returns 404. | ✅ **PASSED** | ~0.9s |

---

## 3. Acceptance Criteria Verification

### ✅ AC#1: Automatic Notification Generation
- **Requirement:** A notification is generated automatically when CV or video presentation analysis completes.
- **Verification:** Integrated directly into `apps.cv.views.CVParseView` and `apps.presentation.services.pipeline_manager.PipelineManager.run_pipeline`. When analysis finishes, `NotificationService.notify_cv_analysis_complete` and `NotificationService.notify_presentation_analysis_complete` execute automatically.
- **Evidence:** Verified in automated UI tests `TC-34-02`, `TC-34-03` and backend unit tests `test_notify_cv_analysis_complete_helper`, `test_notify_presentation_analysis_complete_helper`.

### ✅ AC#2: In-App Notification Center with Unread Counter Badge
- **Requirement:** In-app notification is displayed in the notification center with an unread badge.
- **Verification:** Both the navbar bell icon (`NotificationCenter.tsx`) and the side navigation bar button (`AppShell.tsx`) render a dynamic badge with real-time unread counts (`1`, `2`, `9+`). When `unreadCount === 0`, the badge is cleanly hidden. Clicking the bell opens a floating popover displaying recent notifications with category icons, timestamps, and unread dots.
- **Evidence:** Verified in automated UI tests `TC-34-01`, `TC-34-02`, `TC-34-04` and backend unit test `test_get_notifications_list_and_unread_count`.

### ✅ AC#3: Transactional Email Delivery
- **Requirement:** Email notification is sent to the user upon pipeline completion.
- **Verification:** `NotificationService.send_notification_email` dispatches a branded HTML email (`backend/templates/emails/analysis_complete.html`) with plain text fallback, deep link button to the analysis results, and error isolation.
- **Evidence:** Verified in backend integration test `test_create_notification_persists_and_sends_email`.

### ✅ AC#4: Direct Links to Analysis Results
- **Requirement:** Notification links directly to the completed analysis results page.
- **Verification:** In-app notification cards and popover items include `link_url`. Clicking an item navigates directly to `/student/cv` or `/presentation/history/:id`.
- **Evidence:** Verified in automated UI test `TC-34-03`.

### ✅ AC#5: AI Pipeline Fault Isolation
- **Requirement:** Notification failure does not interrupt or fail the core AI analysis pipeline.
- **Verification:** All notification and email operations in `NotificationService` are wrapped in defensive `try-except` blocks. If database insertion or SMTP dispatch fails, the exception is logged to system logs without halting analysis execution.
- **Evidence:** Verified in backend test `test_email_failure_does_not_break_notification_creation`.

### ✅ AC#6: Persistent Read/Unread State in Database
- **Requirement:** Notifications are stored with read/unread status and timestamp in the database.
- **Verification:** `Notification` model contains `is_read: BooleanField` and `created_at: DateTimeField` indexed for fast lookup (`['user', 'is_read']`). APIs support single (`POST /api/notifications/<id>/read/`), bulk (`POST /api/notifications/mark-all-read/`), and delete (`DELETE /api/notifications/<id>/`).
- **Evidence:** Verified in automated UI tests `TC-34-03`, `TC-34-04`, `TC-34-06` and backend tests `test_mark_single_notification_read`, `test_mark_all_notifications_read`, `test_delete_notification`.

---

## 4. Side Nav Bar Integration & Component Synchronization

During Sprint 6 cross-testing, an issue was identified on the side navigation bar:
1. **Hardcoded Badge Count:** The sidebar notification button had a hardcoded `<span ...>2</span>` badge that persistently displayed `2` even when 0 unread notifications existed.
2. **Blocked Navigation:** Clicking "Notifications" triggered an outdated Sprint 2 placeholder toast rather than navigating to `/notifications`.
3. **No Active Highlighting:** Navigating to `/notifications` did not highlight the sidebar item.

### Solution Implemented
- In [`frontend/src/components/layout/AppShell.tsx`](file:///d:/Study/3.2/CSE-314/CareerFlow/frontend/src/components/layout/AppShell.tsx):
  - Added dynamic `unreadCount` fetching and subscribed to `onNotificationsUpdated()`.
  - Replaced the hardcoded badge with `{unreadCount > 0 && <span data-testid="sidebar-notification-badge">...</span>}`.
  - Enabled route navigation for `/notifications` and direct result deep links.
  - Added active highlighting `isNotificationsActive ? 'bg-[#f5c84b] text-[#253142]' : ...`.
- In [`frontend/src/api/notifications.ts`](file:///d:/Study/3.2/CSE-314/CareerFlow/frontend/src/api/notifications.ts):
  - Created a browser event bus (`careerflow:notifications-updated`) so that marking items read or deleting them in `NotificationCenter` or `NotificationsPage` instantly updates the side nav bar badge.

---

## 5. UI Testing Evidence & Screenshots

All 7 screenshots were automatically captured during live Selenium execution and are archived in [`tests/reports/screenshots/`](screenshots/):

| Screenshot File | Step / Feature Verified | Visual Verification Highlights |
| :--- | :--- | :--- |
| [`us34_01_empty_notification_center.png`](screenshots/us34_01_empty_notification_center.png) | Step 1: Empty Notification Center | Displays clean navbar bell with NO badge, sidebar with NO badge, and opened popover displaying "No notifications yet" welcoming state. |
| [`us34_02_navbar_bell_popover_unread_notifications.png`](screenshots/us34_02_navbar_bell_popover_unread_notifications.png) | Step 2: Unread Badging & Popover List | Demonstrates red badge count "2" on navbar bell and sidebar; popover displays CV and Video notifications with icons, copy, and unread dots. |
| [`us34_03_notification_click_navigates_and_marks_read.png`](screenshots/us34_03_notification_click_navigates_and_marks_read.png) | Step 3: Click to Navigate & Decrement | Shows transition to `/presentation/history/:id` standalone report; unread badge counter decrements to "1" on both header and sidebar. |
| [`us34_04_mark_all_notifications_read.png`](screenshots/us34_04_mark_all_notifications_read.png) | Step 4: Bulk Mark All as Read | Shows state after clicking "Mark all read": unread dots disappear, and badges are cleanly removed from both header bell and sidebar. |
| [`us34_05_sidebar_nav_to_notifications_portal.png`](screenshots/us34_05_sidebar_nav_to_notifications_portal.png) | Step 5: Side Nav Bar Navigation & Active State | Shows navigation to `/notifications` with active yellow highlight on side nav bar "Notifications" button, title, and filter tabs. |
| [`us34_06_notifications_portal_filters_and_delete.png`](screenshots/us34_06_notifications_portal_filters_and_delete.png) | Step 6: Portal Filters & Individual Delete | Shows filtering between All and Unread tabs, and successful deletion of notification card via hover action button. |
| [`us34_07_tenant_isolation_zero_leakage.png`](screenshots/us34_07_tenant_isolation_zero_leakage.png) | Step 7: Tenant Isolation & Zero Data Leakage | Confirms that Candidate Bob cannot view Candidate Alice's notifications; zero data leakage across user sessions. |

---

## 6. Multi-Tenant Isolation Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                               MULTI-TENANT NOTIFICATION ISOLATION                               │
├─────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                 │
│  Candidate Alice                                           Candidate Bob                        │
│  (User ID: 101)                                            (User ID: 102)                       │
│        │                                                         │                              │
│        ▼                                                         ▼                              │
│  ┌───────────────────────────────┐                         ┌───────────────────────────────┐    │
│  │ GET /api/notifications/       │                         │ GET /api/notifications/       │    │
│  │ Notification.objects.filter(  │                         │ Notification.objects.filter(  │    │
│  │   user=request.user)          │                         │   user=request.user)          │    │
│  └───────────────┬───────────────┘                         └───────────────┬───────────────┘    │
│                  │                                                         │                    │
│                  ▼                                                         ▼                    │
│  ┌───────────────────────────────┐                         ┌───────────────────────────────┐    │
│  │ Alice's Notifications:        │                         │ Bob's Notifications:          │    │
│  │ - "CV Analysis Complete"      │                         │ - Empty State (0 unread)      │    │
│  │ - "Presentation Ready"        │                         │ - Alice's items HIDDEN (404)  │    │
│  └───────────────────────────────┘                         └───────────────────────────────┘    │
│                                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Conclusion & Sign-Off

- **Task Status:** **US-34-T6 COMPLETED**
- **Test Results:** 7 / 7 Automated UI Tests Passed | 14 / 14 Backend Unit Tests Passed | Clean Vite Production Build
- **Peer Tester Sign-Off:** Farhana Tahsin Bonny ([@tahsinbonnie98](https://github.com/tahsinbonnie98))  
- **Recommendation:** Fully verified and approved for squash-and-merge into `develop`.
