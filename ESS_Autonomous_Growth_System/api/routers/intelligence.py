from fastapi import APIRouter
from typing import Dict, Any
from models.schemas import CompetitorAnalysisRequest
from services.intelligence import market_intelligence
from services.scoring import opportunity_scoring

router = APIRouter()

@router.get("/discover")
async def discover_opportunities(keywords: str = None, cluster: str = None):
    kw_list = [k.strip() for k in keywords.split(",")] if keywords else ["vfd wastewater", "scada monitoring", "plc programming"]
    results = await market_intelligence.discover_opportunities(kw_list, cluster)
    return {"opportunities": results, "count": len(results)}

@router.post("/score")
async def score_opportunity(data: Dict[str, Any]):
    result = await opportunity_scoring.score_opportunity(data)
    return result

@router.post("/expand-keywords")
async def expand_keywords(seed: str, language: str = "en"):
    seeds = [s.strip() for s in seed.split(",")]
    expanded = await market_intelligence.expand_keywords(seeds, language)
    return {"keywords": expanded, "count": len(expanded)}

@router.post("/analyze-competitors")
async def analyze_competitors(request: CompetitorAnalysisRequest):
    result = await market_intelligence.analyze_competitors(request.urls)
    return result

@router.get("/cluster-balance")
async def cluster_balance():
    result = await market_intelligence.analyze_cluster_balance()
    return result
