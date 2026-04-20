import json
import os
from Features.Face.Mouth import speak
from Features.Face.Ear import understand
from Brain.AI_Brain import ReplyBrain

def _load_codes():
    path = "Data/technical_codes.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def search_code_compliance(query):
    """
    Hybrid search: Checks local verified codes first, then asks the AI Brain.
    """
    codes = _load_codes()
    matches = []
    
    # 1. Local Keyword Search (RAG-lite)
    for c in codes:
        if any(word.lower() in c['topic'].lower() or word.lower() in c['details'].lower() for word in query.split()):
            matches.append(c)
    
    if matches:
        response = f"I found {len(matches)} relevant articles in the verified code database.\n"
        for m in matches:
            response += f"According to {m['code']} regarding {m['topic']}: {m['details']}\n"
        return response
    
    # 2. AI Brain Fallback (Engineering Knowledge)
    speak("I couldn't find an exact match in my verified library. Let me check my general engineering knowledge.")
    ai_response = ReplyBrain(f"Answer this electrical engineering or compliance question based on NEC or OSHA standards: {query}")
    return ai_response

def code_oracle_skill(user):
    speak("What compliance or code question can I answer for you?")
    query = understand(time=10)
    if not query:
        speak("I didn't hear a question.")
        return
    
    result = search_code_compliance(query)
    speak(result)
    
    # Proactive Agentic Action: Offer to save to project
    speak("Should I save this code reference to your current project memory?")
    resp = understand()
    if "yes" in resp:
        from Features.MemoryStore import add_private_memory
        add_private_memory(user, f"Code Query: {query}\nResult: {result}", tags=["compliance", "engineering"])
        speak("Saved.")
