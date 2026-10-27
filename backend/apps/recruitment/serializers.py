from rest_framework import serializers
from apps.authentication.models import User
from .models import RecruitmentRoom, ClientCompany, CandidateApplication, CandidateForwardRecord


class RecruitmentRoomSerializer(serializers.ModelSerializer):
    created_by_name = serializers.ReadOnlyField(source='created_by.full_name')
    created_by_email = serializers.ReadOnlyField(source='created_by.email')
    experience_level_display = serializers.CharField(source='get_experience_level_display', read_only=True)
    share_url = serializers.SerializerMethodField()
    company_name = serializers.CharField(required=False, allow_blank=True)
    client_company = serializers.PrimaryKeyRelatedField(
        queryset=ClientCompany.objects.all(),
        required=False,
        allow_null=True
    )
    client_company_name = serializers.CharField(source='client_company.name', read_only=True)
    client_company_details = serializers.SerializerMethodField()

    class Meta:
        model = RecruitmentRoom
        fields = [
            'id',
            'title',
            'company_name',
            'department',
            'client_company',
            'client_company_name',
            'client_company_details',
            'role_category',
            'experience_level',
            'experience_level_display',
            'description',
            'status',
            'requirements_text',
            'skills_required',
            'cv_weight',
            'video_weight',
            'shortlist_strategy',
            'shortlist_min_score',
            'shortlist_top_n',
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
            'client_company_name',
            'client_company_details',
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

    def get_client_company_details(self, obj):
        if obj.client_company:
            return {
                "id": obj.client_company.id,
                "name": obj.client_company.name,
                "industry": obj.client_company.industry,
                "contact_person": obj.client_company.contact_person,
                "contact_email": obj.client_company.contact_email,
                "is_active": obj.client_company.is_active,
            }
        return None

    def validate_title(self, value):
        val = value.strip()
        if not val:
            raise serializers.ValidationError("Job title cannot be blank.")
        if len(val) < 3:
            raise serializers.ValidationError("Job title must be at least 3 characters long.")
        return val

    def validate(self, attrs):
        request = self.context.get('request')
        user = getattr(request, 'user', None) if request else None
        client_co = attrs.get('client_company')

        # US-30 validation: Client Company rules for Agency Admins vs HR Managers
        if user and user.is_authenticated and getattr(user, 'role', None) == User.Role.AGENCY_ADMIN:
            if not self.instance and not client_co:
                raise serializers.ValidationError({
                    "client_company": "A client company must be selected for agency recruitment rooms."
                })
            if client_co:
                if client_co.agency != user:
                    raise serializers.ValidationError({
                        "client_company": "You cannot associate a room with a client company belonging to another agency."
                    })
                if not self.instance and not client_co.is_active:
                    raise serializers.ValidationError({
                        "client_company": "Cannot create rooms for a deactivated client company. Please reactivate the client first."
                    })
                if not attrs.get('company_name'):
                    attrs['company_name'] = client_co.name
        elif user and user.is_authenticated and getattr(user, 'role', None) == User.Role.HR_MANAGER:
            if client_co:
                raise serializers.ValidationError({
                    "client_company": "HR Managers cannot associate rooms with agency client companies."
                })
            if 'company_name' in attrs and not attrs['company_name'].strip():
                raise serializers.ValidationError({
                    "company_name": "Company name cannot be blank."
                })
            if not self.instance and not attrs.get('company_name', '').strip():
                raise serializers.ValidationError({
                    "company_name": "Company name cannot be blank."
                })
        else:
            if 'company_name' in attrs and not attrs['company_name'].strip():
                raise serializers.ValidationError({
                    "company_name": "Company name cannot be blank."
                })
            if not self.instance and not client_co and not attrs.get('company_name', '').strip():
                raise serializers.ValidationError({
                    "company_name": "Company name cannot be blank."
                })

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


class RoomWeightingSerializer(serializers.ModelSerializer):
    """
    Dedicated serializer for configuring CV and Video score weights (US-20-T2 & US-20-T4).
    Enforces that weights are integers between 0 and 100, and their sum equals exactly 100%.
    """
    class Meta:
        model = RecruitmentRoom
        fields = [
            'id',
            'title',
            'company_name',
            'cv_weight',
            'video_weight',
            'updated_at',
        ]
        read_only_fields = ['id', 'title', 'company_name', 'updated_at']

    def validate_cv_weight(self, value):
        if value is None:
            raise serializers.ValidationError("CV weight cannot be empty.")
        if not isinstance(value, int) or isinstance(value, bool):
            raise serializers.ValidationError("CV weight must be an integer.")
        if value < 0 or value > 100:
            raise serializers.ValidationError("CV weight must be between 0 and 100.")
        return value

    def validate_video_weight(self, value):
        if value is None:
            raise serializers.ValidationError("Video weight cannot be empty.")
        if not isinstance(value, int) or isinstance(value, bool):
            raise serializers.ValidationError("Video weight must be an integer.")
        if value < 0 or value > 100:
            raise serializers.ValidationError("Video weight must be between 0 and 100.")
        return value

    def validate(self, attrs):
        # In partial updates, default to instance values if not provided
        cv_weight = attrs.get(
            'cv_weight',
            self.instance.cv_weight if self.instance else 50
        )
        video_weight = attrs.get(
            'video_weight',
            self.instance.video_weight if self.instance else 50
        )

        if cv_weight + video_weight != 100:
            raise serializers.ValidationError({
                "weights": f"CV weight ({cv_weight}%) and Video weight ({video_weight}%) must total exactly 100% (currently {cv_weight + video_weight}%)."
            })

        attrs['cv_weight'] = cv_weight
        attrs['video_weight'] = video_weight
        return attrs


class RoomShareLinkSerializer(serializers.ModelSerializer):
    """
    US-21-T2 & US-21-T5: Serializer for HR shareable application link management.
    Handles link status, secure token, generated URL, and optional expiration.
    """
    share_url = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = RecruitmentRoom
        fields = [
            'id',
            'title',
            'company_name',
            'share_token',
            'share_url',
            'link_is_active',
            'link_expires_at',
            'is_expired',
            'status',
            'updated_at',
        ]
        read_only_fields = ['id', 'title', 'company_name', 'share_token', 'share_url', 'is_expired', 'updated_at']

    def get_share_url(self, obj):
        request = self.context.get('request')
        from .tokens import build_share_url
        return build_share_url(obj.share_token, request=request)

    def get_is_expired(self, obj):
        from .tokens import is_token_expired
        return is_token_expired(obj)


class PublicRoomDetailsSerializer(serializers.ModelSerializer):
    """
    US-21-T3: Public unauthenticated serializer for candidate application page.
    Returns opening details, requirements, and evaluation weighting formula without exposing sensitive internal metadata.
    """
    share_url = serializers.SerializerMethodField()
    skill_names = serializers.SerializerMethodField()
    experience_level_display = serializers.CharField(source='get_experience_level_display', read_only=True)

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
            'requirements_text',
            'skills_required',
            'skill_names',
            'cv_weight',
            'video_weight',
            'share_token',
            'share_url',
            'link_is_active',
            'link_expires_at',
            'status',
            'created_at',
        ]
        read_only_fields = fields

    def get_share_url(self, obj):
        request = self.context.get('request')
        from .tokens import build_share_url
        return build_share_url(obj.share_token, request=request)

    def get_skill_names(self, obj):
        return obj.get_skill_names()


