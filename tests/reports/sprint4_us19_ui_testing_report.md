# Sprint 4 UI Testing Report — Task US-19-T6

**Sprint:** Sprint 4 (Recruitment Rooms & Candidate Submission)  
**User Story:** US-19: Job Role & Required Skills  
**Task:** US-19-T6 (Peer UI Testing for Job Requirements & Skills Tagging Flow)  
**Peer Tester / Reviewer:** MD. Jubair Bin Hasan (Software Developer & Peer Tester)  
**Developer:** Nafisa Tabassum Maria (@Maria-07-222) (System Architect)  
**Date:** 2026-10-07  
**Framework:** Selenium WebDriver + pytest  
**Platform:** Windows 11 | Python 3.14.0 | pytest 9.1.1 | selenium 4.29.0  
**Environment:** Localhost (Frontend: `http://localhost:5173`, Backend: `http://127.0.0.1:8000`)  
**Browser:** Google Chrome (Headless)  

---

## 1. Executive Summary

| Metric | Result |
| :--- | :--- |
| **Total Automated UI Test Cases** | **5** |
| **Passed** | **5 (100%)** |
| **Failed** | **0 (0%)** |
| **Backend Unit Tests** | **25 / 25 Passed (100%)** (`backend/apps/recruitment/tests/test_job_requirements.py` & `test_room_management.py`) |
| **Execution Duration** | **86.31 seconds** |
| **Automated Suite Status** | 🟢 **PASSED & VERIFIED** |
| **HTML Report Generated** | 🟢 **YES** (`tests/reports/sprint4_us19_report.html`) |
| **Overall Recommendation** | 🟢 **APPROVED FOR MERGE INTO `develop`** |

---

## 2. Test Execution Matrix

| Test Case ID | Test Method Name | Description | Status | Execution Time |
| :--- | :--- | :--- | :---: | :---: |
| **TC-US19-01** | `test_tc_us19_01_requirements_modal_mount_and_context` | HR navigates to `/hr/rooms`; clicks **[Configure]** button (`[data-testid='button-configure-requirements-<id>']`) on room card; verifies modal (`[data-testid='modal-job-requirements']`) mounts with correct room title and company name in header; verifies default role category (`Engineering`) and seniority level (`MID`); asserts clean modal dismissal via close button. | ✅ **PASSED** | ~17.5s |
| **TC-US19-02** | `test_tc_us19_02_skill_validation_rules` | Tests comprehensive validation rules: empty input on Add Skill triggers warning banner (`Please type a skill name before adding.`); short skill tag (<2 characters) triggers minimum length validation (`Skill name must be at least 2 characters long.`); adding valid skill mounts pill in container; adding duplicate case-insensitive tag triggers error (`Skill "python" is already added.`); removing all skills and attempting submission triggers block (`At least one required skill must be defined.`). | ✅ **PASSED** | ~18.2s |
| **TC-US19-03** | `test_tc_us19_03_quick_preset_suggestions_and_enter_key` | Tests rapid skill curation: clicks preset buttons ("Docker", "PostgreSQL"); verifies chips enter disabled state with checkmark; adds custom skill tag ("FastAPI") using keyboard Enter (`Keys.ENTER`); verifies skills container mounts all 3 tags and skill counter updates to "(3)". | ✅ **PASSED** | ~16.8s |
| **TC-US19-04** | `test_tc_us19_04_save_requirements_and_room_card_updates` | Full persistence flow: HR updates Role Category ("Full Stack Engineering"), selects Seniority Level ("SENIOR"), fills detailed requirements description, adds skills ("React", "TypeScript", "Python"), submits form; verifies modal dismissal, and asserts room card reactively renders updated role category, SENIOR badge, and skills list chips in the DOM. | ✅ **PASSED** | ~17.1s |
| **TC-US19-05** | `test_tc_us19_05_skill_tag_removal_and_persistence` | Re-opens configure requirements modal for existing room; verifies pre-existing skills are fetched from backend API; deletes "Docker" tag via `[data-testid='button-remove-skill-docker']`; saves changes; verifies room card reactively drops the removed chip while preserving remaining skills ("Python", "PostgreSQL"). | ✅ **PASSED** | ~16.7s |

