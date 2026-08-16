"""
Workflow state management for LangGraph orchestration.

This module defines the WorkflowState TypedDict that is passed between all nodes
in the LangGraph workflow, along with validation functions to ensure state
consistency throughout execution.

The WorkflowState is the core data structure that tracks command execution
progress, agent responses, retry attempts, and final results as the workflow
progresses through the state graph.
"""

from typing import TypedDict, Optional, Any, Literal
from typing_extensions import NotRequired


# Type alias for command types
CommandType = Literal["simple", "complex", "multi_step"]


class WorkflowState(TypedDict):
    """
    State object passed between LangGraph nodes during workflow execution.
    
    This TypedDict defines all fields that track the execution of a user command
    through the multi-agent system. State is immutable per node - each node
    returns an updated copy rather than modifying in place.
    
    Fields:
        user_input: Original transcribed text from the user
        command_type: Classification of command complexity ("simple", "complex", "multi_step")
        agent_responses: List of responses from agents that have executed
        current_step: Monotonically increasing step counter (starts at 0)
        retry_count: Number of retry attempts for the current operation
        context: Additional context data (conversation history, relevant memory, etc.)
        final_result: Result to return to user (None until workflow completes)
    
    Validates: Requirements 2.2, 2.3, 19.1, 19.4
    """
    
    user_input: str
    command_type: CommandType
    agent_responses: list[dict[str, Any]]
    current_step: int
    retry_count: int
    context: dict[str, Any]
    final_result: NotRequired[Optional[dict[str, Any]]]


class StateValidationError(Exception):
    """Raised when WorkflowState validation fails."""
    pass


def validate_workflow_state(state: WorkflowState) -> None:
    """
    Validate that a WorkflowState contains all required fields with valid values.
    
    Ensures state consistency throughout workflow execution by checking:
    - All required fields are present
    - Field types are correct
    - Field values are within valid ranges
    - Monotonic invariants hold (e.g., current_step is non-negative)
    
    Args:
        state: WorkflowState to validate
        
    Raises:
        StateValidationError: If any validation check fails
        
    Validates: Requirements 19.1, 19.3, 19.4
    
    Examples:
        >>> state = {
        ...     "user_input": "volume up",
        ...     "command_type": "simple",
        ...     "agent_responses": [],
        ...     "current_step": 0,
        ...     "retry_count": 0,
        ...     "context": {},
        ...     "final_result": None
        ... }
        >>> validate_workflow_state(state)  # No exception
        
        >>> invalid_state = {"user_input": "test"}
        >>> validate_workflow_state(invalid_state)
        Traceback (most recent call last):
        ...
        StateValidationError: Missing required field: command_type
    """
    # Check all required fields are present
    required_fields = [
        "user_input",
        "command_type",
        "agent_responses",
        "current_step",
        "retry_count",
        "context"
    ]
    
    for field in required_fields:
        if field not in state:
            raise StateValidationError(f"Missing required field: {field}")
    
    # Validate field types
    if not isinstance(state["user_input"], str):
        raise StateValidationError(
            f"user_input must be str, got {type(state['user_input']).__name__}"
        )
    
    if state["command_type"] not in ("simple", "complex", "multi_step"):
        raise StateValidationError(
            f"command_type must be one of ('simple', 'complex', 'multi_step'), "
            f"got {state['command_type']}"
        )
    
    if not isinstance(state["agent_responses"], list):
        raise StateValidationError(
            f"agent_responses must be list, got {type(state['agent_responses']).__name__}"
        )
    
    if not isinstance(state["current_step"], int):
        raise StateValidationError(
            f"current_step must be int, got {type(state['current_step']).__name__}"
        )
    
    if not isinstance(state["retry_count"], int):
        raise StateValidationError(
            f"retry_count must be int, got {type(state['retry_count']).__name__}"
        )
    
    if not isinstance(state["context"], dict):
        raise StateValidationError(
            f"context must be dict, got {type(state['context']).__name__}"
        )
    
    # Validate field values and invariants
    # Requirement 19.4: current_step must be monotonically increasing (non-negative)
    if state["current_step"] < 0:
        raise StateValidationError(
            f"current_step must be non-negative, got {state['current_step']}"
        )
    
    # Requirement 19.3: retry_count must be non-negative and within reasonable bounds
    if state["retry_count"] < 0:
        raise StateValidationError(
            f"retry_count must be non-negative, got {state['retry_count']}"
        )
    
    # Note: max_retries check is done by RetryHandler, not in state validation
    # to allow flexibility in configuration
    
    # Validate agent_responses structure
    for idx, response in enumerate(state["agent_responses"]):
        if not isinstance(response, dict):
            raise StateValidationError(
                f"agent_responses[{idx}] must be dict, got {type(response).__name__}"
            )
    
    # Validate final_result if present
    if "final_result" in state:
        final_result = state["final_result"]
        if final_result is not None and not isinstance(final_result, dict):
            raise StateValidationError(
                f"final_result must be dict or None, got {type(final_result).__name__}"
            )


