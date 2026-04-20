import os
import datetime
import psycopg2

def _pg_conn():
    uri = os.getenv("ELIO_PG_URI", "").strip()
    return psycopg2.connect(uri)

def generate_daily_recap_text(user_name):
    """
    Synthesizes today's data into a podcast script.
    """
    today = datetime.date.today()
    conn = _pg_conn()
    cur = conn.cursor()
    
    # 1. Today's Expenses
    cur.execute("select coalesce(sum(total_amount), 0) from elio_expenses where user_name = %s and created_at::date = %s", (user_name, today))
    total_spent = cur.fetchone()[0]
    
    # 2. Completed Todos
    # ... logic
    
    # 3. Tomorrow's Calendar (Simulated)
    tomorrow_events = "Meeting with Alex at 10am, Vendor call at 2pm."
    
    script = f"""
    Hello {user_name.capitalize()}, this is your Elio Drive-Home Recap.
    Today, you recorded ${total_spent:,.2f} in business expenses.
    Your main priority for tomorrow is the {tomorrow_events}.
    The team has completed 4 tasks today. Project Phase II remains on track.
    Have a safe drive home.
    """
    cur.close()
    conn.close()
    return script

def get_podcast_audio_url(user_name):
    """
    Generates or fetches the recap audio.
    """
    script = generate_daily_recap_text(user_name)
    # This would call the /tts endpoint or similar
    # For now we return the text to be spoken by the frontend
    return script
