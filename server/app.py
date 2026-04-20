import os
import io
import json
import datetime
import traceback
import shutil
import time
import threading
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Header, HTTPException, File, UploadFile, Request, Depends
import httpx
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import jwt

from server.store import (
    add_private_memory,
    add_shared_message,
    add_lesson,
    list_lessons,
    add_todo,
    list_todos,
    log_audit_action,
    log_error,
    get_error_logs,
    get_evolution_logs,
    get_user,
    create_user,
    verify_device_token,
    register_device,
    add_chat_message,
    get_shared_messages,
    ensure_schema_if_possible,
    list_user_skills,
    consume_mfa_code,
)
from Features.MemoryStore import get_chat_history
from Brain.AI_Brain import ReplyBrain
from server.ai_provider import get_runtime_settings
from server.jobs import (
    enqueue_job,
    get_job_queue_summary,
    list_job_types,
    list_jobs,
    process_due_jobs,
    retry_job,
    schedule_recurring_jobs,
)
from server.personality import get_personality_summary
from server.security import (
    get_jwt_secret,
    needs_password_upgrade,
    resolve_child_path,
    sanitize_upload_name,
    verify_password,
)
from server.voice_provider import get_tts_runtime, synthesize_wav, tts_ready, warm_tts_engine

# --- Auth Configuration ---
JWT_ALGORITHM = "HS256"
security = HTTPBearer()
BASE_DIR = Path(__file__).resolve().parents[1]
PUBLIC_DIR = BASE_DIR / "public"
REPORTS_DIR = BASE_DIR / "reports"
SEO_API_URL = os.getenv("SEO_API_URL", "http://ess_api:8000")
N8N_URL = os.getenv("N8N_URL", "http://ess_n8n:5678")


def _allowed_origins():
    configured = os.getenv("ELIO_ALLOWED_ORIGINS", "").strip()
    if configured:
        return [origin.strip() for origin in configured.split(",") if origin.strip()]
    return [
        "https://app.electricsupplysource.co",
        "https://electricsupplysource.co",
        "https://www.electricsupplysource.co",
        "http://localhost",
        "http://localhost:8000",
        "http://localhost:8001",
        "http://localhost:8080",
        "http://127.0.0.1",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8001",
        "http://127.0.0.1:8080",
    ]


@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_schema_if_possible()
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    get_jwt_secret()
    if os.getenv("ELIO_PREWARM_TTS", "true").strip().lower() in {"1", "true", "yes", "on"}:
        try:
            warm_tts_engine()
        except Exception:
            pass
    if os.getenv("ELIO_RUN_BACKGROUND_WORKER", "true").strip().lower() in {"1", "true", "yes", "on"}:
        threading.Thread(target=background_worker, daemon=True).start()
    yield


app = FastAPI(title="Elio API", version="3.7.0", lifespan=lifespan)

# --- Middlewares ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    """Logs every request to the elio_audit_logs table."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # We log after the request is processed
    # Note: Extracting user from JWT here would require redundant decoding, 
    # so we log general path/method. Specialized logging happens inside endpoints.
    try:
        log_audit_action("system", f"{request.method} {request.url.path}", f"Status: {response.status_code}, Time: {process_time:.3f}s")
    except: pass
    return response

# --- Auth Helpers ---

def create_access_token(data: dict):
    to_encode = data.copy()
    # Sliding session: Default to 30 days
    expire = datetime.datetime.utcnow() + datetime.timedelta(days=30)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, get_jwt_secret(), algorithm=JWT_ALGORITHM)


def _is_admin(identity: dict) -> bool:
    if identity.get("is_admin") is True:
        return True
    user_name = identity.get("user", "").lower()
    if not user_name:
        return False
    user_record = get_user(user_name)
    return bool(user_record and user_record.get("is_admin"))


def _resolve_subject(identity: dict, requested_user: Optional[str] = None) -> str:
    current_user = identity.get("user", "").lower()
    target_user = (requested_user or current_user).lower()
    if target_user != current_user and not _is_admin(identity):
        raise HTTPException(status_code=403, detail="Cross-user access is restricted.")
    return target_user


