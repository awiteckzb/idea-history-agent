# tests/test_agent.py
import asyncio
import os
from openai import AsyncOpenAI

from app.core.agent import IdeaHistoryAgent
from app.services.search.google_search import GoogleSearchClient
from app.services.search.wiki_client import WikipediaClient
from app.services.search.search_manager import SearchManager
from app.config.settings import settings
from app.services.llm.openai_client import OpenAIChatClient
from app.services.llm.claude_client import ClaudeChatClient
from app.models.base import IdeaGraph


async def basic_test():
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini", messages=[{"role": "user", "content": "Hi"}]
        )
        print("Success:", response)
    except Exception as e:
        print("Error type:", type(e))
        print("Error details:", str(e))
        # Print the full exception details
        import traceback

        traceback.print_exc()


# Run the test
# asyncio.run(basic_test())


async def test_agent():
    # openai_client = OpenAIChatClient()
    claude_client = ClaudeChatClient()
    search_manager = SearchManager(
        google_client=GoogleSearchClient(),
        wiki_client=WikipediaClient(),
    )

    agent = IdeaHistoryAgent(
        chat_client=claude_client,
        search_manager=search_manager,
        min_nodes=3,
        max_nodes=5,
    )
    # print("Testing Chat Client connection...")
    # try:
    #     await agent.test_chat_client_connection()
    # except Exception as e:
    #     print(f"Error occurred: {str(e)}")

    # print("Testing function calling...")
    # try:
    #     await agent.test_function_calling()
    # except Exception as e:
    #     print(f"Error occurred: {str(e)}")

    try:
        # Test with a simple concept
        concept = "democracy"
        print(f"\nResearching concept: {concept}")

        # Run research
        graph = await agent.research_concept(concept)

        # Print results
        print("\nResults:")
        print(f"Nodes found: {len(graph.nodes)}")
        print(f"Edges found: {len(graph.edges)}")

        print("\nNodes:")
        for node in graph.nodes:
            print(f"\nTime Period: {node.time_period}")
            print(f"Region: {node.region}")
            print(f"Contributors: {', '.join(node.key_contributors)}")
            print(f"Summary: {node.main_idea_summary}")

        print("\nEdges:")
        for edge in graph.edges:
            print(f"\nFrom {edge.source_node_id} to {edge.target_node_id}")
            print(f"Change: {edge.change_description}")

        # Write graph to file with proper encoding
        with open("graph.json", "w", encoding="utf-8") as f:
            graph_json = graph.to_json()
            print(f"Graph JSON: {graph_json}")
            f.write(graph_json)

        # Later, you can read it back:
        with open("graph.json", "r", encoding="utf-8") as f:
            loaded_graph = IdeaGraph.from_json(f.read())

    except Exception as e:
        print(f"Error occurred: {str(e)}")


if __name__ == "__main__":
    asyncio.run(test_agent())
