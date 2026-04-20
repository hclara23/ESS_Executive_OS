import os
import json
from datetime import datetime
import psycopg2
from server.ai_provider import chat_completion
from server.subagent_client import call_subagent

def _pg_conn():
    uri = os.getenv("ELIO_PG_URI", "").strip()
    return psycopg2.connect(uri)

def initialize_mission(user_name, goal):
    """
    Creates a new autonomous mission with a multi-step flight plan.
    """
    steps = None

    subagent_result = call_subagent(
        "/tasks/mission-plan",
        {"user_name": user_name, "goal": goal},
        timeout=20,
    )
    if subagent_result:
        steps = subagent_result.get("steps", [])

    prompt = f"""
    You are Elio's Strategic Mission Planner.
    Create a 3-5 step plan to achieve the following goal for {user_name}:
    Goal: {goal}
    
    Elio can use these capabilities: 
    - Email (draft/send)
    - Financials (audit/invoice)
    - Vendors (onboard/check compliance)
    - Technical (NEC lookup/blueprint audit)
    - Projects (Jira sync/Status update)
    
    Return a JSON array of steps:
    [ {{"step": 1, "action": "name", "description": "...", "type": "auto/wait_for_user"}} ]
    """
    
    try:
        if steps is None:
            response = chat_completion(
                "mission",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            steps = json.loads(response.choices[0].message.content).get("steps", [])
        
        conn = _pg_conn()
        cur = conn.cursor()
        cur.execute(
            "insert into elio_missions (user_name, goal, steps, created_at, updated_at) values (%s, %s, %s, %s, %s) returning id",
            (user_name, goal, json.dumps(steps), datetime.utcnow(), datetime.utcnow())
        )
        mission_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return mission_id
    except Exception as e:
        print(f"Mission Init Error: {e}")
        return None

def get_active_missions(user_name):
    conn = _pg_conn()
    cur = conn.cursor()
    cur.execute("select id, goal, steps, status, current_step from elio_missions where user_name = %s and status = 'active'", (user_name,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": r[0], "goal": r[1], "steps": r[2], "status": r[3], "current": r[4]} for r in rows]

def execute_mission_step(mission_id):
    """
    Runs the next automated step in a mission.
    """
    # This would involve calling specific feature modules based on 'action' type.
    # Stub for now.
    print(f"Executing next step for mission {mission_id}...")
    return True
