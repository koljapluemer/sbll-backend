from abc import ABC, abstractmethod
from typing import Any


class AIProvider(ABC):
    """Abstract base class for AI providers"""

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> dict[str, Any]:
        """
        Generate AI response.

        Returns dict with:
        - output: the generated content
        - metadata: provider-specific metadata (model, tokens, latency, etc.)
        """
        pass