class ApplicantCvScoreSerializer(serializers.Serializer):
    """
    US-10-T2: Serializer for individual applicant CV match scores and skill breakdown.
    """
    application_id = serializers.IntegerField()
    candidate_id = serializers.IntegerField()
    candidate_name = serializers.CharField(allow_blank=True)
    candidate_email = serializers.EmailField()
    cv_id = serializers.IntegerField(allow_null=True)
    cv_filename = serializers.CharField(allow_null=True, allow_blank=True)
    cv_file_url = serializers.CharField(allow_null=True, allow_blank=True)
    has_cv = serializers.BooleanField()
    has_score = serializers.BooleanField()
    match_score = serializers.IntegerField(allow_null=True)
    keyword_coverage = serializers.IntegerField()
    category_scores = serializers.DictField(child=serializers.IntegerField(), default=dict)
    skills_matched = serializers.ListField(child=serializers.CharField(), default=list)
    skills_missing = serializers.ListField(child=serializers.CharField(), default=list)
    strengths = serializers.ListField(child=serializers.CharField(), default=list)
    gaps = serializers.ListField(child=serializers.CharField(), default=list)
    recommendations = serializers.ListField(child=serializers.CharField(), default=list)
    applied_at = serializers.DateTimeField()
    status = serializers.CharField()
    # US-23 Final Score fields
    cv_score = serializers.FloatField(allow_null=True, required=False)
    video_score = serializers.FloatField(allow_null=True, required=False)
    final_score = serializers.FloatField(allow_null=True, required=False)
    is_partial_score = serializers.BooleanField(default=False, required=False)
    score_calculated_at = serializers.DateTimeField(allow_null=True, required=False)


