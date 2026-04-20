from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from models.database import get_db
from models.schemas import TaskCreate, TaskResponse
from typing import Dict, Any, List
import uuid
from datetime import datetime

router = APIRouter()

@router.post("/")
async def create_task(request: TaskCreate, db: AsyncSession = Depends(get_db)):
    task_id = str(uuid.uuid4())
    await db.execute(
        text(
            """INSERT INTO tasks (id, task_type, payload, status, queue_state, priority)
               VALUES (:id, :type, :payload, :status, :queue, :priority)"""
        ),
        {
            "id": task_id,
            "type": request.task_type,
            "payload": str(request.payload),
            "status": "pending",
            "queue": "brief",
            "priority": request.priority,
        }
    )
    await db.commit()
    return {"task_id": task_id, "status": "pending"}

@router.get("/")
async def list_tasks(status: str = None, limit: int = 50, db: AsyncSession = Depends(get_db)):
    query = "SELECT id, task_type, status, queue_state, priority, created_at, completed_at FROM tasks"
    params: Dict[str, Any] = {}
    if status:
        query += " WHERE status = :status"
        params["status"] = status
    query += " ORDER BY priority ASC, created_at DESC LIMIT :limit"
    params["limit"] = limit
    
    result = await db.execute(text(query), params)
    rows = result.fetchall()
    return [
        {
            "id": r[0], "task_type": r[1], "status": r[2], "queue_state": r[3],
            "priority": r[4], "created_at": r[5].isoformat() if r[5] else None,
            "completed_at": r[6].isoformat() if r[6] else None,
        }
        for r in rows
    ]

@router.get("/{task_id}")
async def get_task(task_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        text(
            "SELECT id, task_type, payload, status, queue_state, priority, error_message, result, created_at, completed_at FROM tasks WHERE id = :id"
        ),
        {"id": task_id}
    )
    row = result.fetchone()
    if not row:
        return {"error": "Task not found"}
    return {
        "id": row[0], "task_type": row[1], "payload": row[2], "status": row[3],
        "queue_state": row[4], "priority": row[5], "error_message": row[6],
        "result": row[7], "created_at": row[8].isoformat() if row[8] else None,
        "completed_at": row[9].isoformat() if row[9] else None,
    }

@router.put("/{task_id}/status")
async def update_task_status(task_id: str, status: str, result: str = None, db: AsyncSession = Depends(get_db)):
    fields = {"status": status, "id": task_id}
    if status == "completed":
        fields["completed_at"] = datetime.utcnow()
    if result:
        fields["result"] = result
    
    await db.execute(
        text("UPDATE tasks SET status = :status, completed_at = :completed_at, result = :result WHERE id = :id"),
        {**fields, "completed_at": fields.get("completed_at"), "result": fields.get("result")}
    )
    await db.commit()
    return {"task_id": task_id, "status": status}
