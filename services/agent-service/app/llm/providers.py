# app/llm/providers.py
# LLM Provider implementations

from abc import ABC, abstractmethod
from typing import Dict


class BaseLLMProvider(ABC):
    """Base class for LLM providers."""
    
    def __init__(self, name: str, api_key: str):
        self.name = name
        self.api_key = api_key
        self.is_available = bool(api_key)
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> Dict:
        pass


class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT provider."""
    
    def __init__(self, api_key: str):
        super().__init__("openai", api_key)
        self.client = None
        if api_key:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=api_key)
    
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> Dict:
        if not self.client:
            raise Exception("OpenAI client not initialized")
        
        response = await self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        return {
            "content": response.choices[0].message.content,
            "tokens_used": response.usage.total_tokens,
            "provider": self.name,
        }


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude provider."""
    
    def __init__(self, api_key: str):
        super().__init__("anthropic", api_key)
        self.client = None
        if api_key:
            import anthropic
            self.client = anthropic.AsyncAnthropic(api_key=api_key)
    
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> Dict:
        if not self.client:
            raise Exception("Anthropic client not initialized")
        
        response = await self.client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        
        return {
            "content": response.content[0].text,
            "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
            "provider": self.name,
        }


class GoogleProvider(BaseLLMProvider):
    """Google Gemini provider."""
    
    def __init__(self, api_key: str):
        super().__init__("google", api_key)
        self.model = None
        if api_key:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel("gemini-pro")
    
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> Dict:
        if not self.model:
            raise Exception("Google model not initialized")
        
        response = await self.model.generate_content_async(
            prompt,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            },
        )
        
        return {
            "content": response.text,
            "tokens_used": 0,
            "provider": self.name,
        }