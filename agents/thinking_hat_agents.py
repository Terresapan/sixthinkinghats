"""Specialized thinking hat agents with search integration for phased execution."""

import time
from typing import Dict, List, Any, Optional
from .base_agent import BaseThinkingHatAgent, AgentProcessingResult, AgentFactory
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from services.phased_search_orchestrator import HatSearchContext


class WhiteHatAgent(BaseThinkingHatAgent):
    """White Hat Agent - Facts and data specialist."""

    def __init__(self, llm: ChatOpenAI):
        system_prompt = """You are the White Hat. You represent neutrality and facts.

Your role:
- Provide objective data, statistics, and verifiable information
- Focus on what is known rather than opinions or speculation
- Present facts clearly and without emotional bias
- Use search results to find current, reliable data sources
- Always prioritize factual accuracy over interesting speculation

Response guidelines:
- Present information in a clear, structured format
- Include source information when available from search results
- Distinguish between verified facts and claims that need verification
- Limit your response to 200 words
- Be precise and avoid generalizations without data support"""

        super().__init__(llm, "white_hat", system_prompt)

    def process(
        self,
        query: str,
        search_context: Optional[List[Dict[str, Any]]] = None
    ) -> AgentProcessingResult:
        """Process query with optional search context."""
        start_time = time.time()

        # Set search results if provided
        if search_context:
            self.set_search_results(search_context, {})

        # Build message with search context
        messages = [self.create_system_message()]
        messages.append(HumanMessage(content=query))

        try:
            response = self.llm.invoke(messages)
            execution_time = time.time() - start_time
            return AgentProcessingResult(
                agent_name="white_hat",
                response=response.content,
                processing_time=execution_time,
                search_used=search_context is not None
            )
        except Exception as e:
            execution_time = time.time() - start_time
            return AgentProcessingResult(
                agent_name="white_hat",
                response=f"Error: {str(e)}",
                processing_time=execution_time,
                search_used=search_context is not None,
                error=str(e)
            )


class RedHatAgent(BaseThinkingHatAgent):
    """Red Hat Agent - Emotions and feelings specialist."""

    def __init__(self, llm: ChatOpenAI):
        system_prompt = """You are the Red Hat. You represent emotions and feelings.

Your role:
- Express emotions, intuition, and gut reactions about the topic
- Share personal feelings without needing justification or explanation
- Use search results to understand public sentiment and emotional responses
- Focus on how people feel, not just what they think
- Express both positive and negative emotional responses honestly

Response guidelines:
- Start with your immediate emotional response to the topic
- Use search results to understand broader emotional landscape
- Express feelings directly and honestly
- Include intuitive insights that may not be logical but feel right
- Limit your response to 200 words
- Don't apologize for having emotions or feelings"""

        super().__init__(llm, "red_hat", system_prompt)

    def process(
        self,
        query: str,
        search_context: Optional[List[Dict[str, Any]]] = None
    ) -> AgentProcessingResult:
        """Process query with optional search context."""
        start_time = time.time()

        # Set search results if provided
        if search_context:
            self.set_search_results(search_context, {})

        # Build message with search context
        messages = [self.create_system_message()]
        messages.append(HumanMessage(content=query))

        try:
            response = self.llm.invoke(messages)
            execution_time = time.time() - start_time
            return AgentProcessingResult(
                agent_name="red_hat",
                response=response.content,
                processing_time=execution_time,
                search_used=search_context is not None
            )
        except Exception as e:
            execution_time = time.time() - start_time
            return AgentProcessingResult(
                agent_name="red_hat",
                response=f"Error: {str(e)}",
                processing_time=execution_time,
                search_used=search_context is not None,
                error=str(e)
            )


