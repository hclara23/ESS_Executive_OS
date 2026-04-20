import os
import threading
from contextlib import contextmanager

import psycopg2
from psycopg2 import pool as pg_pool

def _pg_uri():
    return os.getenv("ELIO_PG_URI", "").strip()

def config_status():
    if _pg_uri():
        return "Postgres config is ready."
    return "ELIO_PG_URI is missing."

def _connect():
    uri = _pg_uri()
    if not uri:
        return None
    return psycopg2.connect(uri)

# --- Connection Pool ---
_pool: pg_pool.ThreadedConnectionPool | None = None
_pool_lock = threading.Lock()

def _get_pool() -> pg_pool.ThreadedConnectionPool | None:
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:
                uri = _pg_uri()
                if not uri:
                    return None
                try:
                    _pool = pg_pool.ThreadedConnectionPool(1, 10, uri)
                except Exception as e:
                    print(f"[DB] Connection pool init failed: {e}")
    return _pool

def get_conn():
    p = _get_pool()
    if p is None:
        raise RuntimeError("ELIO_PG_URI is not set or pool unavailable.")
    return p.getconn()

def release_conn(conn):
    p = _get_pool()
    if p and conn:
        try:
            p.putconn(conn)
        except Exception:
            try:
                conn.close()
            except Exception:
                pass

@contextmanager
def db_cursor():
    """Context manager: yields an open cursor, commits on success, rolls back on error, always releases the connection."""
    conn = get_conn()
    cur = None
    try:
        cur = conn.cursor()
        yield cur
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        if cur:
            try:
                cur.close()
            except Exception:
                pass
        release_conn(conn)

