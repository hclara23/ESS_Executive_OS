import argparse
from datetime import datetime
import os

import psycopg2
from dotenv import load_dotenv

from server.security import encrypt_secret
from server.store import create_user

def _pg_uri():
    return os.getenv("ELIO_PG_URI", "").strip()


def _pg_conn():
    uri = _pg_uri()
    if not uri:
        raise RuntimeError("ELIO_PG_URI is not set.")
    return psycopg2.connect(uri)


def seed_admin(username: str, password: str):
    create_user(username, password, is_admin=True)


def seed_email(email_id: str, email_password: str):
    conn = _pg_conn()
    cur = conn.cursor()
    cur.execute(
        """
        insert into elio_email_config (id, email_id, email_password, updated_at)
        values (1, %s, %s, %s)
        on conflict (id) do update
        set email_id = excluded.email_id,
            email_password = excluded.email_password,
            updated_at = excluded.updated_at;
        """,
        (email_id, encrypt_secret(email_password), datetime.utcnow()),
    )
    conn.commit()
    cur.close()
    conn.close()


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description="Seed admin user and email config.")
    parser.add_argument("--admin-user", required=False, help="Admin username")
    parser.add_argument("--admin-pass", required=False, help="Admin password")
    parser.add_argument("--email-id", required=False, help="Sender email address")
    parser.add_argument("--email-pass", required=False, help="Sender email app password")
    args = parser.parse_args()

    admin_user = args.admin_user or os.getenv("ELIO_ADMIN_USER", "").strip()
    admin_pass = args.admin_pass or os.getenv("ELIO_ADMIN_PASS", "").strip()
    email_id = args.email_id or os.getenv("ELIO_EMAIL_ID", "").strip()
    email_pass = args.email_pass or os.getenv("ELIO_EMAIL_PASS", "").strip()

    if not admin_user or not admin_pass:
        raise SystemExit("Missing admin credentials. Set args or ELIO_ADMIN_USER/ELIO_ADMIN_PASS.")

    seed_admin(admin_user, admin_pass)

    if email_id and email_pass:
        seed_email(email_id, email_pass)

    print("Seed complete.")


if __name__ == "__main__":
    main()