class RoomCvScoresResponseSerializer(serializers.Serializer):
    """
    US-10-T2: Serializer for room-level applicant CV match scores view.
    """
    room_id = serializers.IntegerField()
    room_title = serializers.CharField()
    company_name = serializers.CharField()
    department = serializers.CharField(allow_blank=True)
    total_applicants = serializers.IntegerField()
    scored_applicants = serializers.IntegerField()
    average_cv_score = serializers.FloatField(allow_null=True)
    highest_cv_score = serializers.IntegerField(allow_null=True)
    lowest_cv_score = serializers.IntegerField(allow_null=True)
    results = ApplicantCvScoreSerializer(many=True)


class CalculateScoresResponseSerializer(serializers.Serializer):
    """
    US-23-T5: Serializer for calculate-scores batch calculation response.
    """
    message = serializers.CharField()
    room_id = serializers.IntegerField()
    weights_used = serializers.DictField(child=serializers.IntegerField())
    processed_count = serializers.IntegerField()
    updated_count = serializers.IntegerField()


class CandidateApplicationScoreSerializer(serializers.ModelSerializer):
    """
    US-23-T6: Detailed score serializer for a CandidateApplication.
    """
    candidate_name = serializers.CharField(source='candidate.full_name', read_only=True)
    candidate_email = serializers.EmailField(source='candidate.email', read_only=True)

    class Meta:
        from .models import CandidateApplication
        model = CandidateApplication
        fields = [
            'id',
            'room',
            'candidate',
            'candidate_name',
            'candidate_email',
            'cv_score',
            'video_score',
            'final_score',
            'is_partial_score',
            'score_calculated_at',
            'is_shortlisted',
            'shortlist_reason',
            'shortlisted_at',
            'status',
            'applied_at',
        ]
        read_only_fields = fields


class RankedApplicantItemSerializer(serializers.Serializer):
    """
    US-24-T2: Serializer for a ranked applicant on the room leaderboard.
    """
    rank = serializers.IntegerField()
    badge = serializers.CharField()
    application_id = serializers.IntegerField()
    candidate_id = serializers.IntegerField()
    candidate_name = serializers.CharField(allow_blank=True)
    candidate_email = serializers.EmailField()
    final_score = serializers.FloatField()
    score_tier = serializers.CharField()
    cv_score = serializers.FloatField(allow_null=True)
    video_score = serializers.FloatField(allow_null=True)
    is_partial_score = serializers.BooleanField()
    score_calculated_at = serializers.DateTimeField(allow_null=True)
    is_shortlisted = serializers.BooleanField(default=False)
    shortlist_reason = serializers.CharField(allow_blank=True, default='')
    shortlisted_at = serializers.DateTimeField(allow_null=True, required=False)
    status = serializers.CharField()
    applied_at = serializers.DateTimeField()


