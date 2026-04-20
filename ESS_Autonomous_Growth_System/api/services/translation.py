import json
from typing import Dict, Any, Optional
from services.llm import llm_service

SYSTEM_PROMPT = """You are a professional English-to-Spanish translator for Electric Supply Source (ESS),
an industrial electrical supply company. Translate content while maintaining:
- Technical accuracy (VFD, PLC, SCADA terminology)
- Professional tone
- SEO optimization in Spanish
- Cultural adaptation for US Spanish-speaking industrial audience
- Preserved HTML formatting

Respond with valid JSON only."""

GLOSSARY = {
    "VFD": "VFD (Variador de Frecuencia)",
    "PLC": "PLC (Controlador Lógico Programable)",
    "SCADA": "SCADA (Control Supervisorio y Adquisición de Datos)",
    "wastewater": "aguas residuales",
    "automation": "automatización",
    "industrial controls": "controles industriales",
    "quote": "cotización",
    "request a quote": "solicite una cotización",
    "contact us": "contáctenos",
    "El Paso": "El Paso",
    "Texas": "Texas",
}

class TranslationEngine:
    
    async def translate_content(
        self,
        content: Dict[str, Any],
        glossary_overrides: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        merged_glossary = {**GLOSSARY, **(glossary_overrides or {})}
        
        prompt = f"""Translate this ESS content from English to Spanish:

Title: {content.get('title', '')}
Meta Title: {content.get('meta_title', '')}
Meta Description: {content.get('meta_description', '')}
Body: {content.get('body', '')}
CTA: {content.get('cta', '')}
Excerpt: {content.get('excerpt', '')}
FAQ: {json.dumps(content.get('faq', []), indent=2)}

Use this glossary:
{json.dumps(merged_glossary, indent=2)}

Rules:
- Keep technical acronyms (VFD, PLC, SCADA) with Spanish explanation in parentheses
- Localize CTAs for Spanish-speaking industrial audience
- Maintain all HTML tags and formatting
- Optimize meta description for Spanish search
- Keep brand name "Electric Supply Source" and "ESS" in English

Return JSON with translated fields:
- title, meta_title, meta_description, body, cta, excerpt, faq, slug (Spanish version)"""

        result = await llm_service.generate_json(SYSTEM_PROMPT, prompt, {})
        result["source_language"] = "en"
        result["target_language"] = "es"
        return result
    
    async def translate_keywords(self, keywords: list) -> Dict[str, str]:
        prompt = f"""Translate these industrial electrical keywords from English to Spanish:
{json.dumps(keywords)}

Return JSON mapping of english_keyword -> spanish_keyword."""

        return await llm_service.generate_json(SYSTEM_PROMPT, prompt, {})
    
    async def detect_sync_issues(self, en_content: Dict, es_content: Dict) -> Dict[str, Any]:
        prompt = f"""Compare English and Spanish versions for content sync:

EN: {json.dumps(en_content, indent=2)[:1000]}
ES: {json.dumps(es_content, indent=2)[:1000]}

Identify:
- Missing sections in Spanish
- Outdated translations
- Structural differences
- CTA mismatches

Return JSON with sync_status, issues array, and recommended_actions."""

        return await llm_service.generate_json(SYSTEM_PROMPT, prompt, {})

translation_engine = TranslationEngine()
