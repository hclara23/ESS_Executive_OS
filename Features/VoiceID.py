import os
import json
import time
from Features.Face.Mouth import speak
from Features.Face.Ear import understand, listen

def enroll_voice(user: str):
    """
    Simulates capturing a voice profile for the user.
    """
    speak(f"Starting Voice ID enrollment for {user.capitalize()}.")
    speak("Please repeat the following phrase exactly after I say it.")
    passphrase = "The electrical grid is the backbone of modern engineering."
    speak(passphrase)
    
    # Simulate capturing audio data
    attempt = understand(time=10)
    
    if passphrase.lower() in attempt.lower():
        speak("Voice fingerprint captured successfully.")
        # In a real app, we'd save a MFCC or embedding file
        fingerprint_dir = "Data/VoiceProfiles"
        if not os.path.exists(fingerprint_dir): os.makedirs(fingerprint_dir)
        
        profile = {
            "user": user,
            "enrolled_at": time.ctime(),
            "phrase_verified": True
        }
        with open(f"{fingerprint_dir}/{user}_profile.json", "w") as f:
            json.dump(profile, f)
        
        speak(f"You are now enrolled. I can identify you by your voice in the future.")
        return True
    else:
        speak("I couldn't verify the phrase. Please try enrollment again later.")
        return False

def identify_speaker():
    """
    Mock function to identify who is speaking based on voice profile.
    """
    # In real app: Capture audio -> generate embedding -> compare with Data/VoiceProfiles/
    # For now, we'll return the system user or a default
    from getpass import getuser
    return getuser().lower()
