import os
import psycopg2
from datetime import datetime

def _pg_conn():
    uri = os.getenv("ELIO_PG_URI", "").strip()
    return psycopg2.connect(uri)

def save_team_note(title, content, user_name):
    conn = _pg_conn()
    cur = conn.cursor()
    cur.execute(
        """
        insert into elio_team_notes (title, content, last_edited_by, updated_at)
        values (%s, %s, %s, %s)
        on conflict (title) do update
        set content = excluded.content,
            last_edited_by = excluded.last_edited_by,
            updated_at = excluded.updated_at;
        """,
        (title, content, user_name, datetime.utcnow())
    )
    conn.commit()
    cur.close()
    conn.close()

def get_team_notes():
    conn = _pg_conn()
    cur = conn.cursor()
    cur.execute("select title, content, last_edited_by, updated_at from elio_team_notes order by updated_at desc")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"title": r[0], "content": r[1], "author": r[2], "date": r[3]} for r in rows]
