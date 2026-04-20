from fastapi import APIRouter
from sqlalchemy import text
from typing import Dict, Any
from models.schemas import WordPressPublishRequest, WordPressPublishResponse
from services.wordpress import wp_client
from services.tracking import tracking_engine
from models.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

router = APIRouter()

@router.post("/publish", response_model=WordPressPublishResponse)
async def publish_to_wordpress(request: WordPressPublishRequest, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(
            text("SELECT title, content, slug, meta_description, meta_title, language FROM content_versions WHERE id = :id"),
            {"id": request.content_id}
        )
        row = result.fetchone()
        if not row:
            return WordPressPublishResponse(success=False, message="Content not found", post_id=None, url=None)
        
        status = request.action if request.action != "publish" else "publish"
        if request.schedule_date:
            status = "future"
        
        post = await wp_client.create_post(
            title=row[0],
            content=row[1] or "",
            status=status,
            slug=row[2],
            meta_description=row[3],
            meta_title=row[4],
        )
        
        await db.execute(
            text(
                """UPDATE content_versions SET wordpress_post_id = :post_id, wordpress_url = :url, status = :status, updated_at = NOW() WHERE id = :id"""
            ),
            {"post_id": post.get("id"), "url": post.get("link"), "status": "published", "id": request.content_id}
        )
        await db.commit()
        
        return WordPressPublishResponse(
            success=True,
            post_id=post.get("id"),
            url=post.get("link"),
            message=f"Published as {status}"
        )
    except Exception as e:
        return WordPressPublishResponse(success=False, message=str(e), post_id=None, url=None)

@router.post("/publish-page")
async def publish_page_to_wordpress(request: WordPressPublishRequest, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(
            text("SELECT title, content, slug, meta_description FROM content_versions WHERE id = :id"),
            {"id": request.content_id}
        )
        row = result.fetchone()
        if not row:
            return {"success": False, "message": "Content not found"}
        
        page = await wp_client.create_page(
            title=row[0],
            content=row[1] or "",
            status=request.action,
            slug=row[2],
        )
        
        await db.execute(
            text(
                """UPDATE content_versions SET wordpress_post_id = :post_id, wordpress_url = :url, status = 'published', updated_at = NOW() WHERE id = :id"""
            ),
            {"post_id": page.get("id"), "url": page.get("link"), "id": request.content_id}
        )
        await db.commit()
        
        return {"success": True, "post_id": page.get("id"), "url": page.get("link")}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.get("/test")
async def test_wordpress_connection():
    ok = await wp_client.test_connection()
    return {"connected": ok}

@router.get("/posts")
async def list_posts(status: str = "any", per_page: int = 20):
    posts = await wp_client.get_posts(status=status, per_page=per_page)
    return posts

@router.get("/categories")
async def list_categories():
    categories = await wp_client.get_categories()
    return categories

@router.post("/update/{post_id}")
async def update_post(post_id: int, updates: Dict[str, Any]):
    result = await wp_client.update_post(post_id, **updates)
    return result