def ensure_schema():
    conn = _connect()
    if not conn:
        return False
    cur = None
    try:
        cur = conn.cursor()

        # 0. Enable pgvector
        try:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        except Exception as e:
            print(f"Notice: pgvector extension not enabled ({e}). Semantic search will be limited.")

        # 1. Base Tables
        cur.execute("""
            create table if not exists elio_device_profiles (
                device_id text primary key,
                user_name text not null,
                api_token text,
                updated_at timestamp not null
            );
        """)
        cur.execute("""
            create table if not exists elio_memory_private (
                id bigserial primary key,
                user_name text not null,
                text_body text not null,
                tags text[] not null,
                created_at timestamp not null
            );
        """)
        cur.execute("""
            create table if not exists elio_memory_shared (
                id bigserial primary key,
                from_user text not null,
                to_user text not null,
                text_body text not null,
                created_at timestamp not null
            );
        """)
        cur.execute("""
            create table if not exists elio_lessons_learned (
                id bigserial primary key,
                owner text not null,
                text_body text not null,
                tags text[] not null,
                created_at timestamp not null
            );
        """)
        cur.execute("""
            create table if not exists elio_todos (
                id bigserial primary key,
                user_name text not null,
                text_body text not null,
                done boolean not null default false,
                created_at timestamp not null
            );
        """)
        cur.execute("""
            create table if not exists elio_users (
                user_name text primary key,
                email text,
                password text not null,
                is_admin boolean not null default false,
                created_at timestamp not null
            );
        """)
        cur.execute("""
            create table if not exists elio_email_config (
                id serial primary key,
                user_name text unique references elio_users(user_name),
                email_id text not null,
                email_password text not null,
                smtp_server text,
                smtp_port int,
                imap_server text,
                imap_port int,
                updated_at timestamp not null
            );
        """)
        cur.execute("""
            create table if not exists elio_email_contacts (
                id bigserial primary key,
                email_name text not null,
                email_id text not null,
                created_at timestamp not null
            );
        """)
        cur.execute("""
            create table if not exists elio_audit_logs (
                id bigserial primary key,
                user_name text not null,
                action_type text not null,
                details text,
                created_at timestamp not null
            );
        """)
        cur.execute("""
            create table if not exists elio_second_brain (
                id bigserial primary key,
                user_name text not null,
                fact_key text not null,
                fact_value text not null,
                created_at timestamp not null
            );
        """)
        cur.execute("""
            create table if not exists elio_delegations (
                id bigserial primary key,
                from_user text not null,
                to_user text not null,
                task_description text not null,
                status text default 'pending',
                created_at timestamp not null,
                completed_at timestamp
            );
        """)
        cur.execute("""
            create table if not exists elio_chat_history (
                id bigserial primary key,
                user_name text not null,
                role text not null,
                content text not null,
                created_at timestamp not null,
                reflected boolean default false
            );
        """)
        cur.execute("""
            create table if not exists elio_insights (
                id bigserial primary key,
                user_name text not null,
                category text not null,
                content text not null,
                source_ids bigint[],
                importance int default 1,
                created_at timestamp not null
            );
        """)
        cur.execute("""
            create table if not exists elio_error_logs (
                id bigserial primary key,
                error_message text not null,
                stack_trace text,
                created_at timestamp not null
            );
        """)
        cur.execute("""
            create table if not exists elio_knowledge_base (
                id bigserial primary key,
                file_name text not null,
                content text not null,
                embedding vector(1536),
                metadata jsonb,
                created_at timestamp not null
            );
        """)
        cur.execute("""
            create table if not exists elio_oauth_tokens (
                service_name text primary key,
                access_token text not null,
                refresh_token text not null,
                realm_id text,
                expires_at timestamp not null,
                updated_at timestamp not null
            );
        """)
        cur.execute("""
            create table if not exists elio_processed_emails (
                message_id text primary key,
                subject text,
                sender text,
                received_at timestamp not null,
                summary text,
                status text default 'read',
                created_at timestamp not null
            );
        """)
        cur.execute("""
            create table if not exists elio_user_skills (
                id bigserial primary key,
                skill_name text not null,
                description text,
                code_snippet text,
                status text default 'learned',
                created_at timestamp not null
            );
        """)
        cur.execute("""
            create table if not exists elio_bid_opportunities (
                id bigserial primary key,
                title text not null,
                description text,
                technical_data jsonb,
                draft_proposal text,
                status text default 'pending',
                source_url text,
                project_tag text unique,
                estimated_cost numeric(12,2) default 0,
                markup_percent int default 20,
                created_at timestamp not null
            );
        """)
        cur.execute("""
            create table if not exists elio_bid_documents (
                id bigserial primary key,
                opportunity_id bigint references elio_bid_opportunities(id) on delete cascade,
                file_name text not null,
                gcs_uri text not null,
                created_at timestamp not null
            );
        """)
        cur.execute("""
            create table if not exists elio_vendors (
                id bigserial primary key,
                name text not null,
                email text unique not null,
                w9_url text,
                coi_url text,
                coi_expiry timestamp,
                status text default 'pending',
                created_at timestamp not null
            );
        """)
        cur.execute("""
            create table if not exists elio_bid_quotes (
                id bigserial primary key,
                opportunity_id bigint references elio_bid_opportunities(id) on delete cascade,
                vendor_id bigint references elio_vendors(id),
                item_description text,
                quoted_price numeric(12,2),
                status text default 'pending',
                created_at timestamp not null
            );
        """)
        cur.execute("""
            create table if not exists elio_expenses (
                id bigserial primary key,
                user_name text not null,
                vendor text not null,
                total_amount numeric(12,2) not null,
                tax_amount numeric(12,2),
                category text not null,
                items jsonb,
                receipt_url text,
                project_tag text,
                created_at timestamp not null
            );
        """)
        cur.execute("""
            create table if not exists elio_meetings (
                id bigserial primary key,
                user_name text not null,
                title text,
                audio_url text,
                transcript text,
                action_items jsonb,
                created_at timestamp not null
            );
        """)
        cur.execute("""
            create table if not exists elio_missions (
                id bigserial primary key,
                user_name text not null,
                goal text not null,
                steps jsonb not null,
                status text default 'active',
                current_step int default 0,
                created_at timestamp not null,
                updated_at timestamp not null
            );
        """)
        cur.execute("""
            create table if not exists elio_vector_memory (
                id bigserial primary key,
                user_name text not null,
                content text not null,
                embedding vector(1536),
                metadata jsonb,
                created_at timestamp not null
            );
        """)
        cur.execute("""
            create table if not exists elio_team_notes (
                title text primary key,
                content text not null,
                last_edited_by text not null,
                updated_at timestamp not null
            );
        """)
        cur.execute("""
            create table if not exists elio_mfa_codes (
                id bigserial primary key,
                user_name text not null,
                code text not null,
                expires_at timestamp not null
            );
        """)
        # V3.5 Tables
        cur.execute("""
            create table if not exists elio_custom_workflows (
                id bigserial primary key,
                user_name text not null,
                name text not null,
                trigger_type text not null,
                trigger_config jsonb,
                actions jsonb not null,
                status text default 'active',
                created_at timestamp not null
            );
        """)
        cur.execute("""
            create table if not exists elio_ai_recommendations (
                id bigserial primary key,
                user_name text not null,
                title text not null,
                description text not null,
                category text,
                action_prompt text,
                status text default 'new',
                created_at timestamp not null
            );
        """)
        cur.execute("""
            create table if not exists elio_jobs (
                id bigserial primary key,
                user_name text,
                job_type text not null,
                payload jsonb,
                status text not null default 'queued',
                priority int not null default 100,
                run_at timestamp not null,
                attempts int not null default 0,
                max_attempts int not null default 3,
                last_error text,
                result jsonb,
                locked_at timestamp,
                locked_by text,
                requested_by text,
                created_at timestamp not null,
                updated_at timestamp not null,
                finished_at timestamp
            );
        """)
        cur.execute("create index if not exists idx_elio_jobs_status_run_at on elio_jobs (status, run_at);")
        cur.execute("create index if not exists idx_elio_jobs_user_created on elio_jobs (user_name, created_at desc);")

        # 2. Lightweight migrations for pre-existing databases
        for stmt in [
            "alter table if exists elio_bid_opportunities add column if not exists technical_data jsonb;",
            "alter table if exists elio_bid_opportunities add column if not exists draft_proposal text;",
            "alter table if exists elio_bid_opportunities add column if not exists source_url text;",
            "alter table if exists elio_bid_opportunities add column if not exists project_tag text;",
            "alter table if exists elio_bid_opportunities add column if not exists estimated_cost numeric(12,2) default 0;",
            "alter table if exists elio_bid_opportunities add column if not exists markup_percent int default 20;",
            "alter table if exists elio_expenses add column if not exists tax_amount numeric(12,2);",
            "alter table if exists elio_expenses add column if not exists items jsonb;",
            "alter table if exists elio_expenses add column if not exists receipt_url text;",
            "alter table if exists elio_expenses add column if not exists project_tag text;",
            "alter table if exists elio_custom_workflows add column if not exists trigger_config jsonb;",
            "alter table if exists elio_custom_workflows add column if not exists status text default 'active';",
            "alter table if exists elio_ai_recommendations add column if not exists category text;",
            "alter table if exists elio_ai_recommendations add column if not exists action_prompt text;",
            "alter table if exists elio_ai_recommendations add column if not exists status text default 'new';",
            "alter table if exists elio_jobs add column if not exists result jsonb;",
            "alter table if exists elio_jobs add column if not exists last_error text;",
            "alter table if exists elio_jobs add column if not exists locked_at timestamp;",
            "alter table if exists elio_jobs add column if not exists locked_by text;",
            "alter table if exists elio_jobs add column if not exists finished_at timestamp;",
        ]:
            cur.execute(stmt)

        conn.commit()
        return True
    except Exception as e:
        print(f"[DB] Schema setup failed: {e}")
        try:
            conn.rollback()
        except Exception:
            pass
        return False
    finally:
        if cur:
            try:
                cur.close()
            except Exception:
                pass
        try:
            conn.close()
        except Exception:
            pass

def sync_postgres():
    return "Postgres is ready."

def sync_stub():
    return "Postgres sync is ready. Set ELIO_PG_URI."
