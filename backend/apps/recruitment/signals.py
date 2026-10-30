"""
Django Signals for Automated Score Recalculation (US-23-T5) &
Applicant Application Status Notifications (US-35-T2).
Monitors changes to RecruitmentRoom weighting, CV Job Matches, Video Presentation Scores,
and candidate status transitions (shortlist and HR decisions).
"""

import logging
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from apps.recruitment.models import RecruitmentRoom, CandidateApplication, StatusNotificationLog
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

    # If specific fields were updated and weights are not among them, do not re-score
    if update_fields is not None and 'cv_weight' not in update_fields and 'video_weight' not in update_fields:
        return

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


@receiver(pre_save, sender=CandidateApplication)
def on_application_pre_save(sender, instance, **kwargs):
    """
    US-35-T2: Captures previous shortlist and HR decision states prior to saving.
    Allows post_save to detect genuine status transitions.
    """
    if instance.pk:
        try:
            prev = CandidateApplication.objects.only('is_shortlisted', 'hr_decision').get(pk=instance.pk)
            instance._pre_save_is_shortlisted = prev.is_shortlisted
            instance._pre_save_hr_decision = prev.hr_decision
        except CandidateApplication.DoesNotExist:
            instance._pre_save_is_shortlisted = None
            instance._pre_save_hr_decision = None
    else:
        instance._pre_save_is_shortlisted = None
        instance._pre_save_hr_decision = None


@receiver(post_save, sender=CandidateApplication)
def on_application_created_or_status_changed(sender, instance, created, **kwargs):
    """
    US-23-T5: Initial score computation on creation.
    US-35-T2: Dispatches applicant status notification when shortlist or HR decision changes.
    """
    if created and instance.final_score is None:
        try:
            calculate_application_score(instance, persist=True)
        except Exception as e:
            logger.warning(f"Error on initial application score computation #{instance.id}: {e}")

    # US-35-T2: Detect status changes on existing applications
    if not created:
        prev_shortlisted = getattr(instance, '_pre_save_is_shortlisted', None)
        prev_hr_decision = getattr(instance, '_pre_save_hr_decision', None)

        # Check if HR decision changed to a definitive state
        hr_decision_changed = (
            prev_hr_decision is not None and
            prev_hr_decision != instance.hr_decision and
            instance.hr_decision in [
                CandidateApplication.HrDecision.CONFIRMED,
                CandidateApplication.HrDecision.REJECTED,
                CandidateApplication.HrDecision.OVERRIDDEN,
                CandidateApplication.HrDecision.ON_HOLD,
            ]
        )

        # Check if shortlist status changed
        shortlist_changed = (
            prev_shortlisted is not None and
            prev_shortlisted != instance.is_shortlisted
        )

        if hr_decision_changed or shortlist_changed:
            from apps.recruitment.services.status_notification_service import dispatch_status_notification
            status_type = None
            if instance.hr_decision == CandidateApplication.HrDecision.CONFIRMED:
                status_type = StatusNotificationLog.StatusType.CONFIRMED
            elif instance.hr_decision == CandidateApplication.HrDecision.REJECTED:
                status_type = StatusNotificationLog.StatusType.REJECTED
            elif instance.hr_decision == CandidateApplication.HrDecision.OVERRIDDEN:
                status_type = (
                    StatusNotificationLog.StatusType.SHORTLISTED
                    if instance.is_shortlisted
                    else StatusNotificationLog.StatusType.REJECTED
                )
            elif instance.hr_decision == CandidateApplication.HrDecision.ON_HOLD:
                status_type = StatusNotificationLog.StatusType.ON_HOLD
            elif instance.is_shortlisted:
                status_type = StatusNotificationLog.StatusType.SHORTLISTED

            if status_type:
                try:
                    dispatch_status_notification(
                        instance,
                        status_type=status_type,
                        notes=instance.hr_decision_notes or instance.shortlist_reason,
                    )
                except Exception as notif_err:
                    logger.warning(f"Failed to dispatch status notification for app #{instance.id}: {notif_err}")
