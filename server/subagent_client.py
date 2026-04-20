import os

import requests


def subagent_enabled() -> bool:
    return os.getenv("ELIO_SUBAGENT_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}


def _subagent_headers():
    headers = {"Content-Type": "application/json"}
    token = os.getenv("ELIO_SUBAGENT_TOKEN", "").strip()
    if token:
        headers["X-Elio-Subagent-Token"] = token
    return headers


def call_subagent(path: str, payload: dict, timeout: int = 20):
    if not subagent_enabled():
        return None

    base_url = os.getenv("ELIO_SUBAGENT_URL", "http://localhost:8010").rstrip("/")
    url = f"{base_url}{path}"
    try:
        response = requests.post(url, json=payload, headers=_subagent_headers(), timeout=timeout)
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        print(f"Subagent request failed for {path}: {exc}")
        return None
