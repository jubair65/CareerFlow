# Sprint 2 UI Testing Report — Task 5 & Task 6
**Tester:** Maria  
**Date:** 2026-09-28  
**Framework:** Selenium + pytest  
**Platform:** macOS-26.6.2 | Python 3.14.2 | pytest 9.1.1

---

## Summary

| Task | Test File | Total | Passed | Failed | Duration |
|------|-----------|-------|--------|--------|----------|
| UIT-01-T5: Extraction Failure UI | `test_uit01_t5_extraction_failure_ui.py` | 4 | **4** | 0 | 21.46s |
| UIT-01-T6: Feedback Results UI | `test_uit01_t6_feedback_results_ui.py` | 5 | **5** | 0 | 11.64s |
| **TOTAL** | | **9** | **9** | **0** | **33.10s** |

---

## UIT-01-T5: CV Data Extraction Failure UI

**Acceptance Criteria Verified:**
- ✅ Upload `corrupt_file.pdf` triggers extraction error path
- ✅ UI does NOT crash (no white screen / blank body)
- ✅ `[data-testid="extraction-error-card"]` renders with message: _"Unable to extract text from document"_
- ✅ Advice text: _"Ensure document is not password-protected or scanned as raw image"_
- ✅ `[data-testid="button-try-another-file"]` present, clickable, and clears error
- ✅ `[data-testid="button-retry-extraction"]` present, clickable, page stays intact

| Test Case | Description | Result |
|-----------|-------------|--------|
| TC-UIT-01-T5-01 | Corrupt file upload → extraction failure UI, friendly alert + action buttons | ✅ PASSED |
| TC-UIT-01-T5-02 | CV Results page with no parsed CV → fallback error card + "Try another file" navigates back | ✅ PASSED |
| TC-UIT-01-T5-03 | "Retry extraction" button triggers retry without UI crash | ✅ PASSED |
| TC-UIT-01-T5-04 | ErrorBoundary prevents white screen on unexpected errors | ✅ PASSED |

> **Note:** TC-T5-03 failed on the first run due to a transient ChromeDriver port timeout (race condition between successive Chrome instances). Fixed by adding a 2-second buffer before `driver.get()`. All 4 tests passed on the second run.

---

## UIT-01-T6: CV Feedback Results UI

**Acceptance Criteria Verified:**
- ✅ `[data-testid="cv-overall-score"]` is an integer between 0 and 100
- ✅ `[data-testid="score-tier-badge"]` shows a valid tier label
- ✅ All 5 signal breakdown bars render with `width` between 0–100%
- ✅ At least 3 distinct `[data-testid^="suggestion-item-"]` callouts displayed
- ✅ `[data-testid="extracted-skills-list"]` renders parsed tech skills (Python, React, SQL, etc.)
- ✅ `[data-testid="button-download-cv-report"]` triggers download of `careerflow-cv-report*.txt` containing `CAREERFLOW CV FEEDBACK`, `SIGNAL BREAKDOWN`, and `ACTIONABLE EDITS`

| Test Case | Description | Result |
|-----------|-------------|--------|
| TC-UIT-01-T6-01 | Overall score (0–100 integer) and tier badge render correctly | ✅ PASSED |
| TC-UIT-01-T6-02 | All 5 signal breakdown progress bars have valid widths (0–100%) | ✅ PASSED |
| TC-UIT-01-T6-03 | At least 3 actionable suggestion cards displayed with non-empty text | ✅ PASSED |
| TC-UIT-01-T6-04 | Extracted skills list renders recognized technical skill badges | ✅ PASSED |
| TC-UIT-01-T6-05 | Download CV report button triggers file download with correct content | ✅ PASSED |

---

## Warnings
- `RemovedInDjango70Warning: The EMAIL_BACKEND setting is deprecated.`  
  → Not test-blocking. Backend team to migrate to `MAILERS` before Django 7.0.

---

## Test Files
- [`test_uit01_t5_extraction_failure_ui.py`](file:///Users/nafisatabassummaria/Study/3.2/Project/CareerFlow/tests/test_uit01_t5_extraction_failure_ui.py)
- [`test_uit01_t6_feedback_results_ui.py`](file:///Users/nafisatabassummaria/Study/3.2/Project/CareerFlow/tests/test_uit01_t6_feedback_results_ui.py)
