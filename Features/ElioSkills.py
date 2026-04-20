import json
import os
from datetime import datetime, timedelta

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

from Features.Face.Mouth import speak
from Features.Face.Ear import understand
from Features.Confirm import ask_yes_no, is_affirmative
from Features.MemoryStore import (
    add_private_memory,
    add_shared_message,
    add_lesson,
    list_lessons,
    add_todo,
    list_todos,
    get_shared_messages,
    log_audit_action,
)
from Features.Integrations import status_text
from Features.GmailOAuth import _token_path as gmail_token_path
from Features.CalendarOAuth import _token_path as calendar_token_path
from Features.QuickBooksOAuth import (
    setup_status as qb_setup_status,
    get_overdue_invoices,
    create_quickbooks_expense
)
from Features.DanfossAPI import get_danfoss_drive_options, validate_drive_spec
from Features.PostgresStore import config_status as postgres_config_status


def _get_gmail_service():
    path = gmail_token_path()
    if not os.path.exists(path):
        return None
    try:
        creds = Credentials.from_authorized_user_file(path)
        return build("gmail", "v1", credentials=creds)
    except Exception as e:
        print(f"[ElioSkills] Gmail service build failed: {e}")
        return None


def _get_calendar_service():
    path = calendar_token_path()
    if not os.path.exists(path):
        return None
    try:
        creds = Credentials.from_authorized_user_file(path)
        return build("calendar", "v3", credentials=creds)
    except Exception as e:
        print(f"[ElioSkills] Calendar service build failed: {e}")
        return None


