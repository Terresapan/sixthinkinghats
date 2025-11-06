"""
Phased Workflow Graph - LangGraph Implementation for Sequential Architecture

This module implements the phased sequential workflow:

Phase 0: Query Analysis & Search Orchestration
  → Query Analyzer (Manager Agent)
  → Search Orchestrator

Phase 1: Parallel Hat Execution
  → White Hat (Facts)
  → Red Hat (Emotions)
  → Yellow Hat (Benefits)
  → Black Hat (Risks)
  (All run in parallel)

Phase 2: Sequential Processing
  → Aggregator (collects parallel results)
  → Green Hat (Creativity - receives aggregated context)

Phase 3: Synthesis
  → Blue Hat (Summary - receives all previous results)

Uses LangGraph for state management and orchestration.
"""

from typing import TypedDict, List, Dict, Optional, Any, Annotated
from langgraph.graph import StateGraph, END
from operator import add
from langchain_core.language_models import BaseLanguageModel

# Import agents and services
from agents.manager_agent import ManagerAgent, QueryAnalysis
from services.phased_search_orchestrator import PhasedSearchOrchestrator, HatSearchContext
from agents.thinking_hat_agents import (
    WhiteHatAgent,
    RedHatAgent,
    YellowHatAgent,
    BlackHatAgent,
    GreenHatAgent,
    BlueHatAgent
)


class WorkflowState(TypedDict):
    """State managed by LangGraph throughout the workflow"""
    # Input (only set once at start)
    query: str

    # Phase 0: Analysis (only written by analysis nodes)
    query_analysis: Optional[QueryAnalysis]
    search_contexts: Optional[Dict[str, HatSearchContext]]

    # Phase 1: Parallel hat responses (each hat writes to its own field)
    white_response: Optional[str]
    red_response: Optional[str]
    yellow_response: Optional[str]
    black_response: Optional[str]

    # Phase 2: Sequential processing (only written by sequential nodes)
    green_context: Optional[Dict[str, Any]]
    green_response: Optional[str]

    # Phase 3: Final synthesis (only written by blue hat)
    blue_response: Optional[str]

    # Metadata (accumulated throughout - use Annotated with reducer)
    processing_stats: Annotated[Dict[str, Any], lambda x, y: {**x, **y}]
    errors: Annotated[List[str], add]
    phase_completed: Annotated[List[str], add]


