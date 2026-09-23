# CareerFlow — System Architecture & Module Decoupling Guide

> **User Story US-41 (Modular Architecture)**  
> *As the development team, we want a modular architecture so that audio, video, CV, and scoring components can be maintained independently.*

---

## 1. System Overview

**CareerFlow** is an AI-powered talent matching and recruitment automation platform designed with a **modular monorepo architecture**. The system is split cleanly into three primary layers:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Frontend Layer (React 19)                       │
│      Vite + TypeScript + Tailwind CSS v4 + Wouter Router               │
│      Role Dashboards: /student/dashboard, /hr/dashboard, /agency/...    │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │ HTTPS / REST JSON
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     Backend API Gateway (Django 6)                     │
│      Django REST Framework + SimpleJWT Authentication                  │
└──────┬───────────────────────────┬──────────────────────────────┬──────┘
       │                           │                              │
       ▼                           ▼                              ▼
┌──────────────┐            ┌──────────────┐              ┌──────────────┐
│  apps.auth   │            │  apps.core   │              │ Future Apps  │
│  Users, RBAC │            │ Security,    │              │ CV, Video,   │
│  & Sessions  │            │ File Serving │              │ Scoring      │
└──────┬───────┘            └──────┬───────┘              └──────┬───────┘
       │                           │                             │
       └───────────────────────────┼─────────────────────────────┘
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                          Data & Storage Layer                          │
│      MySQL Database (`careerflow_db`) + Isolated Media Storage         │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Monorepo Directory Organization

```
CareerFlow/
├── backend/
│   ├── apps/
│   │   ├── authentication/      # User model, registration, login, JWT & RBAC (US-01..04)
│   │   ├── core/                # Data access control, secure media proxy & audit logs (US-36)
│   │   ├── cv/                  # [Sprint 2] CV upload, parsing & Sentence-BERT matching (US-06..09)
│   │   ├── presentation/        # [Sprint 3] Video upload, speech/behavioral AI engine (US-11..15)
│   │   ├── rooms/               # [Sprint 4] HR recruitment rooms & weight configs (US-18..22)
│   │   └── decisions/           # [Sprint 5] Scoring engine, ranking & shortlisting (US-23..27)
│   ├── careerflow/              # Project settings, root URL routing, WSGI/ASGI entrypoints
│   ├── media/                   # Protected file uploads (CVs, videos, resumes)
│   └── manage.py                # Django CLI management script
├── frontend/
│   ├── src/
│   │   ├── api/                 # Axios clients, token interceptors, REST endpoints
│   │   ├── components/
│   │   │   ├── auth/            # ProtectedRoute guards and authentication widgets
│   │   │   ├── dashboard/       # Shared UI primitives (PageHeading, StatCard, Chart)
│   │   │   ├── layout/          # AppShell, role-aware sidebar navigation, headers
│   │   │   └── ui/              # Radix UI headless primitives & Tailwind components
│   │   └── pages/               # StudentDashboard, HrDashboard, AgencyDashboard
│   └── package.json             # Frontend dependencies & build scripts
├── tests/                       # Selenium E2E suite, POM models, pytest fixtures
└── docs/                        # Architecture, interface contracts & setup guides
```

---

## 3. Module Boundaries & Decoupling Strategy

To guarantee that future AI pipelines (CV parsing, Sentence-BERT semantic matching, speech recognition, and video computer vision) can evolve without breaking core features, the system adheres to strict **Bounded Contexts**:

### Current Sprint 1 Modules

#### A. `apps.authentication` (Identity & Access Context)
* **Responsibility:** User identity lifecycle, credentials encryption, and role-based permissions.
* **Key Components:**
  * `User` model: Extends `AbstractUser`, defines standard role hierarchy (`STUDENT`, `HR_MANAGER`, `AGENCY_ADMIN`).
  * `RegisterSerializer` & `LoginSerializer`: Enforces password complexity, email uniqueness, and lowercase normalization.
  * `RegisterView`: Issues JWT `access` and `refresh` token pairs and dispatches welcome/confirmation emails via `send_mail()`.
  * `permissions.py`: Reusable DRF permission classes (`IsStudent`, `IsHRManager`, `IsAgencyAdmin`).
* **Decoupling Rule:** `authentication` has **zero dependencies** on other domain apps. All other apps import user permissions and the user model from here, never the reverse.

#### B. `apps.core` (Security, Storage & Audit Context)
* **Responsibility:** Secure file serving, path-traversal prevention, and sensitive data access auditing (fulfilling **US-36**).
* **Key Components:**
  * `DataAccessLog` model: Persists user ID, role, resource path, IP address, user-agent, action (`DOWNLOAD`, `VIEW`), and status (`GRANTED`, `DENIED`).
  * `SecureFileServeView`: Intercepts media file requests, verifies role-based ownership, creates an audit log entry, and streams the file securely without exposing raw filesystem paths.
* **Decoupling Rule:** Does not contain business logic for evaluating CVs or videos. It acts strictly as an authorization and audit gateway.

---

