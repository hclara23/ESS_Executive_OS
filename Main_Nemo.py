print(">> Starting Elio : Wait for a few seconds.")
import threading
import time
from getpass import getuser

from Features.Face.Mouth import speak
from Features.Face.Ear import listen, understand
from Features.Proactive import run_proactive_cycle
from Features.VoiceID import enroll_voice, identify_speaker
from Features.ProjectManagement import project_overview_skill
from Features.TechIntel import code_oracle_skill
from Features.BiddingHub import find_suitable_bids, prefill_submittal, submit_bid
from Features.Verification import verify_user, set_pass, set_user
from Features.GreetMe import greet
from Features.DataCheck import isBlank, isCorrect
from Features.Mode import resolve_user
from Features.Confirm import ask_yes_no
from Features.MemoryStore import add_private_memory
from Features.ElioSkills import (
    daily_overview,
    email_help,
    write_email,
    meetings_help,
    billing_help,
    quotes_help,
    add_todo_item,
    list_todo_items,
    share_message,
    save_lesson,
    read_lessons,
    sales_help,
    drive_builder,
    engineering_support,
    bid_builder,
    payroll_help,
    hr_help,
    company_status,
    schedule_conflicts,
)
from Features.Executive import (
    rfp_summarizer,
    bid_analysis,
    site_note,
    log_expense,
    family_memory,
    travel_autopilot,
    wellness_shield,
    shadow_inbox,
    crm_check,
    emergency_protocol,
)
from Features.AgenticWorkflows import (
    delegate_task,
    check_delegations,
    autonomous_email_triage,
    executive_standup,
    site_vision_analysis,
    cash_flow_forecast,
)
from Features.SkillFactory import (
    audit_self,
    create_new_skill,
    load_dynamic_skills,
    execute_dynamic_skill,
)
from Features.GmailOAuth import connect_stub as gmail_connect
from Features.CalendarOAuth import connect_stub as calendar_connect
from Features.PostgresStore import (
    sync_stub as postgres_sync_stub,
    sync_postgres,
    ensure_schema,
)


