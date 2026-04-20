import json
from typing import Dict, Any, List
from services.llm import llm_service

SYSTEM_PROMPT = """You are an internal linking strategist for Electric Supply Source (ESS).
Analyze content and recommend strategic internal links to improve SEO authority distribution,
fix orphan pages, and improve crawl depth. Respond with valid JSON only."""

class InternalLinkEngine:
    
    async def suggest_links(
        self,
        new_content: Dict[str, Any],
        existing_pages: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        pages_summary = json.dumps([
            {"title": p.get("title", ""), "url": p.get("url", ""), "topic": p.get("topic", "")}
            for p in existing_pages[:50]
        ], indent=2)
        
        prompt = f"""Analyze this new content and recommend internal links from/to existing ESS pages:

NEW CONTENT:
Title: {new_content.get('title', '')}
Keyword: {new_content.get('keyword', '')}
Content Type: {new_content.get('content_type', '')}
Body preview: {new_content.get('body', '')[:500]}

EXISTING ESS PAGES:
{pages_summary}

Recommend:
1. Service links (link to main service pages)
2. Quote links (link to quote/request pages)
3. Cluster links (link to related content in same cluster)
4. Authority links (link to high-authority ESS pages)

Also identify:
- Any orphan pages that should link TO this new content
- Pages that need a link FROM them to this content

Return JSON:
- outgoing_links: array of {target_url, anchor_text, link_type, reason}
- incoming_suggestions: array of {source_url, anchor_text, reason}
- orphan_fixes: array of {orphan_url, suggested_anchor}
- total_links_suggested: number"""

        return await llm_service.generate_json(SYSTEM_PROMPT, prompt, {})
    
    async def audit_existing_links(self, site_pages: List[Dict[str, Any]]) -> Dict[str, Any]:
        prompt = f"""Audit these ESS pages for internal linking issues:
{json.dumps(site_pages[:30], indent=2)}

Identify:
- Orphan pages (no internal links pointing to them)
- Pages with too few internal links (<3)
- Pages that should link to each other but don't
- Deep pages (more than 3 clicks from homepage)

Return JSON with issues and recommendations."""

        return await llm_service.generate_json(SYSTEM_PROMPT, prompt, {})

internal_link_engine = InternalLinkEngine()