class UnrankedApplicantItemSerializer(serializers.Serializer):
    """
    US-24-T5: Serializer for an incomplete/unranked applicant.
    """
    application_id = serializers.IntegerField()
    candidate_id = serializers.IntegerField()
    candidate_name = serializers.CharField(allow_blank=True)
    candidate_email = serializers.EmailField()
    final_score = serializers.FloatField(allow_null=True)
    score_tier = serializers.CharField()
    cv_score = serializers.FloatField(allow_null=True)
    video_score = serializers.FloatField(allow_null=True)
    is_partial_score = serializers.BooleanField()
    status = serializers.CharField()
    applied_at = serializers.DateTimeField()
    pending_reason = serializers.CharField()


class RankedApplicantsResponseSerializer(serializers.Serializer):
    """
    US-24-T2: Serializer for the complete ranked leaderboard response.
    """
    room_id = serializers.IntegerField()
    room_title = serializers.CharField()
    company_name = serializers.CharField()
    department = serializers.CharField(allow_blank=True)
    cv_weight = serializers.IntegerField()
    video_weight = serializers.IntegerField()
    total_applicants = serializers.IntegerField()
    ranked_count = serializers.IntegerField()
    unranked_count = serializers.IntegerField()
    results = RankedApplicantItemSerializer(many=True)
    unranked = UnrankedApplicantItemSerializer(many=True)


class RoomShortlistCriteriaSerializer(serializers.ModelSerializer):
    """
    US-25-T2: Serializer for configuring and viewing automatic shortlisting criteria for a Room.
    Enforces validation on strategy choices, min_score (0-100), and top_n (>=1).
    """
    shortlist_strategy_display = serializers.CharField(source='get_shortlist_strategy_display', read_only=True)

    class Meta:
        model = RecruitmentRoom
        fields = [
            'id',
            'title',
            'company_name',
            'shortlist_strategy',
            'shortlist_strategy_display',
            'shortlist_min_score',
            'shortlist_top_n',
            'updated_at',
        ]
        read_only_fields = ['id', 'title', 'company_name', 'shortlist_strategy_display', 'updated_at']

    def validate(self, attrs):
        strategy = attrs.get(
            'shortlist_strategy',
            self.instance.shortlist_strategy if self.instance else RecruitmentRoom.ShortlistStrategy.NONE
        )
        min_score = attrs.get(
            'shortlist_min_score',
            self.instance.shortlist_min_score if self.instance else None
        )
        top_n = attrs.get(
            'shortlist_top_n',
            self.instance.shortlist_top_n if self.instance else None
        )

        from .services.shortlisting_service import validate_shortlisting_criteria
        is_valid, errors = validate_shortlisting_criteria(strategy, min_score, top_n)
        if not is_valid:
            raise serializers.ValidationError(errors)

        return attrs


class ShortlistedApplicantItemSerializer(serializers.Serializer):
    """
    US-25-T2 & US-25-T4: Serializer for candidates evaluated in the room shortlist.
    """
    application_id = serializers.IntegerField()
    candidate_id = serializers.IntegerField()
    candidate_name = serializers.CharField(allow_blank=True)
    candidate_email = serializers.EmailField()
    rank = serializers.IntegerField(allow_null=True)
    final_score = serializers.FloatField(allow_null=True)
    cv_score = serializers.FloatField(allow_null=True)
    video_score = serializers.FloatField(allow_null=True)
    is_shortlisted = serializers.BooleanField()
    shortlist_reason = serializers.CharField(allow_blank=True)
    shortlisted_at = serializers.DateTimeField(allow_null=True)


