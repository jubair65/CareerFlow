# Sprint 4 UI Testing Report — Task US-20-T6

**Sprint:** Sprint 4 (Recruitment Rooms & Candidate Submission)  
**User Story:** US-20: CV-to-Video Weighting Configuration  
**Task:** US-20-T6 (Peer UI Testing for CV-to-Video Weighting Screen & Sliders)  
**Peer Tester / Reviewer:** Jannatun Naeem Mona (@jn-mona04) (System Analyst / BA & Peer Tester)  
**Developer:** MD. Hasanul Mobin (@hasanulmobin1) (Project Manager)  
**Date:** 2026-10-07  
**Framework:** Selenium WebDriver + pytest  
**Platform:** Windows 11 | Python 3.14.4 | pytest 9.1.1 | selenium 4.29.0  
**Environment:** Localhost (Frontend: `http://localhost:5173`, Backend: `http://127.0.0.1:8000`)  
**Browser:** Google Chrome (Headless)  

---

## 1. Executive Summary

| Metric | Result |
| :--- | :--- |
| **Total Automated UI Test Cases** | **6** |
| **Passed** | **6 (100%)** |
| **Failed** | **0 (0%)** |
| **Backend Unit Tests** | **14 / 14 Passed (100%)** (`backend/apps/recruitment/tests/test_weighting.py`) |
| **Defects Caught & Fixed** | **1** (Falsy zero evaluation bug `||` vs `??` in `RoomList.tsx`) |
| **Execution Duration** | **100.57 seconds** |
| **Automated Suite Status** | 🟢 **PASSED & VERIFIED** |
| **Overall Recommendation** | 🟢 **APPROVED FOR MERGE INTO `develop`** |

---

## 2. Test Execution Matrix

| Test Case ID | Test Method Name | Description | Status | Execution Time |
| :--- | :--- | :--- | :---: | :---: |
| **TC-US20-01** | `test_tc_us20_01_modal_mount_from_badge_and_action_button` | HR navigates to `/hr/rooms`; locates room card with "Evaluation Weights" badge; asserts default text `CV 50% / Video 50%`; clicks badge to open weighting modal; verifies room title, company name, and US-20 header context; tests clean dismissal via close button (X); tests reopening modal via Sliders action button in card footer; asserts clean dismissal via Cancel button. | ✅ **PASSED** | ~17.2s |
| **TC-US20-02** | `test_tc_us20_02_linked_dual_sliders_and_reset` | Tests linked dual slider synchronization: changes CV weight to 65%; asserts Video weight automatically updates to 35% (`100 - cv`); verifies distribution bar displays Total 100%; modifies Video weight to 40%; asserts CV weight updates to 60%; verifies Reset button is enabled; clicks Reset button and asserts restoration to 50/50. | ✅ **PASSED** | ~16.5s |
| **TC-US20-03** | `test_tc_us20_03_quick_recommendation_presets` | Tests rapid preset buttons: clicks Balanced (50/50), CV Focused (70/30), Video Focused (30/70), Technical Depth (80/20), and Client Facing (20/80); verifies all preset values propagate to numeric inputs, distribution split bar, and active styling. | ✅ **PASSED** | ~16.1s |
| **TC-US20-04** | `test_tc_us20_04_save_weighting_and_card_badge_update` | End-to-end persistence flow: selects CV Focused preset (70/30); clicks "Save Weighting"; verifies modal dismissal; verifies room card badge reactively updates DOM to `CV 70% / Video 30%`; asserts backend DB persistence (`cv_weight=70`, `video_weight=30`). | ✅ **PASSED** | ~17.4s |
| **TC-US20-05** | `test_tc_us20_05_live_score_simulation_preview` | Interactive score simulation calculator: sets Candidate CV score to 90 and Video score to 80; with 70/30 weighting, asserts calculated score preview is `87.0%`; switches to 30/70 preset; asserts calculated score dynamically recalculates to `83.0%`. | ✅ **PASSED** | ~16.2s |
| **TC-US20-06** | `test_tc_us20_06_extreme_splits_and_button_states` | Boundary & extreme testing: tests 100% CV / 0% Video; saves and verifies badge updates to `CV 100% / Video 0%` and DB records `cv_weight=100`, `video_weight=0`; tests 0% CV / 100% Video; saves and verifies badge updates to `CV 0% / Video 100%` and DB records `cv_weight=0`, `video_weight=100`. | ✅ **PASSED** | ~17.1s |

