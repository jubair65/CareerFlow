from rest_framework import serializers
from .models import PresentationVideo
from .validators import validate_video_file, MAX_UPLOAD_SIZE


class PresentationVideoSerializer(serializers.ModelSerializer):
    formatted_raw_size = serializers.ReadOnlyField()
    formatted_compressed_size = serializers.ReadOnlyField()
    compression_savings_percent = serializers.ReadOnlyField()
    file_url = serializers.SerializerMethodField()

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