class YellowHatAgent(BaseThinkingHatAgent):
    """Yellow Hat Agent - Optimism and benefits specialist."""

    def __init__(self, llm: ChatOpenAI):
        system_prompt = """You are the Yellow Hat. You represent optimism and positive thinking.

Your role:
- Identify benefits, advantages, and opportunities
- Look for the positive aspects and potential of ideas
- Use search results to find success stories and positive outcomes
- Focus on what could go right rather than what could go wrong
- Generate optimistic scenarios and positive possibilities

Response guidelines:
- Start by identifying the best-case scenarios and benefits
- Use search results to find evidence of positive outcomes
- Look for opportunities and silver linings
- Think creatively about positive potential
- Be specific about the benefits you identify
- Limit your response to 200 words
- Focus on constructive possibilities"""

        super().__init__(llm, "yellow_hat", system_prompt)

    def process(
        self,
        query: str,
        search_context: Optional[List[Dict[str, Any]]] = None
    ) -> AgentProcessingResult:
        """Process query with optional search context."""
        start_time = time.time()

        if search_context:
            self.set_search_results(search_context, {})

        messages = [self.create_system_message()]
        messages.append(HumanMessage(content=query))

        try:
            response = self.llm.invoke(messages)
            execution_time = time.time() - start_time
            return AgentProcessingResult(
                agent_name="yellow_hat",
                response=response.content,
                processing_time=execution_time,
                search_used=search_context is not None
            )
        except Exception as e:
            execution_time = time.time() - start_time
            return AgentProcessingResult(
                agent_name="yellow_hat",
                response=f"Error: {str(e)}",
                processing_time=execution_time,
                search_used=search_context is not None,
                error=str(e)
            )


class BlackHatAgent(BaseThinkingHatAgent):
    """Black Hat Agent - Risks and problems specialist."""

    def __init__(self, llm: ChatOpenAI):
        system_prompt = """You are the Black Hat. You represent caution and risk assessment.

Your role:
- Identify potential problems, risks, and limitations
- Point out what could go wrong or fail
- Use search results to find evidence of risks and failures
- Provide realistic assessment of challenges and obstacles
- Ask critical questions about feasibility and potential downsides

Response guidelines:
- Identify specific risks and potential failure points
- Use search results to find real examples of problems
- Be thorough in risk assessment but not overly pessimistic
- Suggest ways to mitigate identified risks
- Ask critical questions that need to be answered
- Limit your response to 200 words
- Focus on constructive caution rather than pure negativity"""

        super().__init__(llm, "black_hat", system_prompt)

    def process(
        self,
        query: str,
        search_context: Optional[List[Dict[str, Any]]] = None
    ) -> AgentProcessingResult:
        """Process query with optional search context."""
        start_time = time.time()

        if search_context:
            self.set_search_results(search_context, {})

        messages = [self.create_system_message()]
        messages.append(HumanMessage(content=query))

        try:
            response = self.llm.invoke(messages)
            execution_time = time.time() - start_time
            return AgentProcessingResult(
                agent_name="black_hat",
                response=response.content,
                processing_time=execution_time,
                search_used=search_context is not None
            )
        except Exception as e:
            execution_time = time.time() - start_time
            return AgentProcessingResult(
                agent_name="black_hat",
                response=f"Error: {str(e)}",
                processing_time=execution_time,
                search_used=search_context is not None,
                error=str(e)
            )


class GreenHatAgent(BaseThinkingHatAgent):
    """Green Hat Agent - Creativity and innovation specialist."""

    def __init__(self, llm: ChatOpenAI):
        system_prompt = """You are the Green Hat. You represent creativity and innovation.

Your role:
- Generate new ideas, alternatives, and creative solutions
- Think outside the box and challenge conventional thinking
- Use search results to find innovative approaches and creative solutions
- Explore unconventional possibilities and novel approaches
- Focus on "what if" scenarios and creative alternatives
- Build upon and synthesize insights from previous thinking hats

Response guidelines:
- Start by challenging assumptions and conventional approaches
- Use search results to find innovative examples and creative solutions
- Generate multiple creative alternatives and ideas
- Think laterally and make unexpected connections
- Propose novel approaches that haven't been tried
- Use the aggregated context from White, Red, Yellow, and Black hats to inspire creative solutions
- Limit your response to 200 words
- Be bold and innovative in your thinking"""

        super().__init__(llm, "green_hat", system_prompt)

    def process(
        self,
        query: str,
        aggregated_context: Optional[Dict[str, Any]] = None,
        search_context: Optional[List[Dict[str, Any]]] = None
    ) -> AgentProcessingResult:
        """Process query with aggregated context from parallel hats and optional search."""
        start_time = time.time()

        # Set search results if provided
        if search_context:
            self.set_search_results(search_context, {})

        # Build enhanced context with aggregated perspectives
        enhanced_context = self.system_prompt

        if aggregated_context:
            enhanced_context += "\n\n## Aggregated Perspectives from Parallel Hats:\n"

            # Add parallel hat responses
            parallel_responses = aggregated_context.get('parallel_responses', {})
            for hat_name, response in parallel_responses.items():
                enhanced_context += f"\n### {hat_name.upper()} Hat Perspective:\n{response}\n"

            # Add key themes
            themes = aggregated_context.get('key_themes', [])
            if themes:
                enhanced_context += f"\n### Key Themes Identified:\n" + ", ".join(themes)

            # Add synthesis opportunities
            opportunities = aggregated_context.get('synthesis_opportunities', [])
            if opportunities:
                enhanced_context += f"\n\n### Synthesis Opportunities:\n"
                for opp in opportunities:
                    enhanced_context += f"- {opp}\n"

        # Create messages
        messages = [SystemMessage(content=enhanced_context)]
        messages.append(HumanMessage(content=query))

        try:
            response = self.llm.invoke(messages)
            execution_time = time.time() - start_time
            return AgentProcessingResult(
                agent_name="green_hat",
                response=response.content,
                processing_time=execution_time,
                search_used=search_context is not None
            )
        except Exception as e:
            execution_time = time.time() - start_time
            return AgentProcessingResult(
                agent_name="green_hat",
                response=f"Error: {str(e)}",
                processing_time=execution_time,
                search_used=search_context is not None,
                error=str(e)
            )


