# app/core/agent.py
from typing import List, Dict, Optional, Any
from openai import AsyncOpenAI
import networkx as nx
from typing import List
import json
from datetime import datetime
import uuid
from pprint import pprint
from app.config.settings import settings
from app.services.search.search_manager import SearchManager
from app.models.base import Source, Node, Edge, IdeaGraph
from app.services.llm.schemas import (
    CREATE_NODE_SCHEMA,
    CREATE_EDGE_SCHEMA,
    JUDGE_INFORMATION_SCHEMA,
    MERGE_NODES_SCHEMA,
    GENERATE_NEXT_QUERY_SCHEMA,
)
from app.services.llm.base import BaseChatClient
from app.models.responses import ChatCompletion
from app.services.llm.prompts import *


class IdeaHistoryAgent:

    def __init__(
        self,
        chat_client: BaseChatClient,
        search_manager: SearchManager,
        min_nodes: int = 3,
        max_nodes: int = 5,
    ):
        self.chat_client = chat_client
        self.search_manager = search_manager
        self.min_nodes = min_nodes
        self.max_nodes = max_nodes
        self.collected_sources: List[Source] = []
        self.graph = IdeaGraph(concept="", nodes=[], edges=[])
        self.current_query = ""

    async def research_concept(self, concept: str) -> IdeaGraph:
        """Main entry point for researching a concept's history"""
        try:
            self.graph.concept = concept
            self.current_query = (
                f"history of {concept} philosophy evolution development"
            )

            # Initial search
            # TODO: Use LLMs to generate a better query, hardcored for now
            print("Performing initial search...")

            try:
                initial_sources = await self._perform_search(self.current_query)
                if not initial_sources:
                    raise ValueError("No initial sources found")
                self.collected_sources.extend(initial_sources)
            except Exception as e:
                print(f"Error during initial search: {str(e)}")
                raise

            # Initialize the graph with first sources
            print("Processing initial sources...")
            try:
                await self._process_sources(initial_sources)
            except Exception as e:
                print(f"Error processing initial sources: {str(e)}")
                raise

            try:
                while not await self._has_sufficient_information():
                    print("Generating next query...")
                    query = await self._generate_next_query()
                    if not query:
                        raise ValueError("Failed to generate next query")

                    self.current_query = query

                    print(f"Searching for: {query}")
                    sources = await self._perform_search(query)
                    if sources:
                        self.collected_sources.extend(sources)
                        await self._process_sources(sources)
                    else:
                        print("No additional sources found")
                        break
            except Exception as e:
                print(f"Error during iterative search: {str(e)}")
                # Continue with graph finalization even if iterative search fails

            # Finalize the graph
            try:
                await self._merge_similar_nodes()
                await self._validate_graph()
            except Exception as e:
                print(f"Error during graph finalization: {str(e)}")
                raise

            if not self.graph.nodes:
                raise ValueError("Failed to construct graph - no nodes created")

            return self.graph

        except Exception as e:
            print(f"Critical error in research_concept: {str(e)}")
            # Return empty graph rather than raising to avoid complete failure
            return IdeaGraph(concept=concept, nodes=[], edges=[])

    async def _perform_search(self, query: str) -> List[Source]:
        return await self.search_manager.search(query)

    async def _process_sources(self, sources: List[Source]):
        """Extract information from the sources and update the graph"""
        try:
            graph_summary = self._format_graph_for_llm()

            # Construct prompt with all source information
            # Construct prompt with all source information
            sources_text = "\n\n".join(
                [
                    f"Source: {source.title}\nURL: {source.url}\nContent: {source.snippet}"
                    for source in sources
                ]
            )

            node_prompt = PROCESS_SOURCES_PROMPT["nodes"].format(
                concept=self.graph.concept,
                graph_summary=graph_summary,
                sources_text=sources_text,
            )

            # Call openai client
            node_response = await self._call_llm(
                messages=[{"role": "user", "content": node_prompt}],
                functions=[CREATE_NODE_SCHEMA],
                function_call="auto",
            )
            for choice in node_response.choices:  # Access as dictionary
                if choice.message.function_call:
                    try:
                        if choice.message.function_call.name == "create_node":
                            node_data = json.loads(
                                choice.message.function_call.arguments
                            )
                            node = Node(**node_data, sources=sources)
                            self.graph.nodes.append(node)
                    except json.JSONDecodeError as e:
                        print(f"Error parsing function arguments: {str(e)}")
                        continue
                    except ValueError as e:
                        print(f"Error creating node: {str(e)}")
                        continue

            graph_summary = self._format_graph_for_llm()

            # TODO: maybe add extra info on what nodes are newly created, LLM should pay extra attention
            edge_prompt = PROCESS_SOURCES_PROMPT["edges"].format(
                concept=self.graph.concept,
                graph_summary=graph_summary,
                sources_text=sources_text,
            )

            # Call openai client
            edge_response = await self._call_llm(
                messages=[{"role": "user", "content": edge_prompt}],
                functions=[CREATE_EDGE_SCHEMA],
                function_call="auto",
            )
            for choice in edge_response.choices:  # Access as dictionary
                if choice.message.function_call:
                    try:
                        if choice.message.function_call.name == "create_edge":
                            edge_data = json.loads(
                                choice.message.function_call.arguments
                            )
                            edge = Edge(**edge_data, sources=sources)
                            self.graph.edges.append(edge)
                    except json.JSONDecodeError as e:
                        print(f"Error parsing function arguments: {str(e)}")
                        continue
                    except ValueError as e:
                        print(f"Error creating edge: {str(e)}")
                        continue

            # # Process the extracted information and update graph
            # for choice in response.choices:  # Access as dictionary
            #     if choice.message.function_call:
            #         try:
            #             if choice.message.function_call.name == "create_node":
            #                 node_data = json.loads(
            #                     choice.message.function_call.arguments
            #                 )
            #                 node = Node(**node_data, sources=sources)
            #                 self.graph.nodes.append(node)
            #             elif choice.message.function_call.name == "create_edge":
            #                 edge_data = json.loads(
            #                     choice.message.function_call.arguments
            #                 )
            #                 edge = Edge(**edge_data, sources=sources)
            #                 self.graph.edges.append(edge)
            #         except json.JSONDecodeError as e:
            #             print(f"Error parsing function arguments: {str(e)}")
            #             continue
            #         except ValueError as e:
            #             print(f"Error creating node/edge: {str(e)}")
            #             continue

        except Exception as e:
            print(f"Error processing sources: {str(e)}")
            raise

    async def _has_sufficient_information(self) -> bool:
        "Determine if the graph has sufficient information"
        try:
            print(f"Graph nodes: {len(self.graph.nodes)}")
            print(f"Graph edges: {len(self.graph.edges)}")
            if len(self.graph.nodes) >= self.max_nodes:
                return True
            if len(self.graph.nodes) < self.min_nodes:
                return False

            prompt = f"""
            Evaluate if we have sufficient information about the evolution of '{self.graph.concept}'.
            Current nodes: {len(self.graph.nodes)}
            Current edges: {len(self.graph.edges)}
            Node summaries: {[node.main_idea_summary for node in self.graph.nodes]}
            """

            response = await self._call_llm(
                messages=[{"role": "user", "content": prompt}],
                functions=[JUDGE_INFORMATION_SCHEMA],
                function_call={"name": "judge_information_sufficiency"},
            )

            try:
                result = json.loads(response.choices[0].message.function_call.arguments)
                print(f"Is sufficient: {result['is_sufficient']}")
                return result["is_sufficient"]
            except (json.JSONDecodeError, KeyError, IndexError) as e:
                print(f"Error parsing LLM response: {str(e)}")
                return False

        except Exception as e:
            print(f"Error checking information sufficiency: {str(e)}")
            return False

    async def _generate_next_query(self) -> str:
        """Generate next search query based on current information gaps"""
        try:
            # TODO: have a better way of representing the graph to the LLM
            summary = self._format_graph_for_llm()
            prompt = QUERY_UPDATE_PROMPT.format(
                concept=self.graph.concept,
                summary=summary,
                previous_query=self.current_query,
            )
            print(f"Prompt: {prompt}")

            response: ChatCompletion = await self._call_llm(
                messages=[{"role": "user", "content": prompt}],
                functions=[GENERATE_NEXT_QUERY_SCHEMA],
                function_call={"name": "generate_next_query"},
            )

            # Get the query from the response
            try:
                query = json.loads(response.choices[0].message.function_call.arguments)[
                    "query"
                ]
                return query
            except (json.JSONDecodeError, KeyError, IndexError) as e:
                print(f"Error parsing LLM response for next query: {str(e)}")
                return f"More information about {self.graph.concept}"

            # try:
            #     return response.choices[0].message.content
            # except (AttributeError, IndexError) as e:
            #     print(f"Error accessing LLM response content: {str(e)}")
            #     return f"More information about {self.graph.concept}"

        except Exception as e:
            print(f"Error generating next query: {str(e)}")
            # Return a basic fallback query using the original concept
            return f"History and development of {self.graph.concept}"

    async def _merge_similar_nodes(self):
        """Identify and merge nodes that represent the same conceptual development"""
        try:
            nodes_data = [node.model_dump() for node in self.graph.nodes]

            prompt = f"""
            Analyze these nodes representing developments in the concept of '{self.graph.concept}'.
            Identify any nodes that represent the same conceptual development and should be merged.
            Consider:
            - Temporal proximity
            - Geographic overlap
            - Similar key contributors
            - Similar main ideas
            
            Nodes: {nodes_data}
            """

            try:
                # Get ChatCompletion response
                response: ChatCompletion = await self._call_llm(
                    messages=[{"role": "user", "content": prompt}],
                    functions=[MERGE_NODES_SCHEMA],
                    function_call={"name": "merge_nodes"},
                )
            except Exception as e:
                print(f"Error calling LLM for node merging: {str(e)}")
                return

            try:
                # Check if we have a valid function call in the first choice
                if response.choices and response.choices[0].message.function_call:
                    merge_data = json.loads(
                        response.choices[0].message.function_call.arguments
                    )
                else:
                    print("No function call found in response")
                    return
            except (json.JSONDecodeError, AttributeError, IndexError) as e:
                print(f"Error parsing LLM response for node merging: {str(e)}")
                return

            # Execute merge if we have node IDs
            if merge_data.get("node_ids"):
                try:
                    await self._execute_node_merge(
                        node_ids=merge_data["node_ids"],
                        reasoning=merge_data.get("reasoning", "No reasoning provided"),
                        merged_summary=merge_data.get(
                            "merged_summary", "No summary provided"
                        ),
                    )
                except Exception as e:
                    print(f"Error executing node merge: {str(e)}")

        except Exception as e:
            print(f"Error in merge_similar_nodes: {str(e)}")

    async def _execute_node_merge(
        self, node_ids: List[str], reasoning: str, merged_summary: str
    ):
        """Execute the merging of multiple nodes and update affected edges"""
        try:
            # Validate inputs
            if not node_ids:
                raise ValueError("No node IDs provided for merging")
            if not reasoning:
                raise ValueError("No reasoning provided for merge")
            if not merged_summary:
                raise ValueError("No merged summary provided")

            # Find all nodes to be merged
            # TODO: store nodes in a hashmap instead {id: Node}, can index quicker.
            nodes_to_merge = [node for node in self.graph.nodes if node.id in node_ids]
            if not nodes_to_merge:
                raise ValueError(f"No nodes found matching provided IDs: {node_ids}")

            try:
                # Create merged node
                merged_node = self._create_merged_node(
                    nodes_to_merge, merged_summary, reasoning
                )
            except Exception as e:
                raise ValueError(f"Failed to create merged node: {str(e)}")

            try:
                # Update edges
                self._update_edges_for_merged_node(
                    old_node_ids=node_ids, merged_node_id=merged_node.id
                )
            except Exception as e:
                raise ValueError(f"Failed to update edges: {str(e)}")

            # Remove old nodes and add merged node
            self.graph.nodes = [
                node for node in self.graph.nodes if node.id not in node_ids
            ]
            self.graph.nodes.append(merged_node)

            # Add merge info to graph metadata
            try:
                if "merge_history" not in self.graph.metadata:
                    self.graph.metadata["merge_history"] = []

                self.graph.metadata["merge_history"].append(
                    {
                        "merged_node_ids": node_ids,
                        "new_node_id": merged_node.id,
                        "reasoning": reasoning,
                        "timestamp": datetime.now().isoformat(),
                    }
                )
            except Exception as e:
                print(f"Warning: Failed to update merge history: {str(e)}")
                # Continue since this is non-critical

        except Exception as e:
            print(f"Error executing node merge: {str(e)}")
            raise

    def _create_merged_node(
        self, nodes: List[Node], merged_summary: str, reasoning: str
    ) -> Node:
        """Create a new node from merged nodes"""

        # Combine time periods
        # If they're different, take the earlier one and add a note
        time_periods = set(node.time_period for node in nodes)
        merged_time_period = (
            min(time_periods) if len(time_periods) > 1 else nodes[0].time_period
        )

        # Combine regions
        regions = set(node.region for node in nodes)
        merged_region = " & ".join(regions) if len(regions) > 1 else nodes[0].region

        # Combine key contributors without duplicates
        key_contributors = set()
        for node in nodes:
            key_contributors.update(node.key_contributors)

        # Combine sources
        merged_sources = []
        for node in nodes:
            merged_sources.extend(node.sources)

        # Create new node
        return Node(
            id=str(uuid.uuid4()),
            time_period=merged_time_period,
            region=merged_region,
            key_contributors=list(key_contributors),
            main_idea_summary=merged_summary,
            sources=merged_sources,
            metadata={
                "merged_from": [node.id for node in nodes],
                "merge_reasoning": reasoning,
                "original_time_periods": list(time_periods),
                "original_regions": list(regions),
            },
        )

    def _update_edges_for_merged_node(
        self, old_node_ids: List[str], merged_node_id: str
    ):
        """Update all edges affected by the node merge"""

        new_edges = []
        seen_connections = set()  # Track unique connections to avoid duplicates

        for edge in self.graph.edges:
            # Handle source node updates
            if edge.source_node_id in old_node_ids:
                source_id = merged_node_id
            else:
                source_id = edge.source_node_id

            # Handle target node updates
            if edge.target_node_id in old_node_ids:
                target_id = merged_node_id
            else:
                target_id = edge.target_node_id

            # Skip self-loops created by merge
            if source_id == target_id:
                continue

            # Skip duplicate connections
            connection = (source_id, target_id)
            if connection in seen_connections:
                continue

            seen_connections.add(connection)

            # Create updated edge
            new_edge = Edge(
                source_node_id=source_id,
                target_node_id=target_id,
                change_description=edge.change_description,
                weight=edge.weight,
                sources=edge.sources,
            )
            new_edges.append(new_edge)

        # Replace old edges with updated ones
        self.graph.edges = new_edges

    async def _validate_graph(self):
        pass

    def _format_graph_for_llm(self) -> str:
        """Format graph information in a clear, concise way for the LLM"""

        # Format each node's essential information
        nodes_info = []
        for node in self.graph.nodes:
            node_str = (
                f"Node ID: {node.id}\n"
                f"Time: {node.time_period}\n"
                f"Region: {node.region}\n"
                f"Key figures: {', '.join(node.key_contributors)}\n"
                f"Summary: {node.main_idea_summary}\n"
            )
            nodes_info.append(node_str)

        # Format edges if they exist
        edges_info = []
        for edge in self.graph.edges:
            edge_str = f"Evolution: {edge.change_description}"
            edges_info.append(edge_str)

        # Combine into final format
        node_info = (
            "\n" + "-" * 50 + "\n".join(nodes_info)
            if nodes_info
            else "No developments recorded yet"
        )
        edge_info = (
            "\n".join(edges_info) if edges_info else "No evolution paths recorded yet"
        )
        summary = SUMMARY_TEMPLATE.format(
            concept=self.graph.concept, node_info=node_info, edge_info=edge_info
        )
        return summary

    async def _call_llm(
        self,
        messages: List[Dict[str, str]],
        functions: Optional[List[Dict]] = None,
        function_call: Optional[Dict] = None,
    ) -> Any:
        """Generic wrapper for LLM calls"""
        try:
            response = await self.chat_client.chat_completion(
                messages=messages, functions=functions, function_call=function_call
            )
            return response
        except Exception as e:
            print(f"LLM API error: {str(e)}")
            raise

    async def test_chat_client_connection(self):
        """Test basic Chat Client API connectivity"""
        try:
            response = await self.chat_client.chat_completion(
                messages=[{"role": "user", "content": "Say hello"}]
            )
            print("Test response:", response)
            return True
        except Exception as e:
            print("Test failed:", str(e))
            return False

    async def test_function_calling(self):
        """Test function calling specifically"""
        try:
            simple_function = {
                "name": "test_function",
                "description": "A simple test function",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string", "description": "A test message"}
                    },
                    "required": ["message"],
                },
            }

            response = await self.chat_client.chat_completion(
                messages=[{"role": "user", "content": "Say hello"}],
                functions=[simple_function],
                function_call="auto",
            )
            print("Function test response:", response)
            return True
        except Exception as e:
            print("Function test failed:", str(e))
            return False
