import os
import json
from dotenv import load_dotenv
from server.ai_provider import chat_completion
from server.subagent_client import call_subagent

load_dotenv()

def analyze_file_intent(filename, prompt):
    """
    Uses Elio's brain to determine the category and intended action for an uploaded file.
    """
    subagent_result = call_subagent(
        "/tasks/classify-upload",
        {"filename": filename, "prompt": prompt or ""},
        timeout=15,
    )
    if subagent_result:
        return subagent_result
    
    system_prompt = """
    You are Elio's Intelligent Intake Router.
    Analyze the filename and the user's prompt to determine where the file should be stored and what processing should occur.
    
    Categories: receipts, manuals, blueprints, legal, bids, media, general.
    Actions: ProcessExpense, AddToLibrary, AuditBlueprint, Summarize, Archive.
    
    Return ONLY a JSON object:
    {
      "category": "...",
      "action": "...",
      "thought_process": "Brief explanation of why"
    }
    """
    
    user_input = f"Filename: {filename}\nUser Prompt: {prompt if prompt else 'Process this file'}"
    
    try:
        response = chat_completion(
            "intake",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Intake Analysis Error: {e}")
        return {"category": "general", "action": "Archive", "thought_process": "Fallback due to error"}
