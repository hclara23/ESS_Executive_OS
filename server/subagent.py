import json
import os
from typing import Optional

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from server.ai_provider import chat_completion, get_runtime_settings


app = FastAPI(title="Elio Subagent", version="1.0.0")


class UploadIntentRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    prompt: str = Field(default="", max_length=1000)


class MissionPlanRequest(BaseModel):
    user_name: str = Field(min_length=1, max_length=100)
    goal: str = Field(min_length=1, max_length=2000)


class MeetingActionsRequest(BaseModel):
    meeting_topic: str = Field(min_length=1, max_length=255)
    transcript: str = Field(min_length=1)


class ProposalDraftRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)


def _require_token(x_elio_subagent_token: Optional[str]):
    expected = os.getenv("ELIO_SUBAGENT_TOKEN", "").strip()
    if expected and x_elio_subagent_token != expected:
        raise HTTPException(status_code=401, detail="Invalid subagent token.")


def _json_response(task: str, system_prompt: str, user_prompt: str):
    response = chat_completion(
        task,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )
    return json.loads(response.choices[0].message.content)


@app.get("/health")
def health():
    return {
        "ok": True,
        "service": "elio-subagent",
        "runtime": get_runtime_settings(),
    }


@app.post("/tasks/classify-upload")
def classify_upload(payload: UploadIntentRequest, x_elio_subagent_token: Optional[str] = Header(default=None)):
    _require_token(x_elio_subagent_token)
    system_prompt = """
You are Elio's Intelligent Intake Router.
Analyze the filename and the user's prompt to determine where the file should be stored and what processing should occur.

Categories: receipts, manuals, blueprints, legal, bids, media, general.
Actions: ProcessExpense, AddToLibrary, AuditBlueprint, Summarize, Archive.

Return only JSON:
{
  "category": "...",
  "action": "...",
  "thought_process": "Brief explanation of why"
}
"""
    return _json_response(
        "intake",
        system_prompt,
        f"Filename: {payload.filename}\nUser Prompt: {payload.prompt or 'Process this file'}",
    )


@app.post("/tasks/mission-plan")
def mission_plan(payload: MissionPlanRequest, x_elio_subagent_token: Optional[str] = Header(default=None)):
    _require_token(x_elio_subagent_token)
    system_prompt = """
You are Elio's Strategic Mission Planner.
Create a 3-5 step plan that uses Elio's capabilities carefully and efficiently.
Return only JSON in the shape:
{
  "steps": [
    {"step": 1, "action": "name", "description": "...", "type": "auto/wait_for_user"}
  ]
}
"""
    user_prompt = f"""
Create a mission plan for {payload.user_name}.
Goal: {payload.goal}

Elio can use:
- Email drafting
- Financial review
- Vendor compliance checks
- Knowledge search
- Project management updates
"""
    return _json_response("mission", system_prompt, user_prompt)


@app.post("/tasks/meeting-actions")
def meeting_actions(payload: MeetingActionsRequest, x_elio_subagent_token: Optional[str] = Header(default=None)):
    _require_token(x_elio_subagent_token)
    system_prompt = """
You extract action items from meeting transcripts.
Return only JSON:
{
  "items": [
    {"type": "Jira|Procore|Delegation|To-Do", "task": "...", "user": "alex|sandra|optional"}
  ]
}
"""
    user_prompt = f"Meeting topic: {payload.meeting_topic}\nTranscript:\n{payload.transcript}"
    return _json_response("meeting", system_prompt, user_prompt)


@app.post("/tasks/proposal-draft")
def proposal_draft(payload: ProposalDraftRequest, x_elio_subagent_token: Optional[str] = Header(default=None)):
    _require_token(x_elio_subagent_token)
    response = chat_completion(
        "proposal_draft",
        messages=[
            {
                "role": "system",
                "content": "Draft concise, professional proposals for ESS. Respond in Markdown.",
            },
            {
                "role": "user",
                "content": f"Title: {payload.title}\nDescription: {payload.description}",
            },
        ],
        temperature=0.3,
    )
    return {"draft": response.choices[0].message.content.strip()}
