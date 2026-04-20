import json
import os
from functools import lru_cache
from pathlib import Path


PERSONALITY_PATH = Path("Data") / "personality.json"
PERSONALITY_PROFILES_PATH = Path("Data") / "personality_profiles.json"
_DEFAULT_PROFILE = "executive-operator"


def _load_json(path: Path):
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


@lru_cache(maxsize=2)
def _base_personality():
    return _load_json(PERSONALITY_PATH)


@lru_cache(maxsize=2)
def _profile_catalog():
    return _load_json(PERSONALITY_PROFILES_PATH)


def reset_personality_cache():
    _base_personality.cache_clear()
    _profile_catalog.cache_clear()


def get_active_profile_name() -> str:
    base = _base_personality()
    return os.getenv("ELIO_PERSONALITY_PROFILE", base.get("profile", _DEFAULT_PROFILE)).strip() or _DEFAULT_PROFILE


def get_personality(user_name: str | None = None):
    base = dict(_base_personality())
    catalog = _profile_catalog()
    profiles = catalog.get("profiles", {})
    profile_name = get_active_profile_name()
    profile = dict(profiles.get(profile_name, {}))
    merged = {**base, **profile}

    if user_name:
        user_overrides = profile.get("user_overrides", {}).get(user_name.lower(), {})
        merged.update(user_overrides)

    merged["profile"] = profile_name
    merged.setdefault("display_name", profile.get("display_name", profile_name))
    merged.setdefault("voice", "af_heart")
    merged.setdefault("voice_speed", 1.0)
    return merged


def get_voice_defaults(user_name: str | None = None):
    personality = get_personality(user_name)
    return {
        "voice": personality.get("voice", "af_heart"),
        "voice_speed": float(personality.get("voice_speed", 1.0)),
        "voice_provider": personality.get("voice_provider", "kokoro"),
    }


def get_personality_summary(user_name: str | None = None):
    personality = get_personality(user_name)
    return {
        "profile": personality.get("profile"),
        "display_name": personality.get("display_name"),
        "tone": personality.get("tone"),
        "voice": personality.get("voice"),
        "voice_provider": personality.get("voice_provider", "kokoro"),
        "local_model_hint": personality.get("local_model_hint", "qwen3"),
        "description": personality.get("description", ""),
    }
