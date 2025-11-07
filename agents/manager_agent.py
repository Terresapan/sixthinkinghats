"""
Manager Subagent - Query Analyzer

This agent analyzes user queries before processing begins and determines:
1. Query complexity (simple/moderate/complex)
2. Topic domain (business/health/technology/emotional/social)
3. Which hats should search (within 4-search budget)
4. Search priority assignments
5. Hat-specific search queries

This is the first phase of the phased sequential architecture.
"""

from enum import Enum
from typing import Dict, List, Optional, Literal
from dataclasses import dataclass
from langchain_core.language_models import BaseLanguageModel
import re


class Complexity(Enum):
    """Query complexity levels"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


class Topic(Enum):
    """Topic domains for classification"""
    BUSINESS = "business"
    HEALTH = "health"
    TECHNOLOGY = "technology"
    EMOTIONAL = "emotional"
    SOCIAL = "social"
    GENERAL = "general"
    SAFETY = "safety"


class HatType(Enum):
    """Thinking hat types"""
    WHITE = "white"
    RED = "red"
    YELLOW = "yellow"
    BLACK = "black"
    GREEN = "green"
    BLUE = "blue"


class SearchPriority(Enum):
    """Search priority levels"""
    CRITICAL = "critical"  # Must search
    HIGH = "high"          # Should search
    MEDIUM = "medium"      # May search if budget allows
    LOW = "low"            # Rarely searches
    NEVER = "never"        # Never searches


@dataclass
class QueryAnalysis:
    """Result of query analysis"""
    query: str
    complexity: Complexity
    topic: Topic
    search_recommendations: Dict[HatType, SearchPriority]
    search_queries: Dict[HatType, str]
    budget_allocation: List[HatType]
    rationale: str


class ManagerAgent:
    """
    Manager Subagent that analyzes queries and determines search strategy.

    This is the first agent in the phased workflow, responsible for:
    - Analyzing query characteristics
    - Determining search priorities for each hat
    - Allocating the 4-search budget intelligently
    - Generating hat-specific search queries
    """

    def __init__(self, llm: BaseLanguageModel):
        self.llm = llm

    def analyze_query(self, query: str) -> QueryAnalysis:
        """
        Analyze a user query to determine complexity, topic, and search strategy.

        Args:
            query: The user's question or query

        Returns:
            QueryAnalysis with all necessary information for search orchestration
        """
        # Analyze query characteristics
        complexity = self._determine_complexity(query)
        topic = self._classify_topic(query)

        # Determine search priorities
        search_recommendations = self._determine_search_priorities(query, complexity, topic)

        # Allocate search budget (max 4 searches)
        budget_allocation = self._allocate_search_budget(search_recommendations)

        # Generate hat-specific search queries
        search_queries = self._generate_search_queries(query, topic, budget_allocation)

        # Build rationale
        rationale = self._build_rationale(complexity, topic, budget_allocation, search_recommendations)

        return QueryAnalysis(
            query=query,
            complexity=complexity,
            topic=topic,
            search_recommendations=search_recommendations,
            search_queries=search_queries,
            budget_allocation=budget_allocation,
            rationale=rationale
        )

    def _determine_complexity(self, query: str) -> Complexity:
        """
        Determine query complexity based on:
        - Number of concepts/keywords
        - Multi-part questions
        - Technical terms
        - Specialized knowledge requirements
        """
        # Count key indicators
        word_count = len(query.split())
        has_technical_terms = bool(re.search(r'\b(algorithm|quantum|crypto|blockchain|AI|ML|neural|bioinformatics|pharmacology)\b', query.lower()))
        has_multiple_parts = query.count('?') > 1 or query.count(' and ') > 0 or query.count(',') > 2
        has_comparative_terms = bool(re.search(r'\b(compare|versus|difference|trade-off|pros/cons|advantage|disadvantage)\b', query.lower()))

        # Scoring system
        complexity_score = 0
        if word_count > 15:
            complexity_score += 1
        if has_technical_terms:
            complexity_score += 2
        if has_multiple_parts:
            complexity_score += 1
        if has_comparative_terms:
            complexity_score += 1

        # Determine complexity
        if complexity_score <= 1:
            return Complexity.SIMPLE
        elif complexity_score <= 3:
            return Complexity.MODERATE
        else:
            return Complexity.COMPLEX

    def _classify_topic(self, query: str) -> Topic:
        """Classify query into topic domain using keyword matching"""

        topic_keywords = {
            Topic.BUSINESS: [
                'business', 'company', 'startup', 'entrepreneur', 'revenue', 'profit',
                'market', 'competition', 'strategy', 'investment', 'funding', 'IPO',
                'merger', 'acquisition', 'venture', 'ROI', 'sales', 'customer'
            ],
            Topic.HEALTH: [
                'health', 'medical', 'disease', 'treatment', 'therapy', 'doctor',
                'hospital', 'medicine', 'drug', 'symptom', 'diagnosis', 'healthcare',
                'wellness', 'nutrition', 'exercise', 'fitness', 'mental health'
            ],
            Topic.TECHNOLOGY: [
                'technology', 'software', 'programming', 'AI', 'machine learning',
                'data', 'algorithm', 'tech', 'digital', 'computer', 'internet',
                'cloud', 'cybersecurity', 'blockchain', 'quantum', 'robotics'
            ],
            Topic.EMOTIONAL: [
                'feel', 'emotion', 'feeling', 'sad', 'happy', 'angry', 'anxious',
                'relationship', 'love', 'family', 'friendship', 'personal',
                'mood', 'psychology', 'mental', 'self-esteem', 'confidence'
            ],
            Topic.SOCIAL: [
                'society', 'social', 'community', 'culture', 'political',
                'government', 'policy', 'law', 'ethics', 'justice', 'equality',
                'diversity', 'public', 'social media', 'news', 'controversy'
            ],
            Topic.SAFETY: [
                'safety', 'risk', 'danger', 'hazard', 'security', 'threat',
                'vulnerability', 'accident', 'injury', 'harm', 'warning',
                'liability', 'insurance', 'precaution'
            ]
        }

        query_lower = query.lower()

        # Score each topic
        topic_scores = {}
        for topic, keywords in topic_keywords.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            if score > 0:
                topic_scores[topic] = score

        # Return topic with highest score
        if topic_scores:
            return max(topic_scores, key=topic_scores.get) # type: ignore
        else:
            return Topic.GENERAL

    def _determine_search_priorities(
        self,
        query: str,
        complexity: Complexity,
        topic: Topic
    ) -> Dict[HatType, SearchPriority]:
        """
        Determine which hats should search based on query characteristics.
        Returns priorities for all 6 hats.
        """

        priorities = {}

        # White Hat: Always searches for facts and data
        priorities[HatType.WHITE] = SearchPriority.CRITICAL

        # Red Hat: Searches on emotional/social topics
        if topic in [Topic.EMOTIONAL, Topic.SOCIAL] or any(
            word in query.lower() for word in ['feel', 'emotion', 'reaction', 'response', 'sentiment']
        ):
            priorities[HatType.RED] = SearchPriority.HIGH
        else:
            priorities[HatType.RED] = SearchPriority.MEDIUM

        # Yellow Hat: Searches on business/opportunity topics
        if topic == Topic.BUSINESS or complexity == Complexity.COMPLEX or any(
            word in query.lower() for word in ['benefit', 'advantage', 'opportunity', 'success', 'positive']
        ):
            priorities[HatType.YELLOW] = SearchPriority.HIGH
        else:
            priorities[HatType.YELLOW] = SearchPriority.MEDIUM

        # Black Hat: Searches on risk/health/safety topics
        if topic in [Topic.HEALTH, Topic.SAFETY] or any(
            word in query.lower() for word in ['risk', 'problem', 'failure', 'danger', 'criticism']
        ):
            priorities[HatType.BLACK] = SearchPriority.HIGH
        else:
            priorities[HatType.BLACK] = SearchPriority.MEDIUM

        # Green Hat: Searches for complex, innovative solutions
        if complexity == Complexity.COMPLEX or any(
            word in query.lower() for word in ['creative', 'innovation', 'alternative', 'solution', 'breakthrough']
        ):
            priorities[HatType.GREEN] = SearchPriority.MEDIUM
        else:
            priorities[HatType.GREEN] = SearchPriority.LOW

        # Blue Hat: Rarely searches (synthesis focus)
        priorities[HatType.BLUE] = SearchPriority.LOW

        return priorities

    def _allocate_search_budget(
        self,
        search_recommendations: Dict[HatType, SearchPriority]
    ) -> List[HatType]:
        """
        Allocate the 4-search budget based on priorities.
        Returns list of hats that will search, in priority order.
        """

        # Define allocation strategy based on priority
        def should_allocate(priority: SearchPriority) -> bool:
            if priority == SearchPriority.CRITICAL:
                return True
            elif priority == SearchPriority.HIGH:
                return True
            elif priority == SearchPriority.MEDIUM:
                return True
            else:
                return False

        # Get hats that should search, sorted by priority
        candidates = [
            (hat, priority) for hat, priority in search_recommendations.items()
            if should_allocate(priority)
        ]

        # Sort by priority (CRITICAL > HIGH > MEDIUM > LOW > NEVER)
        priority_order = {
            SearchPriority.CRITICAL: 0,
            SearchPriority.HIGH: 1,
            SearchPriority.MEDIUM: 2,
            SearchPriority.LOW: 3,
            SearchPriority.NEVER: 4
        }

        candidates.sort(key=lambda x: priority_order[x[1]])

        # Allocate up to 4 searches
        allocated = [hat for hat, _ in candidates[:4]]

        # Ensure White Hat is always included
        if HatType.WHITE not in allocated and HatType.WHITE in search_recommendations:
            # If White Hat not in top 4, replace the lowest priority
            allocated.pop()
            allocated.insert(0, HatType.WHITE)

        return allocated

    def _generate_search_queries(
        self,
        query: str,
        topic: Topic,
        budget_allocation: List[HatType]
    ) -> Dict[HatType, str]:
        """
        Generate optimized search queries for each hat based on their role.
        """

        search_queries = {}

        for hat_type in budget_allocation:
            if hat_type == HatType.WHITE:
                # White Hat: Facts and data
                search_queries[hat_type] = f"{query} facts statistics data research"

            elif hat_type == HatType.RED:
                # Red Hat: Emotions and reactions
                emotion_terms = {
                    Topic.EMOTIONAL: "reactions opinions feelings response",
                    Topic.SOCIAL: "public opinion social response reactions",
                    Topic.HEALTH: "patient experiences emotional impact",
                    Topic.BUSINESS: "customer reviews business sentiment",
                    Topic.TECHNOLOGY: "user experience community feedback"
                }
                search_terms = emotion_terms.get(topic, "opinion reaction sentiment response")
                search_queries[hat_type] = f"{query} {search_terms}"

            elif hat_type == HatType.YELLOW:
                # Yellow Hat: Benefits and opportunities
                yellow_terms = {
                    Topic.BUSINESS: "business benefits advantages opportunities success case studies",
                    Topic.HEALTH: "health benefits positive outcomes improvements",
                    Topic.TECHNOLOGY: "innovation benefits technological advantages improvements",
                    Topic.GENERAL: "benefits advantages opportunities positive aspects"
                }
                search_terms = yellow_terms.get(topic, "benefits advantages opportunities")
                search_queries[hat_type] = f"{query} {search_terms}"

            elif hat_type == HatType.BLACK:
                # Black Hat: Risks and problems
                black_terms = {
                    Topic.HEALTH: "health risks side effects dangers problems",
                    Topic.SAFETY: "safety risks hazards dangers warnings",
                    Topic.BUSINESS: "business risks challenges problems failures",
                    Topic.TECHNOLOGY: "technology risks cybersecurity threats problems",
                    Topic.GENERAL: "risks problems challenges limitations"
                }
                search_terms = black_terms.get(topic, "risks problems challenges")
                search_queries[hat_type] = f"{query} {search_terms}"

            elif hat_type == HatType.GREEN:
                # Green Hat: Creative alternatives
                search_queries[hat_type] = f"{query} creative solutions alternatives innovation new approaches"

            elif hat_type == HatType.BLUE:
                # Blue Hat: Rarely searches, focuses on synthesis
                search_queries[hat_type] = f"{query} best practices framework methodology"

        return search_queries

    def _build_rationale(
        self,
        complexity: Complexity,
        topic: Topic,
        budget_allocation: List[HatType],
        search_recommendations: Dict[HatType, SearchPriority]
    ) -> str:
        """Build a human-readable rationale for the search allocation decision"""

        rationale = f"Query classified as {complexity.value} complexity, {topic.value} topic. "

        rationale += f"Search budget allocated to {len(budget_allocation)} hats: "

        hat_names = {
            HatType.WHITE: "White (Facts)",
            HatType.RED: "Red (Emotions)",
            HatType.YELLOW: "Yellow (Benefits)",
            HatType.BLACK: "Black (Risks)",
            HatType.GREEN: "Green (Creativity)",
            HatType.BLUE: "Blue (Synthesis)"
        }

        for hat in budget_allocation:
            priority = search_recommendations[hat]
            rationale += f"{hat_names[hat]} ({priority.value}), "

        rationale = rationale.rstrip(", ") + "."

        return rationale