---

## 3. Acceptance Criteria Verified

- ✅ **AC 1 — Requirements Configuration Modal:** HR Manager can open the requirements modal directly from any room card in `/hr/rooms` with clear room and company context.
- ✅ **AC 2 — Job Role & Seniority Customization:** Supports role category customization and seniority level selection (`ENTRY`, `MID`, `SENIOR`, `LEAD`) with default fallbacks.
- ✅ **AC 3 — Strict Skill Validation (US-19-T4):** Enforces minimum 1 skill tag, non-empty/non-whitespace names, 2–60 character length limits, and case-insensitive uniqueness validation.
- ✅ **AC 4 — Interactive Skills Tag Builder:** HR can add skill tags quickly via Enter key, standard Add button, or Quick Suggestion preset chips (*Python, TypeScript, React, Docker, AWS, PostgreSQL*).
- ✅ **AC 5 — Reactive UI & Room Card Integration:** Room cards reactively display role category, seniority badge, and required skills chips (`[data-testid='room-skills-list-<id>']`) immediately upon saving.
- ✅ **AC 6 — Skill Tag Removal & Persistence:** HR can remove individual skill tags dynamically, and changes persist to MySQL database via `PATCH /api/recruitment/rooms/{id}/requirements/`.
- ✅ **AC 7 — CV Semantic Matcher Bridge (US-19-T5):** Synchronizes room requirements with `JobRequirement` models for downstream semantic CV scoring.

---

## 4. Test Environment & Artifacts

- **Automated UI Test Suite:** [`tests/test_us19_job_requirements_ui.py`](file:///d:/Study/3.2/CSE-314/CareerFlow/tests/test_us19_job_requirements_ui.py)
- **HTML Test Report:** [`tests/reports/sprint4_us19_report.html`](file:///d:/Study/3.2/CSE-314/CareerFlow/tests/reports/sprint4_us19_report.html)
- **Backend Unit Tests:** [`backend/apps/recruitment/tests/test_job_requirements.py`](file:///d:/Study/3.2/CSE-314/CareerFlow/backend/apps/recruitment/tests/test_job_requirements.py) (14/14 passed, 25/25 recruitment suite passing)
- **Captured UI Screenshots:**
  - Modal Mounting & Context: [`tests/reports/screenshots/us19_01_requirements_modal_opened.png`](file:///d:/Study/3.2/CSE-314/CareerFlow/tests/reports/screenshots/us19_01_requirements_modal_opened.png)
  - Inline Skill Validation & Error Banner: [`tests/reports/screenshots/us19_02_skill_validation_empty_and_duplicate.png`](file:///d:/Study/3.2/CSE-314/CareerFlow/tests/reports/screenshots/us19_02_skill_validation_empty_and_duplicate.png)
  - Quick Presets & Enter Key Addition: [`tests/reports/screenshots/us19_03_skills_tag_builder_and_quick_presets.png`](file:///d:/Study/3.2/CSE-314/CareerFlow/tests/reports/screenshots/us19_03_skills_tag_builder_and_quick_presets.png)
  - Saved Requirements & Room Card Chips: [`tests/reports/screenshots/us19_04_save_requirements_success_and_room_card_chips.png`](file:///d:/Study/3.2/CSE-314/CareerFlow/tests/reports/screenshots/us19_04_save_requirements_success_and_room_card_chips.png)
  - Skill Tag Removal & Reactive Update: [`tests/reports/screenshots/us19_05_remove_skill_tag_and_modal_dismissal.png`](file:///d:/Study/3.2/CSE-314/CareerFlow/tests/reports/screenshots/us19_05_remove_skill_tag_and_modal_dismissal.png)
- **Markdown Report:** [`tests/reports/sprint4_us19_ui_testing_report.md`](file:///d:/Study/3.2/CSE-314/CareerFlow/tests/reports/sprint4_us19_ui_testing_report.md)
