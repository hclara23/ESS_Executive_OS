import os
from datetime import datetime

from Features.PostgresStore import ensure_schema, db_cursor
from server.security import hash_password, is_password_hash

_schema_ready = False


def _pg_uri():
    return os.getenv("ELIO_PG_URI", "").strip()


def ensure_schema_if_possible():
    if _pg_uri():
        ensure_schema()


def _ready():
    global _schema_ready
    if _schema_ready:
        return True
    _schema_ready = ensure_schema()
    return _schema_ready


def add_private_memory(user: str, text: str, tags: list[str]):
    with db_cursor() as cur:
        cur.execute(
            "insert into elio_memory_private (user_name, text_body, tags, created_at) values (%s, %s, %s, %s);",
            (user, text, tags, datetime.utcnow()),
        )


def add_shared_message(from_user: str, to_user: str, text: str):
    with db_cursor() as cur:
        cur.execute(
            "insert into elio_memory_shared (from_user, to_user, text_body, created_at) values (%s, %s, %s, %s);",
            (from_user, to_user, text, datetime.utcnow()),
        )


def add_lesson(owner: str, text: str, tags: list[str]):
    with db_cursor() as cur:
        cur.execute(
            "insert into elio_lessons_learned (owner, text_body, tags, created_at) values (%s, %s, %s, %s);",
            (owner, text, tags, datetime.utcnow()),
        )


def list_lessons(owner: str, limit: int = 10):
    with db_cursor() as cur:
        cur.execute(
            """
            select text_body, tags, created_at
            from elio_lessons_learned
            where owner = %s
            order by created_at desc
            limit %s;
            """,
            (owner, limit),
        )
        rows = cur.fetchall()
    return [{"text": r[0], "tags": r[1], "created_at": r[2]} for r in rows]


def add_todo(user: str, text: str):
    with db_cursor() as cur:
        cur.execute(
            "insert into elio_todos (user_name, text_body, created_at) values (%s, %s, %s);",
            (user, text, datetime.utcnow()),
        )


def list_todos(user: str, limit: int = 10):
    with db_cursor() as cur:
        cur.execute(
            """
            select user_name, text_body, done, created_at
            from elio_todos
            where user_name = %s
            order by created_at desc
            limit %s;
            """,
            (user, limit),
        )
        rows = cur.fetchall()
    return [{"user": r[0], "text": r[1], "done": r[2], "created_at": r[3]} for r in rows]


def get_shared_messages(user: str, limit: int = 10):
    from Features.MemoryStore import get_shared_messages as _get
    return _get(user, limit)


def verify_device_token(token: str):
    from Features.MemoryStore import verify_device_token as _v
    return _v(token)


def register_device(device_id: str, user_name: str):
    import secrets
    from Features.MemoryStore import set_device_user, set_device_token
    token = f"DEV-{secrets.token_hex(16)}"
    set_device_user(device_id, user_name)
    set_device_token(device_id, token)
    return token


def add_chat_message(user_name: str, role: str, content: str):
    from Features.MemoryStore import add_chat_message as _add
    return _add(user_name, role, content)


def log_audit_action(user: str, action_type: str, details: str):
    with db_cursor() as cur:
        cur.execute(
            "insert into elio_audit_logs (user_name, action_type, details, created_at) values (%s, %s, %s, %s);",
            (user, action_type, details, datetime.utcnow()),
        )


def log_error(message: str, trace: str):
    with db_cursor() as cur:
        cur.execute(
            "insert into elio_error_logs (error_message, stack_trace, created_at) values (%s, %s, %s);",
            (message, trace, datetime.utcnow()),
        )


def get_error_logs(limit: int = 50):
    with db_cursor() as cur:
        cur.execute(
            """
            select id, error_message, stack_trace, created_at
            from elio_error_logs
            order by created_at desc
            limit %s;
            """,
            (limit,),
        )
        rows = cur.fetchall()
    return [{"id": r[0], "message": r[1], "trace": r[2], "created_at": r[3]} for r in rows]


def get_evolution_logs(limit: int = 20):
    with db_cursor() as cur:
        cur.execute(
            """
            select details, created_at
            from elio_audit_logs
            where action_type = 'self_audit'
            order by created_at desc
            limit %s;
            """,
            (limit,),
        )
        rows = cur.fetchall()
    return [{"details": r[0], "created_at": r[1]} for r in rows]


