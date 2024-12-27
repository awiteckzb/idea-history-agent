QUERY_UPDATE_PROMPT = """
Your task is to suggest the next search query to expand our understanding of {concept}.

### Current Knowledge ###
{summary}

### Previous Search Query ###
{previous_query}

Based on this information, formulate a specific search query that will help us discover:
1. New time periods or regions we haven't covered
2. Important transitions or influences we're missing
3. Key figures or developments that should be included

Do not be too specific! The emphasis should be on finding new information across different time periods and regions, not getting super specific about just one version of the concept. 
If there is not a lot of knowledge about the concept, try to write a query that will help find the most important time periods and regions. If there is a lot of knowledge and all the general time periods are covered, feel free to get more specific.

### New Search Query ###
"""

SUMMARY_TEMPLATE = """
Current Understanding of {concept}:

### Key Developments ###
{node_info}

### Evolution ###
{edge_info}
"""


PROCESS_SOURCES_PROMPT = {
    "nodes": """
    Based on these sources, identify distinct points in the evolution of the concept '{concept}'.
    Create nodes for each distinct development. The current graph structure is below:
    {graph_summary}

    Given these new sources, update the graph structure to reflect the new information. You can only add nodes, not remove or modify existing ones.
    If a source is not relevant to the concept, ignore it. If a source is relevant, but does not provide new information (i.e. a node is already present), ignore it.
    That being said, you should be very liberal with your use of the 'create_node' function.

    Sources:
    {sources_text}
""",
    "edges": """
    Based on these sources, identify distinct relationships between nodes in the evolution of the concept '{concept}'.
    Create edges to connect related developments. The current graph structure is below:
    {graph_summary}
    Given these new sources, update the graph structure to reflect the new information. You can only add edges, not remove or modify existing ones. For example, if there are two nodes, A and B, and a source indicates that A and B are related, you should create an edge between them. If you know that A and B are related but the source does not directly mention it, you can still create an edge between them.

    Make sure that the node ids are correct. Do not use the same node id for both source and target. This would be adding a self-loop which we do not want.
    
    You are not required to add new edges! If there is only one node, do not add an edge. Only add edges if there is a meaningful connection between two distinct nodes. If there is an edge between two nodes, do not add a new edge between them!

    If a source is not relevant to the concept, ignore it. If a source is relevant, but does not provide new information (i.e. an edge is already present), ignore it. 
    Sources:
    {sources_text}
""",
}