class RoomShortlistResponseSerializer(serializers.Serializer):
    """
    US-25-T2: Complete response serializer for Room Shortlist configuration & evaluated applicants.
    """
    room_id = serializers.IntegerField()
    room_title = serializers.CharField()
    strategy = serializers.CharField()
    min_score = serializers.FloatField(allow_null=True)
    top_n = serializers.IntegerField(allow_null=True)
    total_applicants = serializers.IntegerField()
    shortlisted_count = serializers.IntegerField()
    non_shortlisted_count = serializers.IntegerField()
    shortlisted_applicants = ShortlistedApplicantItemSerializer(many=True)
    all_applicants = ShortlistedApplicantItemSerializer(many=True)


# ============================================================================
# US-26: HR Review of AI Results & Human Decision Audit Trail
# ============================================================================

class CandidateDecisionSubmitSerializer(serializers.Serializer):
    """
    US-26-T3: Validates human HR decision submission on a candidate application.
    Enforces that overriding an AI recommendation strictly requires an explanatory note.
    """
    DECISION_CHOICES = [
        ('CONFIRMED', 'Shortlist Confirmed'),
        ('OVERRIDDEN', 'AI Recommendation Overridden'),
        ('REJECTED', 'Candidate Rejected'),
        ('ON_HOLD', 'Application On Hold'),
    ]

    decision = serializers.ChoiceField(choices=DECISION_CHOICES)
    notes = serializers.CharField(required=False, allow_blank=True, default='')

    def validate(self, attrs):
        decision = attrs.get('decision')
        notes = (attrs.get('notes') or '').strip()

        # US-26 AC#3 & US-26-T6: Require explanatory note when overriding AI recommendation
        if decision == 'OVERRIDDEN' and (not notes or len(notes) < 5):
            raise serializers.ValidationError({
                "notes": "An explanatory note (minimum 5 characters) is required when overriding the AI recommendation."
            })

        attrs['notes'] = notes
        return attrs


class CandidateReviewDetailSerializer(serializers.Serializer):
    """
    US-26-T2: Comprehensive candidate review serializer combining scores,
    CV summary, video presentation metrics, AI recommendation, and HR decision audit trail.
    """
    application_id = serializers.IntegerField()
    room_id = serializers.IntegerField()
    room_title = serializers.CharField()
    candidate_id = serializers.IntegerField()
    candidate_name = serializers.CharField(allow_blank=True)
    candidate_email = serializers.EmailField()
    status = serializers.CharField()
    applied_at = serializers.DateTimeField()

    # Scores
    final_score = serializers.FloatField(allow_null=True)
    cv_score = serializers.FloatField(allow_null=True)
    video_score = serializers.FloatField(allow_null=True)
    cv_weight = serializers.IntegerField()
    video_weight = serializers.IntegerField()
    is_partial_score = serializers.BooleanField()
    score_calculated_at = serializers.DateTimeField(allow_null=True)

    # AI Shortlist Recommendation (Clearly advisory per US-26 AC#5)
    is_shortlisted = serializers.BooleanField()
    shortlist_reason = serializers.CharField(allow_blank=True)
    shortlisted_at = serializers.DateTimeField(allow_null=True)
    ai_recommendation = serializers.CharField()
    ai_recommendation_label = serializers.CharField()
    ai_disclaimer = serializers.CharField()

    # Detailed signals
    cv_summary = serializers.DictField(default=dict)
    video_summary = serializers.DictField(default=dict)

    # Human HR Review Decision & Audit Trail (US-26 AC#4)
    hr_decision = serializers.CharField()
    hr_decision_display = serializers.CharField()
    hr_decision_notes = serializers.CharField(allow_blank=True)
    hr_decided_by_email = serializers.EmailField(allow_null=True)
    hr_decided_by_name = serializers.CharField(allow_null=True, allow_blank=True)
    hr_decided_at = serializers.DateTimeField(allow_null=True)


