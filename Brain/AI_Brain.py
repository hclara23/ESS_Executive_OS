import json
import os
from datetime import datetime
from dotenv import load_dotenv

from server.ai_provider import chat_completion
from server.personality import get_personality

load_dotenv()


def _get_personality():
    return get_personality()


def _get_latest_lessons():
    # Only if we can connect to PG
    from Features.MemoryStore import list_lessons
    try:
        lessons = list_lessons("admin", limit=3)
        if lessons:
            return "\n".join([f"- {l['text']}" for l in lessons])
    except:
        pass
    return ""


import time

_DOC_CACHE = {"content": "", "last_loaded": 0}

def _load_all_markdown():
    """
    Dynamically loads all root .md files with a 10-minute cache to ensure Elio is aware of capabilities without lag.
    """
    global _DOC_CACHE
    now = time.time()
    if _DOC_CACHE["content"] and (now - _DOC_CACHE["last_loaded"] < 600):
        return _DOC_CACHE["content"]

    docs = []
    try:
        for file in os.listdir("."):
            if file.endswith(".md"):
                with open(file, "r", encoding="utf-8") as f:
                    docs.append(f"--- FILE: {file} ---\n{f.read()}\n")
        _DOC_CACHE["content"] = "\n".join(docs)
        _DOC_CACHE["last_loaded"] = now
    except Exception as e:
        print(f"Error loading system markdown: {e}")
    return _DOC_CACHE["content"]


def _get_capability_summary():
    """
    Returns a very lightweight summary of Elio's core pillars to save tokens and improve latency.
    """
    return """
    CORE PILLARS: 
    1. AI Memory (Refiner/Evolution/pgvector)
    2. Strategic Bidding (Hub V2/Scouting/Profit Modeling)
    3. Field Intelligence (Live Meeting Hub/Intelligent Intake/Vision Ledger)
    4. Executive Automation (PDF Reports/Podcast/Workflows)
    5. Integrations (QuickBooks/Jira/Procore/WhatsApp/Slack)
    Refer to Live Docs for technical details if specifically asked.
    """

