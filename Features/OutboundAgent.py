import json
from Features.Face.Mouth import speak
from Features.Email import send_email_stub as send_email

class OutboundAgent:
    def __init__(self):
        self.active_negotiations = []

    def initiate_negotiation(self, user, vendor_name, vendor_email, target_price, current_price):
        """
        Revolutionary Phase 4: Negotiate vendor terms autonomously.
        """
        from server.mail_service import mail_service
        
        speak(f"Starting automated negotiation with {vendor_name} for target price of {target_price}.")
        
        subject = f"Inquiry: Price Adjustment for {vendor_name} Order"
        negotiation_draft = f"Hi {vendor_name},\n\nWe are reviewing our current project costs. " \
                            f"We'd like to reach a target price of ${target_price} for the upcoming order. " \
                            f"Can we discuss a volume discount or term adjustment?\n\nBest,\n{user.capitalize()}'s Assistant (ELIO)"
        
        # Send the email using MailService
        result = mail_service.send_email(
            to_email=vendor_email,
            subject=subject,
            body=negotiation_draft,
            from_user=user
        )
        
        if result.get("status") == "success":
            speak(f"Negotiation email for {vendor_name} has been sent.")
            status = "SENT"
        else:
            msg = result.get("message", "Unknown error")
            speak(f"Failed to send negotiation email: {msg}")
            print(f">> Agentic Outbound Error: {msg}")
            status = "FAILED"
        
        self.active_negotiations.append({
            "vendor": vendor_name,
            "target": target_price,
            "status": status
        })
        
        return f"Negotiation {status.lower()}."

    def prospect_new_leads(self, user, lead_source):
        """
        Revolutionary Phase 4: Identify and contact new project leads.
        """
        speak(f"Prospecting new leads from {lead_source}.")
        # Mocking the outbound sales logic
        return ["Lead A: High Interest", "Lead B: Medium Interest"]

outbound_agent = OutboundAgent()
