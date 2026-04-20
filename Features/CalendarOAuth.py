import os
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# If modifying these SCOPES, delete the file Data/calendar_token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly", "https://www.googleapis.com/auth/calendar.events"]


def _config_path():
    return os.path.join("Data", "integrations.json")


def _token_path():
    return os.path.join("Data", "calendar_token.json")


def setup_status():
    load_dotenv()
    if os.path.exists(_token_path()):
        return "Calendar is connected."
    if os.getenv("ELIO_CAL_CLIENT_ID") and os.getenv("ELIO_CAL_CLIENT_SECRET"):
        return "Calendar setup is ready. I can connect when you are ready."
    return "Calendar setup is not ready."


def connect_calendar():
    load_dotenv()
    client_id = os.getenv("ELIO_CAL_CLIENT_ID")
    client_secret = os.getenv("ELIO_CAL_CLIENT_SECRET")

    if not client_id or not client_secret:
        return "Please add client_id and client_secret to Data/integrations.json first."

    creds = None
    if os.path.exists(_token_path()):
        creds = Credentials.from_authorized_user_file(_token_path(), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            client_config = {
                "installed": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            }
            flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(_token_path(), "w") as token:
            token.write(creds.to_json())

    return "Calendar connected successfully."


def connect_stub():
    return connect_calendar()
