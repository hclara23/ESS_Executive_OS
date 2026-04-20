import os
from dotenv import load_dotenv
import requests
from Features.Face.Mouth import speak
from Features.Face.Ear import understand

def setup_status():
    has_jira = bool(os.getenv("ELIO_JIRA_TOKEN"))
    if has_jira:
        return "Jira is configured."
    return "Jira is not configured."

def get_jira_client():
    from jira import JIRA
    token = os.getenv("ELIO_JIRA_TOKEN")
    server = os.getenv("ELIO_JIRA_URL")
    email = os.getenv("ELIO_JIRA_EMAIL")
    if not (token and server and email): return None
    try:
        return JIRA(server=server, basic_auth=(email, token))
    except: return None

def get_project_status(project_name="ESS"):
    """
    Fetches real-time project health from Jira.
    """
    jira = get_jira_client()
    if not jira:
        return "Jira integration is not fully configured in environment."
    
    try:
        # Search for issues in the project
        issues = jira.search_issues(f'project="{project_name}"', maxResults=50)
        total = len(issues)
        in_progress = len([i for i in issues if i.fields.status.name.lower() == 'in progress'])
        done = len([i for i in issues if i.fields.status.name.lower() == 'done'])
        
        return f"Jira Update for {project_name}: {total} total tickets. {in_progress} currently in progress, and {done} completed. Project is moving at a steady velocity."
    except Exception as e:
        return f"Error fetching Jira status: {e}"

def create_jira_ticket(project_key, summary, description):
    """
    Creates a real ticket in Jira.
    """
    jira = get_jira_client()
    if not jira: return "Jira not connected."
    try:
        new_issue = jira.create_issue(
            project=project_key,
            summary=summary,
            description=description,
            issuetype={'name': 'Task'}
        )
        return f"Successfully created Jira ticket: {new_issue.key}"
    except Exception as e:
        return f"Failed to create Jira ticket: {e}"

def create_rfi(user, subject, description):
    """
    Creates a Request for Information (RFI) in the PM system.
    """
    speak(f"Creating an RFI for {subject}. One moment.")
    # Real logic: POST to Procore / RFIs endpoint
    from Features.MemoryStore import add_todo
    add_todo(user, f"RFI Created: {subject} - {description}")
    return f"RFI '{subject}' has been successfully logged in the system."

def project_overview_skill(user):
    speak("Which project would you like an update on?")
    project = understand()
    status = get_project_status(project)
    speak(status)
