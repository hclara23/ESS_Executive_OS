from fastapi import APIRouter

router = APIRouter()

from routers import opportunities, content, wordpress, tracking, reports, intelligence, tasks

__all__ = ["router", "opportunities", "content", "wordpress", "tracking", "reports", "intelligence", "tasks"]
