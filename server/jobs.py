import datetime
import json
import os
import socket
from typing import Any

from server.store import _pg_conn, log_error


JOB_DEFINITIONS = {
    "dream_cycle": {
        "description": "Reflect on recent chats and save insights.",
        "admin_only": False,
        "default_priority": 70,
    },
    "workflow_eval": {
        "description": "Evaluate active custom workflows.",
        "admin_only": False,
        "default_priority": 80,
    },
    "recommendations": {
        "description": "Generate proactive dashboard recommendations.",
        "admin_only": False,
        "default_priority": 90,
    },
    "bidding_scout": {
        "description": "Scan for new bid opportunities during business hours.",
        "admin_only": True,
        "default_priority": 95,
    },
    "self_audit": {
        "description": "Run the Elio self-audit and evolution cycle.",
        "admin_only": True,
        "default_priority": 110,
    },
}

RECURRING_JOBS = {
    "workflow_eval": {"interval_seconds": 15 * 60, "admin_only": False},
    "recommendations": {"interval_seconds": 30 * 60, "admin_only": False},
    "dream_cycle": {"interval_seconds": 30 * 60, "admin_only": False},
    "bidding_scout": {"interval_seconds": 30 * 60, "admin_only": True, "business_hours_only": True},
    "self_audit": {"interval_seconds": 24 * 60 * 60, "admin_only": True},
}


def _now() -> datetime.datetime:
    return datetime.datetime.utcnow()


def _normalize_job_type(job_type: str) -> str:
    normalized = (job_type or "").strip().lower().replace("-", "_")
    if normalized not in JOB_DEFINITIONS:
        raise ValueError(f"Unsupported job type: {job_type}")
    return normalized


def list_job_types():
    items = []
    for job_type, meta in JOB_DEFINITIONS.items():
        cadence = RECURRING_JOBS.get(job_type, {})
        items.append(
            {
                "job_type": job_type,
                "description": meta["description"],
                "admin_only": meta["admin_only"],
                "default_priority": meta["default_priority"],
                "recurring": bool(cadence),
                "interval_seconds": cadence.get("interval_seconds"),
            }
        )
    return items


def enqueue_job(
    job_type: str,
    *,
    user_name: str | None = None,
    payload: dict[str, Any] | None = None,
    run_at: datetime.datetime | None = None,
    requested_by: str | None = None,
    priority: int | None = None,
    max_attempts: int = 3,
):
    normalized = _normalize_job_type(job_type)
    run_at = run_at or _now()
    priority = int(priority if priority is not None else JOB_DEFINITIONS[normalized]["default_priority"])
    payload = payload or {}
    conn = _pg_conn()
    cur = conn.cursor()
    cur.execute(
        """
        insert into elio_jobs (
            user_name, job_type, payload, status, priority, run_at, attempts,
            max_attempts, requested_by, created_at, updated_at
        )
        values (%s, %s, %s, 'queued', %s, %s, 0, %s, %s, %s, %s)
        returning id, user_name, job_type, status, priority, run_at, attempts, max_attempts, requested_by, created_at, updated_at;
        """,
        (
            user_name.lower() if user_name else None,
            normalized,
            json.dumps(payload),
            priority,
            run_at,
            max_attempts,
            requested_by.lower() if requested_by else None,
            _now(),
            _now(),
        ),
    )
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return _job_row_to_dict(row)


def _job_row_to_dict(row):
    return {
        "id": row[0],
        "user_name": row[1],
        "job_type": row[2],
        "status": row[3],
        "priority": row[4],
        "run_at": row[5],
        "attempts": row[6],
        "max_attempts": row[7],
        "requested_by": row[8],
        "created_at": row[9],
        "updated_at": row[10],
    }


def list_jobs(*, user_name: str | None = None, statuses: list[str] | None = None, limit: int = 50):
    conn = _pg_conn()
    cur = conn.cursor()
    clauses = []
    params: list[Any] = []
    if user_name:
        clauses.append("user_name = %s")
        params.append(user_name.lower())
    if statuses:
        clauses.append("status = any(%s)")
        params.append(statuses)
    where_clause = f"where {' and '.join(clauses)}" if clauses else ""
    params.append(limit)
    cur.execute(
        f"""
        select id, user_name, job_type, status, priority, run_at, attempts, max_attempts, requested_by, created_at, updated_at,
               last_error, result, finished_at
        from elio_jobs
        {where_clause}
        order by created_at desc
        limit %s
        """,
        params,
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        {
            **_job_row_to_dict(row),
            "last_error": row[11],
            "result": row[12],
            "finished_at": row[13],
        }
        for row in rows
    ]


def get_job_queue_summary():
    conn = _pg_conn()
    cur = conn.cursor()
    cur.execute(
        """
        select status, count(*)
        from elio_jobs
        group by status
        """
    )
    counts = {row[0]: row[1] for row in cur.fetchall()}
    cur.execute(
        """
        select job_type, max(created_at)
        from elio_jobs
        group by job_type
        """
    )
    latest = {row[0]: row[1] for row in cur.fetchall()}
    cur.close()
    conn.close()
    return {"counts": counts, "latest_seen": latest}


