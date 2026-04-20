import os
import imaplib
import email
from email.header import decode_header
from datetime import datetime
import psycopg2
import smtplib
from email.message import EmailMessage
from Features.MSGraphAPI import send_outlook_email, draft_outlook_email, get_access_token
import requests

def _pg_conn():
    uri = os.getenv("ELIO_PG_URI", "").strip()
    return psycopg2.connect(uri)

def is_email_processed(message_id):
    conn = _pg_conn()
    cur = conn.cursor()
    cur.execute("select 1 from elio_processed_emails where message_id = %s", (message_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row is not None

def mark_email_processed(message_id, subject, sender, received_at, summary=None):
    conn = _pg_conn()
    cur = conn.cursor()
    cur.execute(
        """
        insert into elio_processed_emails (message_id, subject, sender, received_at, summary, status, created_at)
        values (%s, %s, %s, %s, %s, %s, %s)
        on conflict (message_id) do nothing;
        """,
        (message_id, subject, sender, received_at, summary, "read", datetime.utcnow())
    )
    conn.commit()
    cur.close()
class ElioEmailManager:
    def __init__(self):
        self.provider = os.getenv("ELIO_EMAIL_PROVIDER", "gmail").lower()
        self.imap_server = os.getenv("ELIO_EMAIL_IMAP_SERVER", "imap.gmail.com")
        self.smtp_server = os.getenv("ELIO_EMAIL_SMTP_SERVER", "smtp.gmail.com")
        self.email_user = os.getenv("ELIO_EMAIL_ID")
        self.email_pass = os.getenv("ELIO_EMAIL_PASS")

    def fetch_unread_emails(self, limit=5):
        if self.provider == "outlook":
            return self._fetch_outlook_emails(limit)
        
        if not self.email_user or not self.email_pass:
            return []

        try:
            mail = imaplib.IMAP4_SSL(self.imap_server)
            mail.login(self.email_user, self.email_pass)
            mail.select("inbox")

            status, messages = mail.search(None, 'UNSEEN')
            if status != 'OK':
                return []

            email_ids = messages[0].split()
            # Process latest first
            email_ids.reverse()
            
            results = []
            for e_id in email_ids[:limit]:
                status, data = mail.fetch(e_id, "(RFC822)")
                if status != 'OK': continue
                
                raw_email = data[0][1]
                msg = email.message_from_bytes(raw_email)
                
                m_id = msg.get("Message-ID")
                if is_email_processed(m_id):
                    continue

                subject, encoding = decode_header(msg.get("Subject"))[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding if encoding else "utf-8")
                
                sender = msg.get("From")
                date_str = msg.get("Date")
                
                # Basic body extraction
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode()
                            break
                else:
                    body = msg.get_payload(decode=True).decode()

                results.append({
                    "id": m_id,
                    "subject": subject,
                    "sender": sender,
                    "body": body,
                    "date": date_str
                })
                
                # Mark as seen in DB
                mark_email_processed(m_id, subject, sender, datetime.utcnow())

            mail.logout()
            return results
        except Exception as e:
            print(f"Email fetch error: {e}")
            return []

    def send_elio_email(self, to_email, subject, body):
        if self.provider == "outlook":
            return send_outlook_email(to_email, subject, body)

        if not self.email_user or not self.email_pass:
            return False

        msg = EmailMessage()
        msg.set_content(body)
        msg['Subject'] = subject
        msg['From'] = self.email_user
        msg['To'] = to_email

        try:
            with smtplib.SMTP_SSL(self.smtp_server, 465) as smtp:
                smtp.login(self.email_user, self.email_pass)
                smtp.send_message(msg)
            return True
        except Exception as e:
            print(f"Email send error: {e}")
            return False

    def _fetch_outlook_emails(self, limit=5):
        token = get_access_token()
        if not token: return []
        
        endpoint = f"https://graph.microsoft.com/v1.0/me/mailFolders/inbox/messages?$filter=isRead eq false&$top={limit}"
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            response = requests.get(endpoint, headers=headers)
            messages = response.json().get("value", [])
            results = []
            for msg in messages:
                m_id = msg.get("id")
                if is_email_processed(m_id): continue
                
                results.append({
                    "id": m_id,
                    "subject": msg.get("subject"),
                    "sender": msg.get("from", {}).get("emailAddress", {}).get("address"),
                    "body": msg.get("body", {}).get("content"),
                    "date": msg.get("receivedDateTime")
                })
                mark_email_processed(m_id, msg.get("subject"), results[-1]["sender"], results[-1]["date"])
            return results
        except Exception as e:
            print(f"Outlook fetch error: {e}")
            return []