### Future Sprint Modules (Sprints 2 – 6)

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Decoupled Module Map                            │
├─────────────────┬──────────────────────┬───────────────────────────────┤
│ Module          │ Sprint               │ Decoupled Responsibilities    │
├─────────────────┼──────────────────────┼───────────────────────────────┤
│ `apps.cv`       │ Sprint 2 (US-06..09) │ • Ingest PDF/DOCX resumes     │
│                 │                      │ • Extract skills & experience │
│                 │                      │ • Sentence-BERT similarity    │
├─────────────────┼──────────────────────┼───────────────────────────────┤
│ `apps.video`    │ Sprint 3 (US-11..15) │ • Video upload & validation   │
│                 │                      │ • Whisper speech analysis     │
│                 │                      │ • CV eye-contact & posture    │
├─────────────────┼──────────────────────┼───────────────────────────────┤
│ `apps.rooms`    │ Sprint 4 (US-18..22) │ • Job room definitions       │
│                 │                      │ • Custom weight ratios        │
│                 │                      │ • Candidate submission links  │
├─────────────────┼──────────────────────┼───────────────────────────────┤
│ `apps.scoring`  │ Sprint 5 (US-23..27) │ • Weighted composite scoring  │
│                 │                      │ • Candidate ranking engine    │
│                 │                      │ • Automatic shortlisting      │
├─────────────────┼──────────────────────┼───────────────────────────────┤
│ `apps.agency`   │ Sprint 6 (US-29..35) │ • Multi-client management     │
│                 │                      │ • Profile forwarding          │
│                 │                      │ • PDF/CSV report generation   │
└─────────────────┴──────────────────────┴───────────────────────────────┘
```

#### Principles of Decoupling between AI Engines:
1. **Model Independence:** The CV engine (`apps.cv`) does not know about the Video engine (`apps.video`). Each generates its own independent, standardized normalized score (0–100) and structured JSON breakdown.
2. **Scoring Aggregator:** The decision engine (`apps.scoring`) consumes the outputs of `apps.cv` and `apps.video` using the weights defined in `apps.rooms`. It never directly manipulates raw video files or CV documents.
3. **Storage Isolation:** Uploaded candidate files are organized into role-isolated paths:
   * Candidate files: `media/students/{student_id}/cv/` and `media/students/{student_id}/videos/`
   * HR room assets: `media/rooms/{room_id}/`

---

## 4. API Interface Contracts

All communication between frontend and backend occurs via REST JSON APIs over HTTPS with JWT Bearer authentication:

### Core Endpoints

| Method | Endpoint | Permission | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/register/` | AllowAny | Register user, hash password, send welcome email |
| `POST` | `/api/auth/login/` | AllowAny | Authenticate credentials, issue access & refresh tokens |
| `POST` | `/api/auth/token/refresh/` | AllowAny | Refresh expired access token using refresh token |
| `POST` | `/api/auth/logout/` | IsAuthenticated | Blacklist refresh token and invalidate session |
| `GET` | `/api/auth/me/` | IsAuthenticated | Retrieve current user profile and role claims |
| `GET` | `/api/core/files/<path>` | IsAuthenticated | Serve authorized media file with audit logging |
| `GET` | `/api/core/audit-logs/` | IsHRManager / IsAgencyAdmin | Retrieve data access audit log records |

### Standard Response Format

Success responses return clean JSON payloads:
```json
{
  "message": "Action completed successfully.",
  "user": {
    "id": 1,
    "email": "student@example.com",
    "full_name": "Alex Rahman",
    "role": "STUDENT",
    "role_display": "Candidate / Student"
  }
}
```

Error responses return structured, human-readable error details:
```json
{
  "message": "Field validation failed.",
  "errors": {
    "email": ["A user with this email address already exists."]
  }
}
```

---

## 5. Security Architecture & Data Protection (US-04 & US-36)

1. **Password Hashing:** Passwords use Django's PBKDF2 algorithm with a SHA-256 hash and a 128-bit salt (minimum 100,000 iterations). Plaintext passwords are never stored, logged, or serialized.
2. **Password Validation:** Enforces four mandatory validation gates: minimum 8 characters, common password dictionary check, user attribute similarity check, and numeric digit requirement.
3. **Data Access Control & Path Traversal Defense:**
   * Files requested via `/api/core/files/<file_path>` are resolved against `settings.MEDIA_ROOT`.
   * Requests containing directory traversal sequences (`../`, `..\`) are blocked and return HTTP 400/404.
   * Access to sensitive candidate files is strictly role-scoped:
     * **Student:** Can access only files within their own user directory (`students/{id}/...`).
     * **HR Manager & Agency Admin:** Can access authorized applicant files.
   * Every access attempt (success or denial) is recorded in `DataAccessLog`.

---

## 6. Microservices & Scalability Migration Path

While CareerFlow operates as a unified modular monorepo for rapid feature delivery, the decoupled app boundaries allow future extraction into independent microservices:

1. **AI Processing Offload (Celery / Background Workers):**
   Heavy tasks like CV parsing and Sentence-BERT vector generation can be converted into asynchronous jobs via Celery + Redis queues without changing frontend API contracts.
2. **Dedicated Video Inference Microservice:**
   The presentation evaluation pipeline (`apps.video`) can be deployed as an independent container with GPU acceleration, communicating with the core backend via webhooks or lightweight REST calls.
3. **Database Independence:**
   Because `apps.authentication`, `apps.core`, and future apps avoid circular foreign keys, each module's tables can be partitioned or moved to dedicated schema namespaces as traffic grows.
