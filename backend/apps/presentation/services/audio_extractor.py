import os
import shutil
import subprocess
import logging
import tempfile

logger = logging.getLogger(__name__)


def get_ffmpeg_binary() -> str:
    """
    Locates ffmpeg executable in PATH or through imageio-ffmpeg.
    """
    bin_path = shutil.which("ffmpeg")
    if bin_path:
        return bin_path
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def extract_audio(video_path: str, output_wav_path: str = None) -> str:
    """
    Extracts 16kHz mono PCM WAV audio from a video file using FFmpeg (US-12-T2).
    Optimal audio profile for Whisper / faster-whisper speech recognition.

    Parameters:
        video_path (str): Absolute filesystem path to source video file.
        output_wav_path (str, optional): Destination path for the WAV audio.
            If None, a temporary WAV file is created in system temp.

    Returns:
        str: Absolute filesystem path to the extracted 16kHz WAV file.

    Raises:
        FileNotFoundError: If the source video file does not exist.
        RuntimeError: If FFmpeg binary is missing or extraction process fails.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found at: {video_path}")

    ffmpeg_bin = get_ffmpeg_binary()
    if not ffmpeg_bin:
        raise RuntimeError("FFmpeg binary not found in system PATH or python environment.")

    if not output_wav_path:
        temp_dir = tempfile.gettempdir()
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        output_wav_path = os.path.join(temp_dir, f"{base_name}_audio16k.wav")

    os.makedirs(os.path.dirname(output_wav_path), exist_ok=True)

    cmd = [
        ffmpeg_bin,
        "-y",
        "-i", video_path,
        "-vn",                   # Disable video recording
        "-ar", "16000",          # 16,000 Hz sample rate (Whisper standard)
        "-ac", "1",              # Mono channel
        "-c:a", "pcm_s16le",     # 16-bit uncompressed PCM
        output_wav_path
    ]

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            timeout=120,
            check=True
        )
        logger.info(f"Successfully extracted audio to: {output_wav_path}")
        return output_wav_path
    except subprocess.TimeoutExpired:
        if os.path.exists(output_wav_path):
            os.remove(output_wav_path)
        raise RuntimeError(f"Audio extraction timed out after 120s for {video_path}")
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode('utf-8', errors='ignore') if e.stderr else str(e)
        if os.path.exists(output_wav_path):
            os.remove(output_wav_path)
        logger.error(f"FFmpeg audio extraction failed: {error_msg}")
        raise RuntimeError(f"FFmpeg audio extraction failed: {error_msg}")


def cleanup_audio_file(audio_path: str):
    """
    Removes temporary extracted audio file.
    """
    if audio_path and os.path.exists(audio_path):
        try:
            os.remove(audio_path)
            logger.info(f"Cleaned up audio file: {audio_path}")
        except OSError as e:
            logger.warning(f"Failed to delete audio file {audio_path}: {e}")
