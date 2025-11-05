"""
Parallel processing system for thinking hat agents with search integration.
Handles concurrent execution and streaming results.
"""

import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import time

from langchain_openai import ChatOpenAI
from services import SearchOrchestrator, SearchAPIFactory
from agents import BaseThinkingHatAgent, AgentFactory, AgentProcessingResult


class ParallelProcessor:
    """Handles parallel processing of thinking hat agents."""
    
    def __init__(self, llm: ChatOpenAI, search_api_provider: str = "tavily", max_searches: int = 4):
        self.llm = llm
        self.max_searches = max_searches
        
        # Initialize search orchestrator
        try:
            search_api = SearchAPIFactory.create_provider(search_api_provider)
            self.search_orchestrator = SearchOrchestrator(search_api, max_searches)
        except Exception as e:
            print(f"Warning: Could not initialize search orchestrator: {e}")
            self.search_orchestrator = None
        
        # Processing statistics
        self.total_processing_time = 0
        self.agents_processed = 0
        self.searches_performed = 0
    
    async def process_query_parallel(self, user_query: str, search_enabled: bool = True) -> Dict[str, Any]:
        """
        Process a query using parallel thinking hat agents with search integration.
        
        Args:
            user_query: The user's query
            search_enabled: Whether to enable web search
            
        Returns:
            Dictionary containing all agent responses and metadata
        """
        start_time = time.time()
        
        # Step 1: Perform search orchestration if enabled
        search_results = {}
        search_context = {}
        
        if search_enabled and self.search_orchestrator:
            try:
                search_data = await self.search_orchestrator.orchestrate_searches(user_query)
                search_results = search_data.get("results", {}).get("by_hat", {})
                search_context = {
                    "search_budget_used": search_data.get("search_budget_used", 0),
                    "search_summary": search_data.get("summary", {}),
                    "cache_stats": search_data.get("cache_stats", {})
                }
                self.searches_performed = search_data.get("search_budget_used", 0)
            except Exception as e:
                print(f"Search orchestration error: {e}")
                # Continue without search
                search_results = {}
                search_context = {"error": str(e)}
        
        # Step 2: Create all agents
        agents = self._create_all_agents()
        
        # Step 3: Assign search results to appropriate agents
        self._assign_search_results(agents, search_results, search_context)
        
        # Step 4: Process agents in parallel groups
        processing_groups = [
            # Group 1: Independent agents that can run in parallel
            ["white_hat", "red_hat"],
            # Group 2: Risk/benefit analysis (may reference Group 1)
            ["yellow_hat", "black_hat"], 
            # Group 3: Creative synthesis (references all previous)
            ["green_hat"],
            # Group 4: Final summary (references all previous)
            ["blue_hat"]
        ]
        
        all_results = {}
        
        for group in processing_groups:
            # Run group in parallel
            group_tasks = []
            for agent_name in group:
                if agent_name in agents:
                    agent = agents[agent_name]
                    task = asyncio.create_task(self._process_agent_async(agent, user_query))
                    group_tasks.append((agent_name, task))
            
            # Wait for group to complete
            for agent_name, task in group_tasks:
                try:
                    result = await task
                    all_results[agent_name] = result
                    self.agents_processed += 1
                except Exception as e:
                    all_results[agent_name] = AgentProcessingResult(
                        agent_name, 
                        f"Error processing: {str(e)}", 
                        0, 
                        False, 
                        str(e)
                    )
        
        # Step 5: Compile final results
        processing_time = time.time() - start_time
        self.total_processing_time += processing_time
        
        return self._compile_final_results(
            user_query, all_results, search_context, processing_time
        )
    
    def _create_all_agents(self) -> Dict[str, BaseThinkingHatAgent]:
        """Create all thinking hat agents."""
        agents = {}
        
        agent_types = ["white_hat", "red_hat", "yellow_hat", "black_hat", "green_hat", "blue_hat"]
        
        for agent_type in agent_types:
            try:
                agent = AgentFactory.create_agent(agent_type, self.llm)
                agents[agent_type] = agent
            except Exception as e:
                print(f"Warning: Could not create {agent_type}: {e}")
        
        return agents
    
    def _assign_search_results(self, agents: Dict[str, BaseThinkingHatAgent], 
                             search_results: Dict[str, Any], 
                             search_context: Dict[str, Any]):
        """Assign search results to appropriate agents."""
        for agent_name, agent in agents.items():
            if agent_name in search_results:
                hat_search_data = search_results[agent_name]
                results_list = hat_search_data.get("results", [])
                agent.set_search_results(results_list, search_context)
    
    async def _process_agent_async(self, agent: BaseThinkingHatAgent, user_query: str) -> AgentProcessingResult:
        """Process an agent asynchronously."""
        start_time = time.time()
        
        try:
            response = agent.process(user_query)
            processing_time = time.time() - start_time
            
            return AgentProcessingResult(
                agent.agent_name,
                response,
                processing_time,
                agent.has_search_access
            )
        except Exception as e:
            processing_time = time.time() - start_time
            return AgentProcessingResult(
                agent.agent_name,
                f"Error: {str(e)}",
                processing_time,
                agent.has_search_access,
                str(e)
            )
    
    def _compile_final_results(self, user_query: str, agent_results: Dict[str, AgentProcessingResult],
                             search_context: Dict[str, Any], processing_time: float) -> Dict[str, Any]:
        """Compile final results from all agents."""
        
        # Organize results by agent
        organized_results = {}
        for agent_name, result in agent_results.items():
            organized_results[agent_name] = result.to_dict()
        
        # Generate summary statistics
        successful_agents = len([r for r in agent_results.values() if not r.error])
        total_agents = len(agent_results)
        search_used_count = len([r for r in agent_results.values() if r.search_used])
        
        return {
            "user_query": user_query,
            "timestamp": datetime.now().isoformat(),
            "processing_time": processing_time,
            "results": organized_results,
            "search_context": search_context,
            "statistics": {
                "total_agents": total_agents,
                "successful_agents": successful_agents,
                "failed_agents": total_agents - successful_agents,
                "agents_with_search": search_used_count,
                "searches_performed": self.searches_performed,
                "success_rate": f"{(successful_agents / max(total_agents, 1)) * 100:.1f}%"
            },
            "performance": {
                "total_processing_time": self.total_processing_time,
                "average_time_per_agent": processing_time / max(total_agents, 1),
                "agents_per_second": total_agents / max(processing_time, 0.1)
            }
        }
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get processing performance statistics."""
        return {
            "total_processing_time": self.total_processing_time,
            "agents_processed": self.agents_processed,
            "searches_performed": self.searches_performed,
            "average_processing_time": self.total_processing_time / max(self.agents_processed, 1),
            "search_efficiency": self.agents_processed / max(self.searches_performed, 1)
        }
    
    def reset_statistics(self):
        """Reset processing statistics."""
        self.total_processing_time = 0
        self.agents_processed = 0
        self.searches_performed = 0
        
        if self.search_orchestrator:
            self.search_orchestrator.reset_statistics()


class StreamingResultHandler:
    """Handles streaming results for real-time UI updates."""
    
    def __init__(self, callback: Optional[Callable[[Dict[str, Any]], None]] = None):
        self.callback = callback
        self.streaming_active = False
    
    async def stream_agent_results(self, processor: ParallelProcessor, 
                                 user_query: str, 
                                 search_enabled: bool = True) -> Dict[str, Any]:
        """
        Stream agent results as they become available.
        
        Args:
            processor: The parallel processor instance
            user_query: The user's query
            search_enabled: Whether to enable web search
            
        Returns:
            Final compiled results
        """
        self.streaming_active = True
        
        # Send initial status
        self._send_stream_update({
            "type": "status",
            "message": "Starting analysis...",
            "timestamp": datetime.now().isoformat()
        })
        
        try:
            # Process query with streaming updates
            final_results = await processor.process_query_parallel(user_query, search_enabled)
            
            # Send completion status
            self._send_stream_update({
                "type": "complete",
                "message": "Analysis complete",
                "timestamp": datetime.now().isoformat(),
                "results": final_results
            })
            
            return final_results
            
        except Exception as e:
            error_update = {
                "type": "error",
                "message": f"Processing error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
            self._send_stream_update(error_update)
            raise
        finally:
            self.streaming_active = False
    
    def _send_stream_update(self, update: Dict[str, Any]):
        """Send a streaming update if callback is available."""
        if self.callback:
            try:
                self.callback(update)
            except Exception as e:
                print(f"Streaming callback error: {e}")


# Utility functions for easy integration
def create_parallel_processor(llm: ChatOpenAI, 
                            search_api_key: Optional[str] = None,
                            search_enabled: bool = True) -> ParallelProcessor:
    """
    Create a configured parallel processor.
    
    Args:
        llm: The language model instance
        search_api_key: Optional search API key
        search_enabled: Whether to enable search functionality
        
    Returns:
        Configured ParallelProcessor instance
    """
    if search_enabled and search_api_key:
        import os
        os.environ["TAVILY_API_KEY"] = search_api_key
    
    return ParallelProcessor(llm, max_searches=4)


async def process_thinking_hats_query(llm: ChatOpenAI, 
                                    user_query: str,
                                    search_enabled: bool = True,
                                    streaming_callback: Optional[Callable[[Dict[str, Any]], None]] = None) -> Dict[str, Any]:
    """
    Convenience function to process a thinking hats query.
    
    Args:
        llm: The language model instance
        user_query: The user's query
        search_enabled: Whether to enable web search
        streaming_callback: Optional callback for streaming updates
        
    Returns:
        Complete processing results
    """
    processor = create_parallel_processor(llm, search_enabled=search_enabled)
    
    if streaming_callback:
        handler = StreamingResultHandler(streaming_callback)
        return await handler.stream_agent_results(processor, user_query, search_enabled)
    else:
        return await processor.process_query_parallel(user_query, search_enabled)
