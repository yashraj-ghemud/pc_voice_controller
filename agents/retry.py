"""
Retry handler with exponential backoff for agent failures.

This module implements retry logic for failed agent executions, including
exponential backoff delays and retry count validation. It provides both
the retry_handler_node function and the should_retry conditional logic
used by the StateManager.

Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5, 9.6
"""

import time
from typing import Literal
from agents.state import WorkflowState


# Default maximum retry attempts
DEFAULT_MAX_RETRIES = 3


def retry_handler_node(state: WorkflowState) -> WorkflowState:
    """
    Handle retry with exponential backoff.
    
    Implements exponential backoff strategy:
    - Retry 1: 2^(1-1) = 2^0 = 1 second
    - Retry 2: 2^(2-1) = 2^1 = 2 seconds  
    - Retry 3: 2^(3-1) = 2^2 = 4 seconds
    
    The retry_count is incremented before applying backoff, then the
    current_step is incremented to track graph progression.
    
    PRECONDITIONS:
    - Retry is recommended (validation failed)
    - state["retry_count"] < max_retries
    
    POSTCONDITIONS:
    - state["retry_count"] incremented by 1
    - Backoff delay applied (blocking)
    - state["current_step"] incremented
    - Backoff duration stored in context for observability
    
    Args:
        state: Current workflow state after validation failure
        
    Returns:
        Updated state with incremented retry_count and current_step
        
    Validates: Requirements 9.1, 9.2, 9.4, 9.5, 9.6
    
    Examples:
        >>> state = {
        ...     "user_input": "test",
        ...     "command_type": "simple",
        ...     "agent_responses": [{"success": False, "error": "timeout"}],
        ...     "current_step": 4,
        ...     "retry_count": 0,
        ...     "context": {"max_retries": 3},
        ...     "final_result": None
        ... }
        >>> new_state = retry_handler_node(state)
        >>> new_state["retry_count"]
        1
        >>> new_state["context"]["last_backoff_seconds"]
        1
        
        >>> # Second retry
        >>> state["retry_count"] = 1
        >>> new_state = retry_handler_node(state)
        >>> new_state["retry_count"]
        2
        >>> new_state["context"]["last_backoff_seconds"]
        2
    """
    # Increment retry count
    new_retry_count = state["retry_count"] + 1
    
    # Calculate exponential backoff: 2^(retry_count - 1)
    # This ensures: retry 1 = 1s, retry 2 = 2s, retry 3 = 4s
    backoff_seconds = 2 ** (new_retry_count - 1)
    
    # Create updated state
    new_state = state.copy()
    new_state["retry_count"] = new_retry_count
    new_state["current_step"] = state["current_step"] + 1
    
    # Update context with backoff info for observability
    new_state["context"] = state["context"].copy()
    new_state["context"]["last_backoff_seconds"] = backoff_seconds
    new_state["context"]["retry_timestamp"] = time.time()
    
    # Apply backoff delay (blocking)
    time.sleep(backoff_seconds)
    
    return new_state


def should_retry(state: WorkflowState) -> Literal["retry", "finalize"]:
    """
    Determine if failed execution should retry.
    
    Evaluates retry conditions:
    1. If validation passed → finalize (success)
    2. If retry_count >= max_retries → finalize (exhausted retries)
    3. If error is not retryable → finalize (permanent failure)
    4. Otherwise → retry (transient failure worth retrying)
    
    PRECONDITIONS:
    - state["agent_responses"] contains at least one response
    - state["retry_count"] is non-negative
    - state["context"]["validation_passed"] is set
    
    POSTCONDITIONS:
    - Returns "retry" if retry conditions met
    - Returns "finalize" if max retries reached or not retryable
    
    Args:
        state: Current workflow state after validation
        
    Returns:
        "retry" to loop back to execute node, "finalize" to complete
        
    Validates: Requirements 9.2, 9.3, 9.6
    
    Examples:
        >>> # Success case - no retry needed
        >>> state = {
        ...     "agent_responses": [{"success": True}],
        ...     "retry_count": 0,
        ...     "context": {"validation_passed": True, "max_retries": 3}
        ... }
        >>> should_retry(state)
        'finalize'
        
        >>> # Failure with retries available
        >>> state = {
        ...     "agent_responses": [{"success": False, "error": "timeout"}],
        ...     "retry_count": 0,
        ...     "context": {"validation_passed": False, "validation_error": "timeout", "max_retries": 3}
        ... }
        >>> should_retry(state)
        'retry'
        
        >>> # Max retries exhausted
        >>> state = {
        ...     "agent_responses": [{"success": False}],
        ...     "retry_count": 3,
        ...     "context": {"validation_passed": False, "max_retries": 3}
        ... }
        >>> should_retry(state)
        'finalize'
        
        >>> # Non-retryable error
        >>> state = {
        ...     "agent_responses": [{"success": False}],
        ...     "retry_count": 0,
        ...     "context": {"validation_passed": False, "validation_error": "invalid input", "max_retries": 3}
        ... }
        >>> should_retry(state)
        'finalize'
    """
    # Check if validation passed (success path)
    if state["context"].get("validation_passed", False):
        return "finalize"
    
    # Get max_retries from context (default to 3)
    max_retries = state["context"].get("max_retries", DEFAULT_MAX_RETRIES)
    
    # Check if retry count exceeded (Requirement 9.3)
    if state["retry_count"] >= max_retries:
        return "finalize"
    
    # Check if error is retryable (Requirement 9.6)
    error = state["context"].get("validation_error", "")
    if not is_retryable_error(error):
        return "finalize"
    
    # Conditions met for retry
    return "retry"


