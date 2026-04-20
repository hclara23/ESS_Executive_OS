from fastapi import APIRouter
from typing import Dict, Any, List
from models.schemas import OpportunityInput, ContentType, ContentRequest
from services.intelligence import market_intelligence
from services.scoring import opportunity_scoring
from services.content import content_generation
from services.validation import validation_engine
from services.linking import internal_link_engine
from services.translation import translation_engine
from models.schemas import TranslationRequest
from models.database import get_db
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
import uuid
from datetime import datetime

router = APIRouter()

@router.post("/generate")
async def generate_content(request: ContentRequest, db: AsyncSession = Depends(get_db)):
    content = await content_generation.generate_content(request.model_dump())
    
    content_id = str(uuid.uuid4())
    await db.execute(
        text(
            """INSERT INTO content_versions (id, title, slug, content_type, content, meta_description, meta_title, schema_markup, status, language)
               VALUES (:id, :title, :slug, :type, :content, :meta_desc, :meta_title, :schema, :status, :lang)"""
        ),
        {
            "id": content_id,
            "title": content.get("title"),
            "slug": content.get("slug"),
            "type": request.content_type.value,
            "content": content.get("body"),
            "meta_desc": content.get("meta_description"),
            "meta_title": content.get("meta_title"),
            "schema": str(content.get("schema_markup", {})),
            "status": "draft",
            "lang": request.language,
        }
    )
    await db.commit()
    
    return {"content_id": content_id, **content}

@router.post("/validate")
async def validate_content(content_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        text("SELECT title, content, meta_description, content_type, language FROM content_versions WHERE id = :id"),
        {"id": content_id}
    )
    row = result.fetchone()
    if not row:
        return {"error": "Content not found"}
    
    content = {
        "title": row[0], "body": row[1], "meta_description": row[2],
        "content_type": row[3], "language": row[4],
    }
    
    validation = await validation_engine.validate_content(content)
    validation["routing"] = validation_engine.determine_routing(validation)
    return validation

@router.post("/translate")
async def translate_content(request: TranslationRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        text("SELECT title, content, meta_description, meta_title, cta, excerpt, schema_markup FROM content_versions WHERE id = :id"),
        {"id": request.content_id}
    )
    row = result.fetchone()
    if not row:
        return {"error": "Content not found"}
    
    source_content = {
        "title": row[0], "body": row[1], "meta_description": row[2],
        "meta_title": row[3], "cta": row[4] or "", "excerpt": row[5] or "",
        "faq": [], "schema_markup": row[6] or {},
    }
    
    translated = await translation_engine.translate_content(source_content, request.glossary_overrides)
    
    trans_id = str(uuid.uuid4())
    await db.execute(
        text(
            """INSERT INTO content_versions (id, title, slug, content_type, content, meta_description, meta_title, status, language)
               VALUES (:id, :title, :slug, 'translated', :content, :meta_desc, :meta_title, 'draft', :lang)"""
        ),
        {
            "id": trans_id,
            "title": translated.get("title"),
            "slug": translated.get("slug", ""),
            "content": translated.get("body"),
            "meta_desc": translated.get("meta_description"),
            "meta_title": translated.get("meta_title"),
            "lang": "es",
        }
    )
    
    pair_id = str(uuid.uuid4())
    await db.execute(
        text(
            """INSERT INTO translations (id, source_content_id, translated_content_id, source_language, target_language, status)
               VALUES (:id, :source_id, :trans_id, 'en', 'es', 'completed')"""
        ),
        {"id": pair_id, "source_id": request.content_id, "trans_id": trans_id}
    )
    await db.commit()
    
    return {"translation_id": trans_id, "pair_id": pair_id, **translated}

@router.post("/suggest-links")
async def suggest_internal_links(content_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        text("SELECT title, slug, content FROM content_versions WHERE id = :id"),
        {"id": content_id}
    )
    row = result.fetchone()
    if not row:
        return {"error": "Content not found"}
    
    existing = await db.execute(
        text("SELECT title, slug, content FROM content_versions WHERE id != :id LIMIT 50"),
        {"id": content_id},
    )
    existing_rows = existing.fetchall()
    
    suggestions = await internal_link_engine.suggest_links(
        {"title": row[0], "body": row[2] or "", "keyword": row[1]},
        [{"title": r[0], "url": r[1], "topic": (r[2] or "")[:200]} for r in existing_rows],
    )
    return suggestions
