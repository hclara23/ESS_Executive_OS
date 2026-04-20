from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from models.database import get_db
from models.schemas import ReportRequest, ReportResponse
from services.reporting import reporting_engine
from typing import Dict, Any

router = APIRouter()

@router.post("/generate")
async def generate_report(request: ReportRequest):
    if request.report_type == "daily":
        data = await reporting_engine.generate_daily_report()
    elif request.report_type == "weekly":
        data = await reporting_engine.generate_weekly_report()
    elif request.report_type == "monthly":
        data = await reporting_engine.generate_monthly_report()
    elif request.report_type == "bilingual":
        data = await reporting_engine.generate_bilingual_report()
    else:
        return {"error": f"Unknown report type: {request.report_type}"}
    return data

@router.get("/daily")
async def daily_report():
    return await reporting_engine.generate_daily_report()

@router.get("/weekly")
async def weekly_report():
    return await reporting_engine.generate_weekly_report()

@router.get("/monthly")
async def monthly_report():
    return await reporting_engine.generate_monthly_report()

@router.get("/bilingual")
async def bilingual_report():
    return await reporting_engine.generate_bilingual_report()
