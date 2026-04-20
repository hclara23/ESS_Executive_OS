import re
import os
from Features.MemoryStore import add_private_memory, add_todo
from Features.Face.Mouth import speak
from server.ai_provider import chat_completion
from server.subagent_client import call_subagent

def process_meeting_transcript(user: str, meeting_topic: str, transcript: str = None) -> str:
    """
    Uses GPT-4o to parse a meeting transcript and automatically extract action items.
    """
    speak(f"Analyzing transcript for {meeting_topic}.")
    
    if not transcript:
        # Fallback to mock for testing if no transcript is provided
        transcript = """
        Alex: We need to update the Jira board for the transformer redesign.
        Sandra: Okay, I will handle the supplier pricing sheet.
        Alex: Also, let's make sure we log a Procore RFI for the concrete depth.
        """
    
    prompt = f"""
    Analyze the following meeting transcript about '{meeting_topic}'.
    Extract specific action items and identify which system they belong to:
    - Jira (Engineering tasks)
    - Procore (Site RFIs/Field tasks)
    - Delegation (Task for a specific person)
    - To-Do (General reminders)
    
    Format the output as a simple JSON list of objects:
    [{"type": "Jira", "task": "description"}, {"type": "Delegation", "user": "Sandra", "task": "description"}]
    
    Transcript:
    {transcript}
    """
    
    try:
        data = call_subagent(
            "/tasks/meeting-actions",
            {"meeting_topic": meeting_topic, "transcript": transcript},
            timeout=20,
        )
        if not data:
            response = chat_completion(
                "meeting",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            import json
            data = json.loads(response.choices[0].message.content)
        items = data.get("items", data.get("action_items", []))
        if not items and isinstance(data, list): items = data
        if not items and "items" not in data: # Handle cases where GPT just returns the list directly
             for k, v in data.items():
                 if isinstance(v, list): items = v; break

        tickets_created = []
        for item in items:
            task_desc = item.get("task", "Unknown task")
            sys_type = item.get("type", "To-Do")
            
            # Real-ish logic: Add to Elio's tracking
            add_todo(user, f"[{sys_type}] {task_desc}")
            tickets_created.append(f"{sys_type}: {task_desc}")
            
        summary = f"Meeting Intelligence for '{meeting_topic}': Extracted {len(tickets_created)} action items\n\nItems Processed:\n- " + "\n- ".join(tickets_created)
        speak(f"I extracted {len(tickets_created)} action items and updated your dashboard.")
        
        add_private_memory(user, f"Meeting intelligence run for {meeting_topic}. {len(tickets_created)} tasks extracted.", tags=["meeting", "ai"])
        return summary
        
    except Exception as e:
        return f"Meeting Intelligence Error: {str(e)}"
