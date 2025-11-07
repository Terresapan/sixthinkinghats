"""
Phased Search Orchestrator - Enhanced Search Manager for Phased Architecture

This module provides search orchestration for the phased sequential workflow:
1. Initial search wave (for White, Red, Yellow, Black hats - parallel execution)
2. Optional search for Green Hat (if budget allows)
3. Optional search for Blue Hat (rarely, for synthesis)

Key features:
- Supports multiple search waves
- Builds context for sequential flow
- Integrates with Manager Agent's search allocation decisions
- Maintains caching and deduplication
- Distributes results to appropriate hats
"""

import time
import hashlib
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, TypedDict, Any, Tuple
from dataclasses import dataclass, field
from services.search_apis import TavilySearchAPI


class SearchCache:
    """Cache for storing search results to prevent duplicate queries."""

    def __init__(self, ttl_seconds: int = 3600):  # 1 hour default TTL
        self.cache = {}
        self.ttl_seconds = ttl_seconds

    def _generate_cache_key(self, query: str, hat_name: str) -> str:
        """Generate a cache key for a query and hat combination."""
        combined = f"{hat_name}:{query.lower().strip()}"
        return hashlib.md5(combined.encode()).hexdigest()

    def get(self, query: str, hat_name: str) -> Optional[List[Dict[str, Any]]]:
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

    def set(self, query: str, hat_name: str, results: List[Dict[str, Any]]):
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


class SearchPhase(Enum):
    """Search execution phases"""
    INITIAL = "initial"  # For parallel hats (White, Red, Yellow, Black)
    GREEN = "green"      # For Green Hat (sequential)
    BLUE = "blue"        # For Blue Hat (synthesis)


@dataclass
class HatSearchContext:
    """Context for a specific hat's search"""
    hat_type: str
    search_query: str
    search_results: List[Dict[str, Any]]
    cache_hit: bool = False
    execution_time: float = 0.0
    metadata: Dict = field(default_factory=dict)


@dataclass
class PhasedSearchResult:
    """Result of phased search orchestration"""
    initial_searches: Dict[str, HatSearchContext]  # For White, Red, Yellow, Black
    green_search: Optional[HatSearchContext] = None
    blue_search: Optional[HatSearchContext] = None
    total_searches_executed: int = 0
    total_cache_hits: int = 0
    total_execution_time: float = 0.0
    budget_status: Dict[str, int] = field(default_factory=dict)


