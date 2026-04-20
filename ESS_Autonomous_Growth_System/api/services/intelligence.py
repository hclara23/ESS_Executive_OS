import json
from typing import List, Dict, Any, Optional
from services.llm import llm_service

SYSTEM_PROMPT = """You are a market intelligence analyst for Electric Supply Source (ESS), 
an industrial electrical supply company specializing in automation, wastewater treatment, 
VFDs, PLCs, SCADA systems, and industrial controls.

Analyze search keywords and market data to identify revenue opportunities.
Respond with valid JSON only."""

class MarketIntelligenceService:
    
    async def discover_opportunities(
        self,
        keywords: List[str],
        cluster: Optional[str] = None,
        min_volume: Optional[int] = None,
        language: str = "en",
    ) -> List[Dict[str, Any]]:
        prompt = f"""Analyze these keywords for Electric Supply Source (ESS):
Keywords: {json.dumps(keywords)}
Cluster: {cluster or 'any'}
Minimum search volume: {min_volume or 'none'}
Language: {language}

For each keyword, evaluate:
1. Search demand (is there real search volume?)
2. Commercial intent (does it indicate buying intent?)
3. Local relevance (El Paso, Texas, Southwest US)
4. Content gap (does ESS likely not rank for this?)
5. Authority fit (does it match ESS's expertise in automation/industrial controls?)

Return a JSON array of objects with:
- keyword: string
- estimated_volume: number
- trend: "rising" | "stable" | "declining"
- competition: "low" | "medium" | "high"
- commercial_intent: boolean
- content_gap: boolean
- recommended_action: "blog" | "landing_page" | "service_expansion" | "faq" | "local_page" | "comparison" | "buyer_guide"
- reasoning: string"""

        result = await llm_service.generate_json(SYSTEM_PROMPT, prompt, {})
        
        if isinstance(result, list):
            return result
        return result.get("opportunities", [])
    
    async def analyze_competitors(self, competitor_urls: List[str]) -> Dict[str, Any]:
        prompt = f"""Analyze these competitor pages for Electric Supply Source:
Competitor URLs: {json.dumps(competitor_urls)}

Identify:
1. Topics they cover that ESS doesn't
2. Keywords they rank for that ESS doesn't
3. Content types they use effectively
4. Gaps ESS can exploit

Return JSON with:
- missing_topics: array of topic objects with {topic, keyword, priority}
- competitor_strengths: array
- recommended_actions: array"""

        return await llm_service.generate_json(SYSTEM_PROMPT, prompt, {})
    
    async def expand_keywords(self, seed_keywords: List[str], language: str = "en") -> List[str]:
        prompt = f"""Expand these seed keywords into a comprehensive list for Electric Supply Source:
Seed keywords: {json.dumps(seed_keywords)}
Language: {language}
Industry: Industrial electrical supply, automation, wastewater, VFDs, PLCs, SCADA

Generate long-tail variations, question-based keywords, location-based (El Paso, Texas, Southwest),
and industry-specific terms. Return a JSON array of keyword strings only."""

        result = await llm_service.generate_json(SYSTEM_PROMPT, prompt, {})
        return result if isinstance(result, list) else result.get("keywords", [])
    
    async def analyze_cluster_balance(self) -> Dict[str, Any]:
        clusters = ["VFD", "PLC", "SCADA", "Wastewater", "Automation", "Electrical"]
        prompt = f"""Analyze content cluster balance for these clusters: {json.dumps(clusters)}
Return JSON with current balance assessment and recommendations for which clusters need more content."""

        return await llm_service.generate_json(SYSTEM_PROMPT, prompt, {})

market_intelligence = MarketIntelligenceService()