class CandidateDecisionResponseSerializer(serializers.Serializer):
    """
    US-26-T3: Response serializer after recording human HR review decision.
    """
    application_id = serializers.IntegerField()
    hr_decision = serializers.CharField()
    hr_decision_display = serializers.CharField()
    hr_decision_notes = serializers.CharField(allow_blank=True)
    hr_decided_by = serializers.CharField()
    hr_decided_at = serializers.DateTimeField()
    is_shortlisted = serializers.BooleanField()
    message = serializers.CharField()


# ============================================================================
# US-27: Explainable Applicant Score Breakdown & Transparency
# ============================================================================

class ScoreComponentContributionSerializer(serializers.Serializer):
    """
    US-27-T2 & US-27-T4: Granular contribution details for CV or Video component.
    """
    name = serializers.CharField()
    is_available = serializers.BooleanField()
    raw_score = serializers.FloatField(allow_null=True)
    weight_percentage = serializers.IntegerField()
    points_contributed = serializers.FloatField(allow_null=True)
    max_points_possible = serializers.FloatField()
    percentage_of_total = serializers.FloatField(allow_null=True)
    missing_reason = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    sub_metrics = serializers.DictField(default=dict)


class ApplicantScoreBreakdownSerializer(serializers.Serializer):
    """
    US-27-T2, US-27-T4, US-27-T5: Complete explainable score breakdown serializer.
    """
    application_id = serializers.IntegerField()
    candidate_id = serializers.IntegerField()
    candidate_name = serializers.CharField(allow_blank=True)
    candidate_email = serializers.EmailField()
    room_id = serializers.IntegerField()
    room_title = serializers.CharField()
    final_score = serializers.FloatField(allow_null=True)
    is_partial_score = serializers.BooleanField()
    score_calculated_at = serializers.DateTimeField(allow_null=True)
    cv_weight = serializers.IntegerField()
    video_weight = serializers.IntegerField()
    formula_display = serializers.CharField()
    missing_components_explanation = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    cv_component = ScoreComponentContributionSerializer()
    video_component = ScoreComponentContributionSerializer()


# ============================================================================
# US-28: Side-by-Side Applicant Comparison
# ============================================================================

class ApplicantComparisonRequestSerializer(serializers.Serializer):
    """
    US-28-T2: Request serializer for comparing 2 to 4 applicants side by side.
    """
    application_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
        help_text="List of 2 to 4 candidate application IDs belonging to this room."
    )

    def validate_application_ids(self, value):
        unique_ids = list(dict.fromkeys(value))
        if len(unique_ids) < 2:
            raise serializers.ValidationError("At least 2 unique applicants are required for side-by-side comparison.")
        if len(unique_ids) > 4:
            raise serializers.ValidationError("Maximum 4 applicants can be compared simultaneously.")
        return unique_ids


class ApplicantComparisonItemSerializer(serializers.Serializer):
    """
    US-28-T2: Candidate metrics item within comparison matrix.
    """
    application_id = serializers.IntegerField()
    candidate_id = serializers.IntegerField()
    candidate_name = serializers.CharField(allow_blank=True)
    email = serializers.EmailField()
    avatar_initials = serializers.CharField(allow_blank=True, default="CA")
    final_score = serializers.FloatField(allow_null=True)
    score_tier = serializers.CharField()
    is_partial_score = serializers.BooleanField()
    cv_score = serializers.FloatField(allow_null=True)
    video_score = serializers.FloatField(allow_null=True)
    matched_skills = serializers.ListField(child=serializers.CharField(), default=list)
    missing_skills = serializers.ListField(child=serializers.CharField(), default=list)
    keyword_coverage = serializers.FloatField(default=0.0)
    wpm = serializers.FloatField(default=0.0)
    eye_contact_percent = serializers.FloatField(allow_null=True)
    posture_score = serializers.FloatField(allow_null=True)
    filler_words_count = serializers.IntegerField(default=0)
    speech_score = serializers.FloatField(allow_null=True)
    visual_score = serializers.FloatField(allow_null=True)
    is_shortlisted = serializers.BooleanField()
    shortlist_reason = serializers.CharField(allow_blank=True)
    hr_decision = serializers.CharField()
    hr_decision_display = serializers.CharField()
    applied_at = serializers.DateTimeField()
    best_in = serializers.ListField(child=serializers.CharField(), default=list)


