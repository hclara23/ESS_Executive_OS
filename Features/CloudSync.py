import json
import os


def load_cloud_config():
    path = os.path.join("Data", "cloud_config.json")
    if not os.path.exists(path):
        return {"provider": "firebase", "sync_enabled": False}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"provider": "firebase", "sync_enabled": False}


def sync_status():
    cfg = load_cloud_config()
    if not cfg.get("sync_enabled"):
        return "Cloud sync is off."
    provider = cfg.get("provider", "firebase")
    return f"Cloud sync is on for {provider}."


def firebase_status():
    path = os.path.join("Data", "firebase_config.json")
    if not os.path.exists(path):
        return "Firebase config is missing."
    return "Firebase config file is ready."


def postgres_status():
    path = os.path.join("Data", "postgres_config.json")
    if not os.path.exists(path):
        return "Postgres config is missing."
    return "Postgres config file is ready."
