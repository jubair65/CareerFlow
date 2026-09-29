import os
import logging
from typing import Optional, Dict, Any
from django.db import transaction

from apps.presentation.models import PresentationVideo, BehavioralAnalysis
from apps.presentation.services.vision_pipeline import VisionPipeline

logger = logging.getLogger(__name__)


class BehavioralAnalyzer:
    """
    Orchestration service for US-13 Behavioral Analysis pipeline.
    Coordinates video frame extraction, MediaPipe Face Mesh & Pose tracking,
    metric computation, and database persistence in BehavioralAnalysis model.
    """

    def __init__(self, vision_pipeline: Optional[VisionPipeline] = None):
        self.vision_pipeline = vision_pipeline or VisionPipeline()

    def analyze_presentation_video(self, video: PresentationVideo) -> BehavioralAnalysis:
        """
        Executes behavioral analysis for a candidate's PresentationVideo.

        Steps:
            1. Validate video existence and resolve file path
            2. Update video status to PROCESSING_VISION
            3. Run VisionPipeline frame sampling & landmark inference
            4. Persist eye contact, posture, and engagement metrics into BehavioralAnalysis model (US-13-T5)
            5. Transition video status to READY_FOR_ANALYSIS
        """
        if not video.file:
            raise ValueError(f"PresentationVideo ID {video.id} has no associated video file.")

        # Safely resolve path whether absolute (e.g. tests) or relative to MEDIA_ROOT
        if hasattr(video.file, 'name') and os.path.isabs(video.file.name) and os.path.exists(video.file.name):
            video_path = video.file.name
        else:
            try:
                video_path = video.file.path
            except Exception:
                from django.conf import settings
                video_path = os.path.join(settings.MEDIA_ROOT, str(video.file))

        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file does not exist at {video_path}")

        # Step 1: Update status
        video.status = 'PROCESSING_VISION'
        video.save(update_fields=['status'])

        try:
            # Step 2: Execute vision pipeline
            results = self.vision_pipeline.analyze_video(video_path)

            eye_contact = results.get("eye_contact_score", 75)
            posture = results.get("posture_score", 80)
            engagement = results.get("engagement_score", 75)
            frame_metrics = results.get("frame_metrics", {})

            # Step 3: Persist in database (US-13-T5)
            with transaction.atomic():
                behavioral_record, _ = BehavioralAnalysis.objects.update_or_create(
                    video=video,
                    defaults={
                        "eye_contact_score": eye_contact,
                        "posture_score": posture,
                        "engagement_score": engagement,
                        "frame_metrics": frame_metrics,
                    }
                )
                video.status = 'READY_FOR_ANALYSIS'
                video.save(update_fields=['status'])

            logger.info(
                f"Successfully completed behavioral analysis for video {video.id}: "
                f"Eye Contact={eye_contact}%, Posture={posture}%, Engagement={engagement}%"
            )
            return behavioral_record

        except Exception as e:
            logger.error(f"Behavioral analysis failed for video {video.id}: {e}")
            video.status = 'FAILED'
            video.save(update_fields=['status'])
            raise e


def analyze_behavior(video: PresentationVideo) -> BehavioralAnalysis:
    """
    Functional helper to trigger behavioral analysis on a presentation video.
    """
    analyzer = BehavioralAnalyzer()
    return analyzer.analyze_presentation_video(video)