def list_user_skills(limit: int = 20):
    with db_cursor() as cur:
        cur.execute(
            """
            select skill_name, description, status, created_at
            from elio_user_skills
            order by created_at desc
            limit %s;
            """,
            (limit,),
        )
        rows = cur.fetchall()
    return [{"name": r[0], "description": r[1], "status": r[2], "created_at": r[3]} for r in rows]


def get_user(identifier: str):
    with db_cursor() as cur:
        cur.execute(
            "select user_name, password, is_admin, email from elio_users where user_name = %s or email = %s",
            (identifier.lower(), identifier.lower()),
        )
        row = cur.fetchone()
    if not row:
        return None
    return {"username": row[0], "password": row[1], "is_admin": row[2], "email": row[3]}


def create_user(user_name: str, password_plain: str, is_admin: bool = False, email: str = None):
    stored_password = password_plain if is_password_hash(password_plain) else hash_password(password_plain)
    with db_cursor() as cur:
        cur.execute(
            """
            insert into elio_users (user_name, password, is_admin, email, created_at)
            values (%s, %s, %s, %s, %s)
            on conflict (user_name) do update
            set password = excluded.password,
                is_admin = excluded.is_admin,
                email = excluded.email;
            """,
            (user_name.lower(), stored_password, is_admin, email.lower() if email else None, datetime.utcnow()),
        )


def consume_mfa_code(user_name: str, code: str) -> bool:
    with db_cursor() as cur:
        cur.execute(
            "select id from elio_mfa_codes where user_name = %s and code = %s and expires_at > %s",
            (user_name, code, datetime.utcnow()),
        )
        row = cur.fetchone()
        if not row:
            return False
        cur.execute("delete from elio_mfa_codes where id = %s", (row[0],))
    return True


def get_email_config(user_name: str):
    with db_cursor() as cur:
        cur.execute(
            "select email_id, email_password, smtp_server, smtp_port, imap_server, imap_port from elio_email_config where user_name = %s",
            (user_name.lower(),),
        )
        row = cur.fetchone()
    if not row:
        return None
    return {
        "email": row[0],
        "password": row[1],
        "smtp_server": row[2],
        "smtp_port": row[3],
        "imap_server": row[4],
        "imap_port": row[5],
    }


def set_email_config(user_name: str, config: dict):
    with db_cursor() as cur:
        cur.execute(
            """
            insert into elio_email_config (user_name, email_id, email_password, smtp_server, smtp_port, imap_server, imap_port, updated_at)
            values (%s, %s, %s, %s, %s, %s, %s, %s)
            on conflict (user_name) do update
            set email_id = excluded.email_id,
                email_password = excluded.email_password,
                smtp_server = excluded.smtp_server,
                smtp_port = excluded.smtp_port,
                imap_server = excluded.imap_server,
                imap_port = excluded.imap_port,
                updated_at = excluded.updated_at;
            """,
            (
                user_name.lower(),
                config["email"],
                config["password"],
                config.get("smtp_server"),
                config.get("smtp_port"),
                config.get("imap_server"),
                config.get("imap_port"),
                datetime.utcnow(),
            ),
        )


def delete_email_config(user_name: str):
    with db_cursor() as cur:
        cur.execute("delete from elio_email_config where user_name = %s", (user_name.lower(),))


def is_email_processed(message_id: str) -> bool:
    with db_cursor() as cur:
        cur.execute("select 1 from elio_processed_emails where message_id = %s", (message_id,))
        row = cur.fetchone()
    return row is not None


def mark_email_processed(message_id: str, subject: str, sender: str, summary: str = None, status: str = "read"):
    with db_cursor() as cur:
        cur.execute(
            """
            insert into elio_processed_emails (message_id, subject, sender, summary, status, received_at, created_at)
            values (%s, %s, %s, %s, %s, %s, %s)
            on conflict (message_id) do update
            set summary = excluded.summary,
                status = excluded.status;
            """,
            (message_id, subject, sender, summary, status, datetime.utcnow(), datetime.utcnow()),
        )


def list_recent_emails(limit: int = 50):
    with db_cursor() as cur:
        cur.execute(
            """
            select message_id, subject, sender, received_at, summary, status
            from elio_processed_emails
            order by received_at desc
            limit %s
            """,
            (limit,),
        )
        rows = cur.fetchall()
    return [
        {"id": r[0], "subject": r[1], "sender": r[2], "received_at": r[3], "summary": r[4], "status": r[5]}
        for r in rows
    ]
