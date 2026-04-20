from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from models.database import get_db
from models.schemas import TrackingSnapshot, TrackingDiff, RollbackRequest
from services.tracking import tracking_engine
from typing import Dict, Any

router = APIRouter()

@router.post("/snapshot")
async def create_snapshot(request: TrackingSnapshot, db: AsyncSession = Depends(get_db)):
    snapshot_id = await tracking_engine.create_snapshot(
        db, request.content_id,
        snapshot_data={"action": "snapshot"},
        reason=request.reason,
        automation_id=request.automation_id,
    )
    return {"snapshot_id": snapshot_id, "content_id": request.content_id}

@router.post("/diff")
async def compute_diff(request: TrackingDiff):
    diff_result = await tracking_engine.compute_diff(request.before, request.after)
    return diff_result

@router.post("/rollback")
async def rollback(request: RollbackRequest, db: AsyncSession = Depends(get_db)):
    result = await tracking_engine.rollback_to_snapshot(
        db, request.content_id, request.snapshot_id
    )
    return result

@router.get("/history/{content_id}")
async def get_history(content_id: str, db: AsyncSession = Depends(get_db)):
    history = await tracking_engine.get_change_history(db, content_id)
    return {"content_id": content_id, "history": history}
