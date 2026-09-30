# Sprint 3 Specification — US-14: Video Presentation Scoring Engine & Rubric

**Author:** Jannatun Naeem Mona (System Analyst / Business Analyst)  
**Story:** US-14: Video Presentation Score (8 Story Points, 15 Hours)  
**Target Module:** `backend/apps/presentation/` & `frontend/src/components/presentation/`  
**Date:** 2026-09-30  
**Status:** Approved Specification  

---

## 1. Overview & Objective

The Presentation Scoring Engine is responsible for synthesizing quantitative presentation metrics into a single, standardized, intuitive composite score (0–100) alongside detailed subcategory diagnostics. 

It consumes:
1. **Speech Analysis Metrics (US-12, Mobin):** Speaking pace (WPM), filler word count and taxonomy, and speech clarity.
2. **Behavioral Vision Metrics (US-13, Mobin):** Eye contact ratio (looking at camera lens), posture stability score, and facial engagement score.

The computed score is displayed via an interactive, animated UI card (`PresentationScoreCard.tsx`), stored in the relational database (`PresentationScore`), and passed downstream to the AI Suggestions Engine (US-15, Bonny) and the Pipeline Supervisor (US-40, Maria).

---

## 2. Mathematical Formulation & Weighting Rubric

### 2.1 Composite Score Equation
The composite score $S_{\text{overall}}$ is a weighted average of the Speech and Behavioral dimensions:

$$S_{\text{overall}} = \text{round}\left(W_{\text{speech}} \times S_{\text{speech}} + W_{\text{behavior}} \times S_{\text{behavior}}\right)$$

Where default weights are:
* $W_{\text{speech}} = 0.50$ (50%)
* $W_{\text{behavior}} = 0.50$ (50%)

All subscores and composite scores are clamped to the closed interval $[0, 100]$ as integers.

---

### 2.2 Speech Score Breakdown ($S_{\text{speech}}$)
Speech quality consists of **Speaking Pace** (50%) and **Filler Word Control** (50%):

$$S_{\text{speech}} = \text{round}\left(0.50 \times S_{\text{pace}} + 0.50 \times S_{\text{filler}}\right)$$

#### A. Pace Subscore ($S_{\text{pace}}$)
* **Optimal Benchmark Range:** **130 to 160 Words Per Minute (WPM)**.
* **Penalty:** For every WPM outside the optimal range, 1 point is deducted from 100:
  $$S_{\text{pace}} = \begin{cases} 
  100 & \text{if } 130 \le \text{WPM} \le 160 \\
  \max(0, 100 - (130 - \text{WPM})) & \text{if } \text{WPM} < 130 \\
  \max(0, 100 - (\text{WPM} - 160)) & \text{if } \text{WPM} > 160 
  \end{cases}$$
* *Example 1:* 145 WPM $\rightarrow 100$ pts (optimal).
* *Example 2:* 115 WPM $\rightarrow 100 - (130 - 115) = 85$ pts.
* *Example 3:* 190 WPM $\rightarrow 100 - (190 - 160) = 70$ pts.

#### B. Filler Word Subscore ($S_{\text{filler}}$)
* **Ideal Benchmark:** 0 filler words ("um", "uh", "like", "you know", "basically", etc.).
* **Penalty:** 5 points deducted per filler occurrence:
  $$S_{\text{filler}} = \max(0, 100 - (\text{filler\_count} \times 5))$$
* *Example 1:* 0 fillers $\rightarrow 100$ pts.
* *Example 2:* 4 fillers $\rightarrow 100 - (4 \times 5) = 80$ pts.
* *Example 3:* 20+ fillers $\rightarrow 0$ pts.

---

### 2.3 Behavioral Score Breakdown ($S_{\text{behavior}}$)
Behavioral presentation quality consists of three computer vision metrics computed via MediaPipe Face Mesh & Pose tracking:

