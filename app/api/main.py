# app/api/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import asyncio
import json
from typing import AsyncGenerator
from datetime import datetime
from app.core.agent import IdeaHistoryAgent
from app.services.search.search_manager import SearchManager
from app.services.search.google_search import GoogleSearchClient
from app.services.search.wiki_client import WikipediaClient
from app.services.llm.claude_client import ClaudeChatClient
from app.services.llm.openai_client import OpenAIChatClient

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Vite's default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ResearchRequest(BaseModel):
    concept: str
    stream: bool = True

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

async def event_generator(queue: asyncio.Queue) -> AsyncGenerator[str, None]:
    while True:
        try:
            data = await queue.get()
            if data is None and queue.empty():  # Signal to stop streaming
                break
            # Use the custom encoder
            yield f"data: {json.dumps(data, cls=CustomJSONEncoder)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'data': str(e)})}\n\n"
            break


@app.post("/research")
async def research_concept(request: ResearchRequest):
    chat_client = OpenAIChatClient(model='gpt-4o-mini')
    search_manager = SearchManager(
        google_client=GoogleSearchClient(),
        wiki_client=WikipediaClient(),
    )

    if not request.stream:
        # Non-streaming response
        try:
            agent = IdeaHistoryAgent(
                chat_client=chat_client,
                search_manager=search_manager,
                min_nodes=3,
                max_nodes=5,
            )
            graph = await agent.research_concept(request.concept)
            return graph.model_dump()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    # Streaming response
    queue = asyncio.Queue()
    
    # Put initial message in queue
    await queue.put({
        "type": "start",
        "data": {"message": "Starting research..."}
    })
    
    def update_handler(data: dict):
        asyncio.create_task(queue.put(data))
    
    async def run_research():
        try:
            agent = IdeaHistoryAgent(
                chat_client=chat_client,
                search_manager=search_manager,
                min_nodes=3,
                max_nodes=5,
                on_update=update_handler
            )
            
            await agent.research_concept(request.concept)
            await queue.put(None)  # Signal completion
        except Exception as e:
            await queue.put({
                "type": "error",
                "data": str(e)
            })
            await queue.put(None)
    
    # Start the research process
    asyncio.create_task(run_research())
    
    return StreamingResponse(
        event_generator(queue),
        media_type="text/event-stream"
    )

@app.get("/")
@app.get("/health")
async def health_check():
    return {"status": "healthy"}