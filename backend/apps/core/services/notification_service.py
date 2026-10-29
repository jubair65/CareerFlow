import logging
from typing import Optional, Dict, Any
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from apps.core.models import Notification

logger = logging.getLogger(__name__)


class NotificationService:
    """
    US-34: Omni-channel notification engine.
    Handles persistent database storage of in-app notifications
    and transactional email dispatch with complete pipeline fault-isolation.
    """

    @classmethod
    def create_notification(
        cls,
        user,
        title: str,
        message: str,
        link_url: str = "",
        notification_type: str = Notification.NotificationType.INFO,
        send_email: bool = True,
        email_template: str = "emails/analysis_complete.html",
        email_context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Notification]:
        """
        Create an in-app notification and optionally dispatch a transactional email.
        Guaranteed not to raise an exception or break calling pipelines.
        """
        if not user:
            logger.warning("Attempted to send notification with null user.")
            return None

        notification = None
        try:
            # 1. Persist notification to database (US-34-T5)
            notification = Notification.objects.create(
                user=user,
                title=title[:200],
                message=message,
                link_url=link_url[:255] if link_url else "",
                notification_type=notification_type,
                is_read=False,
            )
        except Exception as db_err:
            logger.error(f"Failed to persist Notification record: {db_err}", exc_info=True)
            # Do not re-raise; preserve pipeline flow

        # 2. Dispatch transactional email if requested (US-34-T4)
        if send_email and getattr(user, 'email', None):
            try:
                cls.send_notification_email(
                    user=user,
                    title=title,
                    message=message,
                    link_url=link_url,
                    template_name=email_template,
                    context=email_context or {},
                )
            except Exception as email_err:
                logger.warning(f"Transactional email delivery skipped/failed: {email_err}")

        return notification

    @classmethod
    def send_notification_email(
        cls,
        user,
        title: str,
        message: str,
        link_url: str = "",
        template_name: str = "emails/analysis_complete.html",
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Dispatch transactional HTML email with plain-text fallback.
        """
        if not user.email:
            return False

        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173').rstrip('/')
        full_link = link_url
        if link_url and not link_url.startswith('http'):
            full_link = f"{frontend_url}/{link_url.lstrip('/')}"

        merged_context = {
            'user': user,
            'title': title,
            'message': message,
            'link_url': full_link,
            'frontend_url': frontend_url,
            'support_email': 'support@careerflow.com',
            **(context or {})
        }

        subject = f"[CareerFlow] {title}"
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'CareerFlow <noreply@careerflow.com>')

        # Try rendering HTML template, fallback to plain message if template fails
        html_content = ""
        try:
            html_content = render_to_string(template_name, merged_context)
            text_content = strip_tags(html_content)
        except Exception as tmpl_err:
            logger.warning(f"Email template '{template_name}' rendering fallback: {tmpl_err}")
            text_content = f"Hello {getattr(user, 'first_name', '') or user.email},\n\n{message}\n\nView details: {full_link}\n\nBest regards,\nThe CareerFlow Team"

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=[user.email],
        )
        if html_content:
            msg.attach_alternative(html_content, "text/html")

        msg.send(fail_silently=False)
        return True

    # Convenience triggers (US-34-T1 & US-34-T2)
    @classmethod
    def notify_cv_analysis_complete(
        cls,
        user,
        cv=None,
        skills_count: int = 0,
        feedback_summary: Optional[str] = None
    ) -> Optional[Notification]:
        """
        Triggered when CV parsing and AI evaluation finishes.
        """
        title = "CV Analysis Complete"
        message = (
            "Your CV has been successfully parsed and evaluated. "
            f"Extracted {skills_count} skill(s) and generated AI feedback."
            if skills_count > 0 else
            "Your CV has been successfully parsed and evaluated. View your detailed skills and match feedback."
        )
        link_url = "/dashboard"
        return cls.create_notification(
            user=user,
            title=title,
            message=message,
            link_url=link_url,
            notification_type=Notification.NotificationType.CV_ANALYSIS_COMPLETE,
            send_email=True,
            email_context={'analysis_type': 'CV', 'details': feedback_summary}
        )

    @classmethod
    def notify_presentation_analysis_complete(
        cls,
        user,
        video,
        overall_score: Optional[float] = None
    ) -> Optional[Notification]:
        """
        Triggered when Presentation speech and behavioral computer vision analysis finishes.
        """
        title = "Presentation Analysis Ready"
        score_text = f" with an overall score of {int(overall_score)}/100" if overall_score is not None else ""
        message = f"Your video presentation analysis is complete{score_text}. Review your speech pacing, eye contact, and AI coaching suggestions."
        link_url = f"/presentation/history/{video.id}"
        return cls.create_notification(
            user=user,
            title=title,
            message=message,
            link_url=link_url,
            notification_type=Notification.NotificationType.PRESENTATION_ANALYSIS_COMPLETE,
            send_email=True,
            email_context={
                'analysis_type': 'Presentation Video',
                'overall_score': overall_score,
                'video_id': video.id
            }
        )

