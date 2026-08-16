"""
Data models for agent communication and command classification.

This module defines the core data structures used for communication between
agents and the orchestrator, as well as for classifying user commands to
determine routing strategies.

Models:
    - AgentResponse: Result of agent execution with metadata
    - CommandClassification: Analysis of user command for routing decisions
"""

from dataclasses import dataclass, field
from typing import Optional, Any, Literal
from datetime import datetime


# Type alias for command types
CommandType = Literal["simple", "complex", "multi_step"]


@dataclass
class AgentResponse:
    """
    Response object returned by agent execution.
    
    This dataclass encapsulates all information about an agent's execution
    of a task, including success status, results, errors, and recommendations
    for next steps or retries.
    
    Attributes:
        success: Whether the agent execution succeeded
        agent_name: Name of the agent that executed the task
        action_taken: Description of what action was performed
        result: Result data from execution (can be any JSON-serializable type)
        error: Error message if execution failed (None if success=True)
        retry_recommended: Whether the orchestrator should retry this operation
        next_agent: Suggestion for which agent should execute next (optional)
        metadata: Additional metadata (timestamps, execution time, etc.)
        
    Validates: Requirements 4.4, 5.6, 7.4, 1.4
    
    Examples:
        >>> response = AgentResponse(
        ...     success=True,
        ...     agent_name="PCControlAgent",
        ...     action_taken="VOLUME_UP",
        ...     result={"volume_level": 50},
        ...     error=None,
        ...     retry_recommended=False
        ... )
        >>> response.success
        True
        >>> response.validate()  # No exception
        
        >>> error_response = AgentResponse(
        ...     success=False,
        ...     agent_name="WhatsAppAgent",
        ...     action_taken="SEND_MESSAGE",
        ...     result=None,
        ...     error="Contact not found",
        ...     retry_recommended=True
        ... )
        >>> error_response.validate()  # No exception
    """
    
    success: bool
    agent_name: str
    action_taken: str
    result: Optional[Any] = None
    error: Optional[str] = None
    retry_recommended: bool = False
    next_agent: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize metadata with timestamp if not provided."""
        if "timestamp" not in self.metadata:
            self.metadata["timestamp"] = datetime.now().isoformat()
    
    def validate(self) -> None:
        """
        Validate the AgentResponse fields for consistency.
        
        Checks:
        - agent_name is not empty
        - action_taken is not empty
        - If success=True, error should be None
        - If success=False, error should be provided
        - If retry_recommended=True, success should be False
        
        Raises:
            ValueError: If validation fails
            
        Examples:
            >>> response = AgentResponse(
            ...     success=True,
            ...     agent_name="",
            ...     action_taken="test",
            ...     error=None
            ... )
            >>> response.validate()
            Traceback (most recent call last):
            ...
            ValueError: agent_name cannot be empty
        """
        if not self.agent_name:
            raise ValueError("agent_name cannot be empty")
        
        if not self.action_taken:
            raise ValueError("action_taken cannot be empty")
        
        # If successful, error should be None
        if self.success and self.error is not None:
            raise ValueError(
                "error should be None when success=True, "
                f"but got: {self.error}"
            )
        
        # If failed, error should be provided
        if not self.success and not self.error:
            raise ValueError(
                "error must be provided when success=False"
            )
        
        # If retry is recommended, operation must have failed
        if self.retry_recommended and self.success:
            raise ValueError(
                "retry_recommended=True is invalid when success=True"
            )
    
    def to_dict(self) -> dict[str, Any]:
        """
        Convert AgentResponse to a dictionary.
        
        Useful for serialization and storage in WorkflowState.agent_responses.
        
        Returns:
            Dictionary representation of the response
            
        Examples:
            >>> response = AgentResponse(
            ...     success=True,
            ...     agent_name="TestAgent",
            ...     action_taken="test_action",
            ...     result={"key": "value"}
            ... )
            >>> d = response.to_dict()
            >>> d["success"]
            True
            >>> d["agent_name"]
            'TestAgent'
        """
        return {
            "success": self.success,
            "agent_name": self.agent_name,
            "action_taken": self.action_taken,
            "result": self.result,
            "error": self.error,
            "retry_recommended": self.retry_recommended,
            "next_agent": self.next_agent,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentResponse":
        """
        Create an AgentResponse from a dictionary.
        
        Args:
            data: Dictionary containing response fields
            
        Returns:
            AgentResponse instance
            
        Examples:
            >>> data = {
            ...     "success": True,
            ...     "agent_name": "TestAgent",
            ...     "action_taken": "test",
            ...     "result": None,
            ...     "error": None,
            ...     "retry_recommended": False,
            ...     "next_agent": None,
            ...     "metadata": {}
            ... }
            >>> response = AgentResponse.from_dict(data)
            >>> response.agent_name
            'TestAgent'
        """
        return cls(
            success=data["success"],
            agent_name=data["agent_name"],
            action_taken=data["action_taken"],
            result=data.get("result"),
            error=data.get("error"),
            retry_recommended=data.get("retry_recommended", False),
            next_agent=data.get("next_agent"),
            metadata=data.get("metadata", {})
        )


@dataclass
class CommandClassification:
    """
    Classification result for user command routing.
    
    This dataclass contains the analysis of a user command to determine the
    optimal execution strategy - fast route vs. graph workflow, which agents
    are needed, and estimated complexity.
    
    Attributes:
        command_type: Classification of command complexity
        intent: Detected user intent (e.g., "volume_control", "send_message")
        confidence: Confidence score between 0.0 and 1.0
        requires_agents: List of agent types needed for execution
        estimated_steps: Estimated number of execution steps
        use_fast_route: Whether to use fast route execution (bypasses graph)
        metadata: Additional classification metadata
        
    Validates: Requirements 1.1, 1.4, 4.4, 5.6, 7.4
    
    Examples:
        >>> classification = CommandClassification(
        ...     command_type="simple",
        ...     intent="volume_control",
        ...     confidence=0.95,
        ...     requires_agents=["PCControlAgent"],
        ...     estimated_steps=1,
        ...     use_fast_route=True
        ... )
        >>> classification.validate()  # No exception
        >>> classification.confidence
        0.95
        
        >>> complex_classification = CommandClassification(
        ...     command_type="multi_step",
        ...     intent="send_file_whatsapp",
        ...     confidence=0.85,
        ...     requires_agents=["WhatsAppAgent", "FileSearchAgent"],
        ...     estimated_steps=4,
        ...     use_fast_route=False
        ... )
        >>> complex_classification.estimated_steps
        4
    """
    
    command_type: CommandType
    intent: str
    confidence: float
    requires_agents: list[str] = field(default_factory=list)
    estimated_steps: int = 1
    use_fast_route: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize metadata with timestamp if not provided."""
        if "timestamp" not in self.metadata:
            self.metadata["timestamp"] = datetime.now().isoformat()
    
    def validate(self) -> None:
        """
        Validate the CommandClassification fields for consistency.
        
        Checks:
        - confidence is between 0.0 and 1.0 (Requirement 1.4)
        - command_type is valid ("simple", "complex", "multi_step") (Requirement 1.1)
        - intent is not empty
        - estimated_steps is positive
        - requires_agents is a list
        - If use_fast_route=True, command_type should be "simple"
        
        Raises:
            ValueError: If validation fails
            
        Examples:
            >>> classification = CommandClassification(
            ...     command_type="simple",
            ...     intent="test",
            ...     confidence=1.5,
            ...     requires_agents=[],
            ...     estimated_steps=1
            ... )
            >>> classification.validate()
            Traceback (most recent call last):
            ...
            ValueError: confidence must be between 0.0 and 1.0, got 1.5
        """
        # Requirement 1.4: Confidence must be between 0.0 and 1.0
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(
                f"confidence must be between 0.0 and 1.0, got {self.confidence}"
            )
        
        # Requirement 1.1: command_type must be valid
        valid_types = ("simple", "complex", "multi_step")
        if self.command_type not in valid_types:
            raise ValueError(
                f"command_type must be one of {valid_types}, "
                f"got {self.command_type}"
            )
        
        # Intent should not be empty
        if not self.intent:
            raise ValueError("intent cannot be empty")
        
        # Estimated steps must be positive
        if self.estimated_steps < 1:
            raise ValueError(
                f"estimated_steps must be positive, got {self.estimated_steps}"
            )
        
        # requires_agents must be a list
        if not isinstance(self.requires_agents, list):
            raise ValueError(
                f"requires_agents must be a list, "
                f"got {type(self.requires_agents).__name__}"
            )
        
        # Fast route should only be used for simple commands
        if self.use_fast_route and self.command_type != "simple":
            raise ValueError(
                f"use_fast_route=True is only valid for command_type='simple', "
                f"got command_type='{self.command_type}'"
            )
    
    def to_dict(self) -> dict[str, Any]:
        """
        Convert CommandClassification to a dictionary.
        
        Useful for serialization and logging.
        
        Returns:
            Dictionary representation of the classification
            
        Examples:
            >>> classification = CommandClassification(
            ...     command_type="simple",
            ...     intent="test",
            ...     confidence=0.9,
            ...     requires_agents=["TestAgent"]
            ... )
            >>> d = classification.to_dict()
            >>> d["confidence"]
            0.9
            >>> d["command_type"]
            'simple'
        """
        return {
            "command_type": self.command_type,
            "intent": self.intent,
            "confidence": self.confidence,
            "requires_agents": self.requires_agents,
            "estimated_steps": self.estimated_steps,
            "use_fast_route": self.use_fast_route,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CommandClassification":
        """
        Create a CommandClassification from a dictionary.
        
        Args:
            data: Dictionary containing classification fields
            
        Returns:
            CommandClassification instance
            
        Examples:
            >>> data = {
            ...     "command_type": "simple",
            ...     "intent": "test",
            ...     "confidence": 0.8,
            ...     "requires_agents": [],
            ...     "estimated_steps": 1,
            ...     "use_fast_route": False,
            ...     "metadata": {}
            ... }
            >>> classification = CommandClassification.from_dict(data)
            >>> classification.intent
            'test'
        """
        return cls(
            command_type=data["command_type"],
            intent=data["intent"],
            confidence=data["confidence"],
            requires_agents=data.get("requires_agents", []),
            estimated_steps=data.get("estimated_steps", 1),
            use_fast_route=data.get("use_fast_route", False),
            metadata=data.get("metadata", {})
        )


# Factory functions for common response patterns

def success_response(
    agent_name: str,
    action_taken: str,
    result: Any = None,
    next_agent: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None
) -> AgentResponse:
    """
    Create a successful AgentResponse.
    
    Convenience function for creating success responses with less boilerplate.
    
    Args:
        agent_name: Name of the agent
        action_taken: Description of action performed
        result: Optional result data
        next_agent: Optional next agent suggestion
        metadata: Optional metadata dictionary
        
    Returns:
        AgentResponse with success=True
        
    Examples:
        >>> response = success_response("TestAgent", "test_action", {"data": "value"})
        >>> response.success
        True
        >>> response.error
    """
    return AgentResponse(
        success=True,
        agent_name=agent_name,
        action_taken=action_taken,
        result=result,
        error=None,
        retry_recommended=False,
        next_agent=next_agent,
        metadata=metadata or {}
    )


def error_response(
    agent_name: str,
    action_taken: str,
    error: str,
    retry_recommended: bool = False,
    result: Any = None,
    metadata: Optional[dict[str, Any]] = None
) -> AgentResponse:
    """
    Create a failed AgentResponse.
    
    Convenience function for creating error responses with less boilerplate.
    
    Args:
        agent_name: Name of the agent
        action_taken: Description of attempted action
        error: Error message
        retry_recommended: Whether retry should be attempted
        result: Optional partial result data
        metadata: Optional metadata dictionary
        
    Returns:
        AgentResponse with success=False
        
    Examples:
        >>> response = error_response(
        ...     "TestAgent",
        ...     "test_action",
        ...     "Something went wrong",
        ...     retry_recommended=True
        ... )
        >>> response.success
        False
        >>> response.retry_recommended
        True
    """
    return AgentResponse(
        success=False,
        agent_name=agent_name,
        action_taken=action_taken,
        result=result,
        error=error,
        retry_recommended=retry_recommended,
        next_agent=None,
        metadata=metadata or {}
    )


def simple_classification(
    intent: str,
    confidence: float = 0.9,
    use_fast_route: bool = True,
    requires_agents: Optional[list[str]] = None
) -> CommandClassification:
    """
    Create a simple command classification.
    
    Convenience function for creating simple command classifications.
    
    Args:
        intent: Detected intent
        confidence: Confidence score (default: 0.9)
        use_fast_route: Whether to use fast route (default: True)
        requires_agents: List of required agents (default: empty list)
        
    Returns:
        CommandClassification with command_type="simple"
        
    Examples:
        >>> classification = simple_classification("volume_control", confidence=0.95)
        >>> classification.command_type
        'simple'
        >>> classification.use_fast_route
        True
    """
    return CommandClassification(
        command_type="simple",
        intent=intent,
        confidence=confidence,
        requires_agents=requires_agents or [],
        estimated_steps=1,
        use_fast_route=use_fast_route
    )


def complex_classification(
    intent: str,
    confidence: float,
    requires_agents: list[str],
    estimated_steps: int = 2
) -> CommandClassification:
    """
    Create a complex command classification.
    
    Convenience function for creating complex command classifications.
    
    Args:
        intent: Detected intent
        confidence: Confidence score
        requires_agents: List of required agents
        estimated_steps: Estimated number of steps (default: 2)
        
    Returns:
        CommandClassification with command_type="complex"
        
    Examples:
        >>> classification = complex_classification(
        ...     "send_whatsapp",
        ...     0.85,
        ...     ["WhatsAppAgent"],
        ...     estimated_steps=2
        ... )
        >>> classification.command_type
        'complex'
        >>> classification.use_fast_route
        False
    """
    return CommandClassification(
        command_type="complex",
        intent=intent,
        confidence=confidence,
        requires_agents=requires_agents,
        estimated_steps=estimated_steps,
        use_fast_route=False
    )


def multi_step_classification(
    intent: str,
    confidence: float,
    requires_agents: list[str],
    estimated_steps: int
) -> CommandClassification:
    """
    Create a multi-step command classification.
    
    Convenience function for creating multi-step command classifications.
    
    Args:
        intent: Detected intent
        confidence: Confidence score
        requires_agents: List of required agents
        estimated_steps: Estimated number of steps
        
    Returns:
        CommandClassification with command_type="multi_step"
        
    Examples:
        >>> classification = multi_step_classification(
        ...     "screenshot_and_send",
        ...     0.8,
        ...     ["ScreenAIAgent", "WhatsAppAgent"],
        ...     estimated_steps=4
        ... )
        >>> classification.command_type
        'multi_step'
        >>> len(classification.requires_agents)
        2
    """
    return CommandClassification(
        command_type="multi_step",
        intent=intent,
        confidence=confidence,
        requires_agents=requires_agents,
        estimated_steps=estimated_steps,
        use_fast_route=False
    )
