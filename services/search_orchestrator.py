"""
Search Orchestrator module for coordinating search operations across thinking hats.
Manages search budget, prevents duplicates, and coordinates execution.
"""

from typing import List, Dict, Any, Optional, Tuple
import asyncio
from datetime import datetime, timedelta
from collections import defaultdict
import hashlib

from .search_apis import SearchAPI, SearchResult
from .query_analyzer import QueryAnalyzer, HatSearchDecision


class SearchCache:
    """Cache for storing search results to prevent duplicate queries."""
    
    def __init__(self, ttl_seconds: int = 3600):  # 1 hour default TTL
        self.cache = {}
        self.ttl_seconds = ttl_seconds
    
    def _generate_cache_key(self, query: str, hat_name: str) -> str:
        """Generate a cache key for a query and hat combination."""
        combined = f"{hat_name}:{query.lower().strip()}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def get(self, query: str, hat_name: str) -> Optional[List[SearchResult]]:
        """Get cached results if available and not expired."""
        cache_key = self._generate_cache_key(query, hat_name)
        
        if cache_key in self.cache:
            result_data, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < timedelta(seconds=self.ttl_seconds):
                return result_data
            else:
                # Remove expired entry
                del self.cache[cache_key]
        
        return None
    
    def set(self, query: str, hat_name: str, results: List[SearchResult]):
        """Cache search results."""
        cache_key = self._generate_cache_key(query, hat_name)
        self.cache[cache_key] = (results, datetime.now())
    
    def clear(self):
        """Clear all cached results."""
        self.cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_entries = len(self.cache)
        valid_entries = 0
        
        now = datetime.now()
        for result_data, timestamp in self.cache.values():
            if now - timestamp < timedelta(seconds=self.ttl_seconds):
                valid_entries += 1
        
        return {
            "total_entries": total_entries,
            "valid_entries": valid_entries,
            "expired_entries": total_entries - valid_entries,
            "hit_potential": valid_entries / max(total_entries, 1)
        }


class DuplicateDetector:
    """Detects and prevents duplicate search queries."""
    
    def __init__(self, similarity_threshold: float = 0.8):
        self.similarity_threshold = similarity_threshold
        self.query_registry = []
    
    def is_duplicate(self, new_query: str, existing_queries: List[Tuple[str, str]]) -> Tuple[bool, Optional[str]]:
        """
        Check if a new query is similar to existing queries.
        Returns (is_duplicate, matched_query)
        """
        new_words = set(new_query.lower().split())
        
        for existing_query, hat_name in existing_queries:
            existing_words = set(existing_query.lower().split())
            
            # Calculate Jaccard similarity
            intersection = len(new_words & existing_words)
            union = len(new_words | existing_words)
            
            if union > 0:
                similarity = intersection / union
                if similarity >= self.similarity_threshold:
                    return True, existing_query
        
        return False, None
    
    def add_query(self, query: str, hat_name: str):
        """Add a query to the registry."""
        self.query_registry.append((query, hat_name))
    
    def get_registered_queries(self) -> List[Tuple[str, str]]:
        """Get all registered queries."""
        return self.query_registry.copy()
    
    def clear_registry(self):
        """Clear the query registry."""
        self.query_registry.clear()


class SearchExecutionResult:
    """Results from search execution."""
    
    def __init__(self, hat_name: str, search_query: str, results: List[SearchResult], 
                 cached: bool = False, error: Optional[str] = None):
        self.hat_name = hat_name
        self.search_query = search_query
        self.results = results
        self.cached = cached
        self.error = error
        self.execution_time = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "hat_name": self.hat_name,
            "search_query": self.search_query,
            "results_count": len(self.results),
            "cached": self.cached,
            "error": self.error,
            "execution_time": self.execution_time.isoformat()
        }


