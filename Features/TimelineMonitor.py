import json
from datetime import datetime, timedelta
from Features.ProjectManagement import get_project_status
from Features.ElioSkills import _get_calendar_service
from Features.GhostWriter import ghost_writer
from Features.Face.Mouth import speak

class TimelineMonitor:
    def __init__(self):
        self.threshold_days = 2

    def scan_for_upcoming_milestones(self, user):
        """
        Revolutionary Phase 3: Predictive Outcome Engineering.
        Triggers Ghost-Writer to draft responses before the user asks.
        """
        now = datetime.utcnow()
        upcoming_actions = []

        # 1. Check Calendar
        service = _get_calendar_service()
        if service:
            time_max = (now + timedelta(days=self.threshold_days)).isoformat() + "Z"
            events = service.events().list(calendarId='primary', timeMin=now.isoformat() + "Z", timeMax=time_max, singleEvents=True).execute().get('items', [])
            for event in events:
                action = {
                    "type": "event_prep",
                    "title": event.get('summary'),
                    "time": event['start'].get('dateTime')
                }
                upcoming_actions.append(action)
                # Ghost-Writer Proactive Drafting
                draft = ghost_writer.generate_proactive_draft(user, "pre-meeting_note", action['title'])
                speak(f"Ghost-Writer has drafted a pre-meeting note for {action['title']}.")

        # 2. Check Project Milestones
        status = get_project_status()
        if "pending" in status.lower():
            action = {
                "type": "milestone_near",
                "title": "Project Submittal Deadlines",
                "time": "Within 48 hours"
            }
            upcoming_actions.append(action)
            # Ghost-Writer Proactive Drafting
            draft = ghost_writer.generate_proactive_draft(user, "status_update_notification", "Project Submittal Deadline Approaching")
            speak(f"Ghost-Writer staged a status update draft for {action['title']}.")

        return upcoming_actions

timeline_monitor = TimelineMonitor()
