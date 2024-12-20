from typing import List
import asyncio
from app.services.search.google_search import GoogleSearchClient
from app.services.search.wiki_client import WikipediaClient
from app.services.search.base import Source

class SearchManager:

    def __init__(self, google_client: GoogleSearchClient, wiki_client: WikipediaClient):
        self.google_client = google_client
        self.wiki_client = wiki_client

    async def search(
        self, query: str, google_results: int = 5, wiki_results: int = 3
    ) -> List[Source]:
        """
        Perform searches across all sources and combine results

        Args:
            query: Search query string
            google_results: Number of Google results to retrieve
            wiki_results: Number of Wikipedia results to retrieve
        """
        # Run searches in parallel
        # google_task = self.google_client.search(query, google_results)
        # results = await asyncio.gather(google_task, wiki_task)

        # Just Wikipedia for now
        wiki_task = self.wiki_client.search(query, wiki_results)
        results = await asyncio.gather(wiki_task)

        all_sources = []
        seen_urls = set()

        for source_list in results:
            for source in source_list:
                if source.url not in seen_urls:
                    seen_urls.add(source.url)
                    all_sources.append(source)

        return all_sources
