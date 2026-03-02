"""Agents module for LLM-based spec generation."""

from redpill.agents.base import BaseAgent
from redpill.agents.intent_spec_agent import IntentSpecAgent
from redpill.agents.validator import ValidatorAgent, ValidationResult

try:
    from redpill.agents.langgraph_agent import LangGraphAgent, create_spec_agent_graph
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LangGraphAgent = None  # type: ignore
    create_spec_agent_graph = None  # type: ignore
    LANGGRAPH_AVAILABLE = False

__all__ = [
    "BaseAgent",
    "IntentSpecAgent",
    "ValidatorAgent",
    "ValidationResult",
    "LangGraphAgent",
    "create_spec_agent_graph",
]
