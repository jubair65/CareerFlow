import os
import logging
from typing import Dict, List, Optional, Any, Tuple

from apps.presentation.services.behavioral_metrics import (
    LEFT_EYE_INNER,
    LEFT_EYE_OUTER,
    LEFT_EYE_TOP,
    LEFT_EYE_BOTTOM,
    LEFT_IRIS_CENTER,
    RIGHT_EYE_INNER,
    RIGHT_EYE_OUTER,
    RIGHT_EYE_TOP,
    RIGHT_EYE_BOTTOM,
    RIGHT_IRIS_CENTER,
    MOUTH_LEFT_CORNER,
    MOUTH_RIGHT_CORNER,
    MOUTH_UPPER_LIP_TOP,
    MOUTH_LOWER_LIP_BOTTOM,
    POSE_NOSE,
    POSE_LEFT_SHOULDER,
    POSE_RIGHT_SHOULDER,
    compute_eye_aspect_ratio,
    compute_iris_horizontal_ratio,
    is_eye_contact_frame,
    calculate_eye_contact_score,
    calculate_shoulder_tilt_angle,
    check_is_slouched,
    calculate_posture_score,
    calculate_facial_engagement,
    calculate_engagement_score,
)

logger = logging.getLogger(__name__)


class VisionPipeline:
    """
    Computer Vision pipeline for US-13 Behavioral Analysis.
    Extracts frames from video files using OpenCV, analyzes facial landmarks and body pose
    using MediaPipe Face Mesh and Pose models, and aggregates behavioral metrics.
    """

    def __init__(self, sample_fps: float = 3.0):
        """
        :param sample_fps: Target number of frames to sample and analyze per second of video.
                           Default 3.0 FPS balances real-time accuracy and performance.
        """
        self.sample_fps = sample_fps
        self._mp_face_mesh = None
        self._mp_pose = None

    def _init_models(self):
        """Lazy load MediaPipe solutions."""
        if self._mp_face_mesh is None or self._mp_pose is None:
            try:
                import mediapipe as mp
                # Support MediaPipe Solutions API
                if hasattr(mp, 'solutions'):
                    self._mp_face_mesh = mp.solutions.face_mesh.FaceMesh(
                        static_image_mode=False,
                        max_num_faces=1,
                        refine_landmarks=True,
                        min_detection_confidence=0.5,
                        min_tracking_confidence=0.5
                    )
                    self._mp_pose = mp.solutions.pose.Pose(
                        static_image_mode=False,
                        model_complexity=1,
                        smooth_landmarks=True,
                        min_detection_confidence=0.5,
                        min_tracking_confidence=0.5
                    )
                else:
                    logger.warning("MediaPipe solutions module not found; using alternative or mock pipeline.")
            except Exception as e:
                logger.warning(f"Unable to initialize MediaPipe models directly: {e}")

    def analyze_video(self, video_path: str) -> Dict[str, Any]:
        """
        Main video analysis entrypoint. Opens video, samples frames at sample_fps,
        runs face mesh and pose detection, and computes behavioral scores.
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found at: {video_path}")

        try:
            import cv2
        except ImportError:
            raise RuntimeError("opencv-python is required for VisionPipeline execution.")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"OpenCV could not open video file: {video_path}")

        try:
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration_sec = total_frames / fps if fps > 0 else 0.0

            # Determine frame stride
            frame_stride = max(1, int(round(fps / self.sample_fps))) if self.sample_fps > 0 else 1

            self._init_models()

            tilt_angles: List[float] = []
            slouch_flags: List[bool] = []
            frame_engagements: List[float] = []
            contact_frames = 0
            face_detected_frames = 0
            smiling_frames = 0
            sampled_frames_count = 0
            timeline: List[Dict[str, Any]] = []

            frame_idx = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_idx % frame_stride == 0:
                    sampled_frames_count += 1
                    timestamp = round(frame_idx / fps, 2)

                    frame_result = self._process_single_frame(frame, timestamp)
                    
                    if frame_result["face_detected"]:
                        face_detected_frames += 1
                        if frame_result["eye_contact"]:
                            contact_frames += 1
                        if frame_result["is_smiling"]:
                            smiling_frames += 1
                        frame_engagements.append(frame_result["engagement_score"])

                    if frame_result["pose_detected"]:
                        tilt_angles.append(frame_result["shoulder_tilt_deg"])
                        slouch_flags.append(frame_result["is_slouched"])

                    timeline.append({
                        "timestamp_sec": timestamp,
                        "face_detected": frame_result["face_detected"],
                        "eye_contact": frame_result["eye_contact"],
                        "is_slouched": frame_result.get("is_slouched", False),
                        "engagement_score": round(frame_result["engagement_score"], 1),
                        "is_smiling": frame_result.get("is_smiling", False),
                    })

                frame_idx += 1

            # Edge case: No frames sampled or video was empty
            if sampled_frames_count == 0:
                return self._fallback_results(duration_sec, "Empty video stream")

            # Calculate composite scores using behavioral_metrics algorithms
            eye_contact_score = calculate_eye_contact_score(
                total_frames=sampled_frames_count,
                face_detected_frames=face_detected_frames,
                contact_frames=contact_frames
            )

            posture_score, posture_breakdown = calculate_posture_score(
                tilt_angles=tilt_angles,
                slouch_flags=slouch_flags,
                total_frames=sampled_frames_count
            )

            engagement_score, engagement_breakdown = calculate_engagement_score(
                frame_engagement_scores=frame_engagements,
                smiling_frame_count=smiling_frames,
                total_face_frames=face_detected_frames
            )

            metrics_payload = {
                "total_video_frames": total_frames,
                "sampled_frames_count": sampled_frames_count,
                "face_detected_frames": face_detected_frames,
                "contact_frames": contact_frames,
                "duration_seconds": round(duration_sec, 2),
                "sampling_fps": self.sample_fps,
                "eye_contact": {
                    "score": eye_contact_score,
                    "contact_percentage": round((contact_frames / face_detected_frames * 100.0), 1) if face_detected_frames > 0 else 0.0,
                    "presence_percentage": round((face_detected_frames / sampled_frames_count * 100.0), 1)
                },
                "posture": posture_breakdown,
                "engagement": engagement_breakdown,
                "timeline_sample": timeline[::max(1, len(timeline) // 40)],  # Compact ~40 points for UI charts
            }

            return {
                "eye_contact_score": eye_contact_score,
                "posture_score": posture_score,
                "engagement_score": engagement_score,
                "frame_metrics": metrics_payload
            }

        finally:
            cap.release()

    def _process_single_frame(self, frame, timestamp: float) -> Dict[str, Any]:
        """Processes an individual OpenCV BGR frame through Face Mesh and Pose."""
        import cv2

        result = {
            "face_detected": False,
            "eye_contact": False,
            "engagement_score": 70.0,
            "is_smiling": False,
            "pose_detected": False,
            "shoulder_tilt_deg": 0.0,
            "is_slouched": False,
        }

        # Convert to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, _ = frame.shape

        # 1. Face Mesh Analysis
        if self._mp_face_mesh:
            face_results = self._mp_face_mesh.process(rgb_frame)
            if face_results and face_results.multi_face_landmarks:
                face_landmarks = face_results.multi_face_landmarks[0].landmark
                result["face_detected"] = True

                # Extract eye landmarks
                left_inner = (face_landmarks[LEFT_EYE_INNER].x, face_landmarks[LEFT_EYE_INNER].y)
                left_outer = (face_landmarks[LEFT_EYE_OUTER].x, face_landmarks[LEFT_EYE_OUTER].y)
                left_top = (face_landmarks[LEFT_EYE_TOP].x, face_landmarks[LEFT_EYE_TOP].y)
                left_bottom = (face_landmarks[LEFT_EYE_BOTTOM].x, face_landmarks[LEFT_EYE_BOTTOM].y)
                left_iris = (face_landmarks[LEFT_IRIS_CENTER].x, face_landmarks[LEFT_IRIS_CENTER].y)

                right_inner = (face_landmarks[RIGHT_EYE_INNER].x, face_landmarks[RIGHT_EYE_INNER].y)
                right_outer = (face_landmarks[RIGHT_EYE_OUTER].x, face_landmarks[RIGHT_EYE_OUTER].y)
                right_top = (face_landmarks[RIGHT_EYE_TOP].x, face_landmarks[RIGHT_EYE_TOP].y)
                right_bottom = (face_landmarks[RIGHT_EYE_BOTTOM].x, face_landmarks[RIGHT_EYE_BOTTOM].y)
                right_iris = (face_landmarks[RIGHT_IRIS_CENTER].x, face_landmarks[RIGHT_IRIS_CENTER].y)

                # Compute EAR and horizontal iris ratios
                left_ear = compute_eye_aspect_ratio(left_top, left_bottom, left_inner, left_outer)
                right_ear = compute_eye_aspect_ratio(right_top, right_bottom, right_inner, right_outer)
                left_iris_ratio = compute_iris_horizontal_ratio(left_inner, left_outer, left_iris)
                right_iris_ratio = compute_iris_horizontal_ratio(right_inner, right_outer, right_iris)

                # Check eye contact
                result["eye_contact"] = is_eye_contact_frame(
                    left_ratio=left_iris_ratio,
                    right_ratio=right_iris_ratio,
                    left_ear=left_ear,
                    right_ear=right_ear
                )

                # Extract mouth landmarks for engagement
                mouth_left = (face_landmarks[MOUTH_LEFT_CORNER].x, face_landmarks[MOUTH_LEFT_CORNER].y)
                mouth_right = (face_landmarks[MOUTH_RIGHT_CORNER].x, face_landmarks[MOUTH_RIGHT_CORNER].y)
                upper_lip = (face_landmarks[MOUTH_UPPER_LIP_TOP].x, face_landmarks[MOUTH_UPPER_LIP_TOP].y)
                lower_lip = (face_landmarks[MOUTH_LOWER_LIP_BOTTOM].x, face_landmarks[MOUTH_LOWER_LIP_BOTTOM].y)

                eng_score, is_smiling = calculate_facial_engagement(
                    mouth_left=mouth_left,
                    mouth_right=mouth_right,
                    upper_lip=upper_lip,
                    lower_lip=lower_lip,
                    left_ear=left_ear,
                    right_ear=right_ear
                )
                result["engagement_score"] = eng_score
                result["is_smiling"] = is_smiling

        # 2. Pose Analysis
        if self._mp_pose:
            pose_results = self._mp_pose.process(rgb_frame)
            if pose_results and pose_results.pose_landmarks:
                pose_landmarks = pose_results.pose_landmarks.landmark
                result["pose_detected"] = True

                left_shoulder = (pose_landmarks[POSE_LEFT_SHOULDER].x, pose_landmarks[POSE_LEFT_SHOULDER].y)
                right_shoulder = (pose_landmarks[POSE_RIGHT_SHOULDER].x, pose_landmarks[POSE_RIGHT_SHOULDER].y)
                nose = (pose_landmarks[POSE_NOSE].x, pose_landmarks[POSE_NOSE].y)

                # Calculate shoulder tilt angle
                tilt = calculate_shoulder_tilt_angle(left_shoulder, right_shoulder)
                result["shoulder_tilt_deg"] = tilt

                # Check slouch
                is_slouch, _ = check_is_slouched(nose, left_shoulder, right_shoulder)
                result["is_slouched"] = is_slouch

        return result

    def _fallback_results(self, duration_sec: float, reason: str) -> Dict[str, Any]:
        """Provides safe fallback metrics in degraded video conditions (US-40 compatibility)."""
        logger.warning(f"Generating fallback behavioral metrics: {reason}")
        return {
            "eye_contact_score": 70,
            "posture_score": 75,
            "engagement_score": 70,
            "frame_metrics": {
                "total_video_frames": 0,
                "sampled_frames_count": 0,
                "face_detected_frames": 0,
                "contact_frames": 0,
                "duration_seconds": duration_sec,
                "degraded_mode": True,
                "fallback_reason": reason,
                "posture": {"status": "default_fallback"},
                "engagement": {"status": "default_fallback"},
                "timeline_sample": []
            }
        }
