CREATE_NODE_SCHEMA = {
    "name": "create_node",
    "description": "Create a new node in the idea graph",
    "parameters": {
        "type": "object",
        "properties": {
            "time_period": {
                "type": "string",
                "description": "The time period in which this idea appeared. Should be as specific/concrete as possible.",
            },
            "year": {
                "type": "integer",
                "description": "An estimate of the year in which this idea appeared. Does not need to be exact. Should be in 'YYYY' format. If the time period is a range, use the start year. If the idea is BC, make it negative.",
            },
            "region": {
                "type": "string",
                "description": "The geographical or cultural region where this idea was prominent",
            },
            "key_contributors": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Key figures who contributed to this version of the idea",
            },
            "main_idea_summary": {
                "type": "string",
                "description": "A concise summary of how the concept was understood at this time",
            },
        },
        "required": [
            "time_period",
            "year",
            "region",
            "key_contributors",
            "main_idea_summary",
        ],
    },
}

CREATE_EDGE_SCHEMA = {
    "name": "create_edge",
    "description": "Create a new edge representing evolution between two idea snapshots",
    "parameters": {
        "type": "object",
        "properties": {
            "source_node_id": {
                "type": "string",
                "description": "ID of the source node. Should be different from the target node.",
            },
            "target_node_id": {
                "type": "string",
                "description": "ID of the target node. Should be different from the source node.",
            },
            "change_description": {
                "type": "string",
                "description": "Description of how the idea evolved between these points",
            },
        },
        "required": ["source_node_id", "target_node_id", "change_description"],
    },
}

JUDGE_INFORMATION_SCHEMA = {
    "name": "judge_information",
    "description": "Judge whether we have sufficient information to construct a meaningful graph",
    "parameters": {
        "type": "object",
        "properties": {
            "is_sufficient": {
                "type": "boolean",
                "description": "Whether current information is sufficient",
            },
            "reasoning": {
                "type": "string",
                "description": "Explanation of why information is or isn't sufficient",
            },
            "suggested_query": {
                "type": "string",
                "description": "If insufficient, suggested next search query",
            },
        },
        "required": ["is_sufficient", "reasoning"],
    },
}

MERGE_NODES_SCHEMA = {
    "name": "merge_nodes",
    "description": "Identify nodes that represent the same conceptual development and should be merged",
    "parameters": {
        "type": "object",
        "properties": {
            "node_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "IDs of nodes that should be merged",
            },
            "reasoning": {
                "type": "string",
                "description": "Explanation of why these nodes should be merged",
            },
            "merged_summary": {
                "type": "string",
                "description": "Combined summary for the merged node",
            },
        },
        "required": ["node_ids", "reasoning", "merged_summary"],
    },
}

GENERATE_NEXT_QUERY_SCHEMA = {
    "name": "generate_next_query",
    "description": "Generate next search query based on current information gaps",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Next search query. Should be concise and in the style of a Google query.",
            },
            "reasoning": {
                "type": "string",
                "description": "Explanation of why this query is appropriate. Can be a single sentence or a few sentences.",
            },
        },
        "required": ["query", "reasoning"],
    },
}
