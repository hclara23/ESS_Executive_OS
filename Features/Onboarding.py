import json
import os

USER_DATA_PATH = "Data/user_profiles.json"

def get_user_profiles():
    if not os.path.exists(USER_DATA_PATH):
        return {}
    with open(USER_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_user_profile(user_key, profile_data):
    profiles = get_user_profiles()
    profiles[user_key] = profile_data
    with open(USER_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(profiles, f, indent=2)

def is_onboarded(user_key):
    profiles = get_user_profiles()
    return user_key in profiles and profiles[user_key].get("onboarded", False)

def get_profile(user_key):
    return get_user_profiles().get(user_key, {})
