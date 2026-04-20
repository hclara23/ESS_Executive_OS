import os
import json
import webbrowser
from msal import PublicClientApplication, SerializableTokenCache

# Configuration for Microsoft Graph API
# For a personal app, you'd register it in Azure Portal (App Registrations)
# The Client ID and Tenant ID would normally be in .env
CLIENT_ID = os.getenv("ELIO_MS_CLIENT_ID", "your-client-id-placeholder")
AUTHORITY = "https://login.microsoftonline.com/common"
SCOPES = ["User.Read", "Mail.ReadWrite", "Mail.Send"]

TOKEN_CACHE_PATH = "Data/ms_graph_token_cache.bin"

def get_ms_graph_app():
    cache = SerializableTokenCache()
    if os.path.exists(TOKEN_CACHE_PATH):
        cache.deserialize(open(TOKEN_CACHE_PATH, "r").read())
    
    app = PublicClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        token_cache=cache
    )
    return app, cache

def get_access_token():
    app, cache = get_ms_graph_app()
    accounts = app.get_accounts()
    
    result = None
    if accounts:
        # Try to get token silently
        result = app.acquire_token_silent(SCOPES, account=accounts[0])
    
    if not result:
        # Need interactive login
        # In a headless server, this is tricky. We'd use Device Code Flow.
        flow = app.initiate_device_flow(scopes=SCOPES)
        if "user_code" not in flow:
            raise Exception("Could not initiate device flow")
        
        print(f"To sign in, use a web browser to open the page {flow['verification_uri']} and enter the code {flow['user_code']} to authenticate.")
        # speak(f"I need you to authenticate with Microsoft. Please check the terminal for the authorization code.")
        
        result = app.acquire_token_by_device_flow(flow)
        
        if cache.has_state_changed:
            with open(TOKEN_CACHE_PATH, "w") as f:
                f.write(cache.serialize())
                
    return result.get("access_token") if result else None

def send_outlook_email(to_recipient, subject, body):
    token = get_access_token()
    if not token:
        return False
    
    import requests
    endpoint = "https://graph.microsoft.com/v1.0/me/sendMail"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    email_data = {
        "message": {
            "subject": subject,
            "body": {
                "contentType": "Text",
                "content": body
            },
            "toRecipients": [
                {
                    "emailAddress": {
                        "address": to_recipient
                    }
                }
            ]
        }
    }
    
    response = requests.post(endpoint, headers=headers, json=email_data)
    return response.status_code == 202

def draft_outlook_email(to_recipient, subject, body):
    token = get_access_token()
    if not token:
        return False
    
    import requests
    endpoint = "https://graph.microsoft.com/v1.0/me/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    email_data = {
        "subject": subject,
        "body": {
            "contentType": "Text",
            "content": body
        },
        "toRecipients": [
            {
                "emailAddress": {
                    "address": to_recipient
                }
            }
        ]
    }
    
    response = requests.post(endpoint, headers=headers, json=email_data)
    return response.status_code == 201
