"""
Base classes for the Kypzer AI agent system.

This module provides foundational classes and interfaces that all specialized
agents inherit from, ensuring consistent behavior and interfaces across the
multi-agent system.
"""

from typing import Any, Dict, Optional
from abc import ABC, abstractmethod


class BaseAgent(ABC):
    """
    Base class for all Kypzer AI agents.
    
    All specialized agents (PCControlAgent, WhatsAppAgent, etc.) should inherit
    from this class to ensure consistent interface and behavior.
    
    Attributes:
        name: Unique identifier for the agent
        agent_type: Category of the agent (e.g., "pc_control", "whatsapp")
        description: Human-readable description of agent capabilities
    """
    
    def __init__(self, name: str, agent_type: str, description: str = ""):
        """
        Initialize a base agent.
        
        Args:
            name: Unique agent name
            agent_type: Agent category identifier
            description: Optional description of agent capabilities
        """
        self.name = name
        self.agent_type = agent_type
        self.description = description
    
    @abstractmethod
    def execute_task(self, task_description: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a task assigned to this agent.
        
        Args:
            task_description: Natural language description of the task
            context: Optional context from workflow state
            
        Returns:
            Dictionary containing:
                - success: bool indicating if task succeeded
                - result: Any result data from execution
                - error: Optional error message if failed
                - action_taken: Description of what action was performed
                
        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        pass
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', type='{self.agent_type}')"