def create_initial_state(
    user_input: str,
    command_type: CommandType = "simple",
    context: Optional[dict[str, Any]] = None
) -> WorkflowState:
    """
    Create a new WorkflowState with initial values.
    
    This is a convenience factory function for creating properly initialized
    workflow states at the start of command processing.
    
    Args:
        user_input: User's command text
        command_type: Classification of command complexity (default: "simple")
        context: Optional initial context data
        
    Returns:
        A validated WorkflowState ready for graph execution
        
    Examples:
        >>> state = create_initial_state("volume up")
        >>> state["current_step"]
        0
        >>> state["retry_count"]
        0
        >>> len(state["agent_responses"])
        0
    """
    state: WorkflowState = {
        "user_input": user_input,
        "command_type": command_type,
        "agent_responses": [],
        "current_step": 0,
        "retry_count": 0,
        "context": context or {},
        "final_result": None
    }
    
    validate_workflow_state(state)
    return state


def is_terminal_state(state: WorkflowState) -> bool:
    """
    Check if a WorkflowState is in a terminal state.
    
    A state is terminal when final_result has been set, indicating the
    workflow has completed successfully or failed definitively.
    
    Args:
        state: WorkflowState to check
        
    Returns:
        True if state is terminal (workflow complete), False otherwise
        
    Validates: Requirement 19.5
    
    Examples:
        >>> state = create_initial_state("test")
        >>> is_terminal_state(state)
        False
        >>> state["final_result"] = {"success": True}
        >>> is_terminal_state(state)
        True
    """
    return "final_result" in state and state["final_result"] is not None


def increment_step(state: WorkflowState) -> WorkflowState:
    """
    Create a new state with incremented current_step.
    
    Ensures monotonic step counter as required by Requirement 19.4.
    
    Args:
        state: Current workflow state
        
    Returns:
        New state with current_step incremented by 1
        
    Examples:
        >>> state = create_initial_state("test")
        >>> state["current_step"]
        0
        >>> new_state = increment_step(state)
        >>> new_state["current_step"]
        1
        >>> state["current_step"]  # Original unchanged
        0
    """
    new_state = state.copy()
    new_state["current_step"] = state["current_step"] + 1
    return new_state


def increment_retry(state: WorkflowState) -> WorkflowState:
    """
    Create a new state with incremented retry_count.
    
    Args:
        state: Current workflow state
        
    Returns:
        New state with retry_count incremented by 1
        
    Examples:
        >>> state = create_initial_state("test")
        >>> state["retry_count"]
        0
        >>> new_state = increment_retry(state)
        >>> new_state["retry_count"]
        1
    """
    new_state = state.copy()
    new_state["retry_count"] = state["retry_count"] + 1
    return new_state


def add_agent_response(
    state: WorkflowState,
    response: dict[str, Any]
) -> WorkflowState:
    """
    Add an agent response to the state's agent_responses list.
    
    Requirement 19.2: agent_responses only appends, never removes or modifies
    existing entries. This ensures a complete execution history.
    
    Args:
        state: Current workflow state
        response: Agent response dictionary to append
        
    Returns:
        New state with response appended to agent_responses
        
    Examples:
        >>> state = create_initial_state("test")
        >>> len(state["agent_responses"])
        0
        >>> response = {"agent": "test", "success": True}
        >>> new_state = add_agent_response(state, response)
        >>> len(new_state["agent_responses"])
        1
        >>> new_state["agent_responses"][0]["agent"]
        'test'
    """
    new_state = state.copy()
    # Create new list to ensure immutability
    new_state["agent_responses"] = state["agent_responses"] + [response]
    return new_state


