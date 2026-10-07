from rest_framework import serializers
from .models import RecruitmentRoom


class RecruitmentRoomSerializer(serializers.ModelSerializer):
    created_by_name = serializers.ReadOnlyField(source='created_by.full_name')
    created_by_email = serializers.ReadOnlyField(source='created_by.email')
    experience_level_display = serializers.CharField(source='get_experience_level_display', read_only=True)
    share_url = serializers.SerializerMethodField()

    class Meta:
        model = RecruitmentRoom
        fields = [
            'id',
            'title',
            'company_name',
            'department',
            'role_category',
            'experience_level',
            'experience_level_display',
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


class RoomRequirementsSerializer(serializers.ModelSerializer):
    """
    Dedicated serializer for defining job role, seniority level,
    detailed requirements text, and skill tags (US-19-T2 & US-19-T4).
    """
    class Meta:
        model = RecruitmentRoom
        fields = [
            'id',
            'title',
            'role_category',
            'experience_level',
            'requirements_text',
            'skills_required',
            'updated_at',
        ]
        read_only_fields = ['id', 'title', 'updated_at']

    def validate_skills_required(self, value):
        """
        Enforce US-19-T4 skill validation:
        1. Must contain at least 1 skill
        2. No blank or whitespace-only skill names
        3. No duplicate skills (case-insensitive)
        4. Max character length per skill
        """
        if not isinstance(value, list) or len(value) == 0:
            raise serializers.ValidationError("At least one required skill must be defined.")

        clean_skills = []
        seen_lower = set()

        for item in value:
            name = ""
            importance = "REQUIRED"
            category = "Technical"

            if isinstance(item, str):
                name = item.strip()
            elif isinstance(item, dict) and 'name' in item:
                name = str(item['name']).strip()
                importance = item.get('importance', 'REQUIRED')
                category = item.get('category', 'Technical')
            else:
                raise serializers.ValidationError("Invalid skill entry format.")

            if not name:
                raise serializers.ValidationError("Skill name cannot be blank.")

            if len(name) < 2:
                raise serializers.ValidationError(f"Skill name '{name}' is too short (minimum 2 characters).")

            if len(name) > 60:
                raise serializers.ValidationError(f"Skill name '{name}' exceeds maximum limit of 60 characters.")

            lowered = name.lower()
            if lowered in seen_lower:
                raise serializers.ValidationError(f"Duplicate skill tag '{name}' is not allowed.")
            seen_lower.add(lowered)

            clean_skills.append({
                "name": name,
                "importance": importance,
                "category": category,
            })

        return clean_skills

    def validate_requirements_text(self, value):
        if value and len(value) > 10000:
            raise serializers.ValidationError("Requirements text cannot exceed 10,000 characters.")
        return value
