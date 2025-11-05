"""
Query Analyzer module for analyzing user queries and determining search strategy.
"""

from typing import List, Dict, Any, Optional
import re
from enum import Enum


class QueryComplexity(Enum):
    """Enum for query complexity levels."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


class SearchPriority(Enum):
    """Enum for search priorities."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class HatSearchDecision:
    """Represents a search decision for a thinking hat."""
    
    def __init__(self, hat_name: str, should_search: bool, priority: SearchPriority, keywords: List[str]):
        self.hat_name = hat_name
        self.should_search = should_search
        self.priority = priority
        self.keywords = keywords
    
    def __repr__(self):
        return f"HatSearchDecision({self.hat_name}, search={self.should_search}, priority={self.priority})"


class QueryAnalyzer:
    """Analyzes user queries to determine search strategy and priorities."""
    
    def __init__(self):
        # Keywords that trigger different search types
        self.emotional_keywords = [
            "feeling", "emotion", "reaction", "opinion", "sentiment", "mood",
            "happy", "sad", "angry", "excited", "worried", "concerned",
            "public reaction", "people think", "what do people"
        ]
        
        self.risk_keywords = [
            "risk", "danger", "problem", "failure", "criticism", "negative",
            "concern", "issue", "challenge", "limitation", "disadvantage",
            "side effect", "complication", "hazard", "threat"
        ]
        
        self.opportunity_keywords = [
            "opportunity", "benefit", "advantage", "success", "positive",
            "profit", "gain", "improvement", "enhancement", "potential",
            "growth", "development", "innovation", "breakthrough"
        ]
        
        self.creative_keywords = [
            "creative", "innovative", "alternative", "different", "new",
            "solution", "idea", "approach", "method", "technique",
            "unique", "original", "breakthrough", "invention"
        ]
        
        # Topic categories
        self.business_keywords = [
            "business", "investment", "stock", "market", "economy", "finance",
            "profit", "revenue", "growth", "strategy", "corporate"
        ]
        
        self.health_keywords = [
            "health", "medical", "treatment", "diagnosis", "symptom",
            "medicine", "doctor", "hospital", "therapy", "wellness"
        ]
        
        self.technology_keywords = [
            "technology", "software", "app", "AI", "machine learning",
            "digital", "online", "computer", "tech", "innovation"
        ]
    
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """Analyze a query and return comprehensive analysis."""
        query_lower = query.lower()
        
        # Basic analysis
        complexity = self._determine_complexity(query_lower)
        topics = self._identify_topics(query_lower)
        
        # Hat-specific decisions
        hat_decisions = self._analyze_hat_search_needs(query_lower, topics)
        
        # Search budget allocation
        search_budget = self._allocate_search_budget(complexity, hat_decisions)
        
        # Duplicate prevention strategy
        search_optimization = self._optimize_search_queries(hat_decisions)
        
        return {
            "query": query,
            "complexity": complexity,
            "topics": topics,
            "hat_decisions": hat_decisions,
            "search_budget": search_budget,
            "optimization": search_optimization,
            "query_type": self._classify_query_type(query_lower)
        }
    
    def _determine_complexity(self, query: str) -> QueryComplexity:
        """Determine query complexity based on length and content."""
        word_count = len(query.split())
        
        # Check for complex indicators
        complex_indicators = [
            "analyze", "compare", "evaluate", "assess", "strategy",
            "multiple", "various", "different", "pros and cons",
            "what are", "how should", "should I", "what if"
        ]
        
        if word_count > 10 or any(indicator in query for indicator in complex_indicators):
            return QueryComplexity.COMPLEX
        elif word_count > 5:
            return QueryComplexity.MODERATE
        else:
            return QueryComplexity.SIMPLE
    
    def _identify_topics(self, query: str) -> List[str]:
        """Identify topic categories in the query."""
        topics = []
        
        if any(keyword in query for keyword in self.business_keywords):
            topics.append("business")
        
        if any(keyword in query for keyword in self.health_keywords):
            topics.append("health")
        
        if any(keyword in query for keyword in self.technology_keywords):
            topics.append("technology")
        
        if any(keyword in query for keyword in self.emotional_keywords):
            topics.append("emotional")
        
        if not topics:
            topics.append("general")
        
        return topics
    
    def _analyze_hat_search_needs(self, query: str, topics: List[str]) -> List[HatSearchDecision]:
        """Analyze search needs for each thinking hat."""
        decisions = []
        
        # White Hat - Always search for facts
        white_keywords = ["facts", "data", "statistics", "research", "evidence", "information"]
        should_search_white = True  # Always search for facts
        
        decisions.append(HatSearchDecision(
            "white_hat",
            should_search_white,
            SearchPriority.CRITICAL,
            white_keywords
        ))
        
        # Red Hat - Emotional topics
        red_has_keywords = any(keyword in query for keyword in self.emotional_keywords)
        red_should_search = red_has_keywords or "opinion" in query or "feeling" in query
        
        decisions.append(HatSearchDecision(
            "red_hat",
            red_should_search,
            SearchPriority.HIGH if red_should_search else SearchPriority.LOW,
            self.emotional_keywords
        ))
        
        # Black Hat vs Yellow Hat - Topic-based decision
        black_has_keywords = any(keyword in query for keyword in self.risk_keywords)
        yellow_has_keywords = any(keyword in query for keyword in self.opportunity_keywords)
        
        if "business" in topics and not yellow_has_keywords:
            # Business topics favor Yellow Hat (opportunities)
            black_should_search = False
            yellow_should_search = True
        elif "health" in topics and not black_has_keywords:
            # Health topics favor Black Hat (risks)
            black_should_search = True
            yellow_should_search = False
        else:
            # Default behavior based on keywords
            black_should_search = black_has_keywords
            yellow_should_search = yellow_has_keywords or "business" in topics
        
        decisions.append(HatSearchDecision(
            "black_hat",
            black_should_search,
            SearchPriority.HIGH if black_should_search else SearchPriority.MEDIUM,
            self.risk_keywords
        ))
        
        decisions.append(HatSearchDecision(
            "yellow_hat",
            yellow_should_search,
            SearchPriority.HIGH if yellow_should_search else SearchPriority.MEDIUM,
            self.opportunity_keywords
        ))
        
        # Green Hat - Complex problems
        green_has_keywords = any(keyword in query for keyword in self.creative_keywords)
        green_should_search = green_has_keywords or len(query.split()) > 8
        
        decisions.append(HatSearchDecision(
            "green_hat",
            green_should_search,
            SearchPriority.MEDIUM if green_should_search else SearchPriority.LOW,
            self.creative_keywords
        ))
        
        # Blue Hat - Rarely searches
        decisions.append(HatSearchDecision(
            "blue_hat",
            False,  # Blue Hat focuses on synthesis
            SearchPriority.LOW,
            []
        ))
        
        return decisions
    
    def _allocate_search_budget(self, complexity: QueryComplexity, hat_decisions: List[HatSearchDecision]) -> List[str]:
        """Allocate search budget (4 searches max) based on decisions."""
        search_budget = []
        
        # Always include White Hat
        search_budget.append("white_hat")
        
        # Add Red Hat if high priority
        red_decision = next((d for d in hat_decisions if d.hat_name == "red_hat"), None)
        if red_decision and red_decision.should_search and len(search_budget) < 4:
            search_budget.append("red_hat")
        
        # Add Black or Yellow Hat based on topic
        black_decision = next((d for d in hat_decisions if d.hat_name == "black_hat"), None)
        yellow_decision = next((d for d in hat_decisions if d.hat_name == "yellow_hat"), None)
        
        if len(search_budget) < 4:
            if black_decision and black_decision.should_search:
                search_budget.append("black_hat")
            elif yellow_decision and yellow_decision.should_search:
                search_budget.append("yellow_hat")
        
        # Add Green Hat if budget allows
        green_decision = next((d for d in hat_decisions if d.hat_name == "green_hat"), None)
        if len(search_budget) < 4 and green_decision and green_decision.should_search:
            search_budget.append("green_hat")
        
        return search_budget[:4]  # Ensure max 4 searches
    
    def _optimize_search_queries(self, hat_decisions: List[HatSearchDecision]) -> Dict[str, str]:
        """Generate optimized search queries for each hat."""
        queries = {}
        
        for decision in hat_decisions:
            if decision.should_search:
                query = self._generate_hat_specific_query(decision)
                queries[decision.hat_name] = query
        
        return queries
    
    def _generate_hat_specific_query(self, decision: HatSearchDecision) -> str:
        """Generate a hat-specific search query."""
        base_queries = {
            "white_hat": "current facts statistics data research evidence",
            "red_hat": "public opinion sentiment reaction emotional response",
            "black_hat": "risks problems failures challenges limitations",
            "yellow_hat": "benefits advantages opportunities success positive outcomes",
            "green_hat": "innovation creative solutions alternative approaches",
            "blue_hat": "methodology best practices overview summary"
        }
        
        return base_queries.get(decision.hat_name, "information")
    
    def _classify_query_type(self, query: str) -> str:
        """Classify the type of query."""
        if any(word in query for word in ["should", "must", "recommend", "suggest"]):
            return "recommendation"
        elif any(word in query for word in ["what", "who", "where", "when", "how"]):
            return "informational"
        elif any(word in query for word in ["compare", "vs", "versus", "difference"]):
            return "comparative"
        elif any(word in query for word in ["analyze", "evaluate", "assess"]):
            return "analytical"
        else:
            return "general"