class PhasedWorkflowGraph:
    """
    Phased Workflow Graph orchestrating the sequential Six Thinking Hats process.

    Architecture:
    1. Query Analyzer analyzes query and determines search strategy
    2. Search Orchestrator executes searches for parallel hats
    3. Four hats run in parallel (White, Red, Yellow, Black)
    4. Aggregator collects results and builds context
    5. Green Hat processes with aggregated context
    6. Blue Hat synthesizes all perspectives
    """

    def __init__(
        self,
        llm: BaseLanguageModel,
        search_api: Any,
        max_searches_per_query: int = 4
    ):
        self.llm = llm
        self.search_api = search_api
        self.max_searches = max_searches_per_query

        # Initialize agents
        self.manager_agent = ManagerAgent(llm)
        self.search_orchestrator = PhasedSearchOrchestrator(search_api, max_searches_per_query)
        self.white_hat = WhiteHatAgent(llm)
        self.red_hat = RedHatAgent(llm)
        self.yellow_hat = YellowHatAgent(llm)
        self.black_hat = BlackHatAgent(llm)
        self.green_hat = GreenHatAgent(llm)
        self.blue_hat = BlueHatAgent(llm)

        # Build workflow graph
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""

        workflow = StateGraph(WorkflowState)

        # Phase 0: Management
        workflow.add_node("query_analyzer", self._query_analyzer_node)
        workflow.add_node("search_orchestrator", self._search_orchestrator_node)

        # Phase 1: Parallel execution
        workflow.add_node("white_hat", self._white_hat_node)
        workflow.add_node("red_hat", self._red_hat_node)
        workflow.add_node("yellow_hat", self._yellow_hat_node)
        workflow.add_node("black_hat", self._black_hat_node)

        # Phase 2: Sequential processing
        workflow.add_node("aggregator", self._aggregator_node)
        workflow.add_node("green_hat", self._green_hat_node)

        # Phase 3: Synthesis
        workflow.add_node("blue_hat", self._blue_hat_node)

        # Define workflow edges

        # Start with analysis
        workflow.set_entry_point("query_analyzer")
        workflow.add_edge("query_analyzer", "search_orchestrator")

        # From search orchestrator to parallel hats
        workflow.add_edge("search_orchestrator", "white_hat")
        workflow.add_edge("search_orchestrator", "red_hat")
        workflow.add_edge("search_orchestrator", "yellow_hat")
        workflow.add_edge("search_orchestrator", "black_hat")

        # Collect parallel results
        workflow.add_edge("white_hat", "aggregator")
        workflow.add_edge("red_hat", "aggregator")
        workflow.add_edge("yellow_hat", "aggregator")
        workflow.add_edge("black_hat", "aggregator")

        # Sequential flow
        workflow.add_edge("aggregator", "green_hat")
        workflow.add_edge("green_hat", "blue_hat")
        workflow.add_edge("blue_hat", END)

        # Draw the graph
        try:
            workflow.compile().get_graph(xray=True).draw_mermaid_png(output_file_path="graph.png")
        except Exception:
            pass

        return workflow.compile()

    def _query_analyzer_node(self, state: WorkflowState) -> WorkflowState:
        """Phase 0: Analyze query and determine search strategy"""

        try:
            query_analysis = self.manager_agent.analyze_query(state['query'])

            return {
                'query_analysis': query_analysis,
                'processing_stats': {
                    'query_analysis': {
                        'complexity': query_analysis.complexity.value,
                        'topic': query_analysis.topic.value,
                        'searches_allocated': len(query_analysis.budget_allocation),
                        'rationale': query_analysis.rationale
                    }
                },
                'phase_completed': ['query_analysis']
            }

        except Exception as e:
            return {
                'errors': [f"Query analysis failed: {str(e)}"]
            }

    def _search_orchestrator_node(self, state: WorkflowState) -> WorkflowState:
        """Phase 0: Execute initial search wave for parallel hats"""

        try:
            query_analysis = state['query_analysis']

            # Get search queries for allocated hats
            hat_search_queries = {
                hat_type.value: query_analysis.search_queries.get(hat_type, "")
                for hat_type in query_analysis.budget_allocation
            }

            # Execute search wave
            search_contexts = self.search_orchestrator.execute_initial_search_wave(
                hat_search_queries
            )

            return {
                'search_contexts': search_contexts,
                'processing_stats': {
                    'search': {
                        'total_searches': len(search_contexts),
                        'cache_hits': sum(1 for ctx in search_contexts.values() if ctx.cache_hit),
                        'execution_time': sum(ctx.execution_time for ctx in search_contexts.values())
                    }
                },
                'phase_completed': ['search_orchestration']
            }

        except Exception as e:
            return {
                'errors': [f"Search orchestration failed: {str(e)}"]
            }

    def _white_hat_node(self, state: WorkflowState) -> WorkflowState:
        """Phase 1: White Hat - Facts and Data Analysis"""

        try:
            query = state['query']
            search_context = state['search_contexts'].get('white') if state.get('search_contexts') else None

            response = self.white_hat.process(
                query=query,
                search_context=search_context.search_results if search_context else None
            )

            return {
                'white_response': response.response,
                'processing_stats': {
                    'white_hat': {
                        'execution_time': response.processing_time,
                        'search_used': search_context is not None,
                        'response_length': len(response.response)
                    }
                }
            }

        except Exception as e:
            return {
                'white_response': f"Error: Unable to process White Hat perspective.",
                'errors': [f"White hat failed: {str(e)}"]
            }

    def _red_hat_node(self, state: WorkflowState) -> WorkflowState:
        """Phase 1: Red Hat - Emotions and Feelings"""

        try:
            query = state['query']
            search_context = state['search_contexts'].get('red') if state.get('search_contexts') else None

            response = self.red_hat.process(
                query=query,
                search_context=search_context.search_results if search_context else None
            )

            return {
                'red_response': response.response,
                'processing_stats': {
                    'red_hat': {
                        'execution_time': response.processing_time,
                        'search_used': search_context is not None,
                        'response_length': len(response.response)
                    }
                }
            }

        except Exception as e:
            return {
                'red_response': f"Error: Unable to process Red Hat perspective.",
                'errors': [f"Red hat failed: {str(e)}"]
            }

    def _yellow_hat_node(self, state: WorkflowState) -> WorkflowState:
        """Phase 1: Yellow Hat - Benefits and Opportunities"""

        try:
            query = state['query']
            search_context = state['search_contexts'].get('yellow') if state.get('search_contexts') else None

            response = self.yellow_hat.process(
                query=query,
                search_context=search_context.search_results if search_context else None
            )

            return {
                'yellow_response': response.response,
                'processing_stats': {
                    'yellow_hat': {
                        'execution_time': response.processing_time,
                        'search_used': search_context is not None,
                        'response_length': len(response.response)
                    }
                }
            }

        except Exception as e:
            return {
                'yellow_response': f"Error: Unable to process Yellow Hat perspective.",
                'errors': [f"Yellow hat failed: {str(e)}"]
            }

    def _black_hat_node(self, state: WorkflowState) -> WorkflowState:
        """Phase 1: Black Hat - Risks and Problems"""

        try:
            query = state['query']
            search_context = state['search_contexts'].get('black') if state.get('search_contexts') else None

            response = self.black_hat.process(
                query=query,
                search_context=search_context.search_results if search_context else None
            )

            return {
                'black_response': response.response,
                'processing_stats': {
                    'black_hat': {
                        'execution_time': response.processing_time,
                        'search_used': search_context is not None,
                        'response_length': len(response.response)
                    }
                }
            }

        except Exception as e:
            return {
                'black_response': f"Error: Unable to process Black Hat perspective.",
                'errors': [f"Black hat failed: {str(e)}"]
            }

    def _aggregator_node(self, state: WorkflowState) -> WorkflowState:
        """Phase 2: Aggregate parallel hat results for Green Hat"""

        try:
            # Collect all parallel hat responses
            hat_responses = {
                'white': state.get('white_response', ''),
                'red': state.get('red_response', ''),
                'yellow': state.get('yellow_response', ''),
                'black': state.get('black_response', '')
            }

            # Build aggregated context
            aggregated_context = self.search_orchestrator.aggregate_hat_contexts(
                hat_responses,
                state.get('search_contexts', {})
            )

            return {
                'green_context': aggregated_context,
                'processing_stats': {
                    'aggregator': {
                        'context_size': len(str(aggregated_context)),
                        'themes_identified': len(aggregated_context.get('key_themes', [])),
                        'synthesis_opportunities': len(aggregated_context.get('synthesis_opportunities', []))
                    }
                },
                'phase_completed': ['aggregation']
            }

        except Exception as e:
            return {
                'green_context': {
                    'parallel_responses': {
                        'white': state.get('white_response', ''),
                        'red': state.get('red_response', ''),
                        'yellow': state.get('yellow_response', ''),
                        'black': state.get('black_response', '')
                    }
                },
                'errors': [f"Aggregation failed: {str(e)}"]
            }

    def _green_hat_node(self, state: WorkflowState) -> WorkflowState:
        """Phase 2: Green Hat - Creative Solutions"""

        try:
            query = state['query']
            aggregated_context = state.get('green_context', {})
            search_context = state['search_contexts'].get('green') if state.get('search_contexts') else None

            # Check if Green Hat should search (budget allows and complexity warrants)
            query_analysis = state.get('query_analysis')
            budget_used = len(state.get('search_contexts', {}))
            should_green_search = (
                query_analysis and
                query_analysis.search_recommendations.get('green') and
                budget_used < self.max_searches
            )

            green_search_context = None
            if should_green_search:
                green_search_context = self.search_orchestrator.execute_sequential_search(
                    hat_type='green',
                    search_query=query_analysis.search_queries.get('green', ''),
                    current_budget_used=budget_used,
                    context=aggregated_context
                )

            response = self.green_hat.process(
                query=query,
                aggregated_context=aggregated_context,
                search_context=green_search_context.search_results if green_search_context else None
            )

            return {
                'green_response': response.response,
                'processing_stats': {
                    'green_hat': {
                        'execution_time': response.processing_time,
                        'search_used': green_search_context is not None,
                        'response_length': len(response.response),
                        'aggregated_context_size': len(str(aggregated_context))
                    }
                },
                'phase_completed': ['green_hat']
            }

        except Exception as e:
            return {
                'green_response': f"Error: Unable to process Green Hat perspective.",
                'errors': [f"Green hat failed: {str(e)}"]
            }

    def _blue_hat_node(self, state: WorkflowState) -> WorkflowState:
        """Phase 3: Blue Hat - Final Synthesis"""

        try:
            query = state['query']

            # Collect all responses
            all_responses = {
                'white': state.get('white_response', ''),
                'red': state.get('red_response', ''),
                'yellow': state.get('yellow_response', ''),
                'black': state.get('black_response', ''),
                'green': state.get('green_response', '')
            }

            # Build synthesis context
            synthesis_context = self.search_orchestrator.build_synthesis_context(
                white_response=all_responses['white'],
                red_response=all_responses['red'],
                yellow_response=all_responses['yellow'],
                black_response=all_responses['black'],
                green_response=all_responses['green'],
                search_contexts=state.get('search_contexts', {})
            )

            response = self.blue_hat.process(
                query=query,
                all_responses=all_responses,
                synthesis_context=synthesis_context
            )

            # Calculate overall stats
            total_time = sum(
                stats.get('execution_time', 0)
                for stats in state.get('processing_stats', {}).values()
                if isinstance(stats, dict) and 'execution_time' in stats
            )

            return {
                'blue_response': response.response,
                'processing_stats': {
                    'blue_hat': {
                        'execution_time': response.processing_time,
                        'response_length': len(response.response),
                        'synthesis_context_size': len(str(synthesis_context))
                    },
                    'overall': {
                        'total_execution_time': total_time + response.processing_time,
                        'phases_completed': state.get('phase_completed', []) + ['blue_hat'],
                        'total_errors': len(state.get('errors', []))
                    }
                },
                'phase_completed': ['blue_hat']
            }

        except Exception as e:
            return {
                'blue_response': f"Error: Unable to process Blue Hat summary.",
                'errors': [f"Blue hat failed: {str(e)}"]
            }

    def invoke(self, query: str) -> Dict[str, Any]:
        """
        Invoke the workflow with a query.

        Args:
            query: User query

        Returns:
            Dictionary with all responses and metadata
        """
        initial_state: WorkflowState = {
            'query': query,
            'processing_stats': {},
            'errors': []
        }

        final_state = self.workflow.invoke(initial_state)

        return final_state

    def stream(self, query: str):
        """
        Stream results as they become available.

        Args:
            query: User query

        Yields:
            Dict with phase and data as results are computed
        """
        initial_state: WorkflowState = {
            'query': query,
            'processing_stats': {},
            'errors': []
        }

        # Stream through the workflow
        for event in self.workflow.stream(initial_state):
            node_name = list(event.keys())[0]
            node_state = event[node_name]

            yield {
                'node': node_name,
                'data': node_state,
                'phase': self._determine_phase(node_name)
            }

    def _determine_phase(self, node_name: str) -> str:
        """Determine which phase a node belongs to"""

        if node_name in ['query_analyzer', 'search_orchestrator']:
            return 'phase_0_analysis'
        elif node_name in ['white_hat', 'red_hat', 'yellow_hat', 'black_hat']:
            return 'phase_1_parallel'
        elif node_name in ['aggregator', 'green_hat']:
            return 'phase_2_sequential'
        elif node_name == 'blue_hat':
            return 'phase_3_synthesis'
        else:
            return 'unknown'

    def get_search_statistics(self) -> Dict:
        """Get search orchestration statistics"""
        return self.search_orchestrator.get_search_statistics()
