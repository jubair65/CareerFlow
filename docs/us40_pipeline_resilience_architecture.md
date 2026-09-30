# CareerFlow — US-40: AI Pipeline Failure Handling & Resilience Architecture

**Epic:** Epic 9 (Security, Reliability & System Quality)  
**User Story:** US-40: AI Pipeline Failure Handling  
**Architect:** Nafisa Tabassum Maria (System Architect)  
**Sprint:** Sprint 3 (Presentation AI)  
**Status:** Approved & Implemented  

---

## 1. Architectural Objectives

1. **Zero Unhandled Pipeline Crashes:** The video presentation analysis workflow must never throw unhandled 500 errors to the candidate or leave videos in zombie states.
2. **Deterministic Transient Fault Recovery:** Network glitches, thread locks, audio extraction timeouts, and external LLM rate limits must be caught and retried automatically with exponential backoff and jitter.
3. **Graceful Degradation for Real-World Video Quality:** If a candidate's webcam video has low contrast, bad lighting, occlusion, or corrupt frames causing MediaPipe computer vision tracking to fail, the pipeline must preserve speech metrics, calculate a valid score using 100% speech weighting, mark `has_behavioral_data=False`, set status to `PARTIALLY_COMPLETED`, and explain the situation clearly to the student.
4. **End-to-End Observability & Diagnostics:** Every stage transition, retry attempt, latency in milliseconds, and exception trace must be captured in `PipelineExecutionLog` for diagnostic auditing and support.
5. **Empowering Candidate UX:** Candidates must see friendly, non-technical recovery banners on the frontend with a direct **[Retry Analysis]** action and collapsible diagnostics.

---

## 2. Pipeline State Machine & Transitions

```
[Candidate Uploads Video]
           │
           ▼
     (UPLOADED) ───[FFmpeg Compress]──► (READY_FOR_ANALYSIS)
                                                 │
                                                 ▼
                                       (PROCESSING_SPEECH)
                                                 │
                                       [Retry 1..3 Backoff]
                                       /                  \
                            [Success] /                    \ [Fatal Speech Error]
                                     ▼                      ▼
                            (PROCESSING_VISION)          (FAILED)
                                     │                  (UI: Retry Alert)
                           [Vision Landmark Check]
                           /                     \
                [Success] /                       \ [Frames Corrupt/No Face]
                         ▼                         ▼
                     (SCORING)             [Graceful Degradation]
                         │                 - Speech preserved
                         │                 - has_behavioral_data = False
                         │                 - Score = 100% speech weight
                         │                 - Notes attached
                         │                         │
                         ▼                         ▼
                    (COMPLETED)          (PARTIALLY_COMPLETED)
```

---

## 3. Error Classification Matrix

| Error Class | Example Root Causes | Handling Strategy | Maximum Retries | Target State |
| :--- | :--- | :--- | :---: | :--- |
| **Transient I/O & Network** | File lock during extraction, temporary thread saturation, OS subprocess hiccup | Exponential backoff ($2^n \times 1\text{s}$) with randomized jitter ($\pm 0.5\text{s}$) | 3 | `COMPLETED` |
| **External LLM Rate Limits** | Gemini API 429 quota exhaustion, temporary connection reset | Exponential backoff; if still exhausted, seamless fallback to deterministic rule-based feedback engine | 3 | `COMPLETED` |
| **Vision Tracking / Frame Issues** | Dark room, webcam tilted away, no face in frame, codec packet drop | Log `DEGRADED` warning in `PipelineExecutionLog`, preserve `SpeechAnalysis`, adapt composite scoring formula | 1 (Fast failover) | `PARTIALLY_COMPLETED` |
| **Fatal Media Corruption** | 0-byte audio stream, empty file, unsupported internal encoding | Catch immediately without wasteful retries, log stack trace, set status to `FAILED` | 0 | `FAILED` |

---

## 4. Exponential Backoff Formula with Jitter

For attempt $n \in \{1, 2, 3\}$:
$$\text{Delay}(n) = \min\left(\text{max\_delay},\; \text{base\_delay} \times \text{backoff\_factor}^{n-1}\right) + \text{random}(0, 0.5)$$

* Parameters: `base_delay = 1.0s`, `backoff_factor = 2.0`, `max_delay = 8.0s`.
* Attempt 1: $1.0\text{s} + \text{jitter}$
* Attempt 2: $2.0\text{s} + \text{jitter}$
* Attempt 3: $4.0\text{s} + \text{jitter}$

---

## 5. Graceful Degradation Scoring Model

When `has_behavioral_data = True`:
$$\text{Score} = 0.50 \times \text{SpeechScore} + 0.50 \times \text{BehavioralScore}$$

When `has_behavioral_data = False` (Vision failure / Degradation active):
$$\text{Score} = 1.00 \times \text{SpeechScore}$$
$$\text{Status} = \text{PARTIALLY\_COMPLETED}$$
$$\text{Notes} = \text{"Video frames had insufficient facial visibility for eye/posture tracking. Score evaluated based 100% on speech delivery."}$$

---

## 6. Implementation Components

1. **Database Model:** `PipelineExecutionLog` ([`apps.presentation.models`](file:///Users/nafisatabassummaria/Study/3.2/Project/CareerFlow/backend/apps/presentation/models.py))
2. **Supervisor Layer:** `PipelineManager` ([`apps.presentation.services.pipeline_manager`](file:///Users/nafisatabassummaria/Study/3.2/Project/CareerFlow/backend/apps/presentation/services/pipeline_manager.py))
3. **API Endpoints:**
   - `POST /api/presentation/<video_id>/retry/` — Re-triggers pipeline with supervised retry logic.
   - `GET /api/presentation/<video_id>/status/` — Real-time pipeline status and resilience telemetry.
   - `GET /api/presentation/<video_id>/logs/` — Chronological execution audit trail.
4. **Frontend Alert & Recovery Component:** [`PipelineStatusAlert.tsx`](file:///Users/nafisatabassummaria/Study/3.2/Project/CareerFlow/frontend/src/components/presentation/PipelineStatusAlert.tsx)
5. **Testing Verification:**
   - Backend Resilience Unit Suite: `test_pipeline_resilience.py` (7 tests)
   - UI Automation Suite: `test_us40_pipeline_resilience_ui.py` (5 tests)
