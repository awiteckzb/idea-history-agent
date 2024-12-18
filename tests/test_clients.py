import asyncio
from app.config.settings import settings
from app.services.llm.openai_client import OpenAIChatClient
from app.services.llm.claude_client import ClaudeChatClient


async def test_clients():
    openai_client = OpenAIChatClient()
    claude_client = ClaudeChatClient()

    messages_1 = [{"role": "user", "content": "Say hello"}]
    messages_2 = [
        {"role": "user", "content": "What's the weather like in San Francisco?"}
    ]
    weather_schema = {
        "name": "get_weather",
        "description": "Get the current weather in a given location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city and state, e.g. San Francisco, CA",
                }
            },
            "required": ["location"],
        },
    }

    try:
        response = await openai_client.chat_completion(
            messages=messages_1,
        )
        print("OpenAI response:", response)
    except Exception as e:
        print("Error:", e)

    try:
        response = await claude_client.chat_completion(
            messages=messages_1,
        )
        print("Claude response:", response)
    except Exception as e:
        print("Error:", e)

    try:
        response = await openai_client.chat_completion(
            messages=messages_2,
            functions=[weather_schema],
            function_call="auto",
        )
        print("OpenAI response:", response)
    except Exception as e:
        print("Error:", e)

    try:
        response = await claude_client.chat_completion(
            messages=messages_2,
            functions=[weather_schema],
            function_call="auto",
        )
        print("Claude response:", response)
    except Exception as e:
        print("Error:", e)


asyncio.run(test_clients())
