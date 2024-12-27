# app/core/agent.py
from typing import List, Dict, Optional, Any, Callable
import json
from datetime import datetime
import uuid
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
        on_update: Optional[Callable[[Dict[str, Any]], None]] = None
    ):
        self.chat_client = chat_client
        self.search_manager = search_manager
        self.min_nodes = min_nodes
        self.max_nodes = max_nodes
        self.collected_sources: List[Source] = []
        self.graph = IdeaGraph(concept="", nodes=[], edges=[])
        self.current_query = ""
        self.on_update = on_update

    async def research_concept(self, concept: str) -> IdeaGraph:
        """Main entry point for researching a concept's history"""
        try:
            self.graph.concept = concept
            self._emit_update("start", {"concept": concept})

            # self.current_query = (
            #     f"history of {concept} philosophy evolution development"
            # )
            self.current_query = concept
            self._emit_update("query", {"query": self.current_query})

            initial_sources = await self._perform_search(self.current_query)
            if not initial_sources:
                raise ValueError("No initial sources found")
            self.collected_sources.extend(initial_sources)
            
            self._emit_update("sources_found", {
                "count": len(initial_sources),
                "query": self.current_query
            })

            # Initialize the graph with first sources
            await self._process_sources(initial_sources)
            self._emit_update("graph_updated", {
                "nodes": len(self.graph.nodes),
                "edges": len(self.graph.edges)
            })

            while not await self._has_sufficient_information():
                query = await self._generate_next_query()
                if not query:
                    raise ValueError("Failed to generate next query")

                self.current_query = query
                self._emit_update("query", {"query": query})

                print(f"Searching for: {query}")
                sources = await self._perform_search(query)
                if sources:
                    self.collected_sources.extend(sources)
                    self._emit_update("sources_found", {
                        "count": len(sources),
                        "query": query
                    })

                    await self._process_sources(sources)
                    self._emit_update("graph_updated", {
                        "nodes": len(self.graph.nodes),
                        "edges": len(self.graph.edges)
                    })
                else:
                    print("No additional sources found")
                    break

            # Finalize the graph
            print("Starting graph finalization...")
            print("Merging similar nodes")
            await self._merge_similar_nodes()
            print("Merged similar nodes")
            await self._validate_graph()
            print("Graph validated")

            print("Attempting to emit complete event...")
            self._emit_update("complete", {
                "nodes": len(self.graph.nodes),
                "edges": len(self.graph.edges)
            })
            print("Complete event emitted")

            if not self.graph.nodes:
                raise ValueError("Failed to construct graph - no nodes created")

            return self.graph

        except Exception as e:
            self._emit_update("error", {"error": str(e)})
            print(f"Critical error in research_concept: {str(e)}")
            # Return empty graph rather than raising to avoid complete failure
            return IdeaGraph(concept=concept, nodes=[], edges=[])

    
    def _emit_update(self, event_type: str, data: Dict[str, Any]):
        if self.on_update:
            # Convert to dict first to ensure all fields are serializable
            graph_data = self.graph.model_dump()
            self.on_update({
                "type": event_type,
                "data": data,
                "graph": graph_data
            })

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
                            if edge_data['source_node_id'] != edge_data['target_node_id']:

                                '''
                                for edge in edges:
                                    source_node = self._get_node_by_id(edge.source_node_id)
                                    target_node = self._get_node_by_id(edge.target_node_id)
                                    
                                    if source_node and target_node:
                                        if source_node.year <= target_node.year:
                                            correct_edges.append(edge)
                                        else:
                                            # Swap source and target if chronologically backwards
                                            swapped_edge = Edge(
                                                source_node_id=edge.target_node_id,
                                                target_node_id=edge.source_node_id, 
                                                change_description=edge.change_description,
                                                weight=edge.weight,
                                                sources=edge.sources
                                            )
                                            correct_edges.append(swapped_edge)
                                '''
                                # Check if edge is chronologically correct
                                source_node = self._get_node_by_id(edge_data['source_node_id'])
                                target_node = self._get_node_by_id(edge_data['target_node_id'])
                                if source_node and target_node:
                                    if source_node.year <= target_node.year:
                                        edge = Edge(**edge_data, sources=sources)
                                        self.graph.edges.append(edge)
                                    else:
                                        # Swap source and target if chronologically backwards
                                        swapped_edge = Edge(
                                            source_node_id=edge_data['target_node_id'],
                                            target_node_id=edge_data['source_node_id'], 
                                            change_description=edge_data['change_description'],
                                            weight=edge_data['weight'],
                                            sources=edge_data['sources']
                                        )
                                        self.graph.edges.append(swapped_edge)
                    except json.JSONDecodeError as e:
                        print(f"Error parsing function arguments: {str(e)}")
                        continue
                    except ValueError as e:
                        print(f"Error creating edge: {str(e)}")
                        continue

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
                function_call={"name": JUDGE_INFORMATION_SCHEMA["name"]},
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
                print("Calling LLM for node merging")
                response: ChatCompletion = await self._call_llm(
                    messages=[{"role": "user", "content": prompt}],
                    functions=[MERGE_NODES_SCHEMA],
                    function_call={"name": "merge_nodes"},
                )
            except Exception as e:
                print(f"Error calling LLM for node merging: {str(e)}")
                return

            try:
                print("Parsing LLM response for node merging")
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
                    print("Executing node merge")
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
            print("Finding nodes to merge")
            nodes_to_merge = [node for node in self.graph.nodes if node.id in node_ids]
            if not nodes_to_merge:
                raise ValueError(f"No nodes found matching provided IDs: {node_ids}")

            try:
                # Create merged node
                print("Creating merged node")
                merged_node = self._create_merged_node(
                    nodes_to_merge, merged_summary, reasoning
                )
            except Exception as e:
                raise ValueError(f"Failed to create merged node: {str(e)}")

            try:
                # Update edges
                print("Updating edges")
                self._update_edges_for_merged_node(
                    old_node_ids=node_ids, merged_node_id=merged_node.id
                )
            except Exception as e:
                raise ValueError(f"Failed to update edges: {str(e)}")

            # Remove old nodes and add merged node
            print("Removing old nodes and adding merged node")
            self.graph.nodes = [
                node for node in self.graph.nodes if node.id not in node_ids
            ]
            self.graph.nodes.append(merged_node)

            # Add merge info to graph metadata
            try:
                print("Adding merge info to graph metadata")
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

        # Just take the time period of the first node
        # TODO: use small LLM to merge time periods
        time_periods = set(node.time_period for node in nodes)
        merged_time_period = nodes[0].time_period

        # Get years and combine
        years = [node.year for node in nodes if hasattr(node, 'year')]
        merged_year = min(years) if years else 0  # Default to 0 if no years available



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
            id=str(uuid.uuid4())[:8],
            time_period=merged_time_period,
            year=merged_year,
            region=merged_region,
            key_contributors=list(key_contributors),
            main_idea_summary=merged_summary,
            sources=merged_sources,
            metadata={
                "merged_from": [node.id for node in nodes],
                "merge_reasoning": reasoning,
                "original_time_periods": list(time_periods),
                "original_regions": list(regions),
                "original_years": list(years),
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
        """Validate and clean the graph's edges for consistency."""
        try:
            self.graph.edges = self._remove_duplicate_edges(self.graph.edges)
            self.graph.edges = self._enforce_temporal_order(self.graph.edges)
        except Exception as e:
            print(f"Error validating graph: {str(e)}")
            raise

    def _remove_duplicate_edges(self, edges):
        """Remove any duplicate edges with the same source and target nodes."""
        try:
            seen = set()
            unique_edges = []
            
            for edge in edges:
                key = (edge.source_node_id, edge.target_node_id)
                if key not in seen:
                    seen.add(key)
                    unique_edges.append(edge)
                    
            return unique_edges
        except Exception as e:
            print(f"Error removing duplicate edges: {str(e)}")
            raise

    def _enforce_temporal_order(self, edges):
        """Ensure edges only connect from earlier to later nodes chronologically."""
        try:
            correct_edges = []
            
            for edge in edges:
                source_node = self._get_node_by_id(edge.source_node_id)
                target_node = self._get_node_by_id(edge.target_node_id)
                
                if source_node and target_node:
                    if source_node.year <= target_node.year:
                        correct_edges.append(edge)
                    else:
                        # Swap source and target if chronologically backwards
                        swapped_edge = Edge(
                            source_node_id=edge.target_node_id,
                            target_node_id=edge.source_node_id, 
                            change_description=edge.change_description,
                            weight=edge.weight,
                            sources=edge.sources
                        )
                        correct_edges.append(swapped_edge)
                    
            return correct_edges
        except Exception as e:
            print(f"Error enforcing temporal order: {str(e)}")
            raise
            
    def _get_node_by_id(self, node_id):
        """Helper method to find a node by its ID."""
        try:
            return next((node for node in self.graph.nodes if node.id == node_id), None)
        except Exception as e:
            print(f"Error getting node by ID: {str(e)}")
            raise

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
