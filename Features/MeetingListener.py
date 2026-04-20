import os
import json
from datetime import datetime
import psycopg2
from Features.Storage import upload_to_elio_storage
from server.ai_provider import chat_completion

def _pg_conn():
    uri = os.getenv("ELIO_PG_URI", "").strip()
    return psycopg2.connect(uri)

def process_meeting_audio(audio_path, user_name):
    """
    Simulates Whisper/Gemini transcription and action item extraction.
    """
    # 1. Upload to GCS
    upload_ok, gcs_url = upload_to_elio_storage(audio_path, f"meetings/{user_name}/{datetime.utcnow().isoformat()}.wav")
    if not upload_ok:
        print(f"Meeting audio upload failed: {gcs_url}")
        return None
    
    # Mocking transcription for speed in this demo
    transcript = "We discussed the Phase II wiring. Alex needs to order 500ft of copper wire by Friday. Sandra will check the invoice from Danfoss."
    
    prompt = f"""
    Analyze the following meeting transcript and extract a list of action items.
    For each item, identify the task and who it is assigned to (Sandra or Alex).
    
    Transcript: {transcript}
    
    Return JSON: [ {{"task": "...", "assignee": "alex/sandra"}} ]
    """
    
    try:
        response = chat_completion(
            "meeting",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        actions = json.loads(response.choices[0].message.content).get("actions", [])
        if not actions and isinstance(json.loads(response.choices[0].message.content), list):
            actions = json.loads(response.choices[0].message.content)

        # Save Meeting to DB
        conn = _pg_conn()
        cur = conn.cursor()
        cur.execute(
            "insert into elio_meetings (user_name, title, audio_url, transcript, action_items, created_at) values (%s, %s, %s, %s, %s, %s)",
            (user_name, f"Meeting {datetime.now().strftime('%Y-%m-%d %H:%M')}", gcs_url, transcript, json.dumps(actions), datetime.utcnow())
        )
        
        # Auto-populate Todos
        for act in actions:
            target_user = act.get('assignee', user_name).lower()
            cur.execute(
                "insert into elio_todos (user_name, text_body, created_at) values (%s, %s, %s)",
                (target_user, act['task'], datetime.utcnow())
            )
            
        conn.commit()
        cur.close()
        conn.close()
        return actions
    except Exception as e:
        print(f"Meeting process error: {e}")
        return None
