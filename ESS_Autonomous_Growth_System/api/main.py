from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import opportunities, content, wordpress, reports, intelligence, tasks, tracking
from config import settings

app = FastAPI(
    title="ESS Autonomous Growth System",
    description="SEO-driven content generation and publishing platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(intelligence.router, prefix="/api/intelligence", tags=["Market Intelligence"])
app.include_router(opportunities.router, prefix="/api/opportunities", tags=["Opportunities"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["Tasks"])
app.include_router(content.router, prefix="/api/content", tags=["Content Generation"])
app.include_router(wordpress.router, prefix="/api/wordpress", tags=["WordPress"])
app.include_router(tracking.router, prefix="/api/tracking", tags=["Change Tracking"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])

@app.get("/health")
def health():
    return {"status": "ok", "llm_provider": settings.LLM_PROVIDER}
