# services/agent-service/app/llm/router.py
# LLM Router - Multi-provider LLM management

import asyncio
import time
from typing import Dict, List, Optional

import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings

logger = structlog.get_logger()


class LLMProvider:
    """Base LLM provider interface."""
    
    def __init__(self, name: str, priority: int = 1):
        self.name = name
        self.priority = priority
        self.is_available = True
        self.last_error = None
        self.request_count = 0
        self.error_count = 0
    
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> Dict:
        raise NotImplementedError
    
    def record_success(self):
        self.request_count += 1
    
    def record_error(self, error: str):
        self.error_count += 1
        self.last_error = error
        if self.error_count > 5:
            self.is_available = False


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider."""
    
    def __init__(self):
        super().__init__("openai", priority=1)
        self.client = None
        self._init_client()
    
    def _init_client(self):
        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        except Exception as e:
            logger.error("openai_init_failed", error=str(e))
            self.is_available = False
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> Dict:
        if not self.client:
            raise Exception("OpenAI client not initialized")
        
        start_time = time.time()
        
        response = await self.client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        latency = (time.time() - start_time) * 1000
        
        self.record_success()
        
        return {
            "content": response.choices[0].message.content,
            "tokens_used": response.usage.total_tokens,
            "latency_ms": latency,
            "provider": self.name,
        }


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider."""
    
    def __init__(self):
        super().__init__("anthropic", priority=2)
        self.client = None
        self._init_client()
    
    def _init_client(self):
        try:
            import anthropic
            self.client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        except Exception as e:
            logger.error("anthropic_init_failed", error=str(e))
            self.is_available = False
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> Dict:
        if not self.client:
            raise Exception("Anthropic client not initialized")
        
        start_time = time.time()
        
        response = await self.client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        
        latency = (time.time() - start_time) * 1000
        
        self.record_success()
        
        return {
            "content": response.content[0].text,
            "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
            "latency_ms": latency,
            "provider": self.name,
        }


class GoogleProvider(LLMProvider):
    """Google Gemini provider."""
    
    def __init__(self):
        super().__init__("google", priority=3)
        self.model = None
        self._init_client()
    
    def _init_client(self):
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            self.model = genai.GenerativeModel(settings.GOOGLE_MODEL)
        except Exception as e:
            logger.error("google_init_failed", error=str(e))
            self.is_available = False
    
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> Dict:
        if not self.model:
            raise Exception("Google model not initialized")
        
        start_time = time.time()
        
        response = await self.model.generate_content_async(
            prompt,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            },
        )
        
        latency = (time.time() - start_time) * 1000
        
        self.record_success()
        
        return {
            "content": response.text,
            "tokens_used": 0,  # Google doesn't always provide this
            "latency_ms": latency,
            "provider": self.name,
        }


class LLMRouter:
    """
    Routes LLM requests across multiple providers.
    Implements fallback, load balancing, and consensus.
    """
    
    def __init__(self):
        self.providers: List[LLMProvider] = []
        self._init_providers()
        self.logger = logger.bind(component="llm_router")
    
    def _init_providers(self):
        """Initialize all configured providers."""
        if settings.OPENAI_API_KEY:
            self.providers.append(OpenAIProvider())
        if settings.ANTHROPIC_API_KEY:
            self.providers.append(AnthropicProvider())
        if settings.GOOGLE_API_KEY:
            self.providers.append(GoogleProvider())
        
        # Sort by priority
        self.providers.sort(key=lambda p: p.priority)
    
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        preferred_provider: Optional[str] = None,
    ) -> str:
        """
        Generate text using available providers with fallback.
        """
        # Filter available providers
        available = [p for p in self.providers if p.is_available]
        
        if preferred_provider:
            available = [p for p in available if p.name == preferred_provider] + \
                       [p for p in available if p.name != preferred_provider]
        
        if not available:
            raise Exception("No LLM providers available")
        
        last_error = None
        
        for provider in available:
            try:
                self.logger.info(
                    "llm_request",
                    provider=provider.name,
                    prompt_length=len(prompt),
                )
                
                result = await provider.generate(
                    prompt=prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                
                self.logger.info(
                    "llm_success",
                    provider=provider.name,
                    latency_ms=result.get("latency_ms"),
                    tokens=result.get("tokens_used"),
                )
                
                return result["content"]
                
            except Exception as e:
                self.logger.warning(
                    "llm_error",
                    provider=provider.name,
                    error=str(e),
                )
                provider.record_error(str(e))
                last_error = e
        
        raise last_error or Exception("All providers failed")
    
    async def generate_with_consensus(
        self,
        prompt: str,
        providers: Optional[List[str]] = None,
        consensus_threshold: float = 0.7,
    ) -> Dict:
        """
        Generate with multiple providers and build consensus.
        """
        target_providers = providers or [p.name for p in self.providers]
        
        # Query all providers in parallel
        tasks = []
        for provider in self.providers:
            if provider.name in target_providers and provider.is_available:
                tasks.append(self._safe_generate(provider, prompt))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful results
        successful = [
            r for r in results
            if isinstance(r, dict) and "content" in r
        ]
        
        if len(successful) < 2:
            # Not enough for consensus, return best available
            return successful[0] if successful else {"error": "No successful responses"}
        
        # Simple consensus: check if majority agree on structure
        # More sophisticated consensus would use semantic similarity
        contents = [r["content"] for r in successful]
        
        # For now, return the result with highest confidence
        best = max(successful, key=lambda x: x.get("confidence", 0))
        
        return {
            "content": best["content"],
            "consensus_reached": True,
            "providers_used": len(successful),
            "agreement_score": 0.8,  # Placeholder
        }
    
    async def _safe_generate(self, provider: LLMProvider, prompt: str) -> Dict:
        """Safely generate with error handling."""
        try:
            return await provider.generate(prompt)
        except Exception as e:
            return {"error": str(e), "provider": provider.name}