"""
US-35: Applicant Application Status Notification Service.
Dispatches in-app notifications and transactional emails when an applicant's
application status transitions (Shortlisted, Confirmed, Rejected, On Hold).
Persists audit log entries to StatusNotificationLog with fault isolation.
"""

import logging
from datetime import timedelta
from typing import Optional, Dict, Any
from django.conf import settings
from django.utils import timezone
from apps.recruitment.models import CandidateApplication, StatusNotificationLog
from apps.core.models import Notification
from apps.core.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


def dispatch_status_notification(
    application: CandidateApplication,
    status_type: Optional[str] = None,
    notes: Optional[str] = None,
    force_email: bool = True
) -> Dict[str, Any]:
    """
    US-35-T2, US-35-T3, US-35-T5:
    Main entry point for applicant status notification dispatches.
    - Creates in-app notification in core notification center.
    - Sends transactional HTML email with proper template.
    - Logs transmission audit entry in StatusNotificationLog.
    - Completely fault-isolated: guarantees never to crash the caller or roll back HR decisions.
    """
    if not application or not application.candidate:
        logger.warning("Status notification attempted with null application or candidate.")
        return {"success": False, "error": "Invalid application or candidate"}

    try:
        candidate = application.candidate
        room = application.room
        recipient_email = candidate.email or ""

        # 1. Determine status_type if not supplied
        if not status_type:
            if application.hr_decision == CandidateApplication.HrDecision.CONFIRMED:
                status_type = StatusNotificationLog.StatusType.CONFIRMED
            elif application.hr_decision == CandidateApplication.HrDecision.REJECTED:
                status_type = StatusNotificationLog.StatusType.REJECTED
            elif application.is_shortlisted:
                status_type = StatusNotificationLog.StatusType.SHORTLISTED
            elif application.hr_decision == CandidateApplication.HrDecision.OVERRIDDEN:
                status_type = StatusNotificationLog.StatusType.OVERRIDDEN
            elif application.hr_decision == CandidateApplication.HrDecision.ON_HOLD:
                status_type = StatusNotificationLog.StatusType.ON_HOLD
            else:
                status_type = "STATUS_UPDATE"

        # 2. De-duplication check: avoid duplicate dispatch if executed within 5 seconds
        recent_cutoff = timezone.now() - timedelta(seconds=5)
        duplicate_exists = StatusNotificationLog.objects.filter(
            application=application,
            status_type=status_type,
            dispatched_at__gte=recent_cutoff
        ).exists()

        if duplicate_exists:
            logger.info(f"Skipping duplicate status notification for App #{application.id} ({status_type}).")
            return {"success": True, "duplicate": True}

        candidate_name = getattr(candidate, 'full_name', '') or (candidate.email.split('@')[0] if candidate.email else "Candidate")
        room_title = room.title if room else "Hiring Position"
        company_name = room.client_company.name if (room and room.client_company) else ""
        decision_notes = notes or application.hr_decision_notes or application.shortlist_reason or ""

        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173').rstrip('/')
        status_portal_url = f"{frontend_url}/applications/my-status"

        # 3. Prepare titles, messages, and email template
        is_positive = status_type in [
            StatusNotificationLog.StatusType.SHORTLISTED,
            StatusNotificationLog.StatusType.CONFIRMED,
        ]

        if is_positive:
            title = f"Shortlisted: {room_title}"
            message = (
                f"Congratulations! Your application for '{room_title}' has been shortlisted by the hiring team. "
                f"Check your application status portal for next steps and evaluation breakdown."
            )
            email_template = "emails/application_shortlisted.html"
        elif status_type == StatusNotificationLog.StatusType.REJECTED:
            title = f"Application Update: {room_title}"
            message = (
                f"Thank you for applying for '{room_title}'. The hiring team has updated your application status. "
                f"Visit your application portal to review details."
            )
            email_template = "emails/application_rejected.html"
        else:
            title = f"Application Status Update: {room_title}"
            message = (
                f"Your application status for '{room_title}' has been updated to {status_type}. "
                f"Check your candidate portal for recent updates."
            )
            email_template = "emails/application_rejected.html"

        # 4. Create in-app notification (US-35 AC#2)
        in_app_notif = None
        try:
            in_app_notif = NotificationService.create_notification(
                user=candidate,
                title=title,
                message=message,
                link_url="/applications/my-status",
                notification_type=Notification.NotificationType.APPLICATION_STATUS,
                send_email=False,  # We handle status transactional email explicitly below with audit logging
            )
        except Exception as notif_err:
            logger.warning(f"Error creating in-app notification for app #{application.id}: {notif_err}")

        # 5. Send transactional email (US-35-T3 & AC#2, AC#5)
        email_sent = False
        error_message = ""
        if force_email and recipient_email:
            try:
                email_context = {
                    'candidate_name': candidate_name,
                    'room_title': room_title,
                    'company_name': company_name,
                    'decision_notes': decision_notes,
                    'status_type': status_type,
                    'link_url': status_portal_url,
                    'frontend_url': frontend_url,
                    'support_email': 'support@careerflow.com',
                }
                email_sent = NotificationService.send_notification_email(
                    user=candidate,
                    title=title,
                    message=message,
                    link_url="/applications/my-status",
                    template_name=email_template,
                    context=email_context,
                )
            except Exception as email_exc:
                email_sent = False
                error_message = str(email_exc)
                logger.warning(f"Failed to dispatch application status email to {recipient_email}: {email_exc}")
        elif not recipient_email:
            error_message = "Candidate email address missing"

        # 6. Store audit record in database (US-35-T5 & AC#6)
        log_entry = None
        try:
            log_entry = StatusNotificationLog.objects.create(
                application=application,
                recipient_email=recipient_email,
                status_type=status_type,
                email_sent=email_sent,
                error_message=error_message,
            )
        except Exception as db_err:
            logger.error(f"Failed to persist StatusNotificationLog: {db_err}", exc_info=True)

        return {
            "success": True,
            "application_id": application.id,
            "status_type": status_type,
            "in_app_notification_id": in_app_notif.id if in_app_notif else None,
            "email_sent": email_sent,
            "error_message": error_message,
            "log_id": log_entry.id if log_entry else None,
        }

    except Exception as fatal_err:
        logger.error(f"Unexpected error in dispatch_status_notification for app #{getattr(application, 'id', None)}: {fatal_err}", exc_info=True)
        return {"success": False, "error": str(fatal_err)}

