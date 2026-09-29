import math
from typing import Dict, List, Optional, Tuple, Any

# Standard MediaPipe Face Mesh landmark indices
# Left eye
LEFT_EYE_INNER = 133
LEFT_EYE_OUTER = 33
LEFT_EYE_TOP = 159
LEFT_EYE_BOTTOM = 145
LEFT_IRIS_CENTER = 468

# Right eye
RIGHT_EYE_INNER = 362
RIGHT_EYE_OUTER = 263
RIGHT_EYE_TOP = 386
RIGHT_EYE_BOTTOM = 374
RIGHT_IRIS_CENTER = 473

# Mouth / Smile landmarks
MOUTH_LEFT_CORNER = 61
MOUTH_RIGHT_CORNER = 291
MOUTH_UPPER_LIP_TOP = 0
MOUTH_LOWER_LIP_BOTTOM = 17

# Pose Landmark indices
POSE_NOSE = 0
POSE_LEFT_EYE = 2
POSE_RIGHT_EYE = 5
POSE_LEFT_EAR = 7
POSE_RIGHT_EAR = 8
POSE_LEFT_SHOULDER = 11
POSE_RIGHT_SHOULDER = 12


def euclidean_distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Calculates 2D Euclidean distance between two points."""
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


def compute_eye_aspect_ratio(
    top: Tuple[float, float],
    bottom: Tuple[float, float],
    inner: Tuple[float, float],
    outer: Tuple[float, float]
) -> float:
    """
    Computes Eye Aspect Ratio (EAR).
    Values typically 0.22 - 0.38 for open/alert eyes. < 0.18 indicates closed/blinking or drowsy eyes.
    """
    vertical_dist = euclidean_distance(top, bottom)
    horizontal_dist = euclidean_distance(inner, outer)
    if horizontal_dist <= 1e-6:
        return 0.0
    return vertical_dist / horizontal_dist


def compute_iris_horizontal_ratio(
    inner_corner: Tuple[float, float],
    outer_corner: Tuple[float, float],
    iris_center: Tuple[float, float]
) -> float:
    """
    Computes the horizontal ratio of the iris between the inner and outer canthi.
    Returns float roughly in [0.0, 1.0]. A value centered around 0.40 - 0.60 indicates looking straight.
    """
    # Order points from left to right on screen
    x_min = min(inner_corner[0], outer_corner[0])
    x_max = max(inner_corner[0], outer_corner[0])
    eye_width = x_max - x_min
    if eye_width <= 1e-6:
        return 0.5
    ratio = (iris_center[0] - x_min) / eye_width
    return max(0.0, min(1.0, ratio))


def is_eye_contact_frame(
    left_ratio: float,
    right_ratio: float,
    left_ear: float,
    right_ear: float,
    head_yaw_deg: float = 0.0,
    head_pitch_deg: float = 0.0
) -> bool:
    """
    Determines if a single frame represents positive eye contact with the camera.
    Criteria:
      - Eyes must be reasonably open (EAR >= 0.16)
      - Irises centered horizontally in the eye sockets (0.35 <= ratio <= 0.65)
      - Head orientation is generally facing the camera (|yaw| <= 18 deg, |pitch| <= 18 deg)
    """
    # If eyes are closed/blinking, cannot maintain eye contact in this instant
    if left_ear < 0.16 or right_ear < 0.16:
        return False

    # Check iris gaze centering
    left_centered = 0.33 <= left_ratio <= 0.67
    right_centered = 0.33 <= right_ratio <= 0.67

    # Check head pose orientation (if head is turned away, eye contact is broken)
    head_facing_camera = abs(head_yaw_deg) <= 18.0 and abs(head_pitch_deg) <= 18.0

    return left_centered and right_centered and head_facing_camera


def calculate_eye_contact_score(
    total_frames: int,
    face_detected_frames: int,
    contact_frames: int
) -> int:
    """
    Computes overall Eye Contact Score (0-100).
    Formula:
      - Raw ratio of contact frames to face-detected frames.
      - Scaled penalty if face is absent for a significant portion (>20% of video).
    """
    if total_frames <= 0 or face_detected_frames <= 0:
        return 0

    face_presence_ratio = face_detected_frames / total_frames
    contact_ratio = contact_frames / face_detected_frames

    # Direct percentage of face-detected frames looking at camera
    base_score = contact_ratio * 100.0

    # Presence penalty if candidate was missing/off-screen for over 20% of presentation
    if face_presence_ratio < 0.80:
        penalty = (0.80 - face_presence_ratio) * 50.0
        base_score = max(0.0, base_score - penalty)

    return int(round(max(0.0, min(100.0, base_score))))


def calculate_shoulder_tilt_angle(
    left_shoulder: Tuple[float, float],
    right_shoulder: Tuple[float, float]
) -> float:
    """
    Calculates the absolute tilt angle (in degrees) of the shoulder line relative to horizontal.
    0 degrees means perfectly horizontal/level shoulders.
    """
    dx = right_shoulder[0] - left_shoulder[0]
    dy = right_shoulder[1] - left_shoulder[1]
    if abs(dx) <= 1e-6:
        return 90.0
    angle_rad = math.atan2(abs(dy), abs(dx))
    return math.degrees(angle_rad)


def check_is_slouched(
    nose: Tuple[float, float],
    left_shoulder: Tuple[float, float],
    right_shoulder: Tuple[float, float],
    baseline_compression: Optional[float] = None
) -> Tuple[bool, float]:
    """
    Evaluates whether candidate is slouching based on the vertical distance
    between nose and shoulder midpoint relative to shoulder width.
    """
    shoulder_midpoint_y = (left_shoulder[1] + right_shoulder[1]) / 2.0
    shoulder_width = euclidean_distance(left_shoulder, right_shoulder)
    if shoulder_width <= 1e-6:
        return False, 0.0

    # Vertical distance from nose to shoulder line
    vertical_span = abs(shoulder_midpoint_y - nose[1])
    vertical_ratio = vertical_span / shoulder_width

    # A typical upright presenter has vertical_ratio around 0.55 - 0.85
    # Slouching forward compresses vertical distance relative to shoulder width
    is_slouch = vertical_ratio < 0.42
    return is_slouch, round(vertical_ratio, 3)


def calculate_posture_score(
    tilt_angles: List[float],
    slouch_flags: List[bool],
    total_frames: int
) -> Tuple[int, Dict[str, Any]]:
    """
    Calculates Posture Score (0-100) based on:
      1. Average shoulder level angle (degrees from horizontal)
      2. Slouch percentage (% of frames with compressed/slouched torso)
      3. Posture stability (consistency across presentation)
    """
    if not tilt_angles:
        # Default fallback if no pose landmarks detected
        return 75, {"shoulder_tilt_avg_deg": 0.0, "slouch_percentage": 0.0, "status": "insufficient_data"}

    avg_tilt = sum(tilt_angles) / len(tilt_angles)
    slouch_count = sum(1 for s in slouch_flags if s)
    slouch_pct = (slouch_count / len(slouch_flags)) * 100.0 if slouch_flags else 0.0

    # Base score begins at 100
    score = 100.0

    # Penalty for shoulder tilt:
    # 0-3 deg: no penalty (natural posture)
    # 3-8 deg: -1 pt per degree
    # >8 deg: -2.5 pts per degree
    if avg_tilt > 3.0:
        if avg_tilt <= 8.0:
            score -= (avg_tilt - 3.0) * 1.5
        else:
            score -= (5.0 * 1.5) + ((avg_tilt - 8.0) * 2.5)

    # Penalty for slouching:
    # Up to 10% slouch frames tolerated (e.g. looking at notes momentarily)
    # Beyond 10%, penalize proportionally
    if slouch_pct > 10.0:
        score -= (slouch_pct - 10.0) * 0.45

    # Variance / fidgeting stability penalty
    if len(tilt_angles) > 1:
        mean_tilt = sum(tilt_angles) / len(tilt_angles)
        variance = sum((t - mean_tilt) ** 2 for t in tilt_angles) / len(tilt_angles)
        std_dev = math.sqrt(variance)
        if std_dev > 4.0:
            score -= min(15.0, (std_dev - 4.0) * 2.0)

    final_score = int(round(max(0.0, min(100.0, score))))

    breakdown = {
        "shoulder_tilt_avg_deg": round(avg_tilt, 2),
        "slouch_percentage": round(slouch_pct, 1),
        "posture_status": "Upright & Confident" if final_score >= 80 else ("Moderate Posture" if final_score >= 65 else "Needs Alignment")
    }

    return final_score, breakdown


def calculate_facial_engagement(
    mouth_left: Tuple[float, float],
    mouth_right: Tuple[float, float],
    upper_lip: Tuple[float, float],
    lower_lip: Tuple[float, float],
    left_ear: float,
    right_ear: float
) -> Tuple[float, bool]:
    """
    Assesses facial engagement in a single frame:
      - Attentiveness: alert, open eyes (average EAR)
      - Smile / Positivity: mouth corner elevation and mouth opening geometry
    Returns (frame_engagement_score, is_smiling)
    """
    avg_ear = (left_ear + right_ear) / 2.0

    # Eye alertness subscore (0 to 1.0)
    # Optimal presentation eye opening: 0.22 - 0.35 EAR
    if avg_ear >= 0.22:
        alertness = min(1.0, (avg_ear - 0.15) / 0.15)
    elif avg_ear >= 0.16:
        alertness = 0.50
    else:
        alertness = 0.20  # Drowsy / closed

    # Smile / Expression positivity
    # Mouth corner height vs upper lip height (in normalized coords, 0 is top, 1 is bottom)
    corner_y_avg = (mouth_left[1] + mouth_right[1]) / 2.0
    mouth_width = euclidean_distance(mouth_left, mouth_right)
    lip_height = euclidean_distance(upper_lip, lower_lip)

    # When smiling, mouth corners elevate relative to upper lip, and mouth width widens
    is_smiling = corner_y_avg < upper_lip[1] + 0.015 and mouth_width > 0.10

    positivity = 0.90 if is_smiling else 0.70

    frame_score = (alertness * 0.60 + positivity * 0.40) * 100.0
    return frame_score, is_smiling


def calculate_engagement_score(
    frame_engagement_scores: List[float],
    smiling_frame_count: int,
    total_face_frames: int
) -> Tuple[int, Dict[str, Any]]:
    """
    Computes overall Engagement Score (0-100).
    A high engagement score reflects sustained attentiveness, dynamic expression, and warm confidence.
    """
    if not frame_engagement_scores:
        return 75, {"attentiveness": "moderate", "smile_ratio": 0.0, "status": "insufficient_data"}

    avg_engagement = sum(frame_engagement_scores) / len(frame_engagement_scores)
    smile_ratio = (smiling_frame_count / total_face_frames) if total_face_frames > 0 else 0.0

    # Bonus for positive, pleasant engagement (up to +10 pts for balanced warmth)
    bonus = min(10.0, smile_ratio * 25.0)
    final_score = int(round(max(0.0, min(100.0, avg_engagement + bonus))))

    breakdown = {
        "attentiveness_avg": round(avg_engagement, 1),
        "smile_percentage": round(smile_ratio * 100.0, 1),
        "expression_summary": "Engaging & Warm" if final_score >= 80 else ("Attentive" if final_score >= 65 else "Monotone / Low Energy")
    }

    return final_score, breakdown
