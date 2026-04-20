from datetime import datetime, timedelta
from Features.MemoryStore import add_private_memory
from Features.ElioSkills import _get_gmail_service

# Mock database of expected items
EXPECTED_ITEMS = [
    {
        "vendor": "Acme Electrics",
        "email": "sales@acme-electrics-mock.com",
        "type": "Quote",
        "description": "Switchgear Panels",
        "due_date": (datetime.utcnow() - timedelta(days=2)).isoformat(), # Overdue
        "status": "pending"
    },
    {
        "vendor": "Apex HVAC",
        "email": "submittals@apexhvac-mock.com",
        "type": "Submittal",
        "description": "Rooftop RTU Units",
        "due_date": (datetime.utcnow() - timedelta(days=5)).isoformat(), # Overdue
        "status": "pending"
    },
    {
        "vendor": "Steelworks Inc",
        "email": "orders@steelworks-mock.com",
        "type": "Quote",
        "description": "I-Beams",
        "due_date": (datetime.utcnow() + timedelta(days=3)).isoformat(), # Not due yet
        "status": "pending"
    }
]

def process_overdue_vendors(user: str) -> str:
    """
    Checks for overdue quotes and submittals, and drafts follow-up emails via Gmail.
    Returns a summary string of actions taken.
    """
    service = _get_gmail_service()
    if not service:
        return "I could not connect to your Gmail account to draft follow-up emails. Please ensure OAuth credentials are valid."

    now = datetime.utcnow()
    overdue_items = []

    for item in EXPECTED_ITEMS:
        if item["status"] == "pending":
            due = datetime.fromisoformat(item["due_date"])
            if due < now:
                overdue_items.append(item)

    if not overdue_items:
        return "I checked the vendor logs. There are no overdue quotes or submittals at this time."

    drafted_count = 0
    details = []

    for item in overdue_items:
        vendor = item['vendor']
        item_type = item['type']
        desc = item['description']
        email = item['email']
        
        subject = f"ACTION REQUIRED: Overdue {item_type} for {desc}"
        body = f"Hello {vendor} team,\\n\\nOur records indicate we are still waiting on the {item_type} for {desc}, which is now past due. Please provide an update or attach the requested documents as soon as possible to avoid schedule delays.\\n\\nThank you,\\n{user.capitalize()}'s Office"
        
        import base64
        from email.message import EmailMessage
        
        message = EmailMessage()
        message.set_content(body)
        message['To'] = email
        message['From'] = 'me'
        message['Subject'] = subject
        
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {'message': {'raw': encoded_message}}
        
        try:
            draft = service.users().drafts().create(userId="me", body=create_message).execute()
            drafted_count += 1
            details.append(f"{item_type} from {vendor}")
            add_private_memory(user, f"Vendor Hound drafted follow-up to {vendor} for {desc}.", tags=["vendor", "follow-up", "draft"])
        except Exception as e:
            print(f"VendorHound Gmail Error: {e}")

    summary = f"I found {len(overdue_items)} overdue vendor items. I have successfully drafted {drafted_count} follow-up emails in your Gmail for: " + ", ".join(details) + "."
    return summary
