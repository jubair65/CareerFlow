# CareerFlow — Sprint 1 Automated Selenium Test Report

**Execution Date:** 2026-09-22 23:14:41  
**Sprint:** Sprint 1 — Establish Secure Technical Foundation  
**Target Applications:** Frontend (`http://localhost:5173`) & Backend (`http://127.0.0.1:8000`)  
**Database:** MySQL (`careerflow_db`)  

## Executive Summary

| Metric | Value | Status |
| --- | --- | --- |
| **Total Tests** | 26 | - |
| **Passed** | 26 | ✅ 100% |
| **Failed** | 0 | ✅ None |
| **Skipped** | 0 | - |
| **Pass Rate** | **100.0%** | ✅ EXCELLENT |
| **Total Duration** | 195.3 seconds | ⏱️ Fast Execution |

---

## 5 Sprint 1 Testing Sections Overview

| Story ID | Section Name | QA Task | Tests Executed | Passed | Status |
| --- | --- | --- | --- | --- | --- |
| **US-01** | User Registration | US-01-T6 (Write unit tests / UI test for registration) | 6 | 6 | ✅ PASSED |
| **US-02** | User Login | US-02-T5 (Test login flow and sessions) | 5 | 5 | ✅ PASSED |
| **US-03** | Role-Based Access Control | US-03-T6 (Test role-based access control) | 5 | 5 | ✅ PASSED |
| **US-04** | Password Security | US-04-T4 (Test password security measures) | 4 | 4 | ✅ PASSED |
| **US-36** | Data Access Control | US-36-T4 (Test data access controls) | 6 | 6 | ✅ PASSED |

---

## Detailed Test Results by Story

### US-01: User Registration

| Test ID / Method | Status | Duration (s) | Notes |
| --- | --- | --- | --- |
| `test_tc01_01_valid_registration_and_db_creation` | ✅ PASSED | 6.596s | Verified against acceptance criteria |
| `test_tc01_02_invalid_email_format_rejected` | ✅ PASSED | 1.653s | Verified against acceptance criteria |
| `test_tc01_03_short_password_rejected` | ✅ PASSED | 1.574s | Verified against acceptance criteria |
| `test_tc01_04_password_mismatch_rejected` | ✅ PASSED | 1.806s | Verified against acceptance criteria |
| `test_tc01_05_duplicate_email_rejected_by_backend` | ✅ PASSED | 2.239s | Verified against acceptance criteria |
| `test_tc01_06_proceed_to_login_flow` | ✅ PASSED | 3.895s | Verified against acceptance criteria |

### US-02: User Login

| Test ID / Method | Status | Duration (s) | Notes |
| --- | --- | --- | --- |
| `test_tc02_01_valid_credentials_login_success` | ✅ PASSED | 5.622s | Verified against acceptance criteria |
| `test_tc02_02_invalid_credentials_rejected_with_message` | ✅ PASSED | 6.348s | Verified against acceptance criteria |
| `test_tc02_03_jwt_tokens_generated_in_localstorage` | ✅ PASSED | 4.274s | Verified against acceptance criteria |
| `test_tc02_04_session_persists_across_page_refresh` | ✅ PASSED | 6.31s | Verified against acceptance criteria |
| `test_tc02_05_logout_functionality_clears_session` | ✅ PASSED | 5.033s | Verified against acceptance criteria |

### US-03: Role-Based Access Control

| Test ID / Method | Status | Duration (s) | Notes |
| --- | --- | --- | --- |
| `test_tc03_01_student_role_and_restricted_access` | ✅ PASSED | 6.269s | Verified against acceptance criteria |
| `test_tc03_02_hr_manager_role_and_privileged_access` | ✅ PASSED | 6.752s | Verified against acceptance criteria |
| `test_tc03_03_agency_admin_role_and_privileged_access` | ✅ PASSED | 5.166s | Verified against acceptance criteria |
| `test_tc03_04_role_assignments_persisted_in_database` | ✅ PASSED | 2.983s | Verified against acceptance criteria |
| `test_tc03_05_unauthenticated_requests_blocked` | ✅ PASSED | 0.008s | Verified against acceptance criteria |

### US-04: Password Security

| Test ID / Method | Status | Duration (s) | Notes |
| --- | --- | --- | --- |
| `test_tc04_01_passwords_securely_hashed_in_database` | ✅ PASSED | 2.777s | Verified against acceptance criteria |
| `test_tc04_02_password_never_exposed_in_api_payloads` | ✅ PASSED | 4.202s | Verified against acceptance criteria |
| `test_tc04_03_ui_password_strength_meter_dynamically_evaluates` | ✅ PASSED | 1.517s | Verified against acceptance criteria |
| `test_tc04_04_backend_password_validators_enforcement` | ✅ PASSED | 0.106s | Verified against acceptance criteria |

### US-36: Data Access Control

| Test ID / Method | Status | Duration (s) | Notes |
| --- | --- | --- | --- |
| `test_tc36_01_student_can_access_own_cv_file` | ✅ PASSED | 2.774s | Verified against acceptance criteria |
| `test_tc36_02_student_data_isolation_cross_access_blocked` | ✅ PASSED | 2.029s | Verified against acceptance criteria |
| `test_tc36_03_hr_and_agency_can_access_candidate_information` | ✅ PASSED | 5.837s | Verified against acceptance criteria |
| `test_tc36_04_access_logs_maintained_for_audit` | ✅ PASSED | 2.616s | Verified against acceptance criteria |
| `test_tc36_05_path_traversal_attempts_prevented` | ✅ PASSED | 2.49s | Verified against acceptance criteria |
| `test_tc36_06_dashboard_displays_data_access_control_card` | ✅ PASSED | 2.756s | Verified against acceptance criteria |

---

## Conclusion & Sign-Off

All 5 core testing sections specified in Sprint 1 have passed with 100% success rate. The foundation meets all defined security, authentication, role isolation, and database persistence acceptance criteria.