from rest_framework import serializers
from .models import RecruitmentRoom


class RecruitmentRoomSerializer(serializers.ModelSerializer):
    created_by_name = serializers.ReadOnlyField(source='created_by.full_name')
    created_by_email = serializers.ReadOnlyField(source='created_by.email')
    share_url = serializers.SerializerMethodField()

    class Meta:
        model = RecruitmentRoom
        fields = [
            'id',
            'title',
            'company_name',
            'department',
            'description',
            'status',
            'requirements_text',
            'skills_required',
            'cv_weight',
            'video_weight',
            'share_token',
            'share_url',
            'link_is_active',
            'link_expires_at',
            'created_by',
            'created_by_name',
            'created_by_email',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'share_token',
            'share_url',
            'created_by',
            'created_by_name',
            'created_by_email',
            'created_at',
            'updated_at',
        ]

    def get_share_url(self, obj):
        request = self.context.get('request')
        relative_path = f"/apply/{obj.share_token}"
        if request:
            return request.build_absolute_uri(relative_path)
        return relative_path

    def validate_title(self, value):
        val = value.strip()
        if not val:
            raise serializers.ValidationError("Job title cannot be blank.")
        if len(val) < 3:
            raise serializers.ValidationError("Job title must be at least 3 characters long.")
        return val

    def validate_company_name(self, value):
        val = value.strip()
        if not val:
            raise serializers.ValidationError("Company name cannot be blank.")
        return val

    def validate(self, attrs):
        # US-20 forward validation: weights sum check if both supplied
        cv_w = attrs.get('cv_weight')
        vid_w = attrs.get('video_weight')
        if cv_w is not None and vid_w is not None:
            if cv_w + vid_w != 100:
                raise serializers.ValidationError({
                    "weights": f"CV weight ({cv_w}%) and Video weight ({vid_w}%) must total exactly 100%."
                })
        return attrs
