import json
from typing import Dict, Any, List, Optional
from services.llm import llm_service

SYSTEM_PROMPT = """You are an expert SEO content writer for Electric Supply Source (ESS), 
an industrial electrical supply company. You write authoritative, conversion-optimized content 
for automation, wastewater treatment, VFDs, PLCs, SCADA systems, and industrial controls.

Your writing is:
- Technical but accessible
- Focused on solving real industrial problems
- Optimized for search intent
- Conversion-focused with clear CTAs
- Professional and authoritative

Always respond with valid JSON only."""

ESS_BRAND_INFO = """
Company: Electric Supply Source (ESS)
Industry: Industrial electrical supply and automation
Specialties: VFDs, PLCs, SCADA, wastewater treatment, industrial controls
Location: El Paso, Texas (serving Southwest US)
Target audience: Facility managers, plant engineers, maintenance professionals
Languages: English and Spanish
"""

class ContentGenerationService:
    
    async def generate_content(self, request: Dict[str, Any]) -> Dict[str, Any]:
        keyword = request.get("keyword", "")
        content_type = request.get("content_type", "blog")
        language = request.get("language", "en")
        tone = request.get("tone", "professional")
        word_count = request.get("word_count", 1500)
        
        type_prompts = {
            "blog": self._blog_prompt,
            "landing_page": self._landing_page_prompt,
            "service_expansion": self._service_expansion_prompt,
            "faq": self._faq_prompt,
            "local_page": self._local_page_prompt,
            "comparison": self._comparison_prompt,
            "buyer_guide": self._buyer_guide_prompt,
        }
        
        prompt_fn = type_prompts.get(content_type, self._blog_prompt)
        prompt = prompt_fn(keyword, language, tone, word_count)
        
        schema = {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "slug": {"type": "string"},
                "meta_title": {"type": "string"},
                "meta_description": {"type": "string"},
                "body": {"type": "string"},
                "cta": {"type": "string"},
                "faq": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "question": {"type": "string"},
                            "answer": {"type": "string"}
                        }
                    }
                },
                "excerpt": {"type": "string"},
                "schema_markup": {"type": "object"},
                "internal_link_suggestions": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["title", "slug", "meta_description", "body", "cta", "faq"],
        }
        
        result = await llm_service.generate_json(SYSTEM_PROMPT, prompt, schema)
        result["language"] = language
        result["content_type"] = content_type
        return result
    
    def _blog_prompt(self, keyword: str, lang: str, tone: str, wc: int) -> str:
        return f"""Write a comprehensive blog post targeting the keyword "{keyword}".
Language: {lang}
Tone: {tone}
Target word count: {wc}

{ESS_BRAND_INFO}

Include:
- Compelling title with the keyword
- SEO-optimized slug
- Meta title (60 chars max) and meta description (155 chars max)
- Well-structured body with H2/H3 headings
- At least 3 FAQ items with schema markup
- Strong CTA encouraging readers to request a quote from ESS
- 5-8 internal link suggestions to related ESS pages
- Short excerpt for listing pages

Return complete JSON with all fields."""
    
    def _landing_page_prompt(self, keyword: str, lang: str, tone: str, wc: int) -> str:
        return f"""Write a conversion-optimized landing page targeting "{keyword}".
Language: {lang}
Tone: {tone}

{ESS_BRAND_INFO}

Include:
- Hero section with compelling headline
- Problem/solution framing
- Service features and benefits
- Trust signals (experience, certifications, service area)
- Multiple CTAs (quote request, phone call)
- FAQ section with schema markup
- Local relevance for El Paso/Southwest if applicable

Return complete JSON with all fields."""
    
    def _service_expansion_prompt(self, keyword: str, lang: str, tone: str, wc: int) -> str:
        return f"""Write content to expand an existing service page around "{keyword}".
Language: {lang}
Tone: {tone}

{ESS_BRAND_INFO}

Include:
- New section content that integrates into an existing service page
- Technical details and specifications
- Application examples
- CTA for the specific service
- Related internal link suggestions

Return complete JSON with all fields."""
    
    def _faq_prompt(self, keyword: str, lang: str, tone: str, wc: int) -> str:
        return f"""Generate a comprehensive FAQ block targeting "{keyword}".
Language: {lang}

{ESS_BRAND_INFO}

Include:
- 8-12 FAQ items covering the topic thoroughly
- Schema markup for FAQ
- Answers that demonstrate ESS expertise
- Internal link suggestions

Return complete JSON with all fields."""
    
    def _local_page_prompt(self, keyword: str, lang: str, tone: str, wc: int) -> str:
        return f"""Write a local SEO landing page targeting "{keyword}".
Language: {lang}

{ESS_BRAND_INFO}

Include:
- Location-specific headline
- Service area details (El Paso, Texas, Southwest)
- Local market knowledge and expertise
- Service offerings for the area
- Local CTA with phone number prompt
- Local business schema markup

Return complete JSON with all fields."""
    
    def _comparison_prompt(self, keyword: str, lang: str, tone: str, wc: int) -> str:
        return f"""Write a comparison/review page targeting "{keyword}".
Language: {lang}

{ESS_BRAND_INFO}

Include:
- Objective comparison structure
- Pros and cons
- When to choose each option
- ESS's recommendation based on expertise
- CTA to consult with ESS specialists

Return complete JSON with all fields."""
    
    def _buyer_guide_prompt(self, keyword: str, lang: str, tone: str, wc: int) -> str:
        return f"""Write a buyer's guide targeting "{keyword}".
Language: {lang}

{ESS_BRAND_INFO}

Include:
- What to look for when buying
- Key features and specifications
- Common mistakes to avoid
- Budget considerations
- ESS as the trusted supplier
- Strong CTA

Return complete JSON with all fields."""

content_generation = ContentGenerationService()
