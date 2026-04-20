import os
import json
from datetime import datetime
import psycopg2
from server.ai_provider import chat_completion

def _pg_conn():
    uri = os.getenv("ELIO_PG_URI", "").strip()
    return psycopg2.connect(uri)

def get_unreflected_history(limit=50):
    conn = _pg_conn()
    cur = conn.cursor()
    cur.execute(
        """
        select id, user_name, role, content, created_at 
        from elio_chat_history 
        where reflected = false 
        order by created_at asc 
        limit %s;
        """,
        (limit,)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def mark_as_reflected(chat_ids):
    if not chat_ids: return
    conn = _pg_conn()
    cur = conn.cursor()
    cur.execute("update elio_chat_history set reflected = true where id = any(%s)", (chat_ids,))
    conn.commit()
    cur.close()
    conn.close()

def save_insight(user_name, category, content, source_ids, importance=1):
    conn = _pg_conn()
    cur = conn.cursor()
    cur.execute(
        """
        insert into elio_insights (user_name, category, content, source_ids, importance, created_at)
        values (%s, %s, %s, %s, %s, %s);
        """,
        (user_name, category, content, source_ids, importance, datetime.utcnow())
    )
    conn.commit()
    cur.close()
    conn.close()

def run_dream_cycle():
    """
    The background 'Always-On' process that reflects on recent chats.
    """
    history_rows = get_unreflected_history()
    if not history_rows:
        return "No new history to reflect on."

    # Group by user
    user_chats = {}
    for row in history_rows:
        u = row[1]
        if u not in user_chats: user_chats[u] = []
        user_chats[u].append(row)

    insights_found = 0
    for user, chats in user_chats.items():
        chat_ids = [c[0] for c in chats]
        chat_text = "\n".join([f"{c[2]}: {c[3]}" for c in chats])
        
        prompt = f"""
        You are Elio's Memory Consolidation Subsystem.
        Analyze the following recent chat history for the user '{user}'.
        Extract any significant new information that should be remembered long-term.
        
        Look for:
        1. 'fact': Specific facts about the user (birthdays, family, job details).
        2. 'preference': Likes, dislikes, or how they want Elio to behave.
        3. 'project': Status updates, deadlines, or details about engineering projects.
        4. 'lesson': Mistakes made and how to avoid them.
        
        Format your response as a JSON list of objects:
        [ {{"category": "fact", "content": "...", "importance": 1-5}} ]
        
        If nothing significant is found, return [].
        
        Chat History:
        {chat_text}
        """
        
        try:
            response = chat_completion(
                "memory_reflection",
                messages=[{"role": "system", "content": "You are a memory refiner. Output JSON only."},
                          {"role": "user", "content": prompt}],
                response_format={ "type": "json_object" },
                temperature=0.2,
            )
            
            data = json.loads(response.choices[0].message.content)
            insights = data.get("insights", []) # adjusting if model wraps it
            if isinstance(data, list): insights = data
            elif "insights" not in data and len(data.keys()) == 1:
                # Handle common wrapper
                key = list(data.keys())[0]
                if isinstance(data[key], list): insights = data[key]

            for ins in insights:
                save_insight(user, ins['category'], ins['content'], chat_ids, ins.get('importance', 1))
                insights_found += 1
            
            mark_as_reflected(chat_ids)
        except Exception as e:
            print(f"Error during dream cycle for {user}: {e}")

    return f"Dream cycle complete. Generated {insights_found} new insights."

def get_recent_insights(user_name, limit=5):
    conn = _pg_conn()
    cur = conn.cursor()
    cur.execute(
        "select category, content, importance, created_at from elio_insights where user_name = %s order by created_at desc limit %s",
        (user_name, limit)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"category": r[0], "content": r[1], "importance": r[2], "created_at": r[3]} for r in rows]
