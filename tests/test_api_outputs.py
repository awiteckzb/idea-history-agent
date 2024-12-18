import asyncio
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from app.config.settings import settings


async def test_api_outputs():
    openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    try:

        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=1024,
            functions=[
                {
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
            ],
            function_call="auto",
            messages=[
                {"role": "user", "content": "What's the weather like in San Francisco?"}
            ],
        )
        print("OpenAI function test response:", response)
    except Exception as e:
        print("Error type:", type(e))
        print("Error details:", str(e))
        # Print the full exception details
        import traceback

        traceback.print_exc()

    try:
        claude_client = AsyncAnthropic(api_key=settings.CLAUDE_API_KEY)
        response = await claude_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            tools=[
                {
                    "name": "get_weather",
                    "description": "Get the current weather in a given location",
                    "input_schema": {
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
            ],
            messages=[
                {"role": "user", "content": "What's the weather like in San Francisco?"}
            ],
        )
        print("Claude function test response:", response)
    except Exception as e:
        print("Error type:", type(e))
        print("Error details:", str(e))
        # Print the full exception details
        import traceback

        traceback.print_exc()


# Run the test
asyncio.run(test_api_outputs())
