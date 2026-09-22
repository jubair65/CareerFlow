# CareerFlow Sprint 1 — Selenium Test Suite

Automated end-to-end testing suite for **Sprint 1: Establish the Secure Technical Foundation**.

## Overview of 5 Testing Sections

| Section ID | User Story | QA Task | Test File | Key Validations |
| --- | --- | --- | --- | --- |
| **US-01** | User Registration | US-01-T6 | `test_us01_user_registration.py` | Valid registration, format checks, password requirements, error feedback, DB account creation |
| **US-02** | User Login | US-02-T5 | `test_us02_user_login.py` | Valid login, invalid rejection, JWT storage, page refresh persistence, logout |
| **US-03** | Role-Based Access Control | US-03-T6 | `test_us03_rbac.py` | Student, HR Manager, Agency Admin roles, permission barriers (403), DB roles |
| **US-04** | Password Security | US-04-T4 | `test_us04_password_security.py` | PBKDF2/bcrypt hashing verification, non-exposure in plain text, strength meter |
| **US-36** | Data Access Control | US-36-T4 | `test_us36_data_access_control.py` | Candidate CV file access, student isolation, audit logging in MySQL, traversal defense |

---

## Directory Structure

```
f:\CareerFlow\tests/
├── __init__.py
├── conftest.py                          # Pytest fixtures, WebDriver configuration, DB helpers
├── test_us01_user_registration.py       # US-01 Selenium & DB tests
├── test_us02_user_login.py              # US-02 Selenium & Session tests
├── test_us03_rbac.py                    # US-03 Role-Based Access Control tests
├── test_us04_password_security.py       # US-04 Password hashing & strength tests
├── test_us36_data_access_control.py     # US-36 File permissions & audit logging tests
├── test_runner.py                       # Unified test runner with report generation
├── reports/                             # Generated test report (Markdown)
│   └── sprint1_testing_report.md
└── README.md                            # Documentation (this file)
```

---

## Prerequisites

1. **MySQL Database**: Ensure MySQL server is running and `careerflow_db` is configured.
2. **Backend Server**: Running at `http://127.0.0.1:8000` (`python manage.py runserver`).
3. **Frontend Server**: Running at `http://localhost:5173` (`npm run dev`).
4. **Google Chrome / Chromium**: Installed on the system.

---

## Running the Tests

### 1. Run Complete Test Suite with Report Generation
```powershell
& "f:\CareerFlow\venv\Scripts\python.exe" tests/test_runner.py
```

### 2. Run Individual Sections with Pytest
```powershell
# US-01: User Registration
& "f:\CareerFlow\venv\Scripts\python.exe" -m pytest tests/test_us01_user_registration.py -v

# US-02: User Login
& "f:\CareerFlow\venv\Scripts\python.exe" -m pytest tests/test_us02_user_login.py -v

# US-03: Role-Based Access Control
& "f:\CareerFlow\venv\Scripts\python.exe" -m pytest tests/test_us03_rbac.py -v

# US-04: Password Security
& "f:\CareerFlow\venv\Scripts\python.exe" -m pytest tests/test_us04_password_security.py -v

# US-36: Data Access Control
& "f:\CareerFlow\venv\Scripts\python.exe" -m pytest tests/test_us36_data_access_control.py -v
```