class BlueHatAgent(BaseThinkingHatAgent):
    """Blue Hat Agent - Process and summary specialist."""

    def __init__(self, llm: ChatOpenAI):
        system_prompt = """You are the Blue Hat. You represent process and organization.

Your role:
- Summarize discussions and provide overviews
- Focus on methodology and process improvements
- Use search results to find best practices and proven methodologies
- Synthesize insights from all other thinking hats (White, Red, Yellow, Black, Green)
- Provide clear conclusions and actionable recommendations

Response guidelines:
- Synthesize the key insights from all perspectives presented
- Use search results to support recommendations with proven methods
- Provide clear next steps and action items
- Focus on the bigger picture and overarching themes
- Organize information in a logical, structured way
- Address conflicts between perspectives and find balanced solutions
- Limit your response to 200 words
- Address the user's original question directly and clearly"""

        super().__init__(llm, "blue_hat", system_prompt)

    def process(
        self,
        query: str,
        all_responses: Dict[str, str],
        synthesis_context: Optional[Dict[str, Any]] = None
    ) -> AgentProcessingResult:
        """Process query with all hat responses and synthesis context."""
        start_time = time.time()

        # Build enhanced context with all perspectives
        enhanced_context = self.system_prompt

        if all_responses:
            enhanced_context += "\n\n## All Thinking Hat Perspectives:\n"

            hat_names = {
                'white': 'White Hat (Facts)',
                'red': 'Red Hat (Emotions)',
                'yellow': 'Yellow Hat (Benefits)',
                'black': 'Black Hat (Risks)',
                'green': 'Green Hat (Creativity)'
            }

            for hat_key, response in all_responses.items():
                hat_name = hat_names.get(hat_key, hat_key)
                enhanced_context += f"\n### {hat_name}:\n{response}\n"

        if synthesis_context:
            enhanced_context += "\n### Search Evidence:\n"
            search_evidence = synthesis_context.get('search_evidence', {})
            for hat_type, evidence in search_evidence.items():
                if evidence:
                    enhanced_context += f"\n**{hat_type.upper()} Hat Evidence:**\n"
                    for item in evidence[:2]:  # Top 2 pieces of evidence
                        enhanced_context += f"- {item.get('title', '')}\n"

            enhanced_context += f"\n{synthesis_context.get('synthesis_notes', '')}\n"

        # Create messages
        messages = [SystemMessage(content=enhanced_context)]
        messages.append(HumanMessage(content=query))

        try:
            response = self.llm.invoke(messages)
            execution_time = time.time() - start_time
            return AgentProcessingResult(
                agent_name="blue_hat",
                response=response.content,
                processing_time=execution_time,
                search_used=False  # Blue Hat doesn't use search directly in this architecture
            )
        except Exception as e:
            execution_time = time.time() - start_time
            return AgentProcessingResult(
                agent_name="blue_hat",
                response=f"Error: {str(e)}",
                processing_time=execution_time,
                search_used=False,
                error=str(e)
            )


# Register all agents with the factory
AgentFactory.register_agent("white_hat", WhiteHatAgent)
AgentFactory.register_agent("red_hat", RedHatAgent)
AgentFactory.register_agent("yellow_hat", YellowHatAgent)
AgentFactory.register_agent("black_hat", BlackHatAgent)
AgentFactory.register_agent("green_hat", GreenHatAgent)
AgentFactory.register_agent("blue_hat", BlueHatAgent)
