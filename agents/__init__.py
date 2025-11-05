"""Agents module for thinking hat subagents with search integration."""

from .base_agent import BaseThinkingHatAgent, AgentFactory, AgentProcessingResult
from .thinking_hat_agents import (
    WhiteHatAgent, RedHatAgent, YellowHatAgent, 
    BlackHatAgent, GreenHatAgent, BlueHatAgent
)

__all__ = [
    'BaseThinkingHatAgent', 'AgentFactory', 'AgentProcessingResult',
    'WhiteHatAgent', 'RedHatAgent', 'YellowHatAgent',
    'BlackHatAgent', 'GreenHatAgent', 'BlueHatAgent'
]
