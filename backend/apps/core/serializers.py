from rest_framework import serializers
from .models import Notification


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

