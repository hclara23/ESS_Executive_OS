import json
import os
from Features.MemoryStore import get_device_user


def _local_profile_user():
    path = os.path.join("Data", "device_profile.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("user")
    except Exception:
        return None


def resolve_user():
    device_id = os.getenv("ELIO_DEVICE_ID", "").strip()
    if device_id:
        user = get_device_user(device_id)
        if user:
            return user

    local_user = _local_profile_user()
    if local_user:
        return local_user

    # In production GUI mode, we ask via dialog if voice fails
    return "unknown"
