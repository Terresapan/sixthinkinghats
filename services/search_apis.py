"""
Search APIs module for integrating with external search providers.
Currently supports Tavily search API.
"""

from typing import List, Dict, Any, Optional
from tavily import TavilyClient
import os


class SearchResult:
    """Represents a single search result."""
    
    def __init__(self, title: str, url: str, content: str, score: float = 0.0):
        self.title = title
        self.url = url
        self.content = content
        self.score = score
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "url": self.url,
            "content": self.content,
            "score": self.score
        }


class SearchAPI:
    """Abstract base class for search API providers."""

    def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Perform a web search and return results."""
        raise NotImplementedError


class TavilySearchAPI(SearchAPI):
    """Tavily search API implementation."""

    def __init__(self):
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("TAVILY_API_KEY environment variable is required")
        self.client = TavilyClient(api_key=api_key)

    def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Perform a search using Tavily API."""
        try:
            response = self.client.search(
                query=query,
                max_results=max_results,
                include_answer=False,
                include_raw_content=True
            )
            
            results = []
            for item in response.get("results", []):
                result = SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    content=item.get("content", ""),
                    score=item.get("score", 0.0)
                )
                results.append(result)
            
            return results
        except Exception as e:
            print(f"Tavily search error: {e}")
            return []


class SearchAPIFactory:
    """Factory class for creating search API instances."""
    
    _providers = {
        "tavily": TavilySearchAPI,
    }
    
    @classmethod
    def create_provider(cls, provider_name: str) -> SearchAPI:
        """Create a search API provider instance."""
        if provider_name not in cls._providers:
            raise ValueError(f"Unknown search provider: {provider_name}")
        
        return cls._providers[provider_name]()
    
    @classmethod
    def get_available_providers(cls) -> List[str]:
        """Get list of available search providers."""
        return list(cls._providers.keys())