def daily_overview(user: str):
    speak("Here is your day.")

    # Calendar
    cal = _get_calendar_service()
    if cal:
        try:
            now = datetime.utcnow().isoformat() + "Z"
            events_result = (
                cal.events()
                .list(
                    calendarId="primary",
                    timeMin=now,
                    maxResults=5,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            events = events_result.get("items", [])
            if not events:
                speak("You have no upcoming meetings.")
            else:
                speak(f"You have {len(events)} upcoming meetings.")
                for event in events:
                    start = event.get("start", {}).get("dateTime") or event.get("start", {}).get("date", "unknown time")
                    speak(f"{event.get('summary', 'Untitled')} at {start}")
        except Exception as e:
            print(f"[ElioSkills] Calendar fetch failed: {e}")
            speak("I could not fetch your calendar right now.")
    else:
        speak("Calendar is not connected yet.")

    # Gmail
    service = _get_gmail_service()
    if service:
        try:
            results = (
                service.users()
                .messages()
                .list(userId="me", labelIds=["INBOX"], q="is:unread", maxResults=5)
                .execute()
            )
            messages = results.get("messages", [])
            if not messages:
                speak("You have no unread emails in your inbox.")
            else:
                speak(f"You have {len(messages)} unread emails.")
        except Exception as e:
            print(f"[ElioSkills] Gmail fetch failed: {e}")
            speak("I could not fetch your emails right now.")
    else:
        speak("Email is not connected yet.")

    shared = get_shared_messages(user, limit=3)
    if shared:
        speak("Shared messages:")
        for item in shared:
            speak(item.get("text", ""))

    if user == "alex":
        speak("Do you want help with customers, quotes, or bids?")
    elif user == "sandra":
        speak("Do you want help with payroll, billing, HR, or scheduling?")
    else:
        speak("Do you want me to help with any of this?")


def email_help(user: str):
    service = _get_gmail_service()
    if service:
        speak("Gmail is connected. I can check your unread messages if you like.")
    else:
        speak("Gmail is not connected yet. Do you want me to set it up later?")


def write_email(user: str):
    speak("Who is it for?")
    to_name = understand()
    speak("What is the recipient's email address?")
    to_email = input("Type email address: ")
    speak("What is the subject?")
    subject = understand()
    speak("What is the body?")
    body = understand(time=10)

    from email.message import EmailMessage
    import base64

    em = EmailMessage()
    em["To"] = to_email
    em["Subject"] = subject
    em.set_content(body)

    encoded_message = base64.urlsafe_b64encode(em.as_bytes()).decode()
    create_message = {"raw": encoded_message}

    speak("I have prepared the email. Say 'Yes, send it' if you want me to send it now.")
    response = understand()
    if is_affirmative(response):
        service = _get_gmail_service()
        if service:
            try:
                service.users().messages().send(userId="me", body=create_message).execute()
                log_audit_action(user, "EMAIL_SEND", f"Sent to {to_email}")
                speak("Email sent successfully.")
            except Exception as e:
                speak(f"Error sending email: {e}")
        else:
            speak("Gmail is not connected yet. I saved the draft locally.")
            add_private_memory(user, f"Draft to {to_email}: {body}", tags=["email", "draft"])
    else:
        speak("Okay. I saved the draft.")
        add_private_memory(user, f"Draft to {to_email}: {body}", tags=["email", "draft"])


def meetings_help(user: str):
    cal = _get_calendar_service()
    if cal:
        speak("Your calendar is connected. I can check your schedule or help set up a meeting.")
    else:
        speak("Your calendar is not connected yet. Do you want me to set it up later?")


def billing_help(user: str):
    invoices = get_overdue_invoices()
    if invoices is None:
        speak("QuickBooks is not connected yet.")
        return
    
    if not invoices:
        speak("Great news! You have no overdue invoices in QuickBooks.")
    else:
        speak(f"You have {len(invoices)} overdue invoices.")
        total = sum([float(i.get("Balance", 0)) for i in invoices])
        speak(f"The total outstanding balance is {total} dollars.")


def quotes_help(user: str):
    speak("Who is it for?")
    customer = understand()
    speak("What is the job?")
    job = understand(time=10)
    draft = f"Quote draft for {customer}. Job: {job}."
    add_private_memory(user, draft, tags=["quote", "draft"])
    speak("I saved a draft.")
    speak("Do you want me to write the email now?")


def sales_help(user: str):
    speak("Who is the customer?")
    customer = understand()
    speak("What is the job?")
    job = understand(time=10)
    draft = f"Sales follow-up for {customer}. Job: {job}."
    add_private_memory(user, draft, tags=["sales", "draft"])
    speak("I saved a draft.")
    speak("Do you want me to write the email now?")


def drive_builder(user: str):
    speak("I can help you find the right Danfoss drive. Tell me the horsepower needed.")
    hp_text = understand()
    try:
        hp = int(''.join(filter(str.isdigit, hp_text)))
    except:
        hp = None
        
    speak("And the voltage?")
    volts_text = understand()
    try:
        voltage = int(''.join(filter(str.isdigit, volts_text)))
    except:
        voltage = None

    options = get_danfoss_drive_options(hp=hp, voltage=voltage)
    if not options:
        speak("I couldn't find an exact match in the Danfoss catalog for those specs.")
    else:
        speak(f"I found {len(options)} matching drives. The most common is the {options[0]['series']} series, part number {options[0]['part']}.")
        add_private_memory(user, f"Drive search: HP={hp}, Volts={voltage}. Result={options[0]['part']}", tags=["drive", "engineering"])


def engineering_support(user: str):
    speak("Tell me what you need help with.")
    details = understand(time=10)
    note = f"Engineering support: {details}."
    add_private_memory(user, note, tags=["engineering"])
    speak("I saved the note.")


def bid_builder(user: str):
    speak("Who is the customer?")
    customer = understand()
    speak("What is the job?")
    job = understand(time=10)
    draft = f"Bid package draft for {customer}. Job: {job}."
    add_private_memory(user, draft, tags=["bid", "draft"])
    speak("I saved a draft.")


def payroll_help(user: str):
    speak("Payroll is not connected yet.")
    speak("Do you want me to set it up later?")


def hr_help(user: str):
    speak("What is the HR task?")
    task = understand(time=10)
    note = f"HR task: {task}."
    add_private_memory(user, note, tags=["hr"])
    speak("I saved it.")


def company_status(user: str):
    speak(qb_setup_status())
    speak("Payroll is not connected yet.")
    speak(postgres_config_status())
    speak("Do you want me to set those up later?")


def schedule_conflicts(user: str):
    cal = _get_calendar_service()
    if not cal:
        speak("Calendar is not connected yet.")
        return

    now = datetime.utcnow().isoformat() + "Z"
    end_of_day = (datetime.utcnow() + timedelta(days=1)).isoformat() + "Z"
    events_result = (
        cal.events()
        .list(
            calendarId="primary",
            timeMin=now,
            timeMax=end_of_day,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_result.get("items", [])
    if not events:
        speak("You have no meetings scheduled for the next 24 hours.")
        return

    conflicts = []
    last_end = None
    for event in events:
        start_str = event["start"].get("dateTime", event["start"].get("date"))
        end_str = event["end"].get("dateTime", event["end"].get("date"))
        if last_end and start_str < last_end:
            conflicts.append(event["summary"])
        last_end = end_str

    if conflicts:
        speak(f"You have potential conflicts with: {', '.join(conflicts)}")
    else:
        speak("You have no overlapping meetings in the next 24 hours.")

def add_todo_item(user: str, task: str = ""):
    task = task.strip()
    if not task:
        speak("What should I remind you about?")
        task = understand()
    if not task:
        speak("I did not get that.")
        return
    add_todo(user, task)
    speak("Got it. I added it.")


def list_todo_items(user: str):
    todos = list_todos(user, limit=10)
    if not todos:
        speak("You have no tasks right now.")
        return
    speak("Here is your list.")
    for item in todos:
        speak(item.get("text", ""))


def share_message(from_user: str, to_user: str, message: str):
    if not message:
        speak("What should I share?")
        message = understand(time=10)
    if ask_yes_no(f"Should I share this with {to_user.capitalize()}?"):
        add_shared_message(from_user, to_user, message)
        speak("Got it. I shared it.")
    else:
        speak("Okay. I will not share it.")


def save_lesson(user: str, text: str = ""):
    lesson = text.strip()
    if not lesson:
        speak("Please say the lesson.")
        lesson = understand(time=10)
    if not lesson:
        speak("I did not get that.")
        return
    add_lesson(user, lesson, tags=["lesson"])
    speak("Got it. I saved the lesson.")


def read_lessons(user: str):
    lessons = list_lessons(user, limit=5)
    if not lessons:
        speak("No lessons saved yet.")
        return
    speak("Here are the latest lessons.")
    for item in lessons:
        speak(item.get("text", ""))
