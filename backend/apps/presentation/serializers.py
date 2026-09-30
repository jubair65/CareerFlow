from rest_framework import serializers
from .models import (
    PresentationVideo,
    SpeechAnalysis,
    BehavioralAnalysis,
    PresentationScore,
    PresentationFeedback,
    PipelineExecutionLog,
)
from .validators import validate_video_file, MAX_UPLOAD_SIZE


class SpeechAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpeechAnalysis
        fields = [
            'id',
            'video',
            'transcript',
            'words_per_minute',
            'filler_word_count',
            'filler_words_breakdown',
            'clarity_score',
            'duration_seconds',
            'processed_at',
        ]
        read_only_fields = [
            'id',
            'video',
            'transcript',
            'words_per_minute',
            'filler_word_count',
            'filler_words_breakdown',
            'clarity_score',
            'duration_seconds',
            'processed_at',
        ]


class BehavioralAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = BehavioralAnalysis
        fields = [
            'id',
            'video',
            'eye_contact_score',
            'posture_score',
            'engagement_score',
            'frame_metrics',
            'processed_at',
        ]
        read_only_fields = [
            'id',
            'video',
            'eye_contact_score',
            'posture_score',
            'engagement_score',
            'frame_metrics',
            'processed_at',
        ]


class PresentationScoreSerializer(serializers.ModelSerializer):
    grade_label = serializers.ReadOnlyField()
    grade_color = serializers.ReadOnlyField()

    class Meta:
        model = PresentationScore
        fields = [
            'id',
            'video',
            'overall_score',
            'speech_score',
            'behavioral_score',
            'pace_score',
            'filler_score',
            'eye_contact_score',
            'posture_score',
            'engagement_score',
            'has_behavioral_data',
            'notes',
            'grade_label',
            'grade_color',
            'calculated_at',
        ]
        read_only_fields = [
            'id',
            'video',
            'overall_score',
            'speech_score',
            'behavioral_score',
            'pace_score',
            'filler_score',
            'eye_contact_score',
            'posture_score',
            'engagement_score',
            'has_behavioral_data',
            'notes',
            'grade_label',
            'grade_color',
            'calculated_at',
        ]


class PresentationFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = PresentationFeedback
        fields = [
            'id',
            'video',
            'summary',
            'strengths',
            'improvements',
            'practice_tip',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'video',
            'summary',
            'strengths',
            'improvements',
            'practice_tip',
            'created_at',
        ]


class PipelineExecutionLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = PipelineExecutionLog
        fields = [
            'id',
            'video',
            'stage',
            'status',
            'attempt',
            'error_message',
            'details',
            'execution_time_ms',
            'created_at',
        ]
        read_only_fields = fields


class PresentationVideoSerializer(serializers.ModelSerializer):
    formatted_raw_size = serializers.ReadOnlyField()
    formatted_compressed_size = serializers.ReadOnlyField()
    compression_savings_percent = serializers.ReadOnlyField()
    file_url = serializers.SerializerMethodField()
    speech_analysis = SpeechAnalysisSerializer(read_only=True)
    behavioral_analysis = BehavioralAnalysisSerializer(read_only=True)
    presentation_score = PresentationScoreSerializer(read_only=True)
    ai_feedback = PresentationFeedbackSerializer(read_only=True)
    execution_logs = PipelineExecutionLogSerializer(many=True, read_only=True)

    class Meta:
        model = PresentationVideo
        fields = [
            'id',
            'original_filename',
            'file',
            'file_url',
            'raw_file_size',
            'compressed_file_size',
            'formatted_raw_size',
            'formatted_compressed_size',
            'compression_savings_percent',
            'file_type',
            'duration_seconds',
            'is_active',
            'status',
            'uploaded_at',
            'speech_analysis',
            'behavioral_analysis',
            'presentation_score',
            'ai_feedback',
            'execution_logs',
        ]
        read_only_fields = [
            'id',
            'raw_file_size',
            'compressed_file_size',
            'file_type',
            'duration_seconds',
            'is_active',
            'status',
            'uploaded_at',
            'speech_analysis',
            'behavioral_analysis',
            'presentation_score',
            'ai_feedback',
            'execution_logs',
        ]

    def get_file_url(self, obj) -> str:
        request = self.context.get('request')
        if obj.file and hasattr(obj.file, 'url'):
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return ''


class VideoUploadSerializer(serializers.Serializer):
    file = serializers.FileField(required=True)

    def validate_file(self, value):
        validate_video_file(value)
        return value
