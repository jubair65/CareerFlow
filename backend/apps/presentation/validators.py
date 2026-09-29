import os
import shutil
import subprocess
from django.core.exceptions import ValidationError

MAX_UPLOAD_SIZE = 250 * 1024 * 1024  # 250 MB in bytes
MAX_DURATION_SECONDS = 180           # 3 minutes

ALLOWED_EXTENSIONS = ['.mp4', '.webm', '.mov']
ALLOWED_MIME_TYPES = [
    'video/mp4',
    'video/webm',
    'video/quicktime',
    'video/x-matroska',
    'application/octet-stream',  # common generic upload fallback
]


def validate_video_file(file) -> str:
    """
    Validates uploaded file size and extension.
    Returns the normalized file extension without dot (e.g. 'mp4', 'webm', 'mov').
    Raises ValidationError if invalid.
    """
    if file.size > MAX_UPLOAD_SIZE:
        max_mb = MAX_UPLOAD_SIZE // (1024 * 1024)
        actual_mb = file.size / (1024 * 1024)
        raise ValidationError(
            f"File size exceeds maximum allowed limit of {max_mb}MB. "
            f"Uploaded video is {actual_mb:.1f}MB."
        )

    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        allowed_str = ", ".join(ALLOWED_EXTENSIONS)
        raise ValidationError(
            f"Unsupported video format '{ext}'. Allowed formats are: {allowed_str}."
        )

    # Check content type if available
    content_type = getattr(file, 'content_type', '')
    if content_type and content_type not in ALLOWED_MIME_TYPES and not content_type.startswith('video/'):
        raise ValidationError(
            f"Invalid file MIME type '{content_type}'. Must be a valid video stream."
        )

    return ext.lstrip('.')


def probe_video_duration(file_path: str) -> int:
    """
    Attempts to probe video duration in seconds using ffprobe.
    If ffprobe is not installed or inspection fails, returns 0 or estimated duration.
    """
    ffprobe_bin = shutil.which("ffprobe")
    if not ffprobe_bin:
        return 0

    try:
        cmd = [
            ffprobe_bin,
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            file_path
        ]
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
            check=True
        )
        duration_float = float(result.stdout.strip())
        return int(round(duration_float))
    except Exception:
        return 0


def validate_video_duration(duration_seconds: int):
    """
    Ensures video duration does not exceed MAX_DURATION_SECONDS (180s).
    """
    if duration_seconds > MAX_DURATION_SECONDS:
        raise ValidationError(
            f"Video duration ({duration_seconds}s) exceeds the maximum allowed length "
            f"of {MAX_DURATION_SECONDS}s (3 minutes)."
        )
