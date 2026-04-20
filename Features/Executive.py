from Features.Face.Mouth import speak
from Features.Face.Ear import understand
from Features.MemoryStore import add_private_memory, add_todo
from Brain.AI_Brain import ReplyBrain
import datetime

def rfp_summarizer(user: str):
    speak("Please provide the text of the RFP or say the main points.")
    content = understand(time=15)
    if not content:
        speak("I didn't catch the RFP content.")
        return
    speak("Analyzing the RFP. Please wait.")
    prompt = f"Summarize the following RFP and extract key technical requirements, deadlines, and risks:\n{content}"
    summary = ReplyBrain(prompt)
    speak("Here is the summary:")
    speak(summary)
    add_private_memory(user, f"RFP Summary:\n{summary}", tags=["rfp", "professional"])

def bid_analysis(user: str):
    # Mocking integration with an estimating system
    speak("Currently, we have 4 million dollars in bids out.")
    speak("The Smith Electric bid is due in 4 hours, and the final schematic is missing.")
    add_private_memory(user, "Checked bid status: 4M outstanding. Smith Electric due soon.", tags=["bid", "professional"])

def site_note(user: str):
    speak("What is the site note?")
    note = understand(time=10)
    if not note:
        speak("I didn't hear a note.")
        return
    # Add to todo as an action item
    add_todo(user, f"Site Action Item: {note}")
    speak("I have added that as a high-priority action item.")

from Features.QuickBooksOAuth import create_quickbooks_expense

def log_expense(user: str):
    speak("What was the expense for?")
    account_name = understand(time=5)
    speak("How much was it?")
    amount_text = understand()
    try:
        amount = float(''.join(filter(lambda x: x.isdigit() or x == '.', amount_text)))
    except ValueError:
        amount = 0.0
        
    speak("Which project or job is this for?")
    project_name = understand(time=5)
    
    speak(f"I am logging an expense of {amount} dollars for {account_name} against project {project_name}. Say 'Yes, sync it' to confirm.")
    confirm = understand()
    if "yes" in confirm or "sync" in confirm:
        result = create_quickbooks_expense(amount, account_name, project_name)
        speak(result)
        add_private_memory(user, f"QuickBooks Sync: {amount} for {account_name}", tags=["expense", "financial"])
    else:
        speak("Okay, I have saved the expense details locally instead.")
        add_private_memory(user, f"Local Expense: {amount} for {account_name}", tags=["expense", "pending"])

def family_memory(user: str):
    speak("What family or gift memory should I save?")
    memory = understand(time=10)
    if not memory:
        speak("I didn't catch that.")
        return
    add_private_memory(user, memory, tags=["family", "personal", "gift"])
    speak("I've saved that personal detail.")

def travel_autopilot(user: str):
    # Mocking integration with travel APIs
    speak("Checking your upcoming travel.")
    speak("Your flight to the Vegas expo next week is currently on time. I have marked your hotel for late check-in just in case.")

def wellness_shield(user: str):
    speak("Would you like me to block off 2 hours for Deep Work on your calendar?")
    confirm = understand()
    if "yes" in confirm or "sure" in confirm:
        # Here we would normally call the Calendar API to block time
        speak("I have blocked your calendar for Deep Work. I will hold all non-emergency notifications.")
        add_private_memory(user, f"Blocked deep work at {datetime.datetime.now()}", tags=["wellness"])
    else:
        speak("Okay, I won't block time right now.")

def shadow_inbox(user: str):
    # Mocking Shadow Inbox
    speak("Reviewing your Shadow Inbox.")
    speak("You have 3 emails requiring action, 10 informational emails, and 5 junk emails.")
    speak("Would you like me to read the ones requiring action?")
    confirm = understand()
    if "yes" in confirm:
        speak("One from Metro Power regarding the contract. One from the foreman about the Smith job. And one from HR.")

def crm_check(user: str):
    # Mocking CRM
    speak("You haven't checked in with the CEO of Metro Power in 30 days.")
    speak("Would you like me to draft a catching up email?")
    confirm = understand()
    if "yes" in confirm:
        add_private_memory(user, "Draft: Catching up with Metro Power CEO.", tags=["crm", "email"])
        speak("I've saved a draft in your memory bank.")
    else:
        speak("Okay, I will remind you next week.")

def emergency_protocol(user: str):
    speak("Emergency Protocol Activated.")
    speak("I am texting the executive team and clearing your calendar for the next 4 hours.")
    # Mocking text and calendar clear
    add_private_memory(user, f"Emergency Protocol Activated at {datetime.datetime.now()}", tags=["emergency"])
    speak("Please stay safe. Let me know if you need directions to the site.")
