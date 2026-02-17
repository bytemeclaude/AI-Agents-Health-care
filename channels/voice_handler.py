"""
SwasthyaSahayak — Voice Note Handler (Speech-to-Text).

Converts audio recordings to text using OpenAI Whisper.
Supports Indian languages: Hindi, Tamil, Telugu, Marathi, Bengali, Gujarati.

Supported audio formats:
  .ogg  (WhatsApp voice notes — Opus codec)
  .mp3, .wav, .m4a, .webm, .amr

Prerequisites:
  pip install openai-whisper
  # ffmpeg must also be installed and on PATH:
  #   Windows : winget install ffmpeg   OR  choco install ffmpeg
  #   Ubuntu  : sudo apt install ffmpeg
  #   macOS   : brew install ffmpeg

Environment variables:
  WHISPER_MODEL  — model size to use (default: 'base')
                   Options: tiny | base | small | medium | large
                   'base' is recommended for Indian accents (good accuracy, fast).
                   'small' or 'medium' for higher accuracy if hardware allows.
"""

import os
import tempfile
from utils.logger import get_logger

logger = get_logger(__name__)

WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL", "base")

# Map of Whisper language codes to display names (Indian languages + common)
LANGUAGE_NAMES: dict[str, str] = {
    "hi": "Hindi",
    "ta": "Tamil",
    "te": "Telugu",
    "mr": "Marathi",
    "bn": "Bengali",
    "gu": "Gujarati",
    "pa": "Punjabi",
    "ur": "Urdu",
    "kn": "Kannada",
    "ml": "Malayalam",
    "en": "English",
}

# MIME type → file extension mapping (for Twilio media downloads)
MIME_TO_EXT: dict[str, str] = {
    "audio/ogg":       ".ogg",
    "audio/mpeg":      ".mp3",
    "audio/mp4":       ".m4a",
    "audio/wav":       ".wav",
    "audio/x-wav":     ".wav",
    "audio/webm":      ".webm",
    "audio/amr":       ".amr",
    "audio/3gpp":      ".3gp",
}

# Singleton Whisper model
_whisper_model = None


def _load_whisper_model():
    """
    Lazy-load the Whisper model. Cached after first call.
    Raises RuntimeError if openai-whisper is not installed.
    """
    global _whisper_model
    if _whisper_model is not None:
        return _whisper_model

    try:
        import whisper
    except ImportError:
        raise RuntimeError(
            "openai-whisper is not installed.\n"
            "Install it with: pip install openai-whisper\n"
            "Also install ffmpeg: https://ffmpeg.org/download.html"
        )

    logger.info(f"Loading Whisper STT model '{WHISPER_MODEL_SIZE}' (first-time download may take a moment)...")
    _whisper_model = whisper.load_model(WHISPER_MODEL_SIZE)
    logger.info(f"Whisper '{WHISPER_MODEL_SIZE}' model ready.")
    return _whisper_model


def transcribe_audio_file(audio_path: str, language_hint: str | None = None) -> dict:
    """
    Transcribe an audio file to text using Whisper.

    Args:
        audio_path    : Absolute path to the audio file.
        language_hint : Optional ISO 639-1 hint ('hi', 'ta', 'te', 'en').
                        Pass None to let Whisper auto-detect (recommended).

    Returns:
        {
            "text"          : str   — full transcribed text
            "language"      : str   — detected language code (e.g. 'hi')
            "language_name" : str   — human-readable name (e.g. 'Hindi')
            "segments"      : list  — Whisper segment objects with timestamps
            "duration_s"    : float — audio duration in seconds
        }

    Raises:
        FileNotFoundError : if audio_path does not exist
        RuntimeError      : if Whisper / ffmpeg is not installed
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    model = _load_whisper_model()
    logger.info(f"Transcribing: {os.path.basename(audio_path)}")

    transcribe_options: dict = {}
    if language_hint:
        transcribe_options["language"] = language_hint
        logger.info(f"Language hint provided: {language_hint}")

    result = model.transcribe(audio_path, **transcribe_options)

    detected_lang = result.get("language", "en")
    text = result.get("text", "").strip()
    segments = result.get("segments", [])
    duration = segments[-1]["end"] if segments else 0.0

    logger.info(
        f"Transcription complete | lang={detected_lang} | "
        f"duration={duration:.1f}s | text='{text[:80]}{'...' if len(text) > 80 else ''}'"
    )

    return {
        "text":          text,
        "language":      detected_lang,
        "language_name": LANGUAGE_NAMES.get(detected_lang, detected_lang.upper()),
        "segments":      segments,
        "duration_s":    duration,
    }


def transcribe_audio_bytes(audio_bytes: bytes, suffix: str = ".ogg") -> dict:
    """
    Transcribe raw audio bytes (e.g., from a file upload or HTTP download).

    Args:
        audio_bytes : Raw bytes of the audio file.
        suffix      : File extension hint (e.g. '.ogg', '.mp3').

    Returns:
        Same dict as transcribe_audio_file().
    """
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        return transcribe_audio_file(tmp_path)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def transcribe_url(audio_url: str, auth: tuple[str, str] | None = None) -> dict:
    """
    Download an audio file from a URL and transcribe it.

    Primarily used to process Twilio MediaUrl voice notes from WhatsApp.
    Twilio requires HTTP Basic Auth (Account SID + Auth Token).

    Args:
        audio_url : URL to the audio file.
        auth      : Optional (username, password) for authenticated URLs.

    Returns:
        Same dict as transcribe_audio_file().

    Raises:
        requests.HTTPError : if the download fails.
        RuntimeError       : if Whisper / ffmpeg is not installed.
    """
    import requests

    logger.info(f"Downloading audio from URL for transcription...")
    response = requests.get(audio_url, auth=auth, timeout=30)
    response.raise_for_status()

    # Determine file extension from Content-Type header
    content_type = response.headers.get("Content-Type", "audio/ogg").split(";")[0].strip()
    suffix = MIME_TO_EXT.get(content_type, ".ogg")
    logger.info(f"Audio content-type: {content_type} → using extension: {suffix}")

    return transcribe_audio_bytes(response.content, suffix=suffix)
