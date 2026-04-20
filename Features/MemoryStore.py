from datetime import datetime

from Features.PostgresStore import ensure_schema, db_cursor

_schema_ready = False


def _ready():
    global _schema_ready
    if _schema_ready:
        return True
    _schema_ready = ensure_schema()
    return _schema_ready


def get_device_user(device_id: str):
    if not device_id or not _ready():
        return None
    with db_cursor() as cur:
        cur.execute(
            "select user_name from elio_device_profiles where device_id = %s;",
            (device_id,),
        )
        row = cur.fetchone()
    return row[0] if row else None


def set_device_user(device_id: str, user: str):
    if not device_id or not user or not _ready():
        return
    with db_cursor() as cur:
        cur.execute(
            """
            insert into elio_device_profiles (device_id, user_name, updated_at)
            values (%s, %s, %s)
            on conflict (device_id) do update
            set user_name = excluded.user_name,
                updated_at = excluded.updated_at;
            """,
            (device_id, user, datetime.utcnow()),
        )


def set_device_token(device_id: str, token: str):
    if not device_id or not token or not _ready():
        return
    with db_cursor() as cur:
        cur.execute(
            """
            update elio_device_profiles
            set api_token = %s, updated_at = %s
            where device_id = %s;
            """,
            (token, datetime.utcnow(), device_id),
        )


def verify_device_token(token: str):
    if not token or not _ready():
        return None
    with db_cursor() as cur:
        cur.execute(
            "select user_name, device_id from elio_device_profiles where api_token = %s;",
            (token,),
        )
        row = cur.fetchone()
    return {"user": row[0], "device": row[1]} if row else None


def add_private_memory(user: str, text: str, tags=None):
    if not _ready():
        return
    with db_cursor() as cur:
        cur.execute(
            "insert into elio_memory_private (user_name, text_body, tags, created_at) values (%s, %s, %s, %s);",
            (user, text, tags or [], datetime.utcnow()),
        )


def add_shared_message(from_user: str, to_user: str, text: str):
    if not _ready():
        return
    with db_cursor() as cur:
        cur.execute(
            "insert into elio_memory_shared (from_user, to_user, text_body, created_at) values (%s, %s, %s, %s);",
            (from_user, to_user, text, datetime.utcnow()),
        )


def get_shared_messages(for_user: str, limit: int = 5):
    if not _ready():
        return []
    with db_cursor() as cur:
        cur.execute(
            """
            select from_user, to_user, text_body, created_at
            from elio_memory_shared
            where to_user = %s
            order by created_at desc
            limit %s;
            """,
            (for_user, limit),
        )
        rows = cur.fetchall()
    return [{"from_user": r[0], "to_user": r[1], "text": r[2], "created_at": r[3]} for r in rows]


def add_lesson(owner: str, text: str, tags=None):
    if not _ready():
        return
    with db_cursor() as cur:
        cur.execute(
            "insert into elio_lessons_learned (owner, text_body, tags, created_at) values (%s, %s, %s, %s);",
            (owner, text, tags or [], datetime.utcnow()),
        )


def list_lessons(owner: str, limit: int = 5):
    if not _ready():
        return []
    with db_cursor() as cur:
        cur.execute(
            """
            select owner, text_body, tags, created_at
            from elio_lessons_learned
            where owner = %s
            order by created_at desc
            limit %s;
            """,
            (owner, limit),
        )
        rows = cur.fetchall()
    return [{"owner": r[0], "text": r[1], "tags": r[2], "created_at": r[3]} for r in rows]


def add_todo(user: str, text: str):
    if not _ready():
        return
    with db_cursor() as cur:
        cur.execute(
            "insert into elio_todos (user_name, text_body, done, created_at) values (%s, %s, %s, %s);",
            (user, text, False, datetime.utcnow()),
        )


def list_todos(user: str, limit: int = 10):
    if not _ready():
        return []
    with db_cursor() as cur:
        cur.execute(
            """
            select user_name, text_body, done, created_at
            from elio_todos
            where user_name = %s and done = false
            order by created_at desc
            limit %s;
            """,
            (user, limit),
        )
        rows = cur.fetchall()
    return [{"user": r[0], "text": r[1], "done": r[2], "created_at": r[3]} for r in rows]


def log_audit_action(user: str, action: str, details: str):
    if not _ready():
        return
    with db_cursor() as cur:
        cur.execute(
            "insert into elio_audit_logs (user_name, action_type, details, created_at) values (%s, %s, %s, %s);",
            (user, action, details, datetime.utcnow()),
        )


def save_second_brain_fact(user: str, key: str, value: str):
    if not _ready():
        return
    with db_cursor() as cur:
        cur.execute(
            "insert into elio_second_brain (user_name, fact_key, fact_value, created_at) values (%s, %s, %s, %s);",
            (user, key, value, datetime.utcnow()),
        )


def get_second_brain_facts(user: str):
    if not _ready():
        return []
    with db_cursor() as cur:
        cur.execute(
            "select fact_key, fact_value from elio_second_brain where user_name = %s",
            (user,),
        )
        rows = cur.fetchall()
    return [{"key": r[0], "value": r[1]} for r in rows]


def add_delegation(from_user: str, to_user: str, task: str):
    if not _ready():
        return
    with db_cursor() as cur:
        cur.execute(
            "insert into elio_delegations (from_user, to_user, task_description, created_at) values (%s, %s, %s, %s);",
            (from_user, to_user, task, datetime.utcnow()),
        )


def get_pending_delegations(to_user: str):
    if not _ready():
        return []
    with db_cursor() as cur:
        cur.execute(
            "select id, from_user, task_description, created_at from elio_delegations where to_user = %s and status = 'pending'",
            (to_user,),
        )
        rows = cur.fetchall()
    return [{"id": r[0], "from": r[1], "task": r[2], "created_at": r[3]} for r in rows]


def complete_delegation(delegation_id: int):
    if not _ready():
        return
    with db_cursor() as cur:
        cur.execute(
            "update elio_delegations set status = 'completed', completed_at = %s where id = %s",
            (datetime.utcnow(), delegation_id),
        )


def add_chat_message(user_name: str, role: str, content: str):
    if not _ready():
        return
    with db_cursor() as cur:
        cur.execute(
            "insert into elio_chat_history (user_name, role, content, created_at) values (%s, %s, %s, %s);",
            (user_name, role, content, datetime.utcnow()),
        )


def get_chat_history(user_name: str, limit: int = 20):
    if not _ready():
        return []
    with db_cursor() as cur:
        cur.execute(
            """
            select role, content, created_at
            from elio_chat_history
            where user_name = %s
            order by created_at desc
            limit %s;
            """,
            (user_name, limit),
        )
        rows = cur.fetchall()
    history = [{"role": r[0], "content": r[1], "created_at": r[2]} for r in rows]
    history.reverse()
    return history
