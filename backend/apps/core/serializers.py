import uuid
from rest_framework import serializers
from .models import Notification, AIConsentLog


class NotificationSerializer(serializers.ModelSerializer):
    """
    US-34: Serializer for user notifications.
    """
    class Meta:
        model = Notification
        fields = [
            'id',
            'title',
            'message',
            'link_url',
            'notification_type',
            'is_read',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class AIConsentLogSerializer(serializers.ModelSerializer):
    """
    US-48-T2: Serializer for AI biometric consent audit logs.
    """
    user_email = serializers.SerializerMethodField()

    class Meta:
        model = AIConsentLog
        fields = [
            'id',
            'user',
            'user_email',
            'email',
            'consent_type',
            'policy_version',
            'agreed',
            'consent_token',
            'ip_address',
            'user_agent',
            'timestamp',
        ]
        read_only_fields = [
            'id',
            'consent_token',
            'ip_address',
            'user_agent',
            'timestamp',
        ]

    def get_user_email(self, obj):
        if obj.user:
            return obj.user.email
        return obj.email or 'Anonymous'


class AIConsentSubmitSerializer(serializers.Serializer):
    """
    US-48-T2: Request serializer for recording explicit AI consent.
    """
    agreed = serializers.BooleanField(required=True)
    email = serializers.EmailField(required=False, allow_blank=True, default='')
    policy_version = serializers.CharField(max_length=20, default='v1.0')
    consent_type = serializers.CharField(max_length=50, default=AIConsentLog.ConsentType.BIOMETRIC_EVALUATION)


AI_BIOMETRIC_POLICY_V1 = {
    "version": "v1.0",
    "effective_date": "2026-11-01",
    "title": "CareerFlow AI Biometric & Presentation Evaluation Privacy Notice",
    "summary": "In compliance with the EU Artificial Intelligence Act (Title II - High-Risk Employment AI Systems) and GDPR Article 9 (Processing of Special Categories of Personal Data), CareerFlow requires your explicit, informed consent prior to collecting, processing, or analyzing your audio, facial, and posture telemetry during practice recordings and job application presentations.",
    "sections": [
        {
            "id": "audio_analysis",
            "title": "1. Audio & Speech Telemetry",
            "icon": "mic",
            "details": "We analyze your speech waveform and acoustic characteristics to evaluate presentation delivery: speaking pace (words per minute), vocal energy, filler word frequency (e.g., 'um', 'uh', 'like'), articulation clarity, and pitch variance. Raw audio is processed through isolated neural speech recognition models and is never shared with third-party advertisers."
        },
        {
            "id": "facial_posture_telemetry",
            "title": "2. Facial Telemetry & Posture Tracking",
            "icon": "camera",
            "details": "We utilize computer vision models to detect head pose orientation, eye gaze direction, and upper-body posture alignment during your presentation. This telemetry measures audience engagement, eye contact percentage, and professional presentation demeanor. We do NOT perform biometric facial recognition or 1:N identity verification, nor do we construct persistent facial signature databases."
        },
        {
            "id": "human_oversight",
            "title": "3. Ethical AI & Human-in-the-Loop Oversight",
            "icon": "shield",
            "details": "CareerFlow's AI metrics serve as objective developmental and screening aids. Final hiring decisions and candidate evaluations remain under the direct control and responsibility of human hiring managers and authorized recruiters. No applicant is rejected solely by an automated algorithm."
        },
        {
            "id": "retention_storage",
            "title": "4. Data Retention, Storage & Automated Cleanup",
            "icon": "database",
            "details": "Your recorded video files and extracted acoustic/behavioral features are encrypted at rest and in transit. Practice takes can be permanently deleted at any time from your Practice Studio (US-44). In accordance with our storage retention policy (US-49), temporary processing artifacts and expired media are purged automatically."
        },
        {
            "id": "consent_withdrawal",
            "title": "5. Right to Refuse or Withdraw Consent",
            "icon": "lock",
            "details": "Consent is voluntary. If you refuse consent, video recording and upload will be safely aborted without prejudice to your account. You may review or update your consent preferences at any time."
        }
    ]
}
