from typing import Optional, Dict, Any, List
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from config import settings

class LLMService:
    """Dual-provider LLM service supporting OpenAI and Anthropic Claude."""
    
    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
        self.anthropic_client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY) if settings.ANTHROPIC_API_KEY else None
    
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> str:
        if self.provider == "anthropic" and self.anthropic_client:
            return await self._generate_claude(system_prompt, user_prompt, temperature, max_tokens)
        elif self.openai_client:
            return await self._generate_openai(system_prompt, user_prompt, temperature, max_tokens, response_format)
        else:
            raise RuntimeError(f"No LLM provider available. Requested: {self.provider}")
    
    async def _generate_openai(
        self, system: str, user: str, temp: float, max_tokens: int, response_format: Optional[Dict] = None
    ) -> str:
        kwargs = {
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temp,
            "max_tokens": max_tokens,
        }
        if response_format:
            kwargs["response_format"] = response_format
        
        response = await self.openai_client.chat.completions.create(**kwargs)
        return response.choices[0].message.content
    
    async def _generate_claude(self, system: str, user: str, temp: float, max_tokens: int) -> str:
        response = await self.anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            system=system,
            messages=[{"role": "user", "content": user}],
            temperature=temp,
            max_tokens=max_tokens,
        )
        return response.content[0].text
    
    async def generate_json(
        self, system_prompt: str, user_prompt: str, schema: Dict[str, Any], temperature: float = 0.3
    ) -> Dict[str, Any]:
        import json
        if self.provider == "anthropic" and self.anthropic_client:
            result = await self._generate_claude(
                system_prompt + "\n\nRespond with valid JSON only, no markdown wrapping.",
                user_prompt,
                temperature,
                4096,
            )
            cleaned = result.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
            return json.loads(cleaned)
        else:
            result = await self._generate_openai(
                system_prompt, user_prompt, temperature, 4096,
                {"type": "json_object"}
            )
            return json.loads(result)
    
    def switch_provider(self, provider: str):
        if provider.lower() not in ("openai", "anthropic"):
            raise ValueError(f"Unsupported provider: {provider}")
        self.provider = provider.lower()
    
    def get_active_provider(self) -> str:
        return self.provider

llm_service = LLMService()
