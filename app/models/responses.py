from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum


class FinishReason(Enum):
    STOP = "stop"
    LENGTH = "length"
    FUNCTION_CALL = "function_call"
    TOOL_USE = "tool_use"
    CONTENT_FILTER = "content_filter"
    END_TURN = "end_turn"


@dataclass
class FunctionCall:
    name: str
    arguments: str


@dataclass
class TokenUsageDetails:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass
class ChatMessage:
    role: str
    content: Optional[str]
    function_call: Optional[FunctionCall] = None


@dataclass
class Choice:
    finish_reason: str
    index: int
    message: ChatMessage


@dataclass
class ChatCompletion:
    id: str
    choices: List[Choice]
    created: int
    model: str
    usage: TokenUsageDetails

    @classmethod
    def from_openai_response(cls, response: Any) -> "ChatCompletion":
        # Convert OpenAI response to our standardized format
        choices = []
        for choice in response.choices:
            function_call = None
            if choice.message.function_call:
                function_call = FunctionCall(
                    name=choice.message.function_call.name,
                    arguments=choice.message.function_call.arguments,
                )

            message = ChatMessage(
                role=choice.message.role,
                content=choice.message.content,
                function_call=function_call,
            )

            choices.append(
                Choice(
                    finish_reason=choice.finish_reason,
                    index=choice.index,
                    message=message,
                )
            )

        usage = TokenUsageDetails(
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens,
        )

        return cls(
            id=response.id,
            choices=choices,
            created=response.created,
            model=response.model,
            usage=usage,
        )

    @classmethod
    def from_claude_response(cls, response: Dict) -> "ChatCompletion":
        # Convert Claude response to our standardized format
        choices = []
        for choice in response["choices"]:
            function_call = None
            if choice["message"].get("function_call"):
                function_call = FunctionCall(
                    name=choice["message"]["function_call"]["name"],
                    arguments=choice["message"]["function_call"]["arguments"],
                )

            message = ChatMessage(
                role=choice["message"]["role"],
                content=choice["message"]["content"],
                function_call=function_call,
            )

            choices.append(
                Choice(
                    finish_reason=choice["finish_reason"],
                    index=choice["index"],
                    message=message,
                )
            )

        usage = TokenUsageDetails(
            prompt_tokens=response["usage"]["prompt_tokens"],
            completion_tokens=response["usage"]["completion_tokens"],
            total_tokens=response["usage"]["total_tokens"],
        )

        return cls(
            id=response["id"],
            choices=choices,
            created=response["created"],
            model=response["model"],
            usage=usage,
        )