class ApplicantComparisonResponseSerializer(serializers.Serializer):
    """
    US-28-T2: Response serializer for side-by-side applicant comparison.
    """
    room_id = serializers.IntegerField()
    room_title = serializers.CharField()
    company_name = serializers.CharField()
    cv_weight = serializers.IntegerField()
    video_weight = serializers.IntegerField()
    comparison_count = serializers.IntegerField()
    highest_final_score = serializers.FloatField(allow_null=True)
    average_final_score = serializers.FloatField(allow_null=True)
    applicants = ApplicantComparisonItemSerializer(many=True)


# ============================================================================
# US-29: Manage Multiple Client Companies
# ============================================================================

class ClientCompanySerializer(serializers.ModelSerializer):
    """
    US-29-T2: Serializer for recruitment agency client company CRUD.
    Validates company name uniqueness per agency, email formatting, and contact fields.
    """
    agency_id = serializers.ReadOnlyField(source='agency.id')
    agency_name = serializers.ReadOnlyField(source='agency.full_name')
    agency_email = serializers.ReadOnlyField(source='agency.email')
    rooms_count = serializers.SerializerMethodField()

    class Meta:
        model = ClientCompany
        fields = [
            'id',
            'agency_id',
            'agency_name',
            'agency_email',
            'name',
            'industry',
            'contact_person',
            'contact_email',
            'phone',
            'website',
            'notes',
            'is_active',
            'rooms_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'agency_id',
            'agency_name',
            'agency_email',
            'rooms_count',
            'created_at',
            'updated_at',
        ]

    def get_rooms_count(self, obj):
        if hasattr(obj, 'rooms'):
            return obj.rooms.count()
        return 0

    def validate_name(self, value):
        val = (value or '').strip()
        if not val:
            raise serializers.ValidationError("Client company name cannot be blank.")
        if len(val) < 2:
            raise serializers.ValidationError("Client company name must be at least 2 characters long.")
        if len(val) > 200:
            raise serializers.ValidationError("Client company name cannot exceed 200 characters.")
        return val

    def validate_industry(self, value):
        val = (value or '').strip()
        if not val:
            raise serializers.ValidationError("Industry cannot be blank.")
        return val

    def validate_contact_person(self, value):
        val = (value or '').strip()
        if not val:
            raise serializers.ValidationError("Contact person cannot be blank.")
        return val

    def validate_contact_email(self, value):
        val = (value or '').strip().lower()
        if not val:
            raise serializers.ValidationError("Contact email cannot be blank.")
        return val

    def validate(self, attrs):
        name = attrs.get('name')
        request = self.context.get('request')
        
        # When creating or updating name, check for duplicate company name within the same agency
        if name and request and getattr(request, 'user', None) and request.user.is_authenticated:
            qs = ClientCompany.objects.filter(agency=request.user, name__iexact=name.strip())
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError({
                    "name": f"A client company named '{name.strip()}' already exists in your agency portfolio."
                })
        return attrs


class ClientCompanyStatsSerializer(serializers.Serializer):
    """
    US-29-T4: Serializer for Agency client company summary statistics.
    """
    total_clients = serializers.IntegerField()
    active_clients = serializers.IntegerField()
    deactivated_clients = serializers.IntegerField()
    associated_rooms = serializers.IntegerField()