---

## 3. Acceptance Criteria Verified

- ✅ **AC 1 — Configurable Weights:** HR Manager can set custom CV and Video weights for any Recruitment Room.
- ✅ **AC 2 — Strict 100% Total Sum Constraint:** Linked dual sliders and inputs maintain exact 100% total; validated at model, serializer, and UI layers.
- ✅ **AC 3 — Invalid Input Rejection:** Negative values, non-integers, and sums not equal to 100% are strictly rejected with 400 Bad Request.
- ✅ **AC 4 — Default Weighting (50/50):** Newly created rooms automatically default to 50% CV and 50% Video weighting.
- ✅ **AC 5 — Room Persistence & Reactive UI:** Updated weights persist to database and immediately update room cards in `/hr/rooms`.
- ✅ **AC 6 — Live Scoring Simulation:** HR can preview weighted score calculations in real time using candidate test scores.
- ✅ **AC 7 — Extreme Splits Supported:** Boundary allocations (100/0 and 0/100) are fully supported.

---

## 4. Defect Caught & Resolved During QA

- **Defect:** In `frontend/src/components/recruitment/RoomList.tsx` line 332, the badge expression was using the logical OR operator:
  ```tsx
  CV {room.cv_weight || 50}% / Video {room.video_weight || 50}%
  ```
- **Root Cause:** In JavaScript, `0` is a falsy value. When an extreme weighting of `0% Video` or `0% CV` was selected, `0 || 50` evaluated to `50`.
- **Resolution:** Replaced with nullish coalescing `??`:
  ```tsx
  CV {room.cv_weight ?? 50}% / Video {room.video_weight ?? 50}%
  ```

---

## 5. Test Environment & Artifacts

- **Automated UI Test Suite:** [`tests/test_us20_weighting_ui.py`](file:///e:/projectSWE/CareerFlow/tests/test_us20_weighting_ui.py)
- **Backend Unit Tests:** [`backend/apps/recruitment/tests/test_weighting.py`](file:///e:/projectSWE/CareerFlow/backend/apps/recruitment/tests/test_weighting.py) (14/14 passed)
- **Captured UI Screenshots:**
  - Modal Mounting & Context: [`tests/reports/screenshots/us20_01_weighting_modal_opened.png`](file:///e:/projectSWE/CareerFlow/tests/reports/screenshots/us20_01_weighting_modal_opened.png)
  - Linked Dual Sliders & Reset: [`tests/reports/screenshots/us20_02_linked_sliders_sync.png`](file:///e:/projectSWE/CareerFlow/tests/reports/screenshots/us20_02_linked_sliders_sync.png)
  - Quick Recommendation Presets: [`tests/reports/screenshots/us20_03_recommendation_presets_applied.png`](file:///e:/projectSWE/CareerFlow/tests/reports/screenshots/us20_03_recommendation_presets_applied.png)
  - Weighting Saved & Room Card Updated: [`tests/reports/screenshots/us20_04_save_weighting_persisted.png`](file:///e:/projectSWE/CareerFlow/tests/reports/screenshots/us20_04_save_weighting_persisted.png)
  - Live Score Simulation Preview: [`tests/reports/screenshots/us20_05_simulation_score_preview.png`](file:///e:/projectSWE/CareerFlow/tests/reports/screenshots/us20_05_simulation_score_preview.png)
  - Extreme Splits Verified: [`tests/reports/screenshots/us20_06_extreme_splits_verified.png`](file:///e:/projectSWE/CareerFlow/tests/reports/screenshots/us20_06_extreme_splits_verified.png)
- **Markdown Report:** [`tests/reports/sprint4_us20_ui_testing_report.md`](file:///e:/projectSWE/CareerFlow/tests/reports/sprint4_us20_ui_testing_report.md)
