"""
Sarvam AI API Client
Wraps: STT, STT-Translate, TTS, and Translate endpoints.
Auth: api-subscription-key header.
All methods are async and use httpx.

Retry policy: 3 attempts with exponential backoff (1s, 2s, 4s)
on transient network/server errors.
"""
import io
import logging
import httpx
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from config import settings

logger = logging.getLogger(__name__)

BASE_URL = settings.SARVAM_BASE_URL.rstrip("/")
HEADERS = {"api-subscription-key": settings.SARVAM_API_KEY}
TIMEOUT = 60.0  # seconds

_RETRY = dict(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type((httpx.NetworkError, httpx.TimeoutException)),
    reraise=True,
)


class SarvamError(Exception):
    """Raised when Sarvam API returns a non-2xx response."""
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"Sarvam API error {status_code}: {detail}")


def _raise_for_status(response: httpx.Response) -> None:
    if response.status_code >= 400:
        try:
            detail = response.json().get("error", response.text)
        except Exception:
            detail = response.text
        raise SarvamError(response.status_code, detail)


# ─── SPEECH TO TEXT ───────────────────────────────────────────

@retry(**_RETRY)
async def transcribe_audio(
    audio_bytes: bytes,
    filename: str = "audio.wav",
    language_code: Optional[str] = None,
    model: str = "saarika:v2",
) -> dict:
    """
    Transcribe audio to text in its original language.

    Args:
        audio_bytes: Raw audio bytes (WAV/MP3/OGG — mono, ≤ 30s)
        filename: Hint for content type detection (e.g. 'audio.wav')
        language_code: BCP-47 code (e.g. 'hi-IN'). Pass None for auto-detect.
        model: Sarvam STT model. Default: saarika:v2

    Returns:
        {
            "transcript": str,
            "language_code": str,   # detected language
        }
    """
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        form_data = {
            "model": (None, model),
        }
        if language_code:
            form_data["language_code"] = (None, language_code)

        files = {"file": (filename, io.BytesIO(audio_bytes), "audio/wav")}

        response = await client.post(
            f"{BASE_URL}/speech-to-text",
            headers=HEADERS,
            data={k: v[1] for k, v in form_data.items() if v[0] is None},
            files=files,
        )
        _raise_for_status(response)
        data = response.json()
        return {
            "transcript": data.get("transcript", ""),
            "language_code": data.get("language_code", language_code or "unknown"),
        }


# ─── SPEECH TO TEXT + TRANSLATE ───────────────────────────────

async def transcribe_and_translate(
    audio_bytes: bytes,
    filename: str = "audio.wav",
    prompt: Optional[str] = None,
    model: str = "saaras:v2.5",
) -> dict:
    """
    Transcribe audio AND translate to English in one call.
    Useful for getting English text from any Indian language audio.

    Returns:
        {
            "transcript": str,        # original language transcript
            "translation": str,       # English translation
            "language_code": str,     # detected source language
        }
    """
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        form_fields = {"model": model}
        if prompt:
            form_fields["prompt"] = prompt

        files = {"file": (filename, io.BytesIO(audio_bytes), "audio/wav")}

        response = await client.post(
            f"{BASE_URL}/speech-to-text-translate",
            headers=HEADERS,
            data=form_fields,
            files=files,
        )
        _raise_for_status(response)
        data = response.json()
        return {
            "transcript": data.get("transcript", ""),
            "translation": data.get("translation", ""),
            "language_code": data.get("language_code", "unknown"),
        }


# ─── TEXT TO SPEECH ───────────────────────────────────────────

SPEAKER_MAP = {
    "hi-IN": "meera",
    "ta-IN": "arjun",
    "te-IN": "pavithra",
    "kn-IN": "maitreyi",
    "ml-IN": "laleh",
    "bn-IN": "riya",
    "gu-IN": "manisha",
    "mr-IN": "sachin",
    "pa-IN": "amol",
    "en-IN": "meera",
}


async def text_to_speech(
    text: str,
    target_language_code: str = "hi-IN",
    speaker: Optional[str] = None,
    model: str = "bulbul:v2",
    enable_preprocessing: bool = True,
) -> bytes:
    """
    Convert text to speech audio (returns raw WAV bytes).

    Args:
        text: Input text (max ~500 chars per call)
        target_language_code: BCP-47 code of the output language
        speaker: Speaker name. Auto-selected per language if not specified.
        model: TTS model. Default: bulbul:v2
        enable_preprocessing: Auto-normalize numbers/abbreviations.

    Returns:
        bytes: WAV audio data
    """
    chosen_speaker = speaker or SPEAKER_MAP.get(target_language_code, "meera")

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        payload = {
            "inputs": [text],
            "target_language_code": target_language_code,
            "speaker": chosen_speaker,
            "model": model,
            "enable_preprocessing": enable_preprocessing,
        }
        response = await client.post(
            f"{BASE_URL}/text-to-speech",
            headers={**HEADERS, "Content-Type": "application/json"},
            json=payload,
        )
        _raise_for_status(response)
        data = response.json()

        # Sarvam returns base64-encoded audio
        import base64
        audio_b64 = data.get("audios", [""])[0]
        return base64.b64decode(audio_b64)


# ─── TRANSLATE ────────────────────────────────────────────────

async def translate_text(
    input_text: str,
    source_language_code: str,
    target_language_code: str = "en-IN",
    model: str = "mayura:v1",
) -> str:
    """
    Translate text between Indian languages or to/from English.

    Args:
        input_text: Source text to translate
        source_language_code: BCP-47 code of input (e.g. 'hi-IN')
        target_language_code: BCP-47 code of output (default: 'en-IN')
        model: Translation model

    Returns:
        str: Translated text
    """
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        payload = {
            "input": input_text,
            "source_language_code": source_language_code,
            "target_language_code": target_language_code,
            "model": model,
        }
        response = await client.post(
            f"{BASE_URL}/translate",
            headers={**HEADERS, "Content-Type": "application/json"},
            json=payload,
        )
        _raise_for_status(response)
        return response.json().get("translated_text", "")
