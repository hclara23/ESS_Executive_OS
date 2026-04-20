from typing import Dict, Any
from services.llm import llm_service

SCORING_WEIGHTS = {
    "demand": 25,
    "trend": 15,
    "commercial": 20,
    "local_relevance": 15,
    "content_gap": 10,
    "authority_fit": 5,
    "cannibalization": -10,
}

THRESHOLDS = {
    "approve": 75,
    "review": 60,
}

class OpportunityScoringService:
    
    async def score_opportunity(self, keyword_data: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""Score this keyword opportunity for Electric Supply Source (ESS):
Keyword: {keyword_data.get('keyword', '')}
Search Volume: {keyword_data.get('search_volume', 'unknown')}
Difficulty: {keyword_data.get('difficulty', 'unknown')}
CPC: {keyword_data.get('cpc', 'unknown')}
Trend: {keyword_data.get('trend', 'unknown')}
Cluster: {keyword_data.get('cluster', 'unknown')}

Score each component 0-100:
- demand: Based on search volume
- trend: Based on trend direction
- commercial: Based on buying intent signals
- local_relevance: For El Paso/Southwest industrial market
- content_gap: Whether ESS likely lacks content for this
- authority_fit: Alignment with ESS expertise
- cannibalization: Negative if it conflicts with existing ESS pages (0 = no conflict, 100 = severe conflict)

Return JSON with:
- scores: object with each component score (0-100)
- weighted_total: calculated weighted score
- recommendation: "approve" | "review" | "reject"
- reasoning: string"""

        result = await llm_service.generate_json("", prompt, {})
        
        scores = result.get("scores", {})
        weighted_total = self._calculate_weighted_total(scores)
        recommendation = self._get_recommendation(weighted_total)
        
        return {
            "keyword": keyword_data.get("keyword", ""),
            "scores": scores,
            "weighted_total": weighted_total,
            "recommendation": recommendation,
            "score_breakdown": result,
        }
    
    def _calculate_weighted_total(self, scores: Dict[str, float]) -> int:
        total = 0
        for component, weight in SCORING_WEIGHTS.items():
            score = scores.get(component, 0)
            total += (score / 100) * abs(weight) * (1 if weight > 0 else -1)
        return max(0, min(100, int(total)))
    
    def _get_recommendation(self, score: int) -> str:
        if score >= THRESHOLDS["approve"]:
            return "approve"
        elif score >= THRESHOLDS["review"]:
            return "review"
        return "reject"
    
    def decide_content_type(self, keyword: str, score: int, cluster: str = None) -> str:
        if score < THRESHOLDS["review"]:
            return "reject"
        
        keyword_lower = keyword.lower()
        
        if any(w in keyword_lower for w in ["what", "how", "why", "when", "guide", "vs", "compare"]):
            return "blog"
        if any(w in keyword_lower for w in ["el paso", "texas", "near me", "southwest"]):
            return "local_page"
        if any(w in keyword_lower for w in ["service", "repair", "installation", "maintenance", "support"]):
            return "service_expansion"
        if any(w in keyword_lower for w in ["cost", "price", "buy", "purchase", "quote"]):
            return "landing_page"
        return "landing_page"

opportunity_scoring = OpportunityScoringService()
