# CareerFlow — Sprint 5 Ranking Architecture Specification
## US-24: Applicant Ranking by Composite Score with Deterministic Tie-Breaking
**Author / System Architect:** Nafisa Tabassum Maria (Sy De / S Arch)  
**Epic:** Epic 6: Scoring & Shortlisting  
**Target Story:** US-24 (`feat/us-24-applicant-ranking`)  
**Status:** Approved & Implemented  

---

## 1. Executive Summary & Purpose
Following **US-23** (which calculates the weighted Final Applicant Score $Score_{final}$ from CV match and Video presentation scores), **US-24** organizes candidates into an objective, descending leaderboard for HR Managers.

The ranking engine provides:
1. **Strict Descending Order:** Candidates are ordered from highest final score to lowest.
2. **Multi-Tier Deterministic Tie-Breaking:** Explicit rules resolve ties without ambiguity or randomness.
3. **Segregation of Incomplete Applications:** Candidates pending evaluation are isolated from the ranked leaderboard to prevent skewed percentiles.
4. **Dynamic Re-Ranking:** Leaderboards update in real time whenever scores or weights change.

---

## 2. Ranking Algorithm & Tie-Breaking Rules

### 2.1 Order Hierarchy
Candidate ordering in the database query executes according to the following deterministic sort tuple:

$$\text{ORDER BY } \text{final\_score DESC}, \text{cv\_score DESC}, \text{video\_score DESC}, \text{applied\_at ASC}, \text{id ASC}$$

```
                                  ┌──────────────────────────────┐
                                  │   Compare Candidates A & B   │
                                  └──────────────┬───────────────┘
                                                 │
                                                 ▼
                                     ┌───────────────────────┐
                                     │  Are Final Scores     │
                                     │       Different?      │
                                     └───────────┬───────────┘
                                                 │
                                 ┌───────────────┴───────────────┐
                              Yes│                               │No (Tie)
                                 ▼                               ▼
                 ┌──────────────────────────────┐ ┌──────────────────────────────┐
                 │ Higher final_score takes     │ │  Check CV Match Scores       │
                 │ superior rank                │ └──────────────┬───────────────┘
                 └──────────────────────────────┘                │
                                                         ┌───────┴───────┐
                                                      Yes│               │No (Tie)
                                                         ▼               ▼
                                         ┌─────────────────────┐ ┌───────────────────────┐
                                         │ Higher cv_score     │ │ Check Video Scores    │
                                         │ takes superior rank │ └───────────┬───────────┘
                                         └─────────────────────┘             │
                                                                     ┌───────┴───────┐
                                                                  Yes│               │No (Tie)
                                                                     ▼               ▼
                                                     ┌─────────────────────┐ ┌─────────────────────┐
                                                     │ Higher video_score  │ │ Earlier applied_at  │
                                                     │ takes superior rank │ │ (FIFO) wins rank    │
                                                     └─────────────────────┘ └─────────────────────┘
```

### 2.2 Tie-Breaking Rationale
1. **Tier 1 — Higher CV Match Score:**
   CV Match measures objective alignment with core technical skills, verified certifications, and mandatory domain requirements (US-19/US-20). In candidate evaluation, foundational qualifications precede presentation demeanor.
2. **Tier 2 — Higher Video Presentation Score:**
   When CV qualifications are identical, communicative clarity, pacing, and behavioral poise differentiate candidates.
3. **Tier 3 — Earlier Application Date (FIFO):**
   When technical and communicative qualifications are identical, seniority of submission rewards timely applicant initiative.
4. **Tier 4 — Database Primary Key (`id ASC`):**
   Ensures 100% deterministic query order across MySQL cluster nodes.

---

## 3. Unranked & Incomplete Applicant Segregation (US-24-T5)

Applicants whose analysis pipeline is still in progress (or missing documents) have `final_score = None`.

### Rules:
- Candidates with `final_score IS NULL` are excluded from the numeric rank numbering (#1, #2, #3...).
- In API responses and UI views, they are grouped separately under `unranked` with an explicit reason:
  - `NO_CV`: Applicant has not uploaded a CV document.
  - `NO_VIDEO`: Applicant has not completed video pitch.
  - `ANALYZING`: Analysis pipeline is actively processing speech or vision models.
  - `EVALUATION_PENDING`: In queue for score computation.
- This prevents incomplete candidates from deflating room statistics or appearing as "Rank 0".

---

## 4. API Contract (`GET /api/recruitment/rooms/{room_id}/ranked-applicants/`)

### 4.1 Query Parameters
- `min_score` (optional, float): Filter candidates with $Score_{final} \ge \text{min\_score}$.
- `max_score` (optional, float): Filter candidates with $Score_{final} \le \text{max\_score}$.
- `search` (optional, string): Fuzzy search against candidate name or email.
- `status` (optional, string): Filter by application processing status.
- `ordering` (optional, string): Default `-final_score`. Supports `final_score`, `-cv_score`, `-video_score`, `applied_at`.
- `include_unranked` (optional, bool): Whether to include the `unranked` list in the response (default `true`).

### 4.2 Response Payload
```json
{
  "room_id": 12,
  "room_title": "Senior Full Stack Engineer",
  "company_name": "Innovatech Labs",
  "total_applicants": 18,
  "ranked_count": 15,
  "unranked_count": 3,
  "results": [
    {
      "rank": 1,
      "application_id": 101,
      "candidate_id": 45,
      "candidate_name": "Rahim Ahmed",
      "candidate_email": "rahim@example.com",
      "final_score": 87.2,
      "cv_score": 88.5,
      "video_score": 85.0,
      "is_partial_score": false,
      "status": "COMPLETED",
      "applied_at": "2026-10-12T14:30:00Z",
      "badge": "GOLD"
    }
  ],
  "unranked": [
    {
      "application_id": 109,
      "candidate_id": 52,
      "candidate_name": "Fatima Noor",
      "candidate_email": "fatima@example.com",
      "final_score": null,
      "status": "PENDING",
      "applied_at": "2026-10-14T09:15:00Z",
      "pending_reason": "Video analysis in progress"
    }
  ]
}
```
