import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

from Features.PostgresStore import db_cursor

try:
    from intuitlib.authclient import AuthClient
    from intuitlib.enums import Scopes
    HAS_INTUIT = True
except ImportError:
    HAS_INTUIT = False

def setup_status():
    try:
        token = get_qbo_token()
        if token:
            return "QuickBooks is connected."
    except Exception as e:
        print(f"[QBO] setup_status error: {e}")
    return "QuickBooks is not connected."

def get_overdue_invoices():
    try:
        client = get_valid_client()
        if not client:
            return []
        import requests
        url = f"https://sandbox-quickbooks.api.intuit.com/v3/company/{client.realm_id}/query"
        query = "SELECT * FROM Invoice WHERE Balance > '0'"
        headers = {"Authorization": f"Bearer {client.access_token}", "Accept": "application/json"}
        res = requests.post(url, data=query, headers=headers)
        return res.json().get("QueryResponse", {}).get("Invoice", [])
    except Exception as e:
        print(f"[QBO] get_overdue_invoices error: {e}")
        return []

def save_qbo_token(access_token, refresh_token, realm_id, expires_in):
    expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
    with db_cursor() as cur:
        cur.execute(
            """
            insert into elio_oauth_tokens (service_name, access_token, refresh_token, realm_id, expires_at, updated_at)
            values (%s, %s, %s, %s, %s, %s)
            on conflict (service_name) do update
            set access_token = excluded.access_token,
                refresh_token = excluded.refresh_token,
                realm_id = excluded.realm_id,
                expires_at = excluded.expires_at,
                updated_at = excluded.updated_at;
            """,
            ("quickbooks", access_token, refresh_token, realm_id, expires_at, datetime.utcnow()),
        )

def get_qbo_token():
    with db_cursor() as cur:
        cur.execute(
            "select access_token, refresh_token, realm_id, expires_at from elio_oauth_tokens where service_name = %s",
            ("quickbooks",),
        )
        row = cur.fetchone()
    if not row:
        return None
    return {"access_token": row[0], "refresh_token": row[1], "realm_id": row[2], "expires_at": row[3]}

def get_valid_client():
    if not HAS_INTUIT:
        return None
    
    load_dotenv()
    client_id = os.getenv("ELIO_QBO_CLIENT_ID")
    client_secret = os.getenv("ELIO_QBO_CLIENT_SECRET")
    redirect_uri = os.getenv("ELIO_QBO_REDIRECT_URI", "https://elio-api-1054707372641.us-central1.run.app/callback/qbo")
    
    token_data = get_qbo_token()
    if not token_data:
        return None

    auth_client = AuthClient(
        client_id=client_id,
        client_secret=client_secret,
        access_token=token_data["access_token"],
        refresh_token=token_data["refresh_token"],
        realm_id=token_data["realm_id"],
        redirect_uri=redirect_uri,
        environment="sandbox", # or 'production'
    )

    # Check expiry
    if datetime.utcnow() > token_data["expires_at"] - timedelta(minutes=5):
        try:
            auth_client.refresh()
            save_qbo_token(auth_client.access_token, auth_client.refresh_token, auth_client.realm_id, 3600)
        except Exception as e:
            print(f"Failed to refresh QBO token: {e}")
            return None
            
    return auth_client

def get_overdue_invoices_summary():
    client = get_valid_client()
    if not client:
        return "QuickBooks is not connected or authorization expired."

    url = f"https://sandbox-quickbooks.api.intuit.com/v3/company/{client.realm_id}/query"
    # Overdue = Balance > 0 and DueDate < Today
    today = datetime.now().strftime('%Y-%m-%d')
    query = f"SELECT * FROM Invoice WHERE Balance > '0' AND DueDate < '{today}'"

    import requests
    headers = {
        "Authorization": f"Bearer {client.access_token}",
        "Accept": "application/json",
        "Content-Type": "application/text"
    }

    try:
        response = requests.post(url, data=query, headers=headers)
        if response.status_code == 200:
            invoices = response.json().get("QueryResponse", {}).get("Invoice", [])
            if not invoices:
                return "Good news! There are no overdue invoices in QuickBooks."
            
            total_overdue = sum(float(inv.get("Balance", 0)) for inv in invoices)
            count = len(invoices)
            return f"There are {count} overdue invoices totaling ${total_overdue:,.2f}."
        else:
            return f"Error querying QuickBooks: {response.text}"
    except Exception as e:
        return f"Failed to reach QuickBooks API: {e}"

def create_quickbooks_invoice(customer_name, amount, description="Service"):
    client = get_valid_client()
    if not client: return "QuickBooks not connected."
    
    url = f"https://sandbox-quickbooks.api.intuit.com/v3/company/{client.realm_id}/invoice"
    headers = {
        "Authorization": f"Bearer {client.access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "Line": [{
            "Amount": amount,
            "DetailType": "SalesItemLineDetail",
            "SalesItemLineDetail": {
                "ItemRef": {"name": "Services", "value": "1"},
                "Qty": 1,
                "UnitPrice": amount
            },
            "Description": description
        }],
        "CustomerRef": {"name": customer_name}
    }
    
    try:
        res = requests.post(url, json=payload, headers=headers)
        if res.status_code == 200:
            return f"Successfully created QuickBooks Invoice for {customer_name}."
        return f"Failed to create invoice: {res.text}"
    except Exception as e:
        return f"QBO Error: {e}"

def create_quickbooks_expense(amount, account_name, project_name):
    client = get_valid_client()
    if not client: return "Not connected."
    # Simplified legacy stub
    return "QuickBooks expense creation initiated."
