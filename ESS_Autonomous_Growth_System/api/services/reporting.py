import json
from typing import Dict, Any, Optional
from datetime import datetime, date

from sqlalchemy import text

from models.database import async_session
from services.wordpress import wp_client

class ReportingEngine:
    
    async def generate_daily_report(self) -> Dict[str, Any]:
        async with async_session() as db:
            result = await db.execute(
                text(
                    """SELECT task_type, status, COUNT(*) as count
                       FROM tasks
                       WHERE DATE(created_at) = CURRENT_DATE
                       GROUP BY task_type, status"""
                )
            )
            rows = result.fetchall()
            
            result2 = await db.execute(
                text(
                    """SELECT automation_type, status, tasks_completed, tasks_total
                       FROM automation_runs
                       WHERE DATE(started_at) = CURRENT_DATE"""
                )
            )
            runs = result2.fetchall()
        
        return {
            "report_type": "daily",
            "date": date.today().isoformat(),
            "tasks_by_type": [
                {"type": r[0], "status": r[1], "count": r[2]} for r in rows
            ],
            "automation_runs": [
                {"type": r[0], "status": r[1], "completed": r[2], "total": r[3]} for r in runs
            ],
            "generated_at": datetime.utcnow().isoformat(),
        }
    
    async def generate_weekly_report(self) -> Dict[str, Any]:
        async with async_session() as db:
            result = await db.execute(
                text(
                    """SELECT content_type, COUNT(*) as count
                       FROM content_versions
                       WHERE created_at >= NOW() - INTERVAL '7 days'
                       GROUP BY content_type"""
                )
            )
            content_created = result.fetchall()
            
            result2 = await db.execute(
                text("""SELECT COUNT(*) FROM content_versions WHERE created_at >= NOW() - INTERVAL '7 days'""")
            )
            total_new = result2.scalar()
            
            result3 = await db.execute(
                text("""SELECT COUNT(*) FROM translations WHERE created_at >= NOW() - INTERVAL '7 days'""")
            )
            total_translations = result3.scalar()
            
            result4 = await db.execute(
                text(
                    """SELECT title, slug, wordpress_url, language
                       FROM content_versions
                       WHERE created_at >= NOW() - INTERVAL '7 days'
                       ORDER BY created_at DESC"""
                )
            )
            new_pages = result4.fetchall()
        
        return {
            "report_type": "weekly",
            "period": "last_7_days",
            "content_created": {
                r[0]: r[1] for r in content_created
            },
            "total_new_content": total_new,
            "total_translations": total_translations,
            "new_pages": [
                {"title": r[0], "slug": r[1], "url": r[2], "language": r[3]}
                for r in new_pages
            ],
            "generated_at": datetime.utcnow().isoformat(),
        }
    
    async def generate_monthly_report(self) -> Dict[str, Any]:
        async with async_session() as db:
            result = await db.execute(
                text(
                    """SELECT r.status, COUNT(*), COALESCE(SUM(r.closed_value), 0)
                       FROM revenue r
                       WHERE r.created_at >= NOW() - INTERVAL '30 days'
                       GROUP BY r.status"""
                )
            )
            revenue_data = result.fetchall()
            
            result2 = await db.execute(
                text("""SELECT COUNT(*) FROM leads WHERE created_at >= NOW() - INTERVAL '30 days'""")
            )
            total_leads = result2.scalar()
            
            result3 = await db.execute(
                text(
                    """SELECT content_type, COUNT(*) 
                       FROM content_versions
                       WHERE created_at >= NOW() - INTERVAL '30 days'
                       GROUP BY content_type"""
                )
            )
            content_data = result3.fetchall()
        
        return {
            "report_type": "monthly",
            "period": "last_30_days",
            "revenue": {
                r[0]: {"count": r[1], "value": float(r[2])} for r in revenue_data
            },
            "total_leads": total_leads,
            "content_created": {r[0]: r[1] for r in content_data},
            "generated_at": datetime.utcnow().isoformat(),
        }
    
    async def generate_bilingual_report(self) -> Dict[str, Any]:
        async with async_session() as db:
            result = await db.execute(
                text(
                    """SELECT cv.title, cv.slug, cv.wordpress_url, cv.language, cv.status,
                              t.status as translation_status
                       FROM content_versions cv
                       LEFT JOIN translations t ON t.source_content_id = cv.id
                       WHERE cv.created_at >= NOW() - INTERVAL '7 days'
                       ORDER BY cv.created_at DESC"""
                )
            )
            rows = result.fetchall()
        
        paired = {}
        for r in rows:
            base_slug = r[1].replace("/es/", "") if r[3] == "es" else r[1]
            if base_slug not in paired:
                paired[base_slug] = {"en": None, "es": None}
            paired[base_slug][r[3]] = {
                "title": r[0],
                "slug": r[1],
                "url": r[2],
                "status": r[4],
                "translation_status": r[5],
            }
        
        return {
            "report_type": "bilingual",
            "paired_pages": paired,
            "generated_at": datetime.utcnow().isoformat(),
        }

reporting_engine = ReportingEngine()
