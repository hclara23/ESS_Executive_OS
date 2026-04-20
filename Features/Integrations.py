import os
from dotenv import load_dotenv

def is_connected(name: str) -> bool:
    load_dotenv()
    if name == "gmail":
        return bool(os.getenv("ELIO_GMAIL_CLIENT_ID"))
    elif name == "calendar":
        return bool(os.getenv("ELIO_CAL_CLIENT_ID"))
    elif name == "quickbooks":
        return bool(os.getenv("ELIO_QBO_CLIENT_ID"))
    elif name == "project_management":
        return bool(os.getenv("ELIO_PROCORE_CLIENT_ID") or os.getenv("ELIO_JIRA_TOKEN"))
    return False


def status_text(name: str) -> str:
    if is_connected(name):
        return f"{name} is connected."
    return f"{name} is not connected yet."


def connect_stub(name: str) -> str:
    return f"{name} setup is ready. Add keys in Data/integrations.json."
