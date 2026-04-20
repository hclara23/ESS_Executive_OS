import json
from typing import Dict, Any, List
from services.llm import llm_service

SYSTEM_PROMPT = """You are a content validation engine for Electric Supply Source (ESS).
Validate content for quality, SEO completeness, risk, and conversion optimization.
Respond with valid JSON only."""

class ValidationEngine:
    
    async def validate_content(self, content: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""Validate this content for Electric Supply Source:
Title: {content.get('title', '')}
Meta Description: {content.get('meta_description', '')}
Body preview: {content.get('body', '')[:500]}
Content Type: {content.get('content_type', '')}
Language: {content.get('language', 'en')}

Check:
1. Duplicate content risk (generic/templated language)
2. Tone consistency (professional, technical, authoritative)
3. SEO completeness (title length, meta description, keyword density, headings)
4. CTA presence and clarity
5. Readability (sentence length, paragraph structure)
6. Risk level (claims that could be problematic, inaccurate technical info)
7. Internal link presence

Return JSON:
- duplicate_risk: 0-100
- tone_score: 0-100
- seo_score: 0-100
- cta_present: boolean
- readability_score: 0-100
- risk_level: "low" | "medium" | "high"
- issues: array of {severity, description, suggestion}
- overall_score: 0-100
- recommendation: "auto_publish" | "review" | "manual"
- fixes_needed: array of strings"""

        result = await llm_service.generate_json(SYSTEM_PROMPT, prompt, {})
        return result
    
    def determine_routing(self, validation: Dict[str, Any]) -> str:
        risk = validation.get("risk_level", "medium")
        if risk == "low" and validation.get("overall_score", 0) >= 80:
            return "auto_publish"
        elif risk == "high" or validation.get("overall_score", 0) < 50:
            return "manual"
        return "review"

validation_engine = ValidationEngine()
