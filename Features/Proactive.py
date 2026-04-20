import os
import json
from datetime import datetime, timedelta
from Features.Face.Mouth import speak
from Features.ElioSkills import _get_calendar_service, _get_gmail_service
from Features.QuickBooksOAuth import _token_path as qb_token_path

# Track notified IDs to avoid repeating alerts in the same session
_notified_meetings = set()
_last_check_billing = None

def get_proactive_alerts():
    """
    Checks various services and returns a list of urgent strings to be spoken.
    """
    alerts = []
    
    # 1. Calendar: Meeting starting in < 15 mins
    cal = _get_calendar_service()
    if cal:
        try:
            now = datetime.utcnow()
            soon = (now + timedelta(minutes=15)).isoformat() + "Z"
            now_str = now.isoformat() + "Z"
            
            events_result = cal.events().list(
                calendarId='primary', 
                timeMin=now_str,
                timeMax=soon, 
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            for event in events:
                event_id = event['id']
                if event_id not in _notified_meetings:
                    summary = event.get('summary', 'Untitled Meeting')
                    alerts.append(f"Reminder: Your meeting '{summary}' starts in less than 15 minutes.")
                    _notified_meetings.add(event_id)
        except Exception as e:
            print(f"[Proactive Loop] Calendar Error: {e}")

    # 2. QuickBooks: (Mock Logic for now as real QB API requires specific entity IDs)
    # We check if it's been more than 4 hours since we last mentioned billing
    global _last_check_billing
    try:
        if os.path.exists(qb_token_path()):
            if _last_check_billing is None or (datetime.now() - _last_check_billing) > timedelta(hours=4):
                # In a real impl, we would query: select * from Invoices where Balance > 0 and DueDate < today
                # For now, we flag the presence of the connection
                # alerts.append("Financial update: You have 3 overdue invoices in QuickBooks that require follow-up.")
                _last_check_billing = datetime.now()
    except Exception as e:
        print(f"[Proactive Loop] QuickBooks Error: {e}")
        
    # 3. Phase 3: Ghost-Writer (Timeline Monitoring)
    try:
        from Features.TimelineMonitor import timeline_monitor
        upcoming_milestones = timeline_monitor.check_upcoming_milestones()
        for milestone in upcoming_milestones:
            alerts.append(f"Ghost-Writer Update: I have drafted a proposal for your upcoming milestone: {milestone['title']}.")
    except Exception as e:
        print(f"[Proactive Loop] Timeline Monitor Error: {e}")
        
    return alerts

def run_proactive_cycle():
    """
    One-off check to be called by a background thread.
    """
    alerts = get_proactive_alerts()
    for msg in alerts:
        speak(msg)
