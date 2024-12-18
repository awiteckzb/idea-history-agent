# app/services/llm/base.py
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any


class BaseChatClient(ABC):
    """Abstract base class for chat clients (OpenAI, Claude, etc)"""

    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        functions: Optional[List[Dict]] = None,
        function_call: Optional[Dict] = None,
        **kwargs
    ) -> Any:
        """Generate chat completion"""
        pass
