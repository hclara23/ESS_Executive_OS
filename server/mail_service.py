import smtplib
import ssl
import os
import imaplib
import email
from email.message import EmailMessage
from email.utils import parseaddr
from typing import Optional, List, Dict
from server.store import _pg_conn

class MailService:
    def __init__(self):
        # Default ELIO system settings from env
        self.system_email = os.getenv("ELIO_MAIL_ADDRESS", "elio@electricsupplysource.co")
        self.system_password = os.getenv("ELIO_MAIL_PASSWORD", "Elio@ESS")
        self.system_smtp_server = os.getenv("ELIO_MAIL_SMTP_SERVER", "mail.electricsupplysource.co")
        self.system_smtp_port = int(os.getenv("ELIO_MAIL_SMTP_PORT", "465"))
        self.system_imap_server = os.getenv("ELIO_MAIL_IMAP_SERVER", "mail.electricsupplysource.co")
        self.system_imap_port = int(os.getenv("ELIO_MAIL_IMAP_PORT", "993"))

    def _get_config_for_user(self, user_name: Optional[str] = None):
        """
        Retrieves SMTP/IMAP config from DB for a specific user.
        """
        if not user_name:
            return {
                "email": self.system_email,
                "password": self.system_password,
                "smtp_server": self.system_smtp_server,
                "smtp_port": self.system_smtp_port,
                "imap_server": self.system_imap_server,
                "imap_port": self.system_imap_port
            }

        conn = _pg_conn()
        cur = conn.cursor()
        try:
            cur.execute(
                "SELECT email_id, email_password, smtp_server, smtp_port, imap_server, imap_port FROM elio_email_config WHERE user_name = %s",
                (user_name.lower(),)
            )
            row = cur.fetchone()
            if row:
                return {
                    "email": row[0],
                    "password": row[1],
                    "smtp_server": row[2] or self.system_smtp_server,
                    "smtp_port": int(row[3]) if row[3] else self.system_smtp_port,
                    "imap_server": row[4] or self.system_imap_server,
                    "imap_port": int(row[5]) if row[5] else self.system_imap_port
                }
        finally:
            cur.close()
            conn.close()
        
        return self._get_config_for_user(None)

    def send_email(self, 
                   to_email: str, 
                   subject: str, 
                   body: str, 
                   from_user: Optional[str] = None,
                   is_html: bool = False):
        config = self._get_config_for_user(from_user)
        
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = config['email']
        msg['To'] = to_email
        
        if is_html:
            msg.add_alternative(body, subtype='html')
        else:
            msg.set_content(body)

        context = ssl.create_default_context()
        try:
            # 1. Try SSL (Port 465)
            with smtplib.SMTP_SSL(config['smtp_server'], 465, context=context, timeout=10) as server:
                server.login(config['email'], config['password'])
                server.send_message(msg)
            return {"status": "success", "message": f"Email sent via Port 465"}
        except Exception as e465:
            try:
                # 2. Try STARTTLS (Port 587)
                with smtplib.SMTP(config['smtp_server'], 587, timeout=10) as server:
                    server.starttls(context=context)
                    server.login(config['email'], config['password'])
                    server.send_message(msg)
                return {"status": "success", "message": f"Email sent via Port 587"}
            except Exception as e587:
                return {"status": "error", "message": f"SSL Error: {e465} | STARTTLS Error: {e587}"}

    def fetch_emails(self, user_name: Optional[str] = None, folder: str = "INBOX", limit: int = 10) -> List[Dict]:
        """
        Fetches recent emails via IMAP.
        """
        config = self._get_config_for_user(user_name)
        emails = []
        
        try:
            mail = imaplib.IMAP4_SSL(config['imap_server'], config['imap_port'])
            mail.login(config['email'], config['password'])
            mail.select(folder)
            
            # Search for all emails in the folder
            status, messages = mail.search(None, "ALL")
            if status != "OK":
                return []

            # Get the list of message IDs
            msg_ids = messages[0].split()
            # Take only the last 'limit' messages
            msg_ids = msg_ids[-limit:]
            # Reverse to get newest first
            msg_ids.reverse()

            for msg_id in msg_ids:
                status, data = mail.fetch(msg_id, "(RFC822)")
                if status != "OK":
                    continue
                
                raw_email = data[0][1]
                msg = email.message_from_bytes(raw_email)
                
                # Extract details
                subject = msg.get("Subject", "(No Subject)")
                sender = msg.get("From", "(Unknown Sender)")
                date = msg.get("Date", "")
                message_id = msg.get("Message-ID", f"local-{msg_id.decode()}")
                
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            try:
                                body = part.get_payload(decode=True).decode()
                            except:
                                body = part.get_payload()
                            break
                else:
                    try:
                        body = msg.get_payload(decode=True).decode()
                    except:
                        body = msg.get_payload()

                emails.append({
                    "id": message_id,
                    "subject": subject,
                    "from": sender,
                    "date": date,
                    "body": body[:500] if body else "", # Snip for summary
                    "folder": folder
                })
                
            mail.logout()
        except Exception as e:
            print(f">> IMAP Error: {e}")
            return []
            
        return emails

mail_service = MailService()
