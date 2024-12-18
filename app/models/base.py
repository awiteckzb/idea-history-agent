from pydantic import BaseModel, Field
from datetime import datetime
import uuid
from typing import List, Dict
import json


class Source(BaseModel):
    url: str
    title: str
    snippet: str
    source_type: str = Field(..., description="Either 'google' or 'wikipedia'")
    retrieved_at: datetime = Field(default_factory=datetime.now)


class Node(BaseModel):
    """Represents a snapshot of an idea at a particular time and place"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    time_period: str
    year: int
    region: str
    key_contributors: List[str]
    main_idea_summary: str
    sources: List[Source] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "time_period": "4th century BCE",
                "region": "Ancient Greece",
                "key_contributors": ["Aristotle"],
                "main_idea_summary": "Concept of individual moral agency...",
                "sources": [],
            }
        }


class Edge(BaseModel):
    """Represents an evolution or influence between two idea snapshots"""

    source_node_id: str
    target_node_id: str
    change_description: str
    weight: float = 1.0
    sources: List[Source] = Field(default_factory=list)


class IdeaGraph(BaseModel):
    """Represents the complete evolution of an idea"""

    concept: str
    nodes: List[Node] = Field(default_factory=list)
    edges: List[Edge] = Field(default_factory=list)
    metadata: Dict = Field(default_factory=dict)  # For future extensibility

    def to_json(self) -> str:
        """Serialize the graph to JSON string"""
        return json.dumps(
            self.model_dump(), indent=2, default=str  # Handles datetime serialization
        )

    @classmethod
    def from_json(cls, json_str: str) -> "IdeaGraph":
        """Create an IdeaGraph instance from a JSON string"""
        data = json.loads(json_str)
        return cls(**data)
