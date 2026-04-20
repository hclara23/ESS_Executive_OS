import os
import json
import traceback
from Features.Face.Mouth import speak
from Features.Face.Ear import understand
from Features.MemoryStore import log_audit_action
from server.ai_provider import chat_completion

DYNAMIC_SKILL_FILE = os.path.join("Data", "dynamic_skills.json")

def load_dynamic_skills():
    """Loads dynamically generated skills from JSON mapping trigger phrases to python code strings."""
    if not os.path.exists(DYNAMIC_SKILL_FILE):
        return {}
    try:
        with open(DYNAMIC_SKILL_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading dynamic skills: {e}")
        return {}

def save_dynamic_skill(trigger_phrase: str, python_code: str):
    skills = load_dynamic_skills()
    skills[trigger_phrase.lower()] = python_code
    os.makedirs("Data", exist_ok=True)
    with open(DYNAMIC_SKILL_FILE, "w", encoding="utf-8") as f:
        json.dump(skills, f, indent=4)
    print(f"Saved dynamic skill for trigger: {trigger_phrase}")


def execute_dynamic_skill(user: str, python_code: str):
    """Executes the raw python code using exec(). Context is injected so it can use standard functions."""
    # Create an execution environment dictionary with available tools
    global_env = globals().copy()
    local_env = {"user": user}
    
    try:
        # We execute the python code. The code itself should define the execution logic.
        exec(python_code, global_env, local_env)
        
        # We expect the code to define a function `execute_skill(user)`
        if "execute_skill" in local_env:
            local_env["execute_skill"](user)
        elif "execute_skill" in global_env:
            global_env["execute_skill"](user)
        else:
            # Maybe the code just runs sequentially. That's fine too.
            pass
            
    except Exception as e:
        error_msg = f"Failed to run dynamic skill. Check logs. Error: {e}"
        print(error_msg)
        print(traceback.format_exc())
        speak("I encountered an error running that dynamic skill.")


def audit_self(user: str):
    """Reads GEMINI.md and uses OpenAI to describe Elio's features to the user."""
    speak("Let me audit my own capabilities. Give me a moment.")
    manifesto_path = "GEMINI.md"
    
    if not os.path.exists(manifesto_path):
        speak("I cannot find my system architecture file. I cannot audit myself.")
        return
        
    try:
        with open(manifesto_path, "r", encoding="utf-8") as f:
            manifesto_content = f.read()
            
        prompt = f"""
Here is the raw system architecture and feature list for the Elio Personal Virtual Assistant:

{manifesto_content}

Your task is to describe Elio's capabilities to the user in a conversational, concise, and professional tone.
Provide a 3 or 4 sentence summary of what Elio (you) can do. Speak directly to the user as Elio.
Do not use technical jargon like "RESTful API" or "Postgres". Focus on features like tracking goals,
managing emails, managing quickbooks, saving memories, code oracle, handling delegations, and checking calendar.
"""

        response = chat_completion(
            "capability_audit",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.5
        )
        
        audit_summary = response.choices[0].message.content.strip()
        print(f"Self Audit:\n{audit_summary}")
        speak(audit_summary)
        log_audit_action(user, "SELF_AUDIT", "Elio auditted its own features.")
        
    except Exception as e:
        print(f"Audit error: {e}")
        speak("I encountered an error while trying to summarize my features.")


def create_new_skill(user: str):
    """Prompts the user to define a new skill, uses OpenAI to write Python code, and saves it."""
    speak("I can learn a new skill. What should this new skill do?")
    skill_description = understand(time=15)
    
    if not skill_description or len(skill_description) < 3:
        speak("I didn't catch that. Cancelling skill creation.")
        return
        
    speak(f"Got it. What exact voice phrase should trigger this skill?")
    trigger_phrase = understand(time=10)
    
    if not trigger_phrase or len(trigger_phrase) < 3:
        speak("I didn't catch a trigger phrase. Cancelling skill creation.")
        return
        
    speak("Writing the code for my new skill now. Please wait.")
    
    # We use the advanced GPT-4o for code generation
    prompt = f"""
Generate ONLY RAW PYTHON CODE to fulfill the following skill requested by the user.

Skill description: "{skill_description}"

You must define a single function named exactly:
def execute_skill(user):
    # your logic here

Available context inside the environment:
- `speak(text: str)`: Use this to make the assistant say something out loud.
- `understand(time: int = 5) -> str`: Use this to listen to the user and return transcribed text.
- `user`: A string representing the current user's name ('sandra' or 'alex' or 'unknown').
- You may use standard python libraries (import datetime, random, requests, etc.).

Do NOT include markdown formatting like ```python. Do NOT include any explanations. ONLY pure, valid python code.
"""

    try:
        response = chat_completion(
            "skill_codegen",
            messages=[
                {"role": "system", "content": "You are an expert python software engineer writing code for an AI assistant. Return only raw code."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        
        generated_code = response.choices[0].message.content.strip()
        
        # Clean up markdown if the LLM hallucinated it anyway
        if generated_code.startswith("```python"):
            generated_code = generated_code.replace("```python", "", 1)
        if generated_code.startswith("```"):
            generated_code = generated_code.replace("```", "", 1)
        if generated_code.endswith("```"):
            # Use rsplit to only replace the last occurrence
            generated_code = "```".join(generated_code.rsplit("```", 1))
            
        generated_code = generated_code.strip()
        
        save_dynamic_skill(trigger_phrase, generated_code)
        
        speak(f"Skill learned successfully! You can now trigger it by saying: {trigger_phrase}")
        log_audit_action(user, "SKILL_CREATED", f"Created skill triggered by '{trigger_phrase}'")
        
    except Exception as e:
        print(f"Skill creation error: {e}")
        speak("I failed to write the code for the new skill.")
