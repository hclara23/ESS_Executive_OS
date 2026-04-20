import json
import os
import requests
import base64
from datetime import datetime, timedelta
from email.message import EmailMessage
from Features.Face.Mouth import speak
from Features.Face.Ear import understand
from Features.MemoryStore import (
    add_delegation, 
    get_pending_delegations, 
    complete_delegation,
    add_private_memory,
    add_todo,
    get_second_brain_facts
)
from Features.ElioSkills import _get_gmail_service, _get_calendar_service
from Features.QuickBooksOAuth import get_overdue_invoices
from Features.ProjectManagement import get_project_status
from Brain.AI_Brain import ReplyBrain
from Features.VendorHound import process_overdue_vendors
from Features.BrowserAgent import browser_agent
from Features.MSGraphAPI import MSGraphAPI
from Features.CADAgent import cad_agent
from Features.OutboundAgent import outbound_agent
from Features.ComplianceSentinel import compliance_sentinel
from Features.TimelineMonitor import timeline_monitor

# --- 1. Delegation Engine ---
def delegate_task(from_user, to_user, task_raw):
    add_delegation(from_user, to_user, task_raw)
    speak(f"I have delegated that task to {to_user.capitalize()}.")

def check_delegations(user):
    pending = get_pending_delegations(user)
    if pending:
        speak(f"{user.capitalize()}, you have {len(pending)} pending tasks delegated to you.")
        for d in pending:
            speak(f"From {d['from'].capitalize()}: {d['task']}")
            speak("Mark as complete?")
            resp = understand()
            if "yes" in resp:
                complete_delegation(d['id'])

# --- 2. Unified Email Triage (Gmail + Outlook) ---
def autonomous_email_triage(user):
    provider = os.getenv("ELIO_EMAIL_PROVIDER", "gmail").lower()
    if provider == "outlook":
        _outlook_triage(user)
    else:
        _gmail_triage(user)

def _gmail_triage(user):
    service = _get_gmail_service()
    if not service: return
    try:
        results = service.users().messages().list(userId='me', q="is:unread", maxResults=5).execute()
        messages = results.get('messages', [])
        for msg in messages:
            m = service.users().messages().get(userId='me', id=msg['id']).execute()
            sender = next((h['value'] for h in m['payload']['headers'] if h['name'] == 'From'), 'Unknown')
            subject = next((h['value'] for h in m['payload']['headers'] if h['name'] == 'Subject'), 'No Subject')
            speak(f"Processing Gmail from {sender}.")
            # Logic for drafting...
    except Exception as e: print(f"Gmail Error: {e}")

def _outlook_triage(user):
    ms = MSGraphAPI()
    emails = ms.get_unread_emails(max_results=5)
    for email in emails:
        sender = email['from']['emailAddress']['name']
        subject = email['subject']
        speak(f"Priority Outlook email from {sender}. Drafting reply.")
        ms.create_draft(email['id'], f"Re: {subject}", "Elio is processing this request.")
        add_private_memory(user, f"Outlook Draft created for {sender}", tags=["outlook", "agentic"])

# --- 3. Executive Standup & Timeline Monitor ---
def executive_standup(user):
    speak(f"Good morning {user.capitalize()}. Initializing Executive Standup.")
    # Run Timeline Monitor (Ghost-Writer)
    milestones = timeline_monitor.scan_for_upcoming_milestones(user)
    if milestones:
        speak(f"I've identified {len(milestones)} upcoming milestones and pre-drafted the necessary outcomes.")
    
    # Financials...
    invoices = get_overdue_invoices()
    if invoices:
        speak(f"Financial Risk Detected: {len(invoices)} overdue invoices.")

# --- 4. Site Pulse (Vision Compliance) ---
def run_site_pulse_audit(user, image_path):
    from Features.Vision import analyze_image_with_vision
    speak("Activating Site-Pulse Vision Compliance Sentinel.")
    prompt = "Identify NEC/OSHA violations in this construction site photo. Propose specific corrections."
    analysis = analyze_image_with_vision(image_path, prompt)
    # ComplianceSentinel.audit_visual_stream is called internally by analyze_image_with_vision
    return analysis

# --- 5. CAD Automation Bridge ---
def run_cad_bridge(command):
    speak(f"Executing CAD automation command: {command}")
    return cad_agent.execute_command(command)

# --- 6. Negotiation Suite ---
def run_vendor_negotiation(user, vendor, target, current):
    speak(f"Initiating autonomous negotiation with {vendor}.")
    return outbound_agent.initiate_negotiation(user, vendor, target, current)

# --- 7. Digital Double Actions ---
def execute_digital_double(user, action_type, data):
    speak(f"Executing Digital Double action: {action_type}")
    if action_type == "reconcile":
        return browser_agent.reconcile_receipt(os.getenv("QB_URL"), os.getenv("QB_USER"), os.getenv("QB_PASS"), data)
    return "Unsupported action."