class SearchOrchestrator:
    """Main orchestrator for managing search operations across thinking hats."""
    
    def __init__(self, search_api: SearchAPI, max_searches: int = 6):
        self.search_api = search_api
        self.max_searches = max_searches
        self.query_analyzer = QueryAnalyzer()
        self.cache = SearchCache()
        self.duplicate_detector = DuplicateDetector()
        
        # Statistics
        self.total_searches = 0
        self.cached_searches = 0
        self.skipped_duplicate_searches = 0
    
    async def orchestrate_searches(self, user_query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Orchestrate search operations for a user query.
        
        Args:
            user_query: The original user query
            context: Additional context for search optimization
            
        Returns:
            Dictionary containing search results and metadata
        """
        # Step 1: Analyze the query
        analysis = self.query_analyzer.analyze_query(user_query)
        
        # Step 2: Optimize and validate search budget
        search_budget = self._validate_search_budget(analysis["search_budget"])
        
        # Step 3: Execute searches
        search_results = await self._execute_searches(user_query, search_budget, analysis["optimization"])
        
        # Step 4: Process and organize results
        organized_results = self._organize_results(search_results)
        
        # Step 5: Generate summary
        search_summary = self._generate_search_summary(search_results, analysis)
        
        return {
            "user_query": user_query,
            "analysis": analysis,
            "search_budget_used": len(search_budget),
            "results": organized_results,
            "summary": search_summary,
            "statistics": self._get_execution_statistics(),
            "cache_stats": self.cache.get_stats()
        }
    
    def _validate_search_budget(self, budget: List[str]) -> List[str]:
        """Validate and limit search budget."""
        return budget[:self.max_searches]
    
    async def _execute_searches(self, user_query: str, search_budget: List[str], 
                              optimization: Dict[str, str]) -> List[SearchExecutionResult]:
        """Execute searches for the allocated budget."""
        results = []
        registered_queries = self.duplicate_detector.get_registered_queries()
        
        for hat_name in search_budget:
            # Get or generate search query
            if hat_name in optimization:
                search_query = f"{user_query} {optimization[hat_name]}"
            else:
                search_query = user_query
            
            # Check for duplicates
            is_duplicate, matched_query = self.duplicate_detector.is_duplicate(search_query, registered_queries)
            
            if is_duplicate:
                # Use cached results or redirect to existing search
                cached_results = self.cache.get(search_query, hat_name)
                if cached_results:
                    result = SearchExecutionResult(hat_name, search_query, cached_results, cached=True)
                    self.cached_searches += 1
                else:
                    # Find the hat that has the most similar search
                    similar_result = self._find_similar_result(matched_query, registered_queries)
                    if similar_result:
                        result = SearchExecutionResult(hat_name, search_query, similar_result.results, cached=True)
                        self.cached_searches += 1
                    else:
                        result = SearchExecutionResult(hat_name, search_query, [], error="No cached results available")
                
                self.skipped_duplicate_searches += 1
            else:
                # Perform actual search
                try:
                    search_results = await self.search_api.search(search_query, max_results=5)
                    result = SearchExecutionResult(hat_name, search_query, search_results, cached=False)
                    self.cache.set(search_query, hat_name, search_results)
                    self.duplicate_detector.add_query(search_query, hat_name)
                    registered_queries.append((search_query, hat_name))
                    self.total_searches += 1
                except Exception as e:
                    result = SearchExecutionResult(hat_name, search_query, [], error=str(e))
            
            results.append(result)
        
        return results
    
    def _find_similar_result(self, matched_query: str, registered_queries: List[Tuple[str, str]]) -> Optional[SearchExecutionResult]:
        """Find a search result that matches the given query."""
        for query, hat_name in registered_queries:
            if query == matched_query:
                # This is a simplified version - in a full implementation,
                # we'd need to store actual results in the duplicate detector
                cached_results = self.cache.get(query, hat_name)
                if cached_results:
                    return SearchExecutionResult(hat_name, query, cached_results, cached=True)
        return None
    
    def _organize_results(self, search_results: List[SearchExecutionResult]) -> Dict[str, Any]:
        """Organize search results by hat and type."""
        organized = {
            "by_hat": {},
            "summary": {
                "total_searches": len(search_results),
                "successful_searches": len([r for r in search_results if not r.error]),
                "failed_searches": len([r for r in search_results if r.error]),
                "cached_searches": len([r for r in search_results if r.cached])
            }
        }
        
        for result in search_results:
            organized["by_hat"][result.hat_name] = {
                "search_query": result.search_query,
                "results": [r.to_dict() for r in result.results],
                "cached": result.cached,
                "error": result.error,
                "execution_time": result.execution_time.isoformat()
            }
        
        return organized
    
    def _generate_search_summary(self, search_results: List[SearchExecutionResult], 
                               analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of the search execution."""
        return {
            "query_complexity": analysis["complexity"].value,
            "topics_identified": analysis["topics"],
            "search_budget_utilization": f"{len(search_results)}/{self.max_searches}",
            "optimization_applied": len([r for r in search_results if not r.cached]),
            "cache_hit_rate": f"{(self.cached_searches / max(self.total_searches, 1)) * 100:.1f}%",
            "duplicate_prevention": f"{self.skipped_duplicate_searches} queries prevented",
            "execution_timestamp": datetime.now().isoformat()
        }
    
    def _get_execution_statistics(self) -> Dict[str, Any]:
        """Get execution statistics."""
        return {
            "total_searches_performed": self.total_searches,
            "cached_searches_used": self.cached_searches,
            "duplicate_searches_skipped": self.skipped_duplicate_searches,
            "cache_hit_rate": f"{(self.cached_searches / max(self.total_searches + self.cached_searches, 1)) * 100:.1f}%",
            "average_searches_per_query": f"{(self.total_searches / max(self.cached_searches + self.total_searches, 1)):.2f}"
        }
    
    def reset_statistics(self):
        """Reset execution statistics."""
        self.total_searches = 0
        self.cached_searches = 0
        self.skipped_duplicate_searches = 0
    
    def clear_cache(self):
        """Clear all caches and registries."""
        self.cache.clear()
        self.duplicate_detector.clear_registry()
        self.reset_statistics()