def retry_job(job_id: int):
    conn = _pg_conn()
    cur = conn.cursor()
    cur.execute(
        """
        update elio_jobs
        set status = 'queued',
            run_at = %s,
            attempts = 0,
            last_error = null,
            result = null,
            locked_at = null,
            locked_by = null,
            finished_at = null,
            updated_at = %s
        where id = %s
        returning id
        """,
        (_now(), _now(), job_id),
    )
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return bool(row)


def _claim_due_jobs(worker_id: str, limit: int = 5):
    conn = _pg_conn()
    cur = conn.cursor()
    cur.execute(
        """
        with candidates as (
            select id
            from elio_jobs
            where status = 'queued' and run_at <= %s
            order by priority desc, run_at asc, created_at asc
            limit %s
            for update skip locked
        )
        update elio_jobs as jobs
        set status = 'running',
            locked_at = %s,
            locked_by = %s,
            attempts = jobs.attempts + 1,
            updated_at = %s
        from candidates
        where jobs.id = candidates.id
        returning jobs.id, jobs.user_name, jobs.job_type, jobs.payload, jobs.status, jobs.priority,
                  jobs.run_at, jobs.attempts, jobs.max_attempts, jobs.requested_by, jobs.created_at, jobs.updated_at;
        """,
        (_now(), limit, _now(), worker_id, _now()),
    )
    rows = cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()
    return [
        {
            "id": row[0],
            "user_name": row[1],
            "job_type": row[2],
            "payload": row[3] or {},
            "status": row[4],
            "priority": row[5],
            "run_at": row[6],
            "attempts": row[7],
            "max_attempts": row[8],
            "requested_by": row[9],
            "created_at": row[10],
            "updated_at": row[11],
        }
        for row in rows
    ]


def _complete_job(job_id: int, result: Any):
    conn = _pg_conn()
    cur = conn.cursor()
    cur.execute(
        """
        update elio_jobs
        set status = 'completed',
            result = %s,
            last_error = null,
            finished_at = %s,
            updated_at = %s,
            locked_at = null,
            locked_by = null
        where id = %s
        """,
        (json.dumps(result), _now(), _now(), job_id),
    )
    conn.commit()
    cur.close()
    conn.close()


def _fail_job(job: dict[str, Any], error_message: str):
    should_retry = job["attempts"] < job["max_attempts"]
    next_run = _now() + datetime.timedelta(seconds=min(300, 30 * job["attempts"]))
    conn = _pg_conn()
    cur = conn.cursor()
    cur.execute(
        """
        update elio_jobs
        set status = %s,
            last_error = %s,
            run_at = %s,
            updated_at = %s,
            finished_at = %s,
            locked_at = null,
            locked_by = null
        where id = %s
        """,
        (
            "queued" if should_retry else "failed",
            error_message[:4000],
            next_run if should_retry else job["run_at"],
            _now(),
            None if should_retry else _now(),
            job["id"],
        ),
    )
    conn.commit()
    cur.close()
    conn.close()


def _execute_job(job: dict[str, Any]):
    job_type = job["job_type"]
    if job_type == "dream_cycle":
        from Features.MemoryRefiner import run_dream_cycle

        return {"message": run_dream_cycle()}
    if job_type == "workflow_eval":
        from Features.WorkflowEngine import evaluate_custom_workflows

        return {"message": evaluate_custom_workflows()}
    if job_type == "recommendations":
        from Features.RecommendationEngine import generate_proactive_recommendations

        return {"message": generate_proactive_recommendations()}
    if job_type == "bidding_scout":
        from Features.BiddingHub import find_new_opportunities

        return {"message": find_new_opportunities()}
    if job_type == "self_audit":
        from Features.SelfEvolution import run_self_audit

        return {"message": run_self_audit()}
    raise RuntimeError(f"Unsupported job type: {job_type}")


def process_due_jobs(worker_id: str | None = None, limit: int = 5):
    worker_id = worker_id or f"{socket.gethostname()}-{os.getpid()}"
    processed = 0
    for job in _claim_due_jobs(worker_id, limit=limit):
        try:
            result = _execute_job(job)
            _complete_job(job["id"], result)
        except Exception as exc:
            error_text = str(exc)
            log_error(f"Job {job['job_type']} failed", error_text)
            _fail_job(job, error_text)
        processed += 1
    return processed


def _latest_job_times():
    conn = _pg_conn()
    cur = conn.cursor()
    cur.execute(
        """
        select job_type, max(created_at)
        from elio_jobs
        where status in ('queued', 'running', 'completed')
        group by job_type
        """
    )
    data = {row[0]: row[1] for row in cur.fetchall()}
    cur.close()
    conn.close()
    return data


def schedule_recurring_jobs(now_dt: datetime.datetime | None = None):
    now_dt = now_dt or _now()
    existing = _latest_job_times()
    created = []
    for job_type, meta in RECURRING_JOBS.items():
        if meta.get("business_hours_only"):
            local_now = datetime.datetime.now()
            if local_now.weekday() >= 5 or not (5 <= local_now.hour < 20):
                continue
        last_seen = existing.get(job_type)
        if last_seen and (now_dt - last_seen).total_seconds() < meta["interval_seconds"]:
            continue
        created.append(
            enqueue_job(
                job_type,
                requested_by="system",
                priority=JOB_DEFINITIONS[job_type]["default_priority"],
                max_attempts=3,
            )
        )
    return created
