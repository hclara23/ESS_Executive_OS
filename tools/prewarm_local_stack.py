import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.voice_provider import warm_tts_engine


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _local_base_url() -> str:
    return os.getenv("ELIO_LOCAL_BASE_URL", "http://localhost:11434/v1").rstrip("/")


def _subagent_url() -> str:
    return os.getenv("ELIO_SUBAGENT_URL", "http://localhost:8010").rstrip("/")


def _api_key() -> str:
    return os.getenv("ELIO_LOCAL_API_KEY", "ollama")


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_api_key()}",
        "Content-Type": "application/json",
    }


def _post(url: str, payload: dict, timeout: int = 120):
    response = requests.post(url, headers=_headers(), json=payload, timeout=timeout)
    response.raise_for_status()
    return response.json()


def _warm_chat_model(model: str):
    return _post(
        f"{_local_base_url()}/chat/completions",
        {
            "model": model,
            "messages": [{"role": "user", "content": "Reply with the word warm."}],
            "temperature": 0,
            "max_tokens": 8,
        },
    )


def _warm_embedding_model(model: str):
    return _post(
        f"{_local_base_url()}/embeddings",
        {
            "model": model,
            "input": "Elio embedding warmup.",
        },
    )


def _warm_subagent(timeout: int = 120):
    token = os.getenv("ELIO_SUBAGENT_TOKEN", "").strip()
    if not token or not _env_bool("ELIO_SUBAGENT_ENABLED", True):
        return {"skipped": True}
    health_url = f"{_subagent_url()}/health"
    last_error = None
    for _ in range(12):
        try:
            health = requests.get(health_url, timeout=10)
            health.raise_for_status()
            break
        except Exception as exc:
            last_error = exc
            time.sleep(5)
    else:
        raise RuntimeError(f"Subagent health check failed: {last_error}")
    return {"ok": True}


def main():
    parser = argparse.ArgumentParser(description="Prewarm Elio local models and TTS runtime.")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--skip-subagent", action="store_true")
    parser.add_argument("--skip-tts", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    load_dotenv()

    failures: list[str] = []
    warmed: dict[str, object] = {}

    chat_model = os.getenv("ELIO_LOCAL_CHAT_MODEL", "qwen3:8b").strip()
    fast_model = os.getenv("ELIO_LOCAL_FAST_MODEL", chat_model).strip()
    vision_model = os.getenv("ELIO_LOCAL_VISION_MODEL", "").strip()
    embed_model = os.getenv("ELIO_LOCAL_EMBED_MODEL", "nomic-embed-text").strip()

    for model in dict.fromkeys([chat_model, fast_model, vision_model]):
        if not model:
            continue
        key = f"chat:{model}"
        try:
            _warm_chat_model(model)
            warmed[key] = "ok"
        except Exception as exc:
            failures.append(f"{key}: {exc}")

    if embed_model:
        try:
            _warm_embedding_model(embed_model)
            warmed[f"embed:{embed_model}"] = "ok"
        except Exception as exc:
            failures.append(f"embed:{embed_model}: {exc}")

    if not args.skip_subagent:
        try:
            _warm_subagent(timeout=args.timeout)
            warmed["subagent"] = "ok"
        except Exception as exc:
            failures.append(f"subagent: {exc}")

    if not args.skip_tts:
        try:
            warm_tts_engine()
            warmed["tts"] = "ok"
        except Exception as exc:
            failures.append(f"tts: {exc}")

    print(json.dumps({"warmed": warmed, "failures": failures}, indent=2))

    if failures and args.strict:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