def set_final_result(
    state: WorkflowState,
    result: dict[str, Any]
) -> WorkflowState:
    """
    Set the final_result field, marking the workflow as complete.
    
    Once final_result is set, the state is considered terminal (Requirement 19.5).
    
    Args:
        state: Current workflow state
        result: Final result dictionary to set
        
    Returns:
        New state with final_result set
        
    Examples:
        >>> state = create_initial_state("test")
        >>> is_terminal_state(state)
        False
        >>> new_state = set_final_result(state, {"success": True, "message": "Done"})
        >>> is_terminal_state(new_state)
        True
    """
    new_state = state.copy()
    new_state["final_result"] = result
    return new_state


def serialize_workflow_state(state: WorkflowState) -> str:
    """
    Serialize WorkflowState to JSON string.
    
    Converts all state fields to JSON-compatible types and serializes to string
    format for storage or transmission.
    
    Args:
        state: WorkflowState to serialize
        
    Returns:
        JSON string representation of state
        
    Validates: Requirements 28.1, 28.2
    
    Examples:
        >>> state = create_initial_state("test", "simple", {})
        >>> json_str = serialize_workflow_state(state)
        >>> isinstance(json_str, str)
        True
        >>> "user_input" in json_str
        True
    """
    import json
    
    # Create serializable dict (all fields are already JSON-compatible)
    serializable = dict(state)
    
    # Convert to JSON string with proper formatting
    return json.dumps(serializable, indent=2, ensure_ascii=False)


def deserialize_workflow_state(json_str: str) -> WorkflowState:
    """
    Deserialize JSON string back to WorkflowState.
    
    Parses JSON string and reconstructs WorkflowState TypedDict. Validates
    the result to ensure it's a valid state.
    
    Args:
        json_str: JSON string to deserialize
        
    Returns:
        WorkflowState instance
        
    Raises:
        StateValidationError: If deserialized state is invalid
        ValueError: If JSON is malformed
        
    Validates: Requirements 28.2, 28.3
    
    Examples:
        >>> state = create_initial_state("test", "simple", {})
        >>> json_str = serialize_workflow_state(state)
        >>> restored = deserialize_workflow_state(json_str)
        >>> restored["user_input"] == state["user_input"]
        True
    """
    import json
    
    # Parse JSON
    data = json.loads(json_str)
    
    # Reconstruct WorkflowState
    state: WorkflowState = {
        "user_input": data["user_input"],
        "command_type": data["command_type"],
        "agent_responses": data["agent_responses"],
        "current_step": data["current_step"],
        "retry_count": data["retry_count"],
        "context": data["context"]
    }
    
    # Add final_result if present
    if "final_result" in data:
        state["final_result"] = data["final_result"]
    
    # Validate before returning
    validate_workflow_state(state)
    
    return state


def pretty_print_state(state: WorkflowState) -> str:
    """
    Create human-readable string representation of WorkflowState.
    
    Formats state for debugging and logging purposes with proper indentation
    and field labels.
    
    Args:
        state: WorkflowState to format
        
    Returns:
        Pretty-printed string
        
    Validates: Requirement 28.4
    
    Examples:
        >>> state = create_initial_state("test", "simple", {})
        >>> output = pretty_print_state(state)
        >>> "WorkflowState" in output
        True
        >>> "user_input: test" in output
        True
    """
    lines = [
        "WorkflowState:",
        f"  user_input: {state['user_input']}",
        f"  command_type: {state['command_type']}",
        f"  current_step: {state['current_step']}",
        f"  retry_count: {state['retry_count']}",
        f"  agent_responses: [{len(state['agent_responses'])} responses]",
    ]
    
    # Show agent names if any
    if state['agent_responses']:
        agent_names = [r.get('agent_name', 'unknown') for r in state['agent_responses']]
        lines.append(f"    agents: {', '.join(agent_names)}")
    
    # Show context keys
    if state['context']:
        context_keys = list(state['context'].keys())
        lines.append(f"  context_keys: {', '.join(context_keys)}")
    
    # Show final result if present
    if 'final_result' in state and state['final_result'] is not None:
        success = state['final_result'].get('success', False)
        status = "✅" if success else "❌"
        lines.append(f"  final_result: {status}")
    
    return "\n".join(lines)
