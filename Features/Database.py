from datetime import datetime

from Features.PostgresStore import ensure_schema, db_cursor
from server.security import decrypt_secret, encrypt_secret, hash_password, is_encrypted_secret

_schema_ready = False


def _ready():
    global _schema_ready
    if _schema_ready:
        return True
    _schema_ready = ensure_schema()
    return _schema_ready


def Infodetails(uname):
    if not _ready():
        return "", "", False
    with db_cursor() as cur:
        cur.execute(
            "select user_name, password, is_admin from elio_users where user_name = %s;",
            (uname,),
        )
        row = cur.fetchone()
    return (row[0], row[1], row[2]) if row else ("", "", False)


def Updatepassword(name, password):
    if not _ready():
        return
    with db_cursor() as cur:
        cur.execute(
            "update elio_users set password = %s where user_name = %s;",
            (hash_password(password), name),
        )


def Addnewuser(uname, upassword="1234"):
    if not _ready():
        return
    with db_cursor() as cur:
        cur.execute(
            """
            insert into elio_users (user_name, password, is_admin, created_at)
            values (%s, %s, %s, %s)
            on conflict (user_name) do nothing;
            """,
            (uname, hash_password(upassword), False, datetime.utcnow()),
        )


def Emaildetails():
    if not _ready():
        return "", ""
    with db_cursor() as cur:
        cur.execute("select email_id, email_password from elio_email_config where id = 1;")
        row = cur.fetchone()
    if not row:
        return "", ""
    email_id, stored_password = row
    if stored_password and not is_encrypted_secret(stored_password):
        SetEmailID(email_id, stored_password)
        return email_id, stored_password
    return email_id, decrypt_secret(stored_password)


def SetEmailID(EmailID, Password):
    if not _ready():
        return
    with db_cursor() as cur:
        cur.execute(
            """
            insert into elio_email_config (id, email_id, email_password, updated_at)
            values (1, %s, %s, %s)
            on conflict (id) do update
            set email_id = excluded.email_id,
                email_password = excluded.email_password,
                updated_at = excluded.updated_at;
            """,
            (EmailID, encrypt_secret(Password), datetime.utcnow()),
        )


def Add_email_receiver(ename, emailID):
    if not _ready():
        return
    with db_cursor() as cur:
        cur.execute(
            "insert into elio_email_contacts (email_name, email_id, created_at) values (%s, %s, %s);",
            (ename, emailID, datetime.utcnow()),
        )


def Add_email(ename, emailID):
    Add_email_receiver(ename, emailID)


def Known_email(srch=""):
    if not _ready():
        return "", "", ""
    with db_cursor() as cur:
        cur.execute("select email_name, email_id from elio_email_contacts order by email_name asc;")
        rows = cur.fetchall()
    ename = ""
    eid = ""
    found_id = ""
    for name, email_id in rows:
        ename += f"{name},\n"
        eid += f"{email_id},\n"
        if srch and srch == name:
            found_id = email_id
    return ename.rstrip(",\n"), eid.rstrip(",\n"), found_id