def is_retryable_error(error: str) -> bool:
    """
    Determine if an error is retryable.
    
    Classifies errors into retryable (transient) and non-retryable (permanent).
    
    Retryable errors include:
    - Network timeouts and connection issues
    - Rate limiting (429, 503)
    - Temporary unavailability
    - UI element not found (may appear after delay)
    
    Non-retryable errors include:
    - Invalid input / validation errors
    - Authorization failures
    - Resource not found (permanent)
    - Logic errors
    
    Args:
        error: Error message string
        
    Returns:
        True if error should be retried, False otherwise
        
    Validates: Requirements 9.6
    
    Examples:
        >>> is_retryable_error("timeout occurred")
        True
        >>> is_retryable_error("network connection failed")
        True
        >>> is_retryable_error("rate limit exceeded")
        True
        >>> is_retryable_error("invalid input format")
        False
        >>> is_retryable_error("unauthorized access")
        False
    """
    if not error:
        # Empty error string - not retryable
        return False
    
    error_lower = error.lower()
    
    # Retryable patterns (transient errors)
    retryable_patterns = [
        "timeout",
        "timed out",
        "network",
        "connection",
        "rate limit",
        "rate_limit",
        "429",
        "503",
        "502",
        "504",
        "element not found",
        "not found",
        "temporarily unavailable",
        "temporary failure",
        "try again",
        "retry"
    ]
    
    # Check if any retryable pattern matches
    for pattern in retryable_patterns:
        if pattern in error_lower:
            return True
    
    # Non-retryable patterns (permanent errors)
    non_retryable_patterns = [
        "invalid",
        "unauthorized",
        "forbidden",
        "401",
        "403",
        "400",
        "not allowed",
        "permission denied"
    ]
    
    # Explicitly check non-retryable patterns
    for pattern in non_retryable_patterns:
        if pattern in error_lower:
            return False
    
    # Default: not retryable if no pattern matched
    # Conservative approach - only retry known transient errors
    return False


def get_max_retries(state: WorkflowState) -> int:
    """
    Get max_retries from state context or return default.
    
    Args:
        state: Current workflow state
        
    Returns:
        Maximum retry attempts allowed
        
    Examples:
        >>> state = {"context": {"max_retries": 5}}
        >>> get_max_retries(state)
        5
        >>> state = {"context": {}}
        >>> get_max_retries(state)
        3
    """
    return state["context"].get("max_retries", DEFAULT_MAX_RETRIES)


def validate_retry_count(state: WorkflowState) -> bool:
    """
    Validate that retry_count never exceeds max_retries.
    
    This is a validation function that can be used in tests and assertions
    to ensure the retry count invariant is maintained.
    
    Args:
        state: Current workflow state
        
    Returns:
        True if retry_count <= max_retries, False otherwise
        
    Validates: Requirements 9.3, 19.3
    
    Examples:
        >>> state = {"retry_count": 2, "context": {"max_retries": 3}}
        >>> validate_retry_count(state)
        True
        >>> state = {"retry_count": 4, "context": {"max_retries": 3}}
        >>> validate_retry_count(state)
        False
    """
    retry_count = state["retry_count"]
    max_retries = get_max_retries(state)
    return retry_count <= max_retries


def calculate_backoff_time(retry_count: int) -> int:
    """
    Calculate exponential backoff time for a given retry count.
    
    Formula: 2^(retry_count - 1) seconds
    
    Args:
        retry_count: Current retry attempt (1-indexed)
        
    Returns:
        Backoff time in seconds
        
    Validates: Requirements 9.4
    
    Examples:
        >>> calculate_backoff_time(1)
        1
        >>> calculate_backoff_time(2)
        2
        >>> calculate_backoff_time(3)
        4
        >>> calculate_backoff_time(4)
        8
    """
    if retry_count < 1:
        raise ValueError(f"retry_count must be >= 1, got {retry_count}")
    
    return 2 ** (retry_count - 1)