def _read_text(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except OSError as e:
        return f"(Could not read file: {e})"


def _extract_after(command, phrases):
    for p in phrases:
        if p in command:
            return command.split(p, 1)[1].strip()
    return ""


def _role_blocked(user, allowed_for):
    if user in allowed_for or user == "unknown":
        return False
    target = "sandra" if user == "alex" else "alex"
    speak(f"This is for {target.capitalize()}.")
    return True


# ---------------------------------------------------------------------------
# Command registry: (trigger_phrases, handler_fn, allowed_roles_or_None)
# handler_fn signature: handler(user, command) -> None
# allowed_roles: list of usernames, or None meaning any user
# ---------------------------------------------------------------------------

def _cmd_rfp(user, _cmd):             rfp_summarizer(user)
def _cmd_bid_analysis(user, _cmd):    bid_analysis(user)
def _cmd_site_note(user, _cmd):       site_note(user)
def _cmd_log_expense(user, _cmd):     log_expense(user)
def _cmd_family_memory(user, _cmd):   family_memory(user)
def _cmd_travel(user, _cmd):          travel_autopilot(user)
def _cmd_wellness(user, _cmd):        wellness_shield(user)
def _cmd_shadow_inbox(user, _cmd):    shadow_inbox(user)
def _cmd_crm(user, _cmd):             crm_check(user)
def _cmd_emergency(user, _cmd):       emergency_protocol(user)
def _cmd_standup(user, _cmd):         executive_standup(user)
def _cmd_site_vision(user, _cmd):     site_vision_analysis(user)
def _cmd_cash_flow(user, _cmd):       cash_flow_forecast(user)
def _cmd_daily(user, _cmd):           daily_overview(user)
def _cmd_email_check(user, _cmd):     email_help(user)
def _cmd_email_write(user, _cmd):     write_email(user)
def _cmd_meetings(user, _cmd):        meetings_help(user)
def _cmd_quotes(user, _cmd):          quotes_help(user)
def _cmd_todos_list(user, _cmd):      list_todo_items(user)
def _cmd_company(user, _cmd):         company_status(user)
def _cmd_schedule(user, _cmd):        schedule_conflicts(user)
def _cmd_enroll_voice(user, _cmd):    enroll_voice(user)
def _cmd_project_status(user, _cmd):  project_overview_skill(user)
def _cmd_code_check(user, _cmd):      code_oracle_skill(user)
def _cmd_audit(user, _cmd):           audit_self(user)
def _cmd_new_skill(user, _cmd):       create_new_skill(user)

def _cmd_billing(user, _cmd):
    if not _role_blocked(user, ["sandra"]):
        billing_help(user)

def _cmd_payroll(user, _cmd):
    if not _role_blocked(user, ["sandra"]):
        payroll_help(user)

def _cmd_hr(user, _cmd):
    if not _role_blocked(user, ["sandra"]):
        hr_help(user)

def _cmd_sales(user, _cmd):
    if not _role_blocked(user, ["alex"]):
        sales_help(user)

def _cmd_drive_builder(user, _cmd):
    if not _role_blocked(user, ["alex"]):
        drive_builder(user)

def _cmd_engineering(user, _cmd):
    if not _role_blocked(user, ["alex"]):
        engineering_support(user)

def _cmd_bid_builder(user, _cmd):
    if not _role_blocked(user, ["alex"]):
        bid_builder(user)

def _cmd_remind(user, cmd):
    task = _extract_after(cmd, ["remind me to"])
    if task:
        add_todo_item(user, task)

def _cmd_tell_sandra(user, cmd):
    msg = _extract_after(cmd, ["tell sandra that", "tell sandra", "let sandra know"])
    share_message(user, "sandra", msg)

def _cmd_tell_alex(user, cmd):
    msg = _extract_after(cmd, ["tell alex that", "tell alex", "let alex know"])
    share_message(user, "alex", msg)

def _cmd_delegate_alex(user, cmd):
    task = _extract_after(cmd, ["tell alex to", "ask alex to"])
    delegate_task(user, "alex", task)

def _cmd_delegate_sandra(user, cmd):
    task = _extract_after(cmd, ["tell sandra to", "ask sandra to"])
    delegate_task(user, "sandra", task)

def _cmd_lesson(user, cmd):
    lesson = _extract_after(cmd, ["lesson learned", "remember this", "save lesson"])
    save_lesson(user, lesson)

def _cmd_private(user, cmd):
    note = _extract_after(cmd, ["this is private", "keep this to me"])
    if not note:
        if ask_yes_no("Do you want me to save a private note?"):
            speak("Say the note now.")
            note = understand(time=10)
    if note:
        add_private_memory(user, note, tags=["private"])
    speak("Got it. I will keep this private.")

def _cmd_intro(user, _cmd):
    speak(_read_text("Data/intro.txt"))

def _cmd_skills_list(user, _cmd):
    speak("Here are my skills.")
    speak(_read_text("Data/skills.txt"))

def _cmd_correction(user, _cmd):
    speak("I apologize for the mistake. What should I have done or said instead?")
    correction = understand(time=10)
    if correction:
        save_lesson(user, f"Correction: When I said/did something wrong, the user told me: {correction}")
        speak("Thank you. I have learned from this and will do better next time.")

def _cmd_connect_gmail(user, _cmd):     speak(gmail_connect())
def _cmd_connect_calendar(user, _cmd): speak(calendar_connect())
def _cmd_connect_postgres(user, _cmd): speak(postgres_sync_stub())
def _cmd_sync_postgres(user, _cmd):    speak(sync_postgres())

def _cmd_setup_postgres(user, _cmd):
    if ensure_schema():
        speak("Postgres tables are ready.")
    else:
        speak("Postgres is not ready.")

def _cmd_negotiate(user, cmd):
    from Features.OutboundAgent import outbound_agent
    vendor = _extract_after(cmd, ["negotiate with", "start negotiation"])
    speak(f"Negotiating with {vendor}. What is your target price?")
    target = understand()
    outbound_agent.initiate_negotiation(user, vendor, target, "unknown")

def _cmd_digital_double(user, _cmd):
    from Features.AgenticWorkflows import execute_digital_double_action
    execute_digital_double_action(user)

def _cmd_set_password(user, _cmd):
    if verify_user(isnewpass=1):
        set_pass()

def _cmd_add_user(user, _cmd):
    if verify_user(isnewpass=0, setnewuser=True):
        set_user()

def _cmd_find_bids(user, _cmd):          find_suitable_bids(user)

def _cmd_draft_proposal(user, cmd):
    bid_id = _extract_after(cmd, ["draft proposal for bid", "write proposal for bid"]).upper().replace(" ", "").replace("-", "")
    if bid_id:
        prefill_submittal(user, bid_id)
    else:
        speak("Please specify the bid ID.")

def _cmd_submit_bid(user, cmd):
    bid_id = _extract_after(cmd, ["submit bid", "send bid"]).upper().replace(" ", "").replace("-", "")
    if bid_id:
        submit_bid(user, bid_id)
    else:
        speak("Please specify the bid ID.")

def _cmd_temperature(user, cmd):
    from Features.Temperature import check_temperature
    speak(check_temperature(cmd))

def _cmd_datetime(user, cmd):
    from Features.DateTime import check_datetime
    speak(check_datetime(cmd))

def _cmd_open(user, cmd):
    from Features.AppControl import OpenExecute
    OpenExecute(cmd)

def _cmd_close(user, cmd):
    from Features.AppControl import CloseExecute
    CloseExecute(cmd)

def _cmd_screenshot(user, _cmd):
    from Features.Screenshot import take_screenshoot
    take_screenshoot()

def _cmd_whatsapp(user, _cmd):
    from Features.Whatsapp import send_msg
    send_msg()

def _cmd_set_schedule(user, _cmd):
    from Features.Schedule import set_schedule
    set_schedule()

def _cmd_show_schedule(user, _cmd):
    from Features.Schedule import get_schedule
    get_schedule()

def _cmd_location(user, _cmd):
    from Features.GmapLocation import Getmylocation
    Getmylocation()

def _cmd_direction(user, _cmd):
    from Features.GmapLocation import Getgmaplocation
    speak("Please tell me your destination location.")
    subject = understand()
    subject = isBlank(subject, topic_msg="me your destination location.")
    if isCorrect(subject):
        subject = subject.capitalize()
    else:
        speak("Type the destination location below.")
        subject = input("Enter the destination location: ")
    Getgmaplocation(subject)


# Registry: list of (triggers, handler). First match wins.
# Ordered from most-specific to least-specific to prevent short-phrase hijacking.
_COMMAND_REGISTRY = [
    (["audit yourself", "what are your features", "tell me what you can do"], _cmd_audit),
    (["create a new skill", "learn a skill", "make a new skill"], _cmd_new_skill),
    (["summarize this rfp", "read rfp"], _cmd_rfp),
    (["bid analysis", "check bids"], _cmd_bid_analysis),
    (["site note", "new site note"], _cmd_site_note),
    (["log expense", "new expense"], _cmd_log_expense),
    (["family memory", "save family detail"], _cmd_family_memory),
    (["travel autopilot", "check my travel"], _cmd_travel),
    (["wellness shield", "deep work"], _cmd_wellness),
    (["shadow inbox", "check shadow inbox"], _cmd_shadow_inbox),
    (["crm check", "relationship management"], _cmd_crm),
    (["site emergency", "emergency protocol"], _cmd_emergency),
    (["tell alex to", "ask alex to"], _cmd_delegate_alex),
    (["tell sandra to", "ask sandra to"], _cmd_delegate_sandra),
    (["executive standup", "morning briefing"], _cmd_standup),
    (["analyze site photo", "check site photo"], _cmd_site_vision),
    (["cash flow forecast", "financial prediction"], _cmd_cash_flow),
    (["negotiate with", "start negotiation"], _cmd_negotiate),
    (["reconcile portal", "digital double action"], _cmd_digital_double),
    (["introduce", "intro", "introduction"], _cmd_intro),
    (["things you can do", "your skills", "skill"], _cmd_skills_list),
    (["this is private", "keep this to me"], _cmd_private),
    (["tell sandra", "let sandra know"], _cmd_tell_sandra),
    (["tell alex", "let alex know"], _cmd_tell_alex),
    (["lesson learned", "remember this", "save lesson"], _cmd_lesson),
    (["read lessons", "lessons learned"], _cmd_todos_list),
    (["you are wrong", "that is incorrect", "incorrect", "not right", "that's wrong"], _cmd_correction),
    (["what do i have today", "what's going on today", "elio, today", "elio today", "elio, morning", "elio morning"], _cmd_daily),
    (["check my email", "important emails", "help with my email"], _cmd_email_check),
    (["write an email", "reply to this email", "answer that email", "send email"], _cmd_email_write),
    (["do i have meetings today", "set up a meeting", "find time to meet"], _cmd_meetings),
    (["who owes us money", "unpaid invoices", "check billing", "billing"], _cmd_billing),
    (["follow up with a customer", "write a quote email", "remind them about the quote"], _cmd_quotes),
    (["remind me to"], _cmd_remind),
    (["what do i need to do", "did i forget anything"], _cmd_todos_list),
    (["payroll"], _cmd_payroll),
    (["hr", "employee issue", "admin task"], _cmd_hr),
    (["company status", "how are we doing"], _cmd_company),
    (["check my schedule", "do i have conflicts"], _cmd_schedule),
    (["help me with a customer", "write a sales email"], _cmd_sales),
    (["connect gmail", "connect email"], _cmd_connect_gmail),
    (["connect calendar"], _cmd_connect_calendar),
    (["connect postgres", "connect database"], _cmd_connect_postgres),
    (["sync postgres", "sync database"], _cmd_sync_postgres),
    (["setup postgres", "create database tables"], _cmd_setup_postgres),
    (["build a drive", "danfoss drive", "what drive fits"], _cmd_drive_builder),
    (["build a schematic", "explain this drive", "does this meet spec"], _cmd_engineering),
    (["build a bid", "make a bid package", "help with a proposal"], _cmd_bid_builder),
    (["set new password"], _cmd_set_password),
    (["enroll my voice", "voice id enrollment"], _cmd_enroll_voice),
    (["project status", "project update"], _cmd_project_status),
    (["check code", "nec requirement", "compliance question"], _cmd_code_check),
    (["find suitable bids", "search for bids", "new bids"], _cmd_find_bids),
    (["draft proposal for bid", "write proposal for bid"], _cmd_draft_proposal),
    (["submit bid", "send bid"], _cmd_submit_bid),
    (["add new user"], _cmd_add_user),
    (["temperature", "weather"], _cmd_temperature),
    (["time", "date", "day", "week", "year"], _cmd_datetime),
    (["search", "visit", "open", "launch", "start"], _cmd_open),
    (["close"], _cmd_close),
    (["screenshot"], _cmd_screenshot),
    (["whatsapp", "send message"], _cmd_whatsapp),
    (["make schedule", "add schedule", "set schedule", "add to schedule"], _cmd_set_schedule),
    (["show schedule", "my schedule", "schedule"], _cmd_show_schedule),
    (["my location", "location", "current location"], _cmd_location),
    (["direction", "show direction", "show me direction"], _cmd_direction),
]


def _dispatch(user, command):
    # Dynamic skills checked first
    dyn_skills = load_dynamic_skills()
    for trigger, code in dyn_skills.items():
        if trigger in command:
            print(f">> Triggered dynamic skill: {trigger}")
            execute_dynamic_skill(user, code)
            return True

    for triggers, handler in _COMMAND_REGISTRY:
        if any(t in command for t in triggers):
            try:
                handler(user, command)
            except Exception as e:
                print(f"[Skill Error] {handler.__name__}: {e}")
                speak("I ran into an issue with that. Please try again.")
            return True
    return False


def MainExecution(user):
    check_delegations(user)

    while True:
        try:
            command = understand()
        except Exception as e:
            print(f"[Listen Error] {e}")
            speak("I had trouble hearing that. Please try again.")
            continue

        if len(command) <= 3:
            speak("I did not get that. Please say it again.")
            continue

        if "go to sleep" in command or "sleep" in command:
            speak("Okay. You can call me anytime.")
            break

        if "shutdown" in command or "finally sleep" in command:
            speak("Goodbye. See you soon.")
            exit()

        if not _dispatch(user, command):
            speak("I do not have that yet.")


def wakeup_detected(user):
    print('Say "wake up" to start or "shutdown" to quit.')
    command = listen()

    if "wake up" in command:
        from Features.Face.Mouth import set_user
        set_user(user)
        speak(f"{greet()} I'm Elio. I'm ready to help.")
        MainExecution(user)
    elif "shutdown" in command or "finally sleep" in command:
        speak("Goodbye. See you soon.")
        exit()


def _proactive_loop(user):
    while True:
        try:
            run_proactive_cycle()
            autonomous_email_triage(user)
        except Exception as e:
            print(f"[Proactive Loop] Error: {e}")
        time.sleep(300)


def ThisMain():
    if verify_user():
        user = resolve_user()

        p_thread = threading.Thread(target=_proactive_loop, args=(user,), daemon=True)
        p_thread.start()

        speak(f"Welcome, {getuser().capitalize()}!")
        speak("Say \"wake up\" to start or \"shutdown\" to quit.")
        while True:
            wakeup_detected(user)
    else:
        exit()


if __name__ == "__main__":
    ThisMain()
