# app/services/search/google_search.py
from typing import List
import aiohttp
from datetime import datetime
import ssl
import certifi
from app.models.base import Source
from app.services.search.base import BaseSearchClient
from app.config.settings import settings


class GoogleSearchClient(BaseSearchClient):
    """Google search client"""

    def __init__(self):
        self.api_key = settings.GOOGLE_API_KEY
        self.custom_search_id = settings.SEARCH_ENGINE_ID
        self.base_url = settings.GOOGLE_BASE_URL

    async def search(self, query: str, num_results: int = 5) -> List[Source]:
        """
        Perform a Google search using Custom Search API

        Args:
            query: Search query string
            num_results: Number of results to return (max 10 per API limits)
        """

        params = {
            "key": self.api_key,
            "cx": self.custom_search_id,
            "q": query,
            "num": min(num_results, 10),
        }

        # Create SSL context with verified certificates
        ssl_context = ssl.create_default_context(cafile=certifi.where())

        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=ssl_context)
        ) as session:
            async with session.get(self.base_url, params=params) as response:
                if response.status != 200:
                    raise Exception(f"Google search failed: {await response.text()}")

                data = await response.json()

                sources = []
                for item in data.get("items", []):
                    sources.append(
                        Source(
                            url=item.get("link"),
                            title=item.get("title"),
                            snippet=item.get("snippet"),
                            source_type="google",
                            retrieved_at=datetime.now(),
                        )
                    )

                return sources