class PhasedSearchOrchestrator:
    """
    Phased Search Orchestrator for sequential workflow architecture.

    Manages search execution across multiple phases:
    - Phase 0: Initial searches for parallel hats
    - Phase 2: Optional search for Green Hat
    - Phase 3: Optional search for Blue Hat

    Features:
    - Intelligent budget allocation
    - Caching and deduplication
    - Context building for hat processing
    - Performance tracking
    """

    def __init__(self, search_api: TavilySearchAPI, max_searches_per_query: int = 4):
        self.search_api = search_api
        self.max_searches = max_searches_per_query
        self.cache = SearchCache(ttl_seconds=3600)  # 1-hour TTL
        self.duplicate_detector = DuplicateDetector(similarity_threshold=0.8)
        self.search_stats = {
            'total_queries': 0,
            'total_searches': 0,
            'cache_hits': 0,
            'duplicates_prevented': 0
        }

    def execute_initial_search_wave(
        self,
        hat_search_queries: Dict[str, str]
    ) -> Dict[str, HatSearchContext]:
        """
        Execute initial search wave for parallel hats (White, Red, Yellow, Black).

        Args:
            hat_search_queries: Dict of hat_type -> search_query

        Returns:
            Dict of hat_type -> HatSearchContext with search results
        """
        results = {}
        search_count = 0
        registered_queries = self.duplicate_detector.get_registered_queries()

        for hat_type, search_query in hat_search_queries.items():
            if search_count >= self.max_searches:
                # Budget exhausted
                break

            # Check for duplicates
            is_duplicate, matched_query = self.duplicate_detector.is_duplicate(search_query, registered_queries)
            if is_duplicate:
                self.search_stats['duplicates_prevented'] += 1
                # Use cached results
                cached_results = self.cache.get(search_query, hat_type)
                if cached_results:
                    results[hat_type] = HatSearchContext(
                        hat_type=hat_type,
                        search_query=search_query,
                        search_results=cached_results,
                        cache_hit=True,
                        execution_time=0.0,
                        metadata={
                            'query_length': len(search_query),
                            'result_count': len(cached_results) if cached_results else 0,
                            'duplicate_of': matched_query
                        }
                    )
                search_count += 1
                continue

            start_time = time.time()

            # Check cache
            cached_results = self.cache.get(search_query, hat_type)
            cache_hit = cached_results is not None

            if cache_hit:
                search_results = cached_results
                self.search_stats['cache_hits'] += 1
            else:
                # Execute search (synchronously - search_api handles sync)
                search_results = self.search_api.search(search_query, max_results=5)
                # Convert SearchResult objects to dicts
                search_results_dicts = [result.to_dict() if hasattr(result, 'to_dict') else result.__dict__ for result in search_results]
                # Cache results
                self.cache.set(search_query, hat_type, search_results_dicts)
                self.duplicate_detector.add_query(search_query, hat_type)
                registered_queries.append((search_query, hat_type))

            execution_time = time.time() - start_time

            # Use cached results if available, otherwise use new results
            final_results = search_results_dicts if not cache_hit else (cached_results or [])

            results[hat_type] = HatSearchContext(
                hat_type=hat_type,
                search_query=search_query,
                search_results=final_results,
                cache_hit=cache_hit,
                execution_time=execution_time,
                metadata={
                    'query_length': len(search_query),
                    'result_count': len(final_results)
                }
            )

            search_count += 1

        # Update statistics
        self.search_stats['total_searches'] += search_count
        self.search_stats['total_queries'] += 1

        return results

    def execute_sequential_search(
        self,
        hat_type: str,
        search_query: str,
        current_budget_used: int,
        context: Optional[Dict] = None
    ) -> Optional[HatSearchContext]:
        """
        Execute search for sequential hats (Green or Blue).

        Args:
            hat_type: "green" or "blue"
            search_query: The search query
            current_budget_used: Number of searches already executed
            context: Optional context from previous phases

        Returns:
            HatSearchContext if search executed, None otherwise
        """
        # Check if budget allows
        if current_budget_used >= self.max_searches:
            return None

        # Green Hat: May search if budget allows and complexity warrants it
        # Blue Hat: Rarely searches (synthesis focus)
        if hat_type == "blue":
            return None

        # Check for duplicates
        registered_queries = self.duplicate_detector.get_registered_queries()
        is_duplicate, matched_query = self.duplicate_detector.is_duplicate(search_query, registered_queries)
        if is_duplicate:
            self.search_stats['duplicates_prevented'] += 1
            return None

        start_time = time.time()

        # Check cache
        cached_results = self.cache.get(search_query, hat_type)
        cache_hit = cached_results is not None

        if cache_hit:
            search_results = cached_results
            self.search_stats['cache_hits'] += 1
        else:
            # Execute search (synchronously)
            search_results = self.search_api.search(search_query, max_results=5)
            # Convert SearchResult objects to dicts
            search_results_dicts = [result.to_dict() if hasattr(result, 'to_dict') else result.__dict__ for result in search_results]
            # Cache results
            self.cache.set(search_query, hat_type, search_results_dicts)
            self.duplicate_detector.add_query(search_query, hat_type)

        execution_time = time.time() - start_time

        # Update statistics
        self.search_stats['total_searches'] += 1

        # Use cached results if available, otherwise use new results
        final_results = search_results_dicts if not cache_hit else (cached_results or [])

        return HatSearchContext(
            hat_type=hat_type,
            search_query=search_query,
            search_results=final_results,
            cache_hit=cache_hit,
            execution_time=execution_time,
            metadata={
                'query_length': len(search_query),
                'result_count': len(final_results),
                'phase': 'sequential'
            }
        )

    def aggregate_hat_contexts(
        self,
        hat_responses: Dict[str, str],
        search_contexts: Dict[str, HatSearchContext]
    ) -> Dict[str, Any]:
        """
        Aggregate contexts from parallel hats for Green Hat processing.

        Args:
            hat_responses: Dict of hat_type -> response text
            search_contexts: Dict of hat_type -> HatSearchContext

        Returns:
            Aggregated context for Green Hat
        """
        aggregated = {
            'parallel_responses': hat_responses,
            'search_insights': {},
            'key_themes': [],
            'conflicting_views': [],
            'synthesis_opportunities': []
        }

        # Extract key insights from each hat
        for hat_type, context in search_contexts.items():
            if context and context.search_results:
                # Extract top 3 insights from search results
                insights = []
                for result in context.search_results[:3]:
                    insights.append({
                        'title': result.get('title', ''),
                        'snippet': result.get('content', '')[:200] + '...',
                        'url': result.get('url', '')
                    })
                aggregated['search_insights'][hat_type] = insights

        # Identify themes and opportunities
        aggregated['key_themes'] = self._identify_key_themes(hat_responses)
        aggregated['synthesis_opportunities'] = self._identify_synthesis_opportunities(hat_responses)

        return aggregated

    def build_synthesis_context(
        self,
        white_response: str,
        red_response: str,
        yellow_response: str,
        black_response: str,
        green_response: str,
        search_contexts: Dict[str, HatSearchContext]
    ) -> Dict[str, Any]:
        """
        Build comprehensive context for Blue Hat synthesis.

        Args:
            All hat responses
            search_contexts: Search contexts from all hats

        Returns:
            Synthesis context for Blue Hat
        """
        synthesis_context = {
            'all_perspectives': {
                'white': white_response,
                'red': red_response,
                'yellow': yellow_response,
                'black': black_response,
                'green': green_response
            },
            'search_evidence': {},
            'synthesis_notes': '',
            'key_takeaways': [],
            'recommendations': []
        }

        # Aggregate search evidence
        for hat_type, context in search_contexts.items():
            if context and context.search_results:
                evidence = []
                for result in context.search_results[:2]:  # Top 2 results
                    evidence.append({
                        'title': result.get('title', ''),
                        'content': result.get('content', '')[:150] + '...',
                        'url': result.get('url', '')
                    })
                synthesis_context['search_evidence'][hat_type] = evidence

        # Generate synthesis notes
        synthesis_context['synthesis_notes'] = self._generate_synthesis_notes(
            white_response, red_response, yellow_response, black_response, green_response
        )

        return synthesis_context

    def get_search_statistics(self) -> Dict:
        """
        Get comprehensive search orchestration statistics.

        Returns:
            Dictionary with statistics
        """
        cache_hit_rate = 0.0
        if self.search_stats['total_searches'] > 0:
            cache_hit_rate = (self.search_stats['cache_hits'] / self.search_stats['total_searches']) * 100

        return {
            'total_queries': self.search_stats['total_queries'],
            'total_searches_executed': self.search_stats['total_searches'],
            'cache_hit_rate_percent': round(cache_hit_rate, 2),
            'duplicates_prevented': self.search_stats['duplicates_prevented'],
            'max_searches_per_query': self.max_searches,
            'cache_size': len(self.cache.cache),
            'duplicate_detector_size': len(self.duplicate_detector.query_registry)
        }

    def _identify_key_themes(self, hat_responses: Dict[str, str]) -> List[str]:
        """Identify key themes across all hat responses"""

        # Simple keyword extraction (can be enhanced with NLP)
        all_text = ' '.join(hat_responses.values()).lower()

        # Common important terms (simplified)
        theme_keywords = [
            'opportunity', 'risk', 'benefit', 'challenge', 'innovation',
            'solution', 'strategy', 'advantage', 'problem', 'creative'
        ]

        themes = []
        for keyword in theme_keywords:
            if keyword in all_text:
                themes.append(keyword)

        return themes[:5]  # Top 5 themes

    def _identify_synthesis_opportunities(self, hat_responses: Dict[str, str]) -> List[str]:
        """Identify opportunities for creative synthesis"""

        opportunities = []

        # Check for complementary perspectives
        if 'yellow' in hat_responses and 'black' in hat_responses:
            opportunities.append("Balance benefits (Yellow) with risks (Black)")

        if 'white' in hat_responses and 'green' in hat_responses:
            opportunities.append("Use facts (White) to inform creativity (Green)")

        if 'red' in hat_responses and 'yellow' in hat_responses:
            opportunities.append("Combine emotions (Red) with optimism (Yellow)")

        return opportunities

    def _generate_synthesis_notes(
        self,
        white: str,
        red: str,
        yellow: str,
        black: str,
        green: str
    ) -> str:
        """Generate synthesis notes for Blue Hat"""

        notes = []
        notes.append("Perspective Summary:")
        notes.append(f"- White Hat (Facts): {len(white)} characters")
        notes.append(f"- Red Hat (Emotions): {len(red)} characters")
        notes.append(f"- Yellow Hat (Benefits): {len(yellow)} characters")
        notes.append(f"- Black Hat (Risks): {len(black)} characters")
        notes.append(f"- Green Hat (Creativity): {len(green)} characters")
        notes.append("\nKey Insight: Sequential processing allowed each perspective to build on previous insights.")

        return "\n".join(notes)

    def reset_statistics(self):
        """Reset search statistics (useful for testing)"""
        self.search_stats = {
            'total_queries': 0,
            'total_searches': 0,
            'cache_hits': 0,
            'duplicates_prevented': 0
        }
