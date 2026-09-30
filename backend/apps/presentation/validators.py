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
    Probes video duration in seconds using ffprobe, OpenCV, or FFmpeg.
    Ensures accurate duration detection across all machines even when ffprobe is not installed.
    """
    # 1. Try ffprobe if available in system PATH
    ffprobe_bin = shutil.which("ffprobe")
    if ffprobe_bin:
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
            if duration_float > 0:
                return int(round(duration_float))
        except Exception:
            pass

    # 2. Try OpenCV VideoCapture
    try:
        import cv2
        cap = cv2.VideoCapture(file_path)
        if cap.isOpened():
            fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0
            cap.release()
            if fps > 0 and frame_count > 0:
                duration_sec = frame_count / fps
                if duration_sec > 0:
                    return int(round(duration_sec))
    except Exception:
        pass

    # 3. Try FFmpeg stderr parsing (via imageio-ffmpeg or system ffmpeg)
    try:
        import re
        from apps.presentation.services.audio_extractor import get_ffmpeg_binary
        ffmpeg_bin = get_ffmpeg_binary()
        if ffmpeg_bin:
            cmd = [ffmpeg_bin, "-i", file_path]
            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )
            match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.?\d*)", proc.stderr)
            if match:
                hours, mins, secs = match.groups()
                total_sec = int(hours) * 3600 + int(mins) * 60 + float(secs)
                if total_sec > 0:
                    return int(round(total_sec))
    except Exception:
        pass

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
