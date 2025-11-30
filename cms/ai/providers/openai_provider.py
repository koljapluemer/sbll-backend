import time
from typing import Any
from openai import OpenAI
from .base import AIProvider


class OpenAIProvider(AIProvider):
    """OpenAI API provider"""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def generate(self, prompt: str, **kwargs) -> dict[str, Any]:
        """Generate response using OpenAI API"""
        start_time = time.time()

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )

        latency_ms = int((time.time() - start_time) * 1000)

        return {
            "output": response.choices[0].message.content,
            "metadata": {
                "provider": "openai",
                "model": self.model,
                "latency_ms": latency_ms,
                "tokens_used": response.usage.total_tokens if response.usage else None,
                "prompt_tokens": response.usage.prompt_tokens if response.usage else None,
                "completion_tokens": response.usage.completion_tokens if response.usage else None,
            }
        }
