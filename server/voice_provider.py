import io
import os
from functools import lru_cache
from pathlib import Path

import requests

from server.personality import get_voice_defaults


def _configured_provider_mode() -> str:
    return os.getenv("ELIO_TTS_PROVIDER", "").strip().lower()


def _provider_name(user_name: str | None = None) -> str:
    configured = _configured_provider_mode()
    if configured and configured not in {"profile", "auto"}:
        return configured
    defaults = get_voice_defaults(user_name)
    return str(defaults.get("voice_provider", "kokoro")).strip().lower() or "kokoro"


def _lang_code() -> str:
    return os.getenv("ELIO_TTS_LANG", "en-us").strip() or "en-us"


def _remote_tts_url() -> str:
    return os.getenv("ELIO_REMOTE_TTS_URL", "").strip()


def _remote_tts_timeout_seconds() -> int:
    try:
        return max(30, int(os.getenv("ELIO_REMOTE_TTS_TIMEOUT_SECONDS", "900").strip() or "900"))
    except ValueError:
        return 900


def _selected_voice(default_voice: str, requested_voice: str | None = None) -> str:
    if requested_voice:
        return requested_voice

    configured_voice = os.getenv("ELIO_TTS_VOICE", "").strip()
    if _configured_provider_mode() in {"profile", "auto"} or not configured_voice:
        return default_voice or configured_voice
    return configured_voice or default_voice


@lru_cache(maxsize=1)
def _get_kokoro_model():
    from kokoro_onnx import Kokoro

    model_path = Path(os.getenv("ELIO_KOKORO_MODEL_PATH", "kokoro-v1.0.onnx"))
    voices_path = Path(os.getenv("ELIO_KOKORO_VOICES_PATH", "voices-v1.0.bin"))

    if not model_path.exists() or not voices_path.exists():
        raise RuntimeError("Kokoro model files are missing.")

    return Kokoro(str(model_path), str(voices_path))


def tts_ready(user_name: str | None = None) -> bool:
    provider = _provider_name(user_name)
    if provider == "none":
        return False
    if provider == "remote":
        return bool(_remote_tts_url())
    try:
        _get_kokoro_model()
        return True
    except Exception:
        return False


def reset_tts_cache():
    _get_kokoro_model.cache_clear()


def warm_tts_engine(user_name: str | None = None) -> bool:
    provider = _provider_name(user_name)
    if provider == "none":
        return False
    if provider == "remote":
        return bool(_remote_tts_url())
    _get_kokoro_model()
    return True


def get_tts_runtime(user_name: str | None = None):
    defaults = get_voice_defaults(user_name)
    provider = _provider_name(user_name)
    return {
        "provider": provider,
        "ready": tts_ready(user_name),
        "default_voice": _selected_voice(defaults["voice"]),
        "default_speed": float(os.getenv("ELIO_TTS_SPEED", defaults["voice_speed"])),
        "lang": _lang_code(),
        "remote_url": _remote_tts_url() if provider == "remote" else "",
    }


def synthesize_wav(text: str, voice: str | None = None, user_name: str | None = None):
    defaults = get_voice_defaults(user_name)
    provider = _provider_name(user_name)
    selected_voice = _selected_voice(defaults["voice"], requested_voice=voice)
    speed = float(os.getenv("ELIO_TTS_SPEED", defaults["voice_speed"]))

    if provider == "remote":
        url = _remote_tts_url()
        if not url:
            raise RuntimeError("ELIO_REMOTE_TTS_URL is required when ELIO_TTS_PROVIDER=remote.")
        response = requests.post(
            url,
            json={
                "text": text,
                "voice": selected_voice,
                "speed": speed,
                "language": _lang_code(),
            },
            timeout=_remote_tts_timeout_seconds(),
        )
        response.raise_for_status()
        return response.content

    if provider != "kokoro":
        raise RuntimeError(f"Unsupported TTS provider: {provider}")

    samples, sample_rate = _get_kokoro_model().create(
        text,
        voice=selected_voice,
        speed=speed,
        lang=_lang_code(),
    )
    import soundfile as sf

    buffer = io.BytesIO()
    sf.write(buffer, samples, sample_rate, format="WAV")
    buffer.seek(0)
    return buffer.read()
