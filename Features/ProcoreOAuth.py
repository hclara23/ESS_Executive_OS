import os
import json
from datetime import datetime, timedelta
import psycopg2
import requests

def _pg_conn():
    uri = os.getenv("ELIO_PG_URI", "").strip()
    return psycopg2.connect(uri)

def save_procore_token(access_token, refresh_token, expires_in):
    expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
    conn = _pg_conn()
    cur = conn.cursor()
    cur.execute(
        """
        insert into elio_oauth_tokens (service_name, access_token, refresh_token, expires_at, updated_at)
        values (%s, %s, %s, %s, %s)
        on conflict (service_name) do update
        set access_token = excluded.access_token,
            refresh_token = excluded.refresh_token,
            expires_at = excluded.expires_at,
            updated_at = excluded.updated_at;
        """,
        ("procore", access_token, refresh_token, expires_at, datetime.utcnow())
    )
    conn.commit()
    cur.close()
    conn.close()

def get_procore_token():
    conn = _pg_conn()
    cur = conn.cursor()
    cur.execute("select access_token, refresh_token, expires_at from elio_oauth_tokens where service_name = %s", ("procore",))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row: return None
    return {"access_token": row[0], "refresh_token": row[1], "expires_at": row[2]}

def refresh_procore_token():
    token_data = get_procore_token()
    if not token_data: return None
    
    client_id = os.getenv("ELIO_PROCORE_CLIENT_ID")
    client_secret = os.getenv("ELIO_PROCORE_CLIENT_SECRET")
    
    url = "https://login.procore.com/oauth/token"
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": token_data["refresh_token"],
        "client_id": client_id,
        "client_secret": client_secret
    }
    
    res = requests.post(url, data=payload)
    if res.status_code == 200:
        data = res.json()
        save_procore_token(data["access_token"], data["refresh_token"], data["expires_in"])
        return data["access_token"]
    return None

def get_valid_access_token():
    token_data = get_procore_token()
    if not token_data: return None
    if datetime.utcnow() > token_data["expires_at"] - timedelta(minutes=5):
        return refresh_procore_token()
    return token_data["access_token"]

def create_procore_rfi(project_id, subject, question):
    token = get_valid_access_token()
    if not token: return "Procore not connected."
    
    url = f"https://api.procore.com/rest/v1.0/projects/{project_id}/rfis"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "rfi": {
            "subject": subject,
            "question": question
        }
    }
    
    res = requests.post(url, json=payload, headers=headers)
    if res.status_code in [200, 201]:
        return f"Successfully created Procore RFI in project {project_id}."
    return f"Failed to create Procore RFI: {res.text}"

def setup_status():
    token = get_procore_token()
    if token: return "Procore is connected."
    return "Procore is not connected."
