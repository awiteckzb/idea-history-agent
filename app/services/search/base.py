from abc import ABC, abstractmethod
from typing import List
from app.models.base import Source


class BaseSearchClient(ABC):
    """Abstract base client for search services"""

    @abstractmethod
    def search(self, query: str, **kwargs) -> List[Source]:
        """Search for information related to the query"""
        pass
