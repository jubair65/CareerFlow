import os
import shutil
import subprocess
import logging

logger = logging.getLogger(__name__)


def compress_video(input_path: str, output_path: str, crf: int = 26) -> dict:
    """
    Compresses video into standardized 720p H.264 using FFmpeg.
    Reduces 200-250MB raw videos down to ~20-35MB (<50MB) while maintaining
    crisp facial landmarks and speech audio for downstream AI analysis.

    Parameters:
        input_path (str): Full filesystem path to the raw staged video.
        output_path (str): Destination path for the compressed MP4 file.
        crf (int): Constant Rate Factor (default 26; 23-28 is visually lossless for web).

    Returns:
        dict: {
            "compressed_path": str,
            "compressed_size": int,
            "ffmpeg_used": bool,
            "success": bool
        }
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    ffmpeg_bin = shutil.which("ffmpeg")
    if not ffmpeg_bin:
        try:
            import imageio_ffmpeg
            ffmpeg_bin = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            ffmpeg_bin = None

    if not ffmpeg_bin:
        logger.warning(
            "FFmpeg binary not detected in PATH. Copying file directly without transcoding."
        )
        shutil.copy2(input_path, output_path)
        return {
            "compressed_path": output_path,
            "compressed_size": os.path.getsize(output_path),
            "ffmpeg_used": False,
            "success": True,
        }

    cmd = [
        ffmpeg_bin,
        "-y",
        "-i", input_path,
        "-vf", "scale='min(1280,iw)':-2",  # Scale down to 720p max while preserving aspect ratio
        "-c:v", "libx264",                 # Fast & universal H.264 video codec
        "-crf", str(crf),                  # Constant Rate Factor
        "-preset", "veryfast",             # Rapid encoding preset
        "-c:a", "aac",                     # AAC audio codec
        "-b:a", "128k",                    # 128 kbps audio bitrate
        "-movflags", "+faststart",         # Moov atom at beginning for instant web streaming
        output_path
    ]

    try:
        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            timeout=180
        )
        compressed_size = os.path.getsize(output_path)
        return {
            "compressed_path": output_path,
            "compressed_size": compressed_size,
            "ffmpeg_used": True,
            "success": True,
        }
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        logger.error(f"FFmpeg compression failed: {e}. Falling back to copy.")
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except OSError:
                pass
        shutil.copy2(input_path, output_path)
        return {
            "compressed_path": output_path,
            "compressed_size": os.path.getsize(output_path),
            "ffmpeg_used": False,
            "success": True,
        }


def cleanup_staging_file(staging_path: str):
    """
    Removes the raw staged upload from media/temp_uploads/ after compression.
    """
    if staging_path and os.path.exists(staging_path):
        try:
            os.remove(staging_path)
            logger.info(f"Cleaned up temporary staging file: {staging_path}")
        except OSError as e:
            logger.warning(f"Failed to remove staging file {staging_path}: {e}")
