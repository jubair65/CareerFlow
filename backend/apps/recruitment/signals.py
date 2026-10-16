"""
Django Signals for Automated Score Recalculation (US-23-T5).
Monitors changes to RecruitmentRoom weighting, CV Job Matches, and Video Presentation Scores
to ensure candidate final scores remain up-to-date and consistent without manual intervention.
"""

import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.recruitment.models import RecruitmentRoom, CandidateApplication
from apps.presentation.models import PresentationScore
from apps.cv.models import CVJobMatch
from apps.recruitment.services.scoring_service import (
    calculate_application_score,
    calculate_room_applicant_scores,
)

logger = logging.getLogger(__name__)


@receiver(post_save, sender=RecruitmentRoom)
def on_room_weight_or_update(sender, instance, created, update_fields, **kwargs):
    """
    Recalculates all applicant scores in a room when room weights or configuration change.
    """
    if created:
        return

    # Check if update_fields was specified and weights are in it, or update_fields is None (full save)
    if update_fields is None or 'cv_weight' in update_fields or 'video_weight' in update_fields:
        try:
            calculate_room_applicant_scores(instance)
            logger.info(f"Recalculated scores for room #{instance.id} due to weight update.")
        except Exception as e:
            logger.warning(f"Error recalculating scores for room #{instance.id}: {e}")


@receiver(post_save, sender=PresentationScore)
def on_presentation_score_saved(sender, instance, created, **kwargs):
    """
    Recalculates application final score when a video analysis pipeline produces/updates a PresentationScore.
    """
    try:
        applications = CandidateApplication.objects.filter(video=instance.video)
        for app in applications:
            calculate_application_score(app, persist=True)
            logger.info(f"Updated final score for application #{app.id} following presentation score save.")
    except Exception as e:
        logger.warning(f"Error updating score on presentation save: {e}")


@receiver(post_save, sender=CVJobMatch)
def on_cv_job_match_saved(sender, instance, created, **kwargs):
    """
    Recalculates application final score when a CV match score is computed or updated.
    """
    try:
        applications = CandidateApplication.objects.filter(cv=instance.cv)
        for app in applications:
            calculate_application_score(app, persist=True)
            logger.info(f"Updated final score for application #{app.id} following CV job match save.")
    except Exception as e:
        logger.warning(f"Error updating score on CV match save: {e}")


@receiver(post_save, sender=CandidateApplication)
def on_application_created(sender, instance, created, **kwargs):
    """
    Automatically calculates initial score when an application is first created with attached CV/video.
    """
    if created and instance.final_score is None:
        try:
            calculate_application_score(instance, persist=True)
        except Exception as e:
            logger.warning(f"Error on initial application score computation #{instance.id}: {e}")
