# services/llm/claude_client.py
from typing import List, Dict, Optional, Any
import json
from anthropic import AsyncAnthropic
import time

from app.services.llm.base import BaseChatClient
from app.config.settings import settings
from app.models.responses import ChatCompletion


class ClaudeChatClient(BaseChatClient):
    def __init__(self, model: str = "claude-3-5-haiku-20241022"):
        self.client = AsyncAnthropic(api_key=settings.CLAUDE_API_KEY)
        self.model = model

    def _convert_functions_to_tools(self, functions: List[Dict]) -> List[Dict]:
        """Convert OpenAI function format to Claude tools format"""
        if not functions:
            return None

        tools = []
        for function in functions:
            tool = {
                "name": function["name"],
                "description": function["description"],
                "input_schema": function["parameters"],
            }
            tools.append(tool)
        return tools

    def _convert_claude_response_to_openai(self, claude_response) -> Dict:
        """Convert Claude response format to match OpenAI's structure"""
        # Extract tool use if present
        function_call = None
        content = None
        finish_reason = claude_response.stop_reason

        if claude_response.content:
            if isinstance(claude_response.content, list):
                for block in claude_response.content:
                    if block.type == "tool_use":
                        function_call = {
                            "name": block.name,
                            "arguments": json.dumps(block.input),
                        }
                    elif block.type == "text":
                        content = block.text
            else:
                content = claude_response.content

        # Create choice object matching OpenAI format
        choice = {
            "finish_reason": finish_reason if finish_reason else "end_turn",
            "index": 0,
            "message": {
                "role": claude_response.role,
                "content": content,
                "function_call": function_call,
            },
        }

        # Construct full response matching OpenAI structure
        response_dict = {
            "id": claude_response.id,
            "choices": [choice],
            "created": int(time.time()),
            "model": claude_response.model,
            "usage": {
                "prompt_tokens": claude_response.usage.input_tokens,
                "completion_tokens": claude_response.usage.output_tokens,
                "total_tokens": claude_response.usage.input_tokens
                + claude_response.usage.output_tokens,
            },
        }

        return ChatCompletion.from_claude_response(response_dict)

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        functions: Optional[List[Dict]] = None,
        function_call: Optional[Dict] = None,
        **kwargs,
    ) -> ChatCompletion:
        """Generate chat completion using Claude API"""
        try:
            request_params = {
                "model": self.model,
                "messages": messages,
                "max_tokens": kwargs.get("max_tokens", 1024),
            }

            if functions:
                tools = self._convert_functions_to_tools(functions)
                request_params["tools"] = tools

            response = await self.client.messages.create(**request_params)
            return self._convert_claude_response_to_openai(response)

        except Exception as e:
            print(f"Claude API error: {str(e)}")
            raise