def ReplyBrain(question, chat_log=None, user_override=None):
    # Attempt to resolve user for context
    from Features.Mode import resolve_user
    from Features.Onboarding import get_profile
    from Features.MemoryStore import get_second_brain_facts
    
    user_key = user_override if user_override else resolve_user()
    profile = get_profile(user_key)
    brain_facts = get_second_brain_facts(user_key)
    
    # Format Second Brain knowledge
    brain_context = "\n".join([f"- {f['key']}: {f['value']}" for f in brain_facts])

    # Fetch Autonomous AI Insights
    from Features.MemoryRefiner import get_recent_insights
    ai_insights = get_recent_insights(user_key, limit=5)
    insights_context = "\n".join([f"- [{i['category'].upper()}] {i['content']}" for i in ai_insights])

    user_context = f"User: {profile.get('full_name', user_key.capitalize()) if profile else user_key.capitalize()}\nRole: {profile.get('role', 'Executive') if profile else 'Executive'}"

    personality = get_personality(user_key)
    from Features.Face.Mouth import set_user
    set_user(user_key)
    
    lessons = _get_latest_lessons()

    # SPEED OPTIMIZATION: Only load full docs for capability queries
    is_capability_query = any(word in question.lower() for word in ["what can you do", "features", "capabilities", "how do you work", "help", "instructions"])
    
    if is_capability_query:
        system_capabilities = _load_all_markdown()
    else:
        system_capabilities = _get_capability_summary()

    system_prompt = f"""{user_context}
    Persona: {personality.get('persona', '')}
    Tone: {profile.get('tone', personality.get('tone', 'professional'))}
    Special Instructions: {personality.get('instructions', '')}

    Second Brain (Core Facts):
    {brain_context}

    Autonomous AI Insights (Learned from Context):
    {insights_context}

    Latest Lessons:
    {lessons}


SYSTEM CAPABILITIES (Live Context):
{system_capabilities}

Agentic Instructions: 
You are an ELITE AGENTIC virtual assistant named Elio. Do not just answer questions passively.
CRITICAL MANDATES:
1. CAPABILITY AWARENESS: You are a production-grade enterprise assistant. You MUST strictly adhere to the features defined in the Live Docs above.
2. SKILL BUILDING: Proactively offer to automate repetitive tasks via the Skill Factory.
3. SELF-EVOLUTION: Improve yourself autonomously based on logs.
4. DEEP MEMORY: Use `save_to_vector_memory` for strategic facts.
"""

    try:
        # Build messages payload starting with System Prompt
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Append historical chat from DB
        from Features.MemoryStore import get_chat_history
        # Limit to last 15 interactions to save tokens while keeping context
        history = get_chat_history(user_key, limit=30) 
        
        for msg in history:
            role = "assistant" if msg["role"] == "agent" else "user"
            messages.append({"role": role, "content": msg["content"]})
            
        # Append the new user question
        messages.append({"role": "user", "content": question})
        
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "save_to_memory_bank",
                    "description": "Saves an important fact, preference, or goal about the user to their permanent Second Brain.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "fact_key": {"type": "string", "description": "Short category or subject of the fact."},
                            "fact_value": {"type": "string", "description": "The actual detail to remember."}
                        },
                        "required": ["fact_key", "fact_value"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "save_lesson",
                    "description": "Saves a correction, rule, or learned lesson about how the assistant should behave.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "lesson_text": {"type": "string", "description": "The lesson learned or instruction to remember."}
                        },
                        "required": ["lesson_text"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "run_vendor_hound",
                    "description": "Runs the Vendor and Subcontractor Hound to check for overdue quotes and submittals, and automatically drafts follow-up emails to the vendors.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_blueprint",
                    "description": "Analyzes architectural CAD/BIM blueprints using visual AI and checks NEC/OSHA codes.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "What to look for in the blueprint (e.g., electrical panel clearance)."}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "approve_document_voice",
                    "description": "Approves a field document like a change order or timesheet using voice biometrics.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "document_id": {"type": "string", "description": "The ID or name of the document to approve."},
                            "voice_signature": {"type": "string", "description": "The exact voice phrase the user said (e.g. 'approve', 'authorize')."}
                        },
                        "required": ["document_id", "voice_signature"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_project_risk",
                    "description": "Runs a predictive delay and risk analysis on a project considering weather, materials, and financials.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "project_name": {"type": "string", "description": "The name of the project to analyze."}
                        },
                        "required": ["project_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_drive_home_podcast",
                    "description": "Generates a daily audio synthesis script summarizing the day's events, financials, and prep for tomorrow.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "process_meeting_transcript",
                    "description": "Processes a meeting transcript, extracts action items, and auto-delegates them to Jira/Procore.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "meeting_topic": {"type": "string", "description": "The topic or name of the meeting."}
                        },
                        "required": ["meeting_topic"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "query_knowledge_base",
                    "description": "Searches through uploaded PDF manuals, blueprints, and documents for specific technical information.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "The technical question or topic to search for in the manuals."}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "save_to_vector_memory",
                    "description": "Saves a high-value strategic fact or technical spec to the long-term deep memory archive.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "content": {"type": "string", "description": "The detailed information to archive."}
                        },
                        "required": ["content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "propose_self_improvement",
                    "description": "Elio proposes a fix for an error or a new feature script to the Skill Factory.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Name of the improvement."},
                            "description": {"type": "string", "description": "Why this is needed."},
                            "code": {"type": "string", "description": "The actual Python code snippet."}
                        },
                        "required": ["name", "description", "code"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_project_report",
                    "description": "Generates a professional executive PDF report for a project.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "project_title": {"type": "string", "description": "Title of the project."},
                            "financial_summary": {"type": "string", "description": "Overview of budget and expenses."}
                        },
                        "required": ["project_title", "financial_summary"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "verify_mfa_code",
                    "description": "Verifies a multi-factor authentication code for sensitive actions.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "code": {"type": "string", "description": "The 6-digit code provided by the user."}
                        },
                        "required": ["code"]
                    }
                }
            }
        ]

        response = chat_completion(
            "brain",
            messages=messages,
            tools=tools,
            temperature=0.3,
            max_tokens=1000, # Increased from 100 to prevent cutoff
            top_p=0.3,
            frequency_penalty=0,
            presence_penalty=0
        )
        
        msg_obj = response.choices[0].message
        print(f"DEBUG: tool_calls? {msg_obj.tool_calls}")

        if msg_obj.tool_calls:
            # Reconstruct the assistant message as a dict for OpenAI API
            assistant_message = {
                "role": "assistant",
                "content": msg_obj.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in msg_obj.tool_calls
                ]
            }
            messages.append(assistant_message)
            from Features.MemoryStore import save_second_brain_fact, add_lesson
            
            for tool_call in msg_obj.tool_calls:
                func_name = tool_call.function.name
                try:
                    args = json.loads(tool_call.function.arguments)
                    if func_name == "save_to_memory_bank":
                        save_second_brain_fact(user_key, args.get("fact_key", "Unknown"), args.get("fact_value", ""))
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": func_name,
                            "content": "Fact successfully saved to permanent memory bank."
                        })
                    elif func_name == "save_lesson":
                        add_lesson(user_key, args.get("lesson_text", ""))
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": func_name,
                            "content": "Lesson successfully saved to lessons bank."
                        })
                    elif func_name == "run_vendor_hound":
                        from Features.AgenticWorkflows import run_vendor_hound
                        summary = run_vendor_hound(user_key)
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": func_name,
                            "content": summary
                        })
                    elif func_name == "analyze_blueprint":
                        from Features.BlueprintChat import analyze_blueprint
                        summary = analyze_blueprint(user_key, args.get("query", ""))
                        messages.append({"role": "tool", "tool_call_id": tool_call.id, "name": func_name, "content": summary})
                    elif func_name == "approve_document_voice":
                        from Features.FieldApprovals import approve_document_voice
                        summary = approve_document_voice(user_key, args.get("document_id", ""), args.get("voice_signature", ""))
                        messages.append({"role": "tool", "tool_call_id": tool_call.id, "name": func_name, "content": summary})
                    elif func_name == "analyze_project_risk":
                        from Features.RiskAnalysis import analyze_project_risk
                        summary = analyze_project_risk(user_key, args.get("project_name", ""))
                        messages.append({"role": "tool", "tool_call_id": tool_call.id, "name": func_name, "content": summary})
                    elif func_name == "generate_drive_home_podcast":
                        from Features.ExecutivePodcast import generate_drive_home_podcast
                        summary = generate_drive_home_podcast(user_key)
                        messages.append({"role": "tool", "tool_call_id": tool_call.id, "name": func_name, "content": summary})
                    elif func_name == "process_meeting_transcript":
                        from Features.MeetingIntelligence import process_meeting_transcript
                        summary = process_meeting_transcript(user_key, args.get("meeting_topic", ""))
                        messages.append({"role": "tool", "tool_call_id": tool_call.id, "name": func_name, "content": summary})
                    elif func_name == "query_knowledge_base":
                        from Features.KnowledgeBase import search_knowledge_base
                        results = search_knowledge_base(args.get("query", ""))
                        if not results:
                            content = "No matching information found in the uploaded documents."
                        else:
                            content = "Found the following information in manuals:\n" + "\n".join([f"Source: {r['file']}\n{r['snippet']}" for r in results])
                        messages.append({"role": "tool", "tool_call_id": tool_call.id, "name": func_name, "content": content})
                    elif func_name == "save_to_vector_memory":
                        from server.store import _pg_conn
                        conn = _pg_conn()
                        cur = conn.cursor()
                        cur.execute("insert into elio_vector_memory (user_name, content, created_at) values (%s, %s, %s)", (user_key, args.get("content"), datetime.utcnow()))
                        conn.commit()
                        cur.close()
                        conn.close()
                        messages.append({"role": "tool", "tool_call_id": tool_call.id, "name": func_name, "content": "Information successfully archived in deep memory."})
                    elif func_name == "propose_self_improvement":
                        from server.store import _pg_conn
                        conn = _pg_conn()
                        cur = conn.cursor()
                        cur.execute(
                            "insert into elio_user_skills (skill_name, description, code_snippet, status, created_at) values (%s, %s, %s, %s, %s)",
                            (args.get("name"), args.get("description"), args.get("code"), "learned", datetime.utcnow())
                        )
                        conn.commit()
                        cur.close()
                        conn.close()
                        messages.append({"role": "tool", "tool_call_id": tool_call.id, "name": func_name, "content": "Improvement successfully proposed to Skill Factory."})
                    elif func_name == "generate_project_report":
                        from Features.ReportEngine import generate_project_report
                        # Using dummy tech data for now
                        path = generate_project_report(user_key, args.get("project_title"), {"spec": "N/A"}, args.get("financial_summary"))
                        messages.append({"role": "tool", "tool_call_id": tool_call.id, "name": func_name, "content": f"Project report generated successfully as {path}. Download it from /reports/download?filename={path}."})
                    elif func_name == "verify_mfa_code":
                        from server.store import consume_mfa_code
                        verified = consume_mfa_code(user_key, args.get("code", ""))
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": func_name,
                            "content": "MFA verified. You are authorized to proceed." if verified else "MFA verification failed.",
                        })
                except Exception as e:
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": func_name,
                        "content": f"Error saving memory: {str(e)}"
                    })
            
            second_response = chat_completion(
                "brain",
                messages=messages,
                temperature=0.3,
                max_tokens=1000,
                top_p=0.3,
                frequency_penalty=0,
                presence_penalty=0
            )
            return second_response.choices[0].message.content.strip()

        return msg_obj.content.strip() if msg_obj.content else ""

    except Exception as e:
        import traceback
        traceback.print_exc()
        error_msg = str(e)
        if "ELIO_PG_URI" in error_msg or "psycopg2" in error_msg:
            return "Critical Error: I cannot connect to my deep memory bank (PostgreSQL). Please verify the database credentials."
        if "api_key" in error_msg.lower() or "invalid_api_key" in error_msg.lower():
            return "Configuration Error: the active LLM provider is missing credentials or is rejecting requests. Check the local/cloud model settings in your environment."
        
        return f"System Error: I encountered an issue processing your request. Details: {error_msg}"


# while True:
#     question = input("Enter: ")
#     print(ReplyBrain(question))
