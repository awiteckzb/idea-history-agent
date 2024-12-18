from typing import List, Dict, Optional, Any
from openai import AsyncOpenAI
from app.services.llm.base import BaseChatClient
from app.config.settings import settings


class OpenAIChatClient(BaseChatClient):
    def __init__(self, model: str = "gpt-4o-mini"):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = model

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        functions: Optional[List[Dict]] = None,
        function_call: Optional[Dict] = None,
        **kwargs,
    ) -> Any:
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                functions=functions,
                function_call=function_call,
            )
            return response
        except Exception as e:
            print(f"OpenAI API error: {str(e)}")
            raise
