"""
Multi-Agent System for Kypzer AI

This package implements the LangGraph and AutoGen integration for Kypzer AI,
providing intelligent command orchestration, specialized agents, and graph-based
workflow management.

Components:
- orchestrator: Central coordinator for command routing
- state: Workflow state management and data models
- registry: Agent registration and discovery
- state_manager: LangGraph workflow builder and executor
- specialized: Domain-specific agents (PC Control, WhatsApp, Screen AI, Web, Memory)
"""

from agents.base import BaseAgent
from agents.state import (
    WorkflowState,
    CommandType,
    StateValidationError,
    validate_workflow_state,
    create_initial_state,
    is_terminal_state,
    increment_step,
    increment_retry,
    add_agent_response,
    set_final_result,
)
from agents.models import (
    AgentResponse,
    CommandClassification,
    success_response,
    error_response,
    simple_classification,
    complex_classification,
    multi_step_classification,
)
from agents.registry import AgentRegistry

__all__ = [
    # Base classes
    "BaseAgent",
    # State management
    "WorkflowState",
    "CommandType",
    "StateValidationError",
    "validate_workflow_state",
    "create_initial_state",
    "is_terminal_state",
    "increment_step",
    "increment_retry",
    "add_agent_response",
    "set_final_result",
    # Data models
    "AgentResponse",
    "CommandClassification",
    "success_response",
    "error_response",
    "simple_classification",
    "complex_classification",
    "multi_step_classification",
    # Agent Registry
    "AgentRegistry",
]

__version__ = "0.1.0"