class AgencyCrossClientApplicantSerializer(serializers.ModelSerializer):
    """
    US-31-T2: Serializer for cross-client candidate application aggregation.
    Provides candidate details, client company association, room metadata,
    evaluation scores (CV, Video, Final), and workflow/decision statuses.
    """
    candidate_id = serializers.IntegerField(source='candidate.id', read_only=True)
    candidate_name = serializers.SerializerMethodField()
    candidate_email = serializers.EmailField(source='candidate.email', read_only=True)

    client_company_id = serializers.IntegerField(source='room.client_company.id', read_only=True)
    client_company_name = serializers.CharField(source='room.client_company.name', read_only=True)
    client_company_industry = serializers.CharField(source='room.client_company.industry', read_only=True)

    room_id = serializers.IntegerField(source='room.id', read_only=True)
    room_title = serializers.CharField(source='room.title', read_only=True)
    role_category = serializers.CharField(source='room.role_category', read_only=True)
    experience_level = serializers.CharField(source='room.experience_level', read_only=True)
    experience_level_display = serializers.CharField(source='room.get_experience_level_display', read_only=True)
    cv_weight = serializers.IntegerField(source='room.cv_weight', read_only=True)
    video_weight = serializers.IntegerField(source='room.video_weight', read_only=True)

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    hr_decision_display = serializers.CharField(source='get_hr_decision_display', read_only=True)

    has_cv = serializers.SerializerMethodField()
    has_video = serializers.SerializerMethodField()

    class Meta:
        model = CandidateApplication
        fields = [
            'id',
            'candidate_id',
            'candidate_name',
            'candidate_email',
            'client_company_id',
            'client_company_name',
            'client_company_industry',
            'room_id',
            'room_title',
            'role_category',
            'experience_level',
            'experience_level_display',
            'cv_weight',
            'video_weight',
            'status',
            'status_display',
            'cv_score',
            'video_score',
            'final_score',
            'is_partial_score',
            'score_calculated_at',
            'is_shortlisted',
            'shortlist_reason',
            'shortlisted_at',
            'hr_decision',
            'hr_decision_display',
            'hr_decision_notes',
            'hr_decided_at',
            'has_cv',
            'has_video',
            'is_forwarded',
            'forwarded_at',
            'applied_at',
        ]
        read_only_fields = fields

    def get_candidate_name(self, obj):
        name = getattr(obj.candidate, 'full_name', None)
        if name and name.strip():
            return name.strip()
        email_prefix = obj.candidate.email.split('@')[0]
        return email_prefix.replace('.', ' ').replace('_', ' ').title()

    def get_has_cv(self, obj):
        return bool(obj.cv_id)

    def get_has_video(self, obj):
        return bool(obj.video_id)


class AgencyCrossClientSummaryStatsSerializer(serializers.Serializer):
    """
    US-31: High-level KPI metrics for cross-client applicant pipeline.
    """
    total_applicants = serializers.IntegerField()
    completed_evaluations = serializers.IntegerField()
    shortlisted_candidates = serializers.IntegerField()
    pending_reviews = serializers.IntegerField()
    average_final_score = serializers.FloatField()
    clients_count = serializers.IntegerField()
    rooms_count = serializers.IntegerField()


class ForwardShortlistRequestSerializer(serializers.Serializer):
    """
    US-32-T2: Request serializer for forwarding shortlisted candidate dossiers to a client company.
    """
    client_id = serializers.IntegerField(required=True)
    application_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        required=True
    )
    recipient_email = serializers.EmailField(required=True)
    recipient_name = serializers.CharField(required=False, allow_blank=True, default="")
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class CandidateForwardRecordSerializer(serializers.ModelSerializer):
    """
    US-32-T5: Serializer for CandidateForwardRecord audit logs.
    """
    client_company_name = serializers.CharField(source='client_company.name', read_only=True)
    forwarded_candidates_count = serializers.SerializerMethodField()
    application_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        read_only=True,
        source='applications'
    )

    class Meta:
        model = CandidateForwardRecord
        fields = [
            'id',
            'agency_id',
            'client_company_id',
            'client_company_name',
            'recipient_email',
            'recipient_name',
            'status',
            'notes',
            'dossier_data',
            'application_ids',
            'forwarded_candidates_count',
            'sent_at',
        ]
        read_only_fields = fields

    def get_forwarded_candidates_count(self, obj):
        return obj.applications.count()



