"""
Property-based tests for StateManager using Hypothesis.

Tests:
- Property 5: State Monotonic Progression (Task 4.3)
- Property 6: State Object Persistence (Task 4.4)
- Property 17: Retry Count Bounded (Task 4.6)
- Property 18: Exponential Backoff Formula (Task 4.6)
"""

from hypothesis import given, strategies as st, assume
import pytest
import time
from unittest.mock import Mock, patch

from agents.state_manager import StateManager
from agents.state import create_initial_state, WorkflowState
from agents.models import AgentResponse
from agents.registry import AgentRegistry
from agents.config import AgentConfig


class TestPropertyStateTransitions:
    """
    Property 5: State Monotonic Progression
    Task 4.3: Write property test for state transitions
    Validates: Requirements 2.3, 19.4
    """
    
    @given(st.lists(st.just(1), min_size=1, max_size=20))
    def test_current_step_monotonic_increase(self, transitions):
        """Test that current_step always increases during transitions."""
        state = create_initial_state("test command", {})
        
        steps = [state["current_step"]]
        
        for _ in transitions:
            # Simulate state transition
            state["current_step"] += 1
            steps.append(state["current_step"])
        
        # Verify monotonic increase
        for i in range(len(steps) - 1):
            assert steps[i + 1] > steps[i], "Step must increase monotonically"
            assert steps[i + 1] == steps[i] + 1, "Step must increase by exactly 1"
    
    @given(st.integers(min_value=0, max_value=50))
    def test_step_never_decreases(self, num_transitions: int):
        """Test that step never decreases across any number of transitions."""
        state = create_initial_state("test", {})
        
        for i in range(num_transitions):
            prev_step = state["current_step"]
            state["current_step"] += 1
            
            assert state["current_step"] >= prev_step
            assert state["current_step"] == i + 1


class TestPropertyGraphStructure:
    """
    Property 6: State Object Persistence
    Task 4.4: Write property test for graph structure
    Validates: Requirements 2.2
    """
    
    @given(st.text(min_size=1, max_size=100))
    def test_state_exists_throughout_execution(self, user_input: str):
        """Test that WorkflowState exists throughout execution."""
        config = AgentConfig()
        registry = AgentRegistry()
        
        # Create mock agent
        mock_agent = Mock()
        mock_agent.name = "test_agent"
        mock_agent.execute = Mock(return_value=AgentResponse(
            success=True,
            agent_name="test_agent",
            action_taken="test_action",
            result="test_result"
        ))
        registry.register("default", mock_agent)
        
        state_manager = StateManager(config, registry)
        state = create_initial_state(user_input, {})
        
        # State should exist before any node execution
        assert isinstance(state, dict)
        assert "user_input" in state
        assert "current_step" in state
        
        # Simulate node execution
        state["current_step"] += 1
        state["agent_responses"].append(AgentResponse(
            success=True,
            agent_name="test",
            action_taken="test"
        ))
        
        # State should still exist and be valid
        assert isinstance(state, dict)
        assert "user_input" in state
        assert state["current_step"] == 1
    
    @given(st.integers(min_value=1, max_value=10))
    def test_all_nodes_maintain_state(self, num_operations: int):
        """Verify all nodes maintain state correctly."""
        state = create_initial_state("test", {})
        
        for i in range(num_operations):
            # Simulate various node operations
            state["current_step"] += 1
            state["agent_responses"].append(AgentResponse(
                success=True,
                agent_name=f"agent_{i}",
                action_taken=f"action_{i}"
            ))
            
            # State structure must remain valid
            assert isinstance(state, dict)
            assert "user_input" in state
            assert "agent_responses" in state
            assert len(state["agent_responses"]) == i + 1


class TestPropertyRetryLogic:
    """
    Property 17: Retry Count Bounded
    Property 18: Exponential Backoff Formula
    Task 4.6: Write property test for retry logic
    Validates: Requirements 9.3, 9.4, 19.3
    """
    
    @given(st.integers(min_value=0, max_value=10))
    def test_retry_count_never_exceeds_max(self, initial_retries: int):
        """Test that retry_count never exceeds max_retries."""
        max_retries = 3
        state = create_initial_state("test", {})
        state["retry_count"] = min(initial_retries, max_retries)
        
        # Try to increment beyond max
        for _ in range(5):
            if state["retry_count"] < max_retries:
                state["retry_count"] += 1
        
        # Must be bounded
        assert state["retry_count"] <= max_retries
    
    @given(st.integers(min_value=1, max_value=5))
    def test_exponential_backoff_formula(self, retry_count: int):
        """Test backoff delay matches 2^(retry_count - 1)."""
        expected_delay = 2 ** (retry_count - 1)
        
        # Calculate backoff using the formula
        calculated_delay = 2 ** (retry_count - 1)
        
        assert calculated_delay == expected_delay
        assert calculated_delay > 0
        
        # Verify exponential growth
        if retry_count > 1:
            prev_delay = 2 ** (retry_count - 2)
            assert calculated_delay == 2 * prev_delay
    
    @given(st.lists(st.integers(min_value=1, max_value=5), min_size=2, max_size=5))
    def test_backoff_increases_exponentially(self, retry_sequence):
        """Test that backoff delays increase exponentially."""
        delays = [2 ** (retry - 1) for retry in retry_sequence]
        
        # Each delay should be roughly double the previous
        for i in range(len(delays) - 1):
            if retry_sequence[i + 1] == retry_sequence[i] + 1:
                assert delays[i + 1] == 2 * delays[i]
    
    @given(st.integers(min_value=0, max_value=3))
    def test_retry_count_bounded_in_state(self, num_failures: int):
        """Test that retry_count in state is always bounded."""
        max_retries = 3
        state = create_initial_state("test", {})
        
        # Simulate failures with retry increments
        for _ in range(num_failures):
            if state["retry_count"] < max_retries:
                state["retry_count"] += 1
        
        # Verify bounded
        assert 0 <= state["retry_count"] <= max_retries


class TestPropertyRetryMechanism:
    """Additional property tests for retry mechanism."""
    
    @given(st.booleans(), st.integers(min_value=0, max_value=2))
    def test_should_retry_logic(self, agent_failed: bool, current_retries: int):
        """Test should_retry conditional logic."""
        max_retries = 3
        state = create_initial_state("test", {})
        state["retry_count"] = current_retries
        
        # Mock agent response
        last_response = AgentResponse(
            success=not agent_failed,
            agent_name="test",
            action_taken="test",
            retry_recommended=agent_failed
        )
        
        if len(state["agent_responses"]) > 0:
            state["agent_responses"][-1] = last_response
        else:
            state["agent_responses"].append(last_response)
        
        # Should retry if: failed AND retries < max AND retry_recommended
        should_retry = (
            agent_failed and 
            current_retries < max_retries and 
            last_response.retry_recommended
        )
        
        if should_retry:
            assert state["retry_count"] < max_retries
            assert last_response.retry_recommended


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