def _persist_upload(prefix: str, upload_name: str, raw_bytes: bytes):
    safe_name = sanitize_upload_name(upload_name)
    suffix = Path(safe_name).suffix or ".bin"
    handle = tempfile.NamedTemporaryFile(delete=False, prefix=prefix, suffix=suffix)
    try:
        handle.write(raw_bytes)
    finally:
        handle.close()
    return handle.name, safe_name

def _auth(auth: HTTPAuthorizationCredentials = Depends(security)):
    token = auth.credentials
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        if "is_admin" not in payload:
            payload["is_admin"] = _is_admin(payload)
        return payload
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except jwt.InvalidTokenError:
        identity = verify_device_token(token)
        if not identity:
            raise HTTPException(status_code=401, detail="Unauthorized")
        identity = dict(identity)
        identity["is_admin"] = _is_admin(identity)
        return identity

@app.post("/login/refresh")
def refresh_token(identity: dict = Depends(_auth)):
    user_name = identity.get("user")
    new_token = create_access_token(
        {
            "user": user_name,
            "device": identity.get("device", "web"),
            "is_admin": _is_admin(identity),
        }
    )
    return {"ok": True, "token": new_token}

# --- Models ---
class LoginIn(BaseModel):
    username: str
    password: str

class ChatIn(BaseModel):
    message: str

class EmailConfigIn(BaseModel):
    email: str
    password: str
    smtp_server: str
    smtp_port: int
    imap_server: Optional[str] = None
    imap_port: Optional[int] = None

class EmailSendIn(BaseModel):
    to: str
    subject: str
    body: str
    is_html: bool = False

class TodoIn(BaseModel):
    user: str
    text: str

class TodoDelegateIn(BaseModel):
    todo_id: int
    to_user: str

class BidUpdateIn(BaseModel):
    id: int
    status: str
    draft_proposal: Optional[str] = None

class MissionIn(BaseModel):
    goal: str

class WorkflowIn(BaseModel):
    name: str
    trigger_type: str
    actions: list


