import os
from rest_framework import serializers
from .models import CandidateCV, ParsedCV

MAX_CV_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_CV_EXTENSIONS = ['.pdf', '.docx']
ALLOWED_MIME_TYPES = [
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/msword',
    'application/octet-stream',
]


class CandidateCVSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = CandidateCV
        fields = [
            'id',
            'file',
            'original_filename',
            'file_size',
            'file_type',
            'is_active',
            'uploaded_at',
            'updated_at',
            'file_url',
        ]
        read_only_fields = [
            'id',
            'original_filename',
            'file_size',
            'file_type',
            'is_active',
            'uploaded_at',
            'updated_at',
            'file_url',
        ]
        extra_kwargs = {
            'file': {'write_only': True}
        }

    def get_file_url(self, obj):
        if obj.file:
            return f"/api/core/files/{obj.file.name}"
        return None

    def validate_file(self, value):
        if not value:
            raise serializers.ValidationError("A CV file must be provided.")

        filename = getattr(value, 'name', '')
        ext = os.path.splitext(filename)[1].lower()

        # 1. Format check
        if ext not in ALLOWED_CV_EXTENSIONS:
            raise serializers.ValidationError(
                f"Unsupported file format '{ext}'. Only PDF (.pdf) and Word (.docx) documents are supported."
            )

        # 2. Size check (10 MB maximum)
        file_size = getattr(value, 'size', 0)
        if file_size > MAX_CV_FILE_SIZE:
            size_mb = round(file_size / (1024 * 1024), 2)
            raise serializers.ValidationError(
                f"File size exceeds 10 MB limit (uploaded file is {size_mb} MB)."
            )

        # 3. Content type check if available
        content_type = getattr(value, 'content_type', '')
        if content_type and content_type not in ALLOWED_MIME_TYPES:
            raise serializers.ValidationError(
                f"Invalid file MIME type '{content_type}'. Only PDF and DOCX documents are supported."
            )

        return value


class ParsedCVSerializer(serializers.ModelSerializer):
    """
    Serializer for structured parsed CV data (US-07-T5).
    """
    skills_count = serializers.IntegerField(read_only=True)
    original_filename = serializers.CharField(source='cv.original_filename', read_only=True)
    candidate_email = serializers.EmailField(source='cv.user.email', read_only=True)

    class Meta:
        model = ParsedCV
        fields = [
            'id',
            'cv',
            'candidate_email',
            'original_filename',
            'raw_text',
            'skills',
            'skills_count',
            'education',
            'experience',
            'parsed_at',
        ]
        read_only_fields = ['id', 'parsed_at', 'candidate_email', 'original_filename', 'skills_count']

