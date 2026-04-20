from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class ContentType(str, Enum):
    BLOG = "blog"
    LANDING_PAGE = "landing_page"
    SERVICE_EXPANSION = "service_expansion"
    FAQ = "faq"
    LOCAL_PAGE = "local_page"
    COMPARISON = "comparison"
    BUYER_GUIDE = "buyer_guide"
    PRODUCT_PAGE = "product_page"

class OpportunityStatus(str, Enum):
    DISCOVERED = "discovered"
    APPROVED = "approved"
    REVIEW = "review"
    REJECTED = "rejected"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class QueueState(str, Enum):
    BRIEF = "brief"
    WRITING = "writing"
    VALIDATION = "validation"
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    TRANSLATED = "translated"
    SYNCED = "synced"

class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

# --- Request/Response Models ---

class OpportunityInput(BaseModel):
    keyword: str
    search_volume: Optional[int] = None
    difficulty: Optional[int] = None
    cpc: Optional[float] = None
    trend: Optional[str] = None
    cluster: Optional[str] = None

class OpportunityResponse(BaseModel):
    id: str
    keyword: str
    score: int
    score_breakdown: Dict[str, Any]
    content_type: Optional[str]
    priority: Optional[str]
    status: str
    cluster: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class ContentRequest(BaseModel):
    opportunity_id: Optional[str] = None
    keyword: str
    content_type: ContentType
    language: str = "en"
    word_count: Optional[int] = None
    tone: Optional[str] = "professional"
    target_cluster: Optional[str] = None

class ContentResponse(BaseModel):
    title: str
    slug: str
    meta_description: str
    meta_title: str
    body: str
    cta: str
    faq: List[Dict[str, str]]
    excerpt: str
    schema_markup: Dict[str, Any]
    internal_link_suggestions: List[str]
    language: str

class TranslationRequest(BaseModel):
    content_id: str
    source_language: str = "en"
    target_language: str = "es"
    glossary_overrides: Optional[Dict[str, str]] = None

class WordPressPublishRequest(BaseModel):
    content_id: str
    action: str = "draft"
    schedule_date: Optional[datetime] = None

class WordPressPublishResponse(BaseModel):
    success: bool
    post_id: Optional[int]
    url: Optional[str]
    message: str

class TaskCreate(BaseModel):
    task_type: str
    payload: Dict[str, Any]
    priority: int = 5

class TaskResponse(BaseModel):
    id: str
    task_type: str
    status: str
    queue_state: str
    priority: int
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True

class ReportRequest(BaseModel):
    report_type: str
    period_start: Optional[str] = None
    period_end: Optional[str] = None

class ReportResponse(BaseModel):
    id: str
    report_type: str
    period_start: Optional[str]
    period_end: Optional[str]
    data: Dict[str, Any]
    generated_at: datetime

    class Config:
        from_attributes = True

class IntelligenceQuery(BaseModel):
    keywords: Optional[List[str]] = None
    cluster: Optional[str] = None
    min_volume: Optional[int] = None
    language: str = "en"

class IntelligenceResult(BaseModel):
    keyword: str
    search_volume: Optional[int]
    trend: Optional[str]
    competition: Optional[str]
    opportunity_score: Optional[int]
    content_gap: bool

class CompetitorAnalysisRequest(BaseModel):
    urls: List[str]

class TrackingSnapshot(BaseModel):
    content_id: str
    reason: str
    automation_id: Optional[str] = None

class TrackingDiff(BaseModel):
    content_id: str
    before: str
    after: str
    summary: Optional[str] = None

class RollbackRequest(BaseModel):
    content_id: str
    snapshot_id: Optional[str] = None
    batch_id: Optional[str] = None
