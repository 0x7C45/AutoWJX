from enum import Enum
from typing import Optional
import anthropic
import openai
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class LLMProvider(str, Enum):
    CLAUDE = "claude"
    OPENAI = "openai"

class LLMClient:
    def __init__(self, default_provider: Optional[LLMProvider] = None):
        self.default_provider = default_provider or LLMProvider(settings.DEFAULT_LLM_PROVIDER)
        self._claude_client = anthropic.AsyncAnthropic(api_key=settings.CLAUDE_API_KEY)
        self._openai_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        provider: Optional[LLMProvider] = None
    ) -> str:
        """Generate text using LLM with automatic fallback."""
        provider = provider or self.default_provider
        
        try:
            if provider == LLMProvider.CLAUDE:
                return await self._generate_claude(prompt, max_tokens, temperature)
            else:
                return await self._generate_openai(prompt, max_tokens, temperature)
        except Exception as e:
            logger.warning(f"{provider} failed: {e}, falling back")
            # Fallback to other provider
            fallback = LLMProvider.OPENAI if provider == LLMProvider.CLAUDE else LLMProvider.CLAUDE
            try:
                if fallback == LLMProvider.CLAUDE:
                    return await self._generate_claude(prompt, max_tokens, temperature)
                else:
                    return await self._generate_openai(prompt, max_tokens, temperature)
            except Exception as fallback_error:
                logger.error(f"Both LLM providers failed: {fallback_error}")
                raise RuntimeError("所有 LLM 提供商都失败了") from fallback_error
    
    async def _generate_claude(self, prompt: str, max_tokens: int, temperature: float) -> str:
        message = await self._claude_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    
    async def _generate_openai(self, prompt: str, max_tokens: int, temperature: float) -> str:
        completion = await self._openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}]
        )
        return completion.choices[0].message.content

# Global instance
llm_client = LLMClient()
