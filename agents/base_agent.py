"""
Base agent class for thinking hat agents.
Provides common functionality for search integration and processing.
"""

from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
from datetime import datetime

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
import os


class BaseThinkingHatAgent(ABC):
    """Base class for all thinking hat agents."""
    
    def __init__(self, llm: ChatOpenAI, agent_name: str, system_prompt: str):
        self.llm = llm
        self.agent_name = agent_name
        self.system_prompt = system_prompt
        
        # Search-related attributes
        self.has_search_access = False
        self.search_results = []
        self.search_context = {}
    
    def set_search_results(self, search_results: List[Dict[str, Any]], search_context: Dict[str, Any]):
        """Set search results for the agent to use."""
        self.search_results = search_results
        self.search_context = search_context
        self.has_search_access = True
    
    def format_search_context(self) -> str:
        """Format search results into a context string for the LLM."""
        if not self.has_search_access or not self.search_results:
            return ""
        
        context_parts = []
        context_parts.append("## Search Results Available:")
        
        for i, result in enumerate(self.search_results, 1):
            title = result.get('title', 'No title')
            url = result.get('url', 'No URL')
            content = result.get('content', 'No content')
            score = result.get('score', 0.0)
            
            context_parts.append(f"\n### Search Result {i} (Score: {score:.2f})")
            context_parts.append(f"**Title:** {title}")
            context_parts.append(f"**URL:** {url}")
            context_parts.append(f"**Content:** {content[:500]}...")  # Limit content length
        
        if self.search_context:
            context_parts.append(f"\n### Search Metadata:")
            for key, value in self.search_context.items():
                context_parts.append(f"**{key}:** {value}")
        
        return "\n".join(context_parts)
    
    def create_system_message(self) -> SystemMessage:
        """Create the system message for the agent."""
        search_context = self.format_search_context()
        full_prompt = self.system_prompt
        
        if search_context:
            full_prompt += f"\n\n{search_context}\n\nUse the search results above to inform your response. If search results are not relevant, you may ignore them."
        
        full_prompt += f"\n\nCurrent timestamp: {datetime.now().isoformat()}"
        
        return SystemMessage(content=full_prompt)
    
    def process(self, user_query: str, conversation_history: Optional[List] = None) -> str:
        """
        Process a user query and return the agent's response.
        
        Args:
            user_query: The user's query
            conversation_history: Previous messages in the conversation
            
        Returns:
            The agent's response as a string
        """
        # Build message history
        messages = [self.create_system_message()]
        
        # Add conversation history if provided
        if conversation_history:
            for msg in conversation_history:
                if isinstance(msg, HumanMessage):
                    messages.append(msg) # type: ignore
                elif isinstance(msg, AIMessage):
                    messages.append(msg) # type: ignore
        
        # Add current user query
        messages.append(HumanMessage(content=user_query)) # type: ignore
        
        try:
            # Get response from LLM
            response = self.llm.invoke(messages)
            return response.content # type: ignore
        except Exception as e:
            return f"I apologize, but I encountered an error while processing your query: {str(e)}"
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics for this agent."""
        return {
            "agent_name": self.agent_name,
            "has_search_access": self.has_search_access,
            "search_results_count": len(self.search_results),
            "system_prompt_length": len(self.system_prompt),
            "search_context_available": bool(self.search_context)
        }
    
    def reset_state(self):
        """Reset the agent's state."""
        self.search_results = []
        self.search_context = {}
        self.has_search_access = False


class AgentProcessingResult:
    """Result from agent processing."""
    
    def __init__(self, agent_name: str, response: str, processing_time: float, 
                 search_used: bool = False, error: Optional[str] = None):
        self.agent_name = agent_name
        self.response = response
        self.processing_time = processing_time
        self.search_used = search_used
        self.error = error
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "response": self.response,
            "processing_time": self.processing_time,
            "search_used": self.search_used,
            "error": self.error,
            "timestamp": self.timestamp.isoformat()
        }


class AgentFactory:
    """Factory for creating thinking hat agents."""
    
    _agents = {}
    
    @classmethod
    def create_agent(cls, agent_type: str, llm: ChatOpenAI, **kwargs) -> BaseThinkingHatAgent:
        """Create an agent of the specified type."""
        if agent_type not in cls._agents:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        return cls._agents[agent_type](llm, **kwargs)
    
    @classmethod
    def register_agent(cls, agent_type: str, agent_class):
        """Register an agent class."""
        cls._agents[agent_type] = agent_class
    
    @classmethod
    def get_available_agents(cls) -> List[str]:
        """Get list of available agent types."""
        return list(cls._agents.keys())
