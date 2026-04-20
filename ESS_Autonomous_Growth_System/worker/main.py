import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import text
from services.llm import llm_service
from services.intelligence import market_intelligence
from services.scoring import opportunity_scoring
from services.content import content_generation
from services.validation import validation_engine
from services.translation import translation_engine
from services.wordpress import wp_client
from services.tracking import tracking_engine
from services.reporting import reporting_engine
from config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)
HEARTBEAT_FILE = Path(os.getenv("WORKER_HEARTBEAT_FILE", "/tmp/ess-worker-heartbeat"))


def touch_heartbeat() -> None:
    HEARTBEAT_FILE.parent.mkdir(parents=True, exist_ok=True)
    HEARTBEAT_FILE.touch()

async def scheduled_keyword_discovery():
    touch_heartbeat()
    logger.info("Running scheduled keyword discovery...")
    seed_keywords = ["vfd wastewater", "scada monitoring", "plc programming", "industrial automation", "wastewater treatment controls"]
    try:
        expanded = await market_intelligence.expand_keywords(seed_keywords)
        logger.info(f"Expanded to {len(expanded)} keywords")
        
        opportunities = await market_intelligence.discover_opportunities(expanded[:20])
        logger.info(f"Found {len(opportunities)} opportunities")
        
        for opp in opportunities:
            score = await opportunity_scoring.score_opportunity(opp)
            if score["recommendation"] == "approve":
                logger.info(f"APPROVED: {opp.get('keyword', '')} (score: {score['weighted_total']})")
    except Exception as e:
        logger.error(f"Keyword discovery failed: {e}")

async def scheduled_content_generation():
    touch_heartbeat()
    logger.info("Running scheduled content generation for approved opportunities...")
    try:
        from models.database import async_session
        async with async_session() as db:
            result = await db.execute(
                text("SELECT id, keyword, content_type FROM opportunities WHERE status = 'approved' ORDER BY score DESC LIMIT 5")
            )
            rows = result.fetchall()
            
            for row in rows:
                opp_id, keyword, content_type = row
                logger.info(f"Generating {content_type} for: {keyword}")
                
                content = await content_generation.generate_content({
                    "keyword": keyword,
                    "content_type": content_type,
                    "language": "en",
                })
                
                validation = await validation_engine.validate_content(content)
                routing = validation_engine.determine_routing(validation)
                
                if routing == "auto_publish":
                    logger.info(f"Auto-publishing: {keyword}")
                    post = await wp_client.create_post(
                        title=content["title"],
                        content=content["body"],
                        status="draft",
                        slug=content["slug"],
                        meta_description=content["meta_description"],
                    )
                    logger.info(f"Published: {post.get('link')}")
                    
                    translated = await translation_engine.translate_content(content)
                    logger.info(f"Translated to Spanish: {keyword}")
    except Exception as e:
        logger.error(f"Content generation failed: {e}")

async def scheduled_report_generation():
    touch_heartbeat()
    logger.info("Generating scheduled reports...")
    try:
        daily = await reporting_engine.generate_daily_report()
        logger.info(f"Daily report: {json.dumps(daily, indent=2)}")
    except Exception as e:
        logger.error(f"Report generation failed: {e}")

async def main():
    logger.info("ESS Worker starting...")
    logger.info(f"LLM Provider: {settings.LLM_PROVIDER}")
    touch_heartbeat()
    
    scheduler = AsyncIOScheduler()
    
    scheduler.add_job(scheduled_keyword_discovery, "interval", hours=6)
    scheduler.add_job(scheduled_content_generation, "interval", hours=12)
    scheduler.add_job(scheduled_report_generation, "cron", hour=8, minute=0)
    
    scheduler.start()
    logger.info("Scheduler started. Jobs running on schedule.")
    
    try:
        while True:
            touch_heartbeat()
            await asyncio.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
