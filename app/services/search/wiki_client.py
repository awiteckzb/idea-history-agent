# services/search/wiki_client.py
import wikipedia
from typing import List
import asyncio
from datetime import datetime
import warnings

from app.models.base import Source
from app.services.search.base import BaseSearchClient


class WikipediaClient(BaseSearchClient):
    def __init__(self, user_agent: str = "IdeaHistoryAgent/1.0"):
        wikipedia.set_user_agent(user_agent)  # Set user agent for Wikipedia API

        # # Patch BeautifulSoup usage in wikipedia package to specify parser
        # def new_bs(*args, **kwargs):
        #     kwargs["features"] = "html.parser"
        #     return BeautifulSoup(*args, **kwargs)

        # Suppress the specific warning
        warnings.filterwarnings("ignore", category=UserWarning, module="wikipedia")

    async def search(self, query: str, num_results: int = 3) -> List[Source]:
        """
        Search Wikipedia and return relevant pages

        Args:
            query: Search query string
            num_results: Number of results to return
        """

        # Run Wikipedia API calls in a thread pool since they're blocking
        def _search():
            # Search for pages
            search_results = wikipedia.search(query, results=num_results)
            sources = []

            for title in search_results:
                try:
                    page = wikipedia.page(title)
                    # Get the first section (usually the most relevant summary)
                    summary = page.summary.split("\n")[0] if page.summary else ""

                    sources.append(
                        Source(
                            url=page.url,
                            title=page.title,
                            snippet=(
                                summary[:500] + "..." if len(summary) > 500 else summary
                            ),
                            source_type="wikipedia",
                            retrieved_at=datetime.now(),
                        )
                    )
                except wikipedia.exceptions.DisambiguationError as e:
                    # Handle disambiguation pages by taking the first option
                    try:
                        page = wikipedia.page(e.options[0])
                        sources.append(
                            Source(
                                url=page.url,
                                title=page.title,
                                snippet=(
                                    page.summary[:500] + "..."
                                    if len(page.summary) > 500
                                    else page.summary
                                ),
                                source_type="wikipedia",
                                retrieved_at=datetime.now(),
                            )
                        )
                    except:
                        continue
                except:
                    continue

            return sources

        # Run blocking code in thread pool
        loop = asyncio.get_event_loop()
        sources = await loop.run_in_executor(None, _search)
        return sources