class TeamNoteIn(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    content: str = Field(min_length=1, max_length=5000)


class JobIn(BaseModel):
    job_type: str = Field(min_length=1, max_length=80)
    user: Optional[str] = Field(default=None, max_length=120)
    payload: dict = Field(default_factory=dict)
    priority: Optional[int] = Field(default=None, ge=1, le=1000)
    max_attempts: int = Field(default=3, ge=1, le=10)
    run_at: Optional[datetime.datetime] = None

# --- Endpoints ---

@app.api_route("/", methods=["GET", "HEAD"])
def read_root():
    if not PUBLIC_DIR.exists():
        return {"message": "Elio V3.7 local-first API is operational."}
    return FileResponse(PUBLIC_DIR / "index.html")


@app.api_route("/guide", methods=["GET", "HEAD"])
def read_guide():
    if not PUBLIC_DIR.exists():
        raise HTTPException(status_code=404)
    return FileResponse(PUBLIC_DIR / "guide.html")


@app.api_route("/vendor-upload", methods=["GET", "HEAD"])
def read_vendor_upload():
    if not PUBLIC_DIR.exists():
        raise HTTPException(status_code=404)
    return FileResponse(PUBLIC_DIR / "vendor-upload.html")


@app.get("/health")
def health():
    return {"ok": True, "service": "elio-api"}


@app.get("/system/runtime")
def get_runtime(identity: dict = Depends(_auth)):
    return {
        "llm": get_runtime_settings(),
        "voice": get_tts_runtime(identity.get("user")),
        "personality": get_personality_summary(identity.get("user")),
        "subagent": {
            "enabled": os.getenv("ELIO_SUBAGENT_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"},
            "url": os.getenv("ELIO_SUBAGENT_URL", ""),
        },
        "jobs": get_job_queue_summary() if _is_admin(identity) else {},
    }

@app.post("/login")
def login(payload: LoginIn):
    user_record = get_user(payload.username)
    if user_record and verify_password(payload.password, user_record["password"]):
        if needs_password_upgrade(user_record["password"]):
            create_user(
                user_record["username"],
                payload.password,
                is_admin=user_record["is_admin"],
                email=user_record["email"],
            )
        token = create_access_token(
            {
                "user": user_record["username"],
                "device": "web",
                "is_admin": bool(user_record["is_admin"]),
            }
        )
        return {"ok": True, "token": token, "username": user_record["username"]}
    return JSONResponse(status_code=401, content={"ok": False, "detail": "Invalid credentials."})

@app.post("/chat")
def chat_endpoint(payload: ChatIn, identity: dict = Depends(_auth)):
    user_name = identity.get("user")
    add_chat_message(user_name, "user", payload.message)
    answer = ReplyBrain(payload.message, user_override=user_name)
    add_chat_message(user_name, "agent", answer)
    return {"ok": True, "reply": answer}

@app.get("/chat/history")
def read_chat_history(limit: int = 20, identity: dict = Depends(_auth)):
    user_name = identity.get("user")
    return {"items": get_chat_history(user_name, limit)}

@app.get("/integrations/status")
def get_integrations_status(identity: dict = Depends(_auth)):
    from Features.GmailOAuth import setup_status as gmail_status
    from Features.CalendarOAuth import setup_status as cal_status
    from Features.QuickBooksOAuth import setup_status as qb_status
    from Features.ProjectManagement import setup_status as jira_status
    from Features.ProcoreOAuth import setup_status as procore_status
    return {
        "gmail": gmail_status(),
        "calendar": cal_status(),
        "quickbooks": qb_status(),
        "jira": jira_status(),
        "procore": procore_status(),
        "neon": "Connected"
    }

@app.get("/analytics/sales")
def get_sales_forecast(identity: dict = Depends(_auth)):
    from Features.SalesAnalytics import calculate_sales_forecast
    return {"forecast": calculate_sales_forecast()}

@app.get("/analytics/efficiency")
def get_team_efficiency_api(identity: dict = Depends(_auth)):
    from Features.SalesAnalytics import get_team_efficiency
    return {"metrics": get_team_efficiency()}

@app.get("/recommendations")
def get_ai_recommendations(identity: dict = Depends(_auth)):
    from server.store import _pg_conn
    user = identity.get("user", "unknown")
    conn = _pg_conn(); cur = conn.cursor()
    cur.execute("select id, title, description, category, action_prompt from elio_ai_recommendations where user_name = %s and status = 'new' order by created_at desc", (user,))
    rows = cur.fetchall(); cur.close(); conn.close()
    return {"items": [{"id": r[0], "title": r[1], "description": r[2], "category": r[3], "prompt": r[4]} for r in rows]}

@app.get("/workflows")
def list_workflows(identity: dict = Depends(_auth)):
    from server.store import _pg_conn
    user = identity.get("user", "unknown")
    conn = _pg_conn(); cur = conn.cursor()
    cur.execute("select id, name, trigger_type, actions, status from elio_custom_workflows where user_name = %s", (user,))
    rows = cur.fetchall(); cur.close(); conn.close()
    return {"items": [{"id": r[0], "name": r[1], "trigger": r[2], "actions": r[3], "status": r[4]} for r in rows]}

@app.post("/workflows")
def create_workflow(payload: WorkflowIn, identity: dict = Depends(_auth)):
    from server.store import _pg_conn
    user = identity.get("user", "unknown")
    conn = _pg_conn(); cur = conn.cursor()
    cur.execute("insert into elio_custom_workflows (user_name, name, trigger_type, actions, created_at) values (%s, %s, %s, %s, %s)",
                (user, payload.name, payload.trigger_type, json.dumps(payload.actions), datetime.datetime.utcnow()))
    conn.commit(); cur.close(); conn.close()
    return {"ok": True}

# --- Standard Feature Routes ---

@app.get("/projects/pulse")
def get_project_pulse(identity: dict = Depends(_auth)):
    from server.store import _pg_conn
    conn = _pg_conn()
    cur = conn.cursor()
    cur.execute("""
        select b.project_tag, b.title, b.estimated_cost as bid_total, 
               coalesce(sum(e.total_amount), 0) as actual_total
        from elio_bid_opportunities b
        left join elio_expenses e on b.project_tag = e.project_tag
        where b.status = 'approved'
        group by b.project_tag, b.title, b.estimated_cost
    """)
    rows = cur.fetchall(); cur.close(); conn.close()
    return {"projects": [{"tag": r[0], "title": r[1], "bid": float(r[2] or 0), "actual": float(r[3])} for r in rows]}

@app.get("/projects/forecast")
def get_project_forecast_api(project_tag: str, identity: dict = Depends(_auth)):
    from Features.ProjectAnalytics import calculate_project_forecast
    return {"forecast": calculate_project_forecast(project_tag)}

@app.get("/expenses")
def list_expenses(user: Optional[str] = None, identity: dict = Depends(_auth)):
    from server.store import _pg_conn

    target_user = _resolve_subject(identity, user)
    conn = _pg_conn()
    cur = conn.cursor()
    cur.execute(
        """
        select id, vendor, category, total_amount, receipt_url, created_at
        from elio_expenses
        where user_name = %s
        order by created_at desc
        limit 100
        """,
        (target_user,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {
        "items": [
            {
                "id": r[0],
                "vendor": r[1],
                "category": r[2],
                "total": float(r[3] or 0),
                "receipt_url": r[4],
                "created_at": r[5],
            }
            for r in rows
        ]
    }


@app.post("/upload/dynamic")
async def intelligent_upload(file: UploadFile = File(...), prompt: str = Header(default=""), identity: dict = Depends(_auth)):
    from Features.IntelligentIntake import analyze_file_intent
    from Features.Storage import upload_to_elio_storage
    from server.store import _pg_conn
    
    user = identity.get("user", "unknown")
    temp_path, safe_name = _persist_upload("intake_", file.filename, await file.read())
    
    try:
        # 1. Analyze Intent
        intent = analyze_file_intent(safe_name, prompt)
        category = intent.get("category", "general")
        action = intent.get("action", "Archive")
        
        # 2. Upload to GCS at determined path
        gcs_blob_name = f"intake/{user}/{category}/{datetime.datetime.now().isoformat()}_{safe_name}"
        upload_ok, gcs_url = upload_to_elio_storage(temp_path, gcs_blob_name)
        if not upload_ok:
            raise HTTPException(status_code=502, detail=f"Storage upload failed: {gcs_url}")
        
        # 3. Trigger Specialized Actions
        result_message = intent.get("thought_process", "")
        
        if action == "ProcessExpense":
            from Features.ReceiptProcessor import process_receipt_image
            data = process_receipt_image(temp_path)
            if data:
                conn = _pg_conn(); cur = conn.cursor()
                cur.execute("insert into elio_expenses (user_name, vendor, total_amount, category, items, receipt_url, created_at) values (%s, %s, %s, %s, %s, %s, %s)",
                            (user, data['vendor'], data['total_amount'], data['category'], json.dumps(data['items']), gcs_url, datetime.datetime.utcnow()))
                conn.commit(); cur.close(); conn.close()
                result_message += f"\nProcessed as expense: {data['vendor']} - ${data['total_amount']}"
        
        elif action == "AddToLibrary":
            from Features.KnowledgeBase import ingest_pdf
            success, msg = ingest_pdf(temp_path, safe_name)
            if success:
                result_message += f"\nAdded to Knowledge Library: {safe_name}"
            else:
                result_message += f"\nFailed to ingest into Library: {msg}"
            
        return {"ok": True, "intent": intent, "message": result_message, "url": gcs_url}
    finally:
        if os.path.exists(temp_path): os.remove(temp_path)

@app.post("/expenses/upload")
async def upload_receipt(file: UploadFile = File(...), identity: dict = Depends(_auth)):
    from Features.ReceiptProcessor import process_receipt_image
    from Features.Storage import upload_to_elio_storage
    user = identity.get("user", "unknown")
    temp_path, safe_name = _persist_upload("receipt_", file.filename, await file.read())
    try:
        upload_ok, gcs_url = upload_to_elio_storage(
            temp_path,
            f"receipts/{user}/{datetime.datetime.now().isoformat()}_{safe_name}",
        )
        if not upload_ok:
            raise HTTPException(status_code=502, detail=f"Storage upload failed: {gcs_url}")
        data = process_receipt_image(temp_path)
        from server.store import _pg_conn
        conn = _pg_conn(); cur = conn.cursor()
        cur.execute("insert into elio_expenses (user_name, vendor, total_amount, category, items, receipt_url, created_at) values (%s, %s, %s, %s, %s, %s, %s)",
                    (user, data['vendor'], data['total_amount'], data['category'], json.dumps(data['items']), gcs_url, datetime.datetime.utcnow()))
        conn.commit(); cur.close(); conn.close()
        return {"ok": True, "data": data}
    finally:
        if os.path.exists(temp_path): os.remove(temp_path)

@app.get("/bids/opportunities")
def list_bids(identity: dict = Depends(_auth)):
    from Features.BiddingHub import get_pending_opportunities
    return {"items": get_pending_opportunities(limit=10)}

@app.patch("/bids/opportunities")
def update_bid(payload: BidUpdateIn, identity: dict = Depends(_auth)):
    from server.store import _pg_conn
    from Features.ProjectManagement import create_jira_ticket
    from Features.ProcoreOAuth import create_procore_rfi
    conn = _pg_conn(); cur = conn.cursor()
    if payload.draft_proposal:
        cur.execute("update elio_bid_opportunities set status = %s, draft_proposal = %s where id = %s returning title, description", (payload.status, payload.draft_proposal, payload.id))
    else:
        cur.execute("update elio_bid_opportunities set status = %s where id = %s returning title, description", (payload.status, payload.id))
    row = cur.fetchone(); conn.commit()
    if payload.status == 'approved' and row:
        create_jira_ticket("ESS", f"Project Kickoff: {row[0]}", row[1])
        create_procore_rfi("123", f"Initial Spec Review: {row[0]}", "Please confirm technical specs.")
    cur.close(); conn.close()
    return {"ok": True}

@app.get("/missions")
def list_missions(identity: dict = Depends(_auth)):
    from Features.MissionEngine import get_active_missions
    return {"items": get_active_missions(identity.get("user", "unknown"))}

@app.post("/missions")
def start_mission(payload: MissionIn, identity: dict = Depends(_auth)):
    from Features.MissionEngine import initialize_mission
    m_id = initialize_mission(identity.get("user"), payload.goal)
    return {"ok": True, "mission_id": m_id}

@app.get("/audit")
def get_audit_logs_api(user: Optional[str] = None, identity: dict = Depends(_auth)):
    from server.store import _pg_conn
    target_user = _resolve_subject(identity, user)
    conn = _pg_conn(); cur = conn.cursor()
    cur.execute("select details, created_at from elio_audit_logs where user_name = %s order by created_at desc limit 20", (target_user,))
    rows = cur.fetchall(); cur.close(); conn.close()
    return {"items": [{"details": r[0], "date": r[1]} for r in rows]}

@app.get("/audit/evolution")
def get_evolution_logs_api(identity: dict = Depends(_auth)):
    if not _is_admin(identity):
        raise HTTPException(status_code=403, detail="Admin access required.")
    return {"items": get_evolution_logs()}

@app.get("/brain/facts")
def api_get_brain_facts(user: Optional[str] = None, identity: dict = Depends(_auth)):
    from Features.MemoryStore import get_second_brain_facts
    target_user = _resolve_subject(identity, user)
    return {"items": get_second_brain_facts(target_user)}

@app.get("/insights")
def api_get_insights(user: Optional[str] = None, identity: dict = Depends(_auth)):
    from Features.MemoryRefiner import get_recent_insights
    target_user = _resolve_subject(identity, user)
    return {"items": get_recent_insights(target_user)}

@app.get("/lessons")
def api_list_lessons(owner: Optional[str] = None, identity: dict = Depends(_auth)):
    target_user = _resolve_subject(identity, owner)
    return {"items": list_lessons(target_user)}

@app.get("/todos")
def api_list_todos(user: Optional[str] = None, identity: dict = Depends(_auth)):
    target_user = _resolve_subject(identity, user)
    return {"items": list_todos(target_user)}

@app.post("/todos/delegate")
def delegate_todo(payload: TodoDelegateIn, identity: dict = Depends(_auth)):
    from server.store import _pg_conn
    conn = _pg_conn(); cur = conn.cursor()
    acting_user = identity.get("user", "").lower()
    if _is_admin(identity):
        cur.execute("update elio_todos set user_name = %s where id = %s", (payload.to_user.lower(), payload.todo_id))
    else:
        cur.execute(
            "update elio_todos set user_name = %s where id = %s and user_name = %s",
            (payload.to_user.lower(), payload.todo_id, acting_user),
        )
    if cur.rowcount == 0:
        cur.close(); conn.close()
        raise HTTPException(status_code=404, detail="Todo not found.")
    conn.commit(); cur.close(); conn.close()
    return {"ok": True}

@app.delete("/todos/{todo_id}")
def delete_todo_api(todo_id: int, identity: dict = Depends(_auth)):
    from server.store import _pg_conn
    conn = _pg_conn(); cur = conn.cursor()
    if _is_admin(identity):
        cur.execute("delete from elio_todos where id = %s", (todo_id,))
    else:
        cur.execute(
            "delete from elio_todos where id = %s and user_name = %s",
            (todo_id, identity.get("user", "").lower()),
        )
    if cur.rowcount == 0:
        cur.close(); conn.close()
        raise HTTPException(status_code=404, detail="Todo not found.")
    conn.commit()
    cur.close(); conn.close()
    return {"ok": True}

@app.get("/docs/list")
def api_list_docs(identity: dict = Depends(_auth)):
    from Features.KnowledgeBase import list_knowledge_files
    return {"items": list_knowledge_files()}

@app.post("/docs/upload")
async def api_upload_doc(file: UploadFile = File(...), identity: dict = Depends(_auth)):
    from Features.KnowledgeBase import ingest_pdf
    temp_path, safe_name = _persist_upload("kb_", file.filename, await file.read())
    try:
        if not safe_name.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Knowledge library only accepts PDF files.")
        success, msg = ingest_pdf(temp_path, safe_name)
        return {"ok": success, "message": msg}
    finally:
        if os.path.exists(temp_path): os.remove(temp_path)

@app.delete("/docs/delete/{filename}")
def api_delete_doc(filename: str, identity: dict = Depends(_auth)):
    from Features.KnowledgeBase import delete_knowledge_file
    if Path(filename).name != filename:
        raise HTTPException(status_code=400, detail="Invalid document name.")
    success = delete_knowledge_file(filename)
    return {"ok": success}

@app.get("/reports/download")
def download_report(filename: str, identity: dict = Depends(_auth)):
    try:
        report_path = resolve_child_path(REPORTS_DIR, filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not report_path.exists():
        raise HTTPException(status_code=404)
    return FileResponse(report_path, filename=report_path.name)

@app.get("/tts")
def generate_tts(text: str, voice: str = "", identity: dict = Depends(_auth)):
    if not tts_ready(identity.get("user")):
        raise HTTPException(status_code=500, detail="TTS engine not initialized.")
    if len(text) > 500:
        raise HTTPException(status_code=400, detail="Text is too long for a single TTS request.")
    try:
        buffer = io.BytesIO(synthesize_wav(text, voice=voice, user_name=identity.get("user")))
        return StreamingResponse(buffer, media_type="audio/wav")
    except Exception as e:
        if os.path.exists(temp_path): os.remove(temp_path)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/settings/email")
def get_user_email_settings(identity: dict = Depends(_auth)):
    from server.store import get_email_config
    user = identity.get("user", "").lower()
    config = get_email_config(user)
    if not config:
        return {"ok": False, "config": None}
    # Don't return the actual password for security in GET
    config["password"] = "********" 
    return {"ok": True, "config": config}

@app.post("/settings/email")
def update_user_email_settings(payload: EmailConfigIn, identity: dict = Depends(_auth)):
    from server.store import set_email_config
    user = identity.get("user", "").lower()
    set_email_config(user, payload.dict())
    return {"ok": True}
@app.delete("/settings/email")
def delete_user_email_settings(identity: dict = Depends(_auth)):
    from server.store import delete_email_config
    user = identity.get("user", "").lower()
    delete_email_config(user)
    return {"ok": True}

@app.post("/email/send")
def api_send_email(payload: EmailSendIn, identity: dict = Depends(_auth)):
    from server.mail_service import mail_service
    user = identity.get("user", "").lower()
    return mail_service.send_email(
        to_email=payload.to,
        subject=payload.subject,
        body=payload.body,
        from_user=user,
        is_html=payload.is_html
    )

@app.get("/email/inbox")
def api_get_inbox(limit: int = 10, identity: dict = Depends(_auth)):
    from server.mail_service import mail_service
    user = identity.get("user", "").lower()
    emails = mail_service.fetch_emails(user_name=user, folder="INBOX", limit=limit)
    return {"ok": True, "emails": emails}

@app.get("/email/outbox")
def api_get_outbox(limit: int = 10, identity: dict = Depends(_auth)):
    from server.mail_service import mail_service
    user = identity.get("user", "").lower()
    # Note: Some servers call it "Sent", some "Sent Messages", some "INBOX.Sent"
    # We'll try "Sent" as a default
    emails = mail_service.fetch_emails(user_name=user, folder="Sent", limit=limit)
    return {"ok": True, "emails": emails}

@app.get("/email/history")
def api_get_email_history(limit: int = 50, identity: dict = Depends(_auth)):
    from server.store import list_recent_emails
    return {"ok": True, "emails": list_recent_emails(limit)}

@app.get("/security/mfa/generate")
def generate_mfa(identity: dict = Depends(_auth)):
    import secrets
    from server.store import _pg_conn
    user = identity.get("user", "unknown")
    code = "".join([str(secrets.randbelow(10)) for _ in range(6)])
    conn = _pg_conn(); cur = conn.cursor()
    cur.execute("insert into elio_mfa_codes (user_name, code, expires_at) values (%s, %s, %s)",
                (user, code, datetime.datetime.utcnow() + datetime.timedelta(minutes=10)))
    conn.commit(); cur.close(); conn.close()
    print(f"MFA CODE FOR {user}: {code}")
    return {"ok": True, "message": "Verification code sent."}

@app.post("/security/mfa/verify")
def verify_mfa(code: str, identity: dict = Depends(_auth)):
    user = identity.get("user", "unknown")
    if consume_mfa_code(user, code):
        return {"ok": True, "message": "Identity verified."}
    raise HTTPException(status_code=401, detail="Invalid code.")


@app.get("/errors")
def get_error_logs_api(identity: dict = Depends(_auth)):
    if not _is_admin(identity):
        raise HTTPException(status_code=403, detail="Admin access required.")
    return {"items": get_error_logs()}


@app.get("/skills")
def get_skills_api(identity: dict = Depends(_auth)):
    return {"items": list_user_skills()}


@app.get("/notes")
def get_team_notes_api(identity: dict = Depends(_auth)):
    from Features.Collaboration import get_team_notes
    return {"items": get_team_notes()}


@app.post("/notes")
def save_team_note_api(payload: TeamNoteIn, identity: dict = Depends(_auth)):
    from Features.Collaboration import save_team_note
    save_team_note(payload.title.strip(), payload.content.strip(), identity.get("user", "unknown"))
    return {"ok": True}


@app.get("/vendors/compliance")
def get_vendor_compliance(identity: dict = Depends(_auth)):
    from server.store import _pg_conn

    conn = _pg_conn()
    cur = conn.cursor()
    cur.execute(
        """
        select name, status, coi_expiry
        from elio_vendors
        order by status asc, name asc
        limit 100
        """
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {
        "items": [
            {"name": r[0], "status": r[1], "coi_expiry": r[2]}
            for r in rows
        ]
    }


@app.get("/jobs/catalog")
def get_job_catalog(identity: dict = Depends(_auth)):
    user_is_admin = _is_admin(identity)
    return {
        "items": [
            item
            for item in list_job_types()
            if user_is_admin or not item["admin_only"]
        ]
    }


@app.get("/jobs")
def get_jobs_api(
    user: Optional[str] = None,
    status: str = "",
    limit: int = 50,
    identity: dict = Depends(_auth),
):
    target_user = None
    if user:
        target_user = _resolve_subject(identity, user)
    elif not _is_admin(identity):
        target_user = identity.get("user", "").lower()
    statuses = [item.strip().lower() for item in status.split(",") if item.strip()]
    return {"items": list_jobs(user_name=target_user, statuses=statuses or None, limit=min(limit, 100))}


# --- SEO & Automation Proxy Routes ---

@app.get("/api/seo/health")
async def proxy_seo_health():
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{SEO_API_URL}/health", timeout=5)
            return resp.json()
        except Exception as e:
            return {"status": "error", "detail": str(e)}

@app.get("/api/seo/stats")
async def proxy_seo_stats(identity: dict = Depends(_auth)):
    def _normalize_stats_payload(payload: dict) -> dict:
        if isinstance(payload, dict) and isinstance(payload.get("items"), list):
            return payload
        if not isinstance(payload, dict):
            return {"items": []}

        items = []
        for run in payload.get("automation_runs", []) or []:
            run_type = str(run.get("type", "automation")).replace("_", " ").title()
            items.append({"topic": f"{run_type} automation", "status": run.get("status", "unknown")})
        for task in payload.get("tasks_by_type", []) or []:
            task_type = str(task.get("type", "task")).replace("_", " ").title()
            count = task.get("count")
            suffix = f" ({count})" if count is not None else ""
            items.append({"topic": f"{task_type}{suffix}", "status": task.get("status", "unknown")})
        return {"items": items, "source": payload}

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{SEO_API_URL}/api/reports/daily", timeout=5)
            return _normalize_stats_payload(resp.json())
        except Exception as e:
            return {"status": "error", "detail": str(e)}

@app.get("/api/n8n/status")
async def proxy_n8n_status(identity: dict = Depends(_auth)):
    if not _is_admin(identity):
        raise HTTPException(status_code=403, detail="Admin access required.")
    return {"url": N8N_URL}


@app.get("/jobs/summary")
def get_jobs_summary_api(identity: dict = Depends(_auth)):
    if not _is_admin(identity):
        raise HTTPException(status_code=403, detail="Admin access required.")
    return get_job_queue_summary()


@app.post("/jobs")
def create_job_api(payload: JobIn, identity: dict = Depends(_auth)):
    user_is_admin = _is_admin(identity)
    try:
        normalized_job_type = payload.job_type.strip().lower().replace("-", "_")
        catalog = {item["job_type"]: item for item in list_job_types()}
        item = catalog[normalized_job_type]
    except Exception:
        raise HTTPException(status_code=400, detail="Unsupported job type.")
    if item["admin_only"] and not user_is_admin:
        raise HTTPException(status_code=403, detail="Admin access required for this job.")
    target_user = None
    if payload.user:
        target_user = _resolve_subject(identity, payload.user)
    elif not user_is_admin:
        target_user = identity.get("user", "").lower()
    job = enqueue_job(
        normalized_job_type,
        user_name=target_user,
        payload=payload.payload,
        run_at=payload.run_at,
        requested_by=identity.get("user"),
        priority=payload.priority,
        max_attempts=payload.max_attempts,
    )
    return {"ok": True, "job": job}


@app.post("/jobs/{job_id}/retry")
def retry_job_api(job_id: int, identity: dict = Depends(_auth)):
    if not _is_admin(identity):
        raise HTTPException(status_code=403, detail="Admin access required.")
    if not retry_job(job_id):
        raise HTTPException(status_code=404, detail="Job not found.")
    return {"ok": True}

# --- Background Worker ---

def background_worker():
    worker_id = f"{os.getenv('ELIO_DEVICE_ID', 'elio')}-{os.getpid()}"
    poll_seconds = int(os.getenv("ELIO_JOB_POLL_SECONDS", "60"))
    batch_size = int(os.getenv("ELIO_JOB_BATCH_SIZE", "4"))
    while True:
        try:
            schedule_recurring_jobs()
            process_due_jobs(worker_id=worker_id, limit=batch_size)
        except Exception as exc:
            try:
                log_error("Background worker failed", str(exc))
            except Exception:
                pass
        time.sleep(poll_seconds)


if PUBLIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(PUBLIC_DIR), html=True), name="public")