$$S_{\text{behavior}} = \text{round}\left(0.40 \times S_{\text{eye}} + 0.30 \times S_{\text{posture}} + 0.30 \times S_{\text{engagement}}\right)$$

#### A. Eye Contact Subscore ($S_{\text{eye}}$ — 40% weight)
* Direct percentage of sampled video frames where the candidate maintains direct gaze at the webcam lens:
  $$S_{\text{eye}} \in [0, 100]$$

#### B. Posture Stability Subscore ($S_{\text{posture}}$ — 30% weight)
* Measures shoulder horizontal alignment, upright torso positioning, and minimization of excessive sway:
  $$S_{\text{posture}} \in [0, 100]$$

#### C. Facial Engagement Subscore ($S_{\text{engagement}}$ — 30% weight)
* Evaluates facial expressiveness, smile frequency, attentiveness, and positive emotional delivery:
  $$S_{\text{engagement}} \in [0, 100]$$

---

### 2.4 Graceful Degradation & Resilience (US-40 Alignment)
In real-world network or hardware conditions, candidate webcam video frames may be corrupted, dark, or missing vision landmarks.
* **If `BehavioralAnalysis` is missing or invalid:**
  * The system activates graceful degradation.
  * $S_{\text{overall}}$ is calculated solely on speech:
    $$S_{\text{overall}} = S_{\text{speech}}$$
  * Flag `has_behavioral_data` is marked as `False`.
  * An informative note is attached: *"Behavioral tracking was unavailable for this video; overall presentation score is evaluated 100% on speech delivery."*

---

## 3. Qualitative Performance Tiers & Color Rubric

| Score Range | Tier Label | Color Code | Hex Code | Pedagogical Guidance |
| :---: | :---: | :---: | :---: | :--- |
| **85 – 100** | **Excellent** | 🟢 Green | `#277254` | Outstanding executive presence; delivery is clear, well-paced, and engaging. |
| **70 – 84** | **Competent** | 🟡 Amber | `#d97706` | Strong baseline performance; minor adjustments needed in pacing or filler control. |
| **0 – 69** | **Needs Practice** | 🔴 Coral / Red | `#dc2626` | Significant areas for improvement in speech pacing, filler words, or camera gaze. |

---

## 4. Database Schema Contract (`PresentationScore`)

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `id` | BigAutoField | Primary Key | Unique record ID |
| `video` | OneToOneField | Cascade | Related `PresentationVideo` record |
| `overall_score` | PositiveIntegerField | 0 | Final composite score (0–100) |
| `speech_score` | PositiveIntegerField | 0 | Composite speech score (0–100) |
| `behavioral_score` | PositiveIntegerField | 0 | Composite behavioral score (0–100) |
| `pace_score` | PositiveIntegerField | 0 | Pacing subscore (0–100) |
| `filler_score` | PositiveIntegerField | 0 | Filler words subscore (0–100) |
| `eye_contact_score`| PositiveIntegerField | 0 | Eye contact subscore (0–100) |
| `posture_score` | PositiveIntegerField | 0 | Posture stability subscore (0–100) |
| `engagement_score` | PositiveIntegerField | 0 | Facial engagement subscore (0–100) |
| `has_behavioral_data` | BooleanField | True | Flag indicating whether vision data was present |
| `notes` | TextField | Blank | Explanatory notes or degradation warnings |
| `calculated_at` | DateTimeField | Auto Now | Timestamp when scores were calculated |

---

## 5. API Endpoints

1. **`GET /api/presentation/<video_id>/score/`**
   * Returns the current `PresentationScore` for the given video.
   * If not yet calculated, returns 404 with status `detail`.
2. **`POST /api/presentation/<video_id>/score/`** (or `/calculate/`)
   * Triggers score aggregation for the given video using existing `SpeechAnalysis` and `BehavioralAnalysis` records.
   * Updates `PresentationVideo.status` to `COMPLETED` (or `SCORING`).
   * Returns the populated `PresentationScore` object.
