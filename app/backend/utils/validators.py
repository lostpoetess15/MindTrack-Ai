# ══════════════════════════════════════════════════════
#  Input validators — called before any model prediction
# ══════════════════════════════════════════════════════
import os

MAX_TEXT_LENGTH = int(os.getenv('MAX_TEXT_LENGTH', 2000))
MAX_AUDIO_BYTES = int(os.getenv('MAX_AUDIO_MB', 10)) * 1024 * 1024


def validate_text(text) -> tuple[bool, str]:
    """
    Returns (is_valid: bool, error_message: str).
    Empty string on error_message means no error.
    """
    if not text or not isinstance(text, str):
        return False, "No text provided."

    text = text.strip()

    if len(text) == 0:
        return False, "Text is empty."

    if len(text) < 3:
        return False, "Text is too short — please write at least a few words."

    if len(text) > MAX_TEXT_LENGTH:
        return False, f"Text is too long. Maximum {MAX_TEXT_LENGTH} characters allowed."

    return True, ""


def validate_audio(file) -> tuple[bool, str]:
    """
    Validates an uploaded audio file object (werkzeug FileStorage).
    """
    if file is None:
        return False, "No audio file provided."

    filename = file.filename.lower()
    if not filename.endswith(('.wav', '.mp3', '.ogg', '.flac')):
        return False, "Unsupported format. Please upload a .wav file."

    # Read content length without consuming the stream
    file.seek(0, 2)           # seek to end
    size = file.tell()
    file.seek(0)              # reset to beginning

    if size == 0:
        return False, "Audio file is empty."

    if size > MAX_AUDIO_BYTES:
        mb = MAX_AUDIO_BYTES // (1024 * 1024)
        return False, f"Audio file too large. Maximum {mb} MB allowed."

    return True, ""