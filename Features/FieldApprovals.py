from Features.Face.Mouth import speak
from Features.MemoryStore import add_private_memory
from Features.Face.Ear import understand

def approve_document_voice(user: str, document_id: str) -> str:
    """
    Secures field document approval with a 4-digit PIN challenge.
    """
    speak(f"Elio is requesting authorization for {user} to approve document {document_id}.")
    speak("Please state your 4-digit security PIN.")
    
    pin_attempt = understand()
    
    # Mock PINs for Alex and Sandra (In production, these come from the Profile DB)
    VALID_PINS = {
        "alex": "1234",
        "sandra": "5678",
        "admin": "0000"
    }
    
    clean_pin = "".join(filter(str.isdigit, pin_attempt))
    
    if clean_pin == VALID_PINS.get(user.lower()):
        summary = f"Identity verified for {user}. Document {document_id} has been securely approved."
        speak(summary)
        add_private_memory(user, f"PIN Approved Document: {document_id}", tags=["approval", "security", "pin-verified"])
        return summary
    else:
        summary = "PIN verification failed. Authorization denied."
        speak(summary)
        add_private_memory(user, f"FAILED Approval Attempt for: {document_id} - Incorrect PIN", tags=["security-alert", "warning"])
        return summary

