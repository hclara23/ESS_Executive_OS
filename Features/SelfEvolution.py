import os
import json
from datetime import datetime
import psycopg2
from server.ai_provider import chat_completion

def _pg_conn():
    uri = os.getenv("ELIO_PG_URI", "").strip()
    return psycopg2.connect(uri)

def run_self_audit():
    """
    Autonomous process where Elio reviews its own logs and documentation to improve.
    """
    conn = _pg_conn()
    cur = conn.cursor()
    
    # 1. Fetch recent errors
    cur.execute("select error_message, stack_trace from elio_error_logs order by created_at desc limit 10")
    errors = cur.fetchall()
    error_context = "\n".join([f"Error: {e[0]}\nTrace: {e[1]}" for e in errors])
    
    # 2. Fetch current features from MD
    docs = []
    for file in os.listdir("."):
        if file.endswith(".md"):
            with open(file, "r", encoding="utf-8") as f:
                docs.append(f.read())
    doc_context = "\n".join(docs)

    prompt = f"""
    You are Elio's Self-Evolution Core.
    Review your current performance and system health.
    
    RECENT ERRORS:
    {error_context}
    
    SYSTEM CAPABILITIES:
    {doc_context}
    
    MISSION:
    1. Identify any repeating bugs and propose a Python fix.
    2. Suggest one new 'Proactive' feature that would help Alex (Engineering) or Sandra (Executive).
    
    Return JSON:
    {{
      "findings": "Summary of audit",
      "proposals": [
        {{ "name": "Fix X", "description": "...", "code": "...", "type": "bugfix/feature" }}
      ]
    }}
    """
    
    try:
        response = chat_completion(
            "self_audit",
            messages=[{"role": "system", "content": "You are a self-healing AI. Output JSON."},
                      {"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        data = json.loads(response.choices[0].message.content)
        
        # Log findings to audit table
        cur.execute(
            "insert into elio_audit_logs (user_name, action_type, details, created_at) values (%s, %s, %s, %s)",
            ("elio", "self_audit", data.get("findings", ""), datetime.utcnow())
        )
        
        # Propose to Skill Factory
        for prop in data.get("proposals", []):
            cur.execute(
                "insert into elio_user_skills (skill_name, description, code_snippet, status, created_at) values (%s, %s, %s, %s, %s)",
                (prop['name'], prop['description'], prop['code'], "learned", datetime.utcnow())
            )
            
        conn.commit()
        cur.close()
        conn.close()
        return data.get("findings", "Self-audit complete.")
    except Exception as e:
        print(f"Self-Evolution Error: {e}")
        return f"Audit failed: {e}"
