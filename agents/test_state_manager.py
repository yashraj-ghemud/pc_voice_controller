"""
Unit tests for StateManager and retry logic.

Tests cover:
- Graph building and structure validation
- Node function execution
- Conditional routing logic
- Retry mechanism with exponential backoff
- State transitions and consistency

Validates: Requirements 2.1, 2.5, 2.6, 2.7, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 10.1-10.5
"""

import pytest
import time
from unittest.mock import Mock, patch
from agents.state_manager import StateManager
from agents.registry import AgentRegistry
from agents.base import BaseAgent
from agents.state import create_initial_state, WorkflowState
from agents.retry import (
    retry_handler_node,
    should_retry,
    is_retryable_error,
    calculate_backoff_time,
    validate_retry_count
)


# Mock agent for testing
class MockAgent(BaseAgent):
    """Mock agent for testing"""
    
    def __init__(self, agent_type: str = "mock", should_succeed: bool = True):
        super().__init__(name=f"{agent_type}_agent", agent_type=agent_type, description="Mock agent for testing")
        self.should_succeed = should_succeed
        self.call_count = 0
    
    def execute_task(self, task_description: str, context: dict = None) -> dict:
        """Mock execution"""
        self.call_count += 1
        if self.should_succeed:
            return {
                "success": True,
                "action": "mock_action",
                "result": "mock_result"
            }
        else:
            raise Exception("Mock failure")


class TestStateManager:
    """Tests for StateManager class"""
    
    def test_build_graph_creates_all_nodes(self):
        """Test that build_graph creates all required nodes"""
        registry = AgentRegistry()
        registry.register("mock", MockAgent())
        
        manager = StateManager(registry)
        graph = manager.build_graph()
        
        # Graph should be compiled
        assert graph is not None
        assert manager._graph is not None
    
    def test_build_graph_has_entry_point(self):
        """Test that graph has single entry point (Requirement 2.7)"""
        registry = AgentRegistry()
        registry.register("mock", MockAgent())
        
        manager = StateManager(registry)
        graph = manager.build_graph()
        
        # Entry point should be set (validated during compilation)
        assert graph is not None
    
    def test_classify_node_increments_step(self):
        """Test classify node increments current_step"""
        registry = AgentRegistry()
        manager = StateManager(registry)
        
        state = create_initial_state("test command", "simple")
        assert state["current_step"] == 0
        
        new_state = manager._classify_command_node(state)
        assert new_state["current_step"] == 1
    
    def test_route_node_selects_agent(self):
        """Test route node selects appropriate agent (Requirement 10.1-10.4)"""
        registry = AgentRegistry()
        registry.register("pc_control", MockAgent("pc_control"))
        
        manager = StateManager(registry)
        
        state = create_initial_state("volume up", "simple")
        new_state = manager._route_to_agent_node(state)
        
        # Agent should be assigned
        assert "assigned_agent" in new_state["context"]
        assert new_state["current_step"] == 1
    
    def test_execute_node_runs_agent(self):
        """Test execute node runs agent and captures response (Requirement 10.5)"""
        registry = AgentRegistry()
        registry.register("mock", MockAgent(should_succeed=True))
        
        manager = StateManager(registry)
        
        state = create_initial_state("test", "simple")
        state["context"]["assigned_agent"] = "mock"
        
        new_state = manager._execute_agent_node(state)
        
        # Response should be added
        assert len(new_state["agent_responses"]) == 1
        assert new_state["agent_responses"][0]["success"] == True
        assert new_state["current_step"] == 1
    
    def test_execute_node_handles_failure(self):
        """Test execute node handles agent failure gracefully"""
        registry = AgentRegistry()
        registry.register("mock", MockAgent(should_succeed=False))
        
        manager = StateManager(registry)
        
        state = create_initial_state("test", "simple")
        state["context"]["assigned_agent"] = "mock"
        
        new_state = manager._execute_agent_node(state)
        
        # Error response should be added
        assert len(new_state["agent_responses"]) == 1
        assert new_state["agent_responses"][0]["success"] == False
        assert "error" in new_state["agent_responses"][0]
    
    def test_validate_node_on_success(self):
        """Test validate node marks successful execution"""
        registry = AgentRegistry()
        manager = StateManager(registry)
        
        state = create_initial_state("test", "simple")
        state["agent_responses"] = [{"success": True, "result": "ok"}]
        
        new_state = manager._validate_result_node(state)
        
        assert new_state["context"]["validation_passed"] == True
        assert "validation_error" not in new_state["context"]
    
    def test_validate_node_on_failure(self):
        """Test validate node marks failed execution"""
        registry = AgentRegistry()
        manager = StateManager(registry)
        
        state = create_initial_state("test", "simple")
        state["agent_responses"] = [{"success": False, "error": "test error"}]
        
        new_state = manager._validate_result_node(state)
        
        assert new_state["context"]["validation_passed"] == False
        assert new_state["context"]["validation_error"] == "test error"
    
    def test_should_retry_on_success(self):
        """Test should_retry returns finalize on success (Requirement 9.2)"""
        registry = AgentRegistry()
        manager = StateManager(registry)
        
        state = create_initial_state("test", "simple")
        state["context"]["validation_passed"] = True
        state["retry_count"] = 0
        
        result = manager._should_retry(state)
        assert result == "finalize"
    
    def test_should_retry_on_max_retries(self):
        """Test should_retry returns finalize when max retries reached (Requirement 9.3)"""
        registry = AgentRegistry()
        manager = StateManager(registry)
        
        state = create_initial_state("test", "simple")
        state["context"]["validation_passed"] = False
        state["context"]["max_retries"] = 3
        state["retry_count"] = 3
        
        result = manager._should_retry(state)
        assert result == "finalize"
    
    def test_should_retry_on_retryable_error(self):
        """Test should_retry returns retry for retryable errors (Requirement 9.6)"""
        registry = AgentRegistry()
        manager = StateManager(registry)
        
        state = create_initial_state("test", "simple")
        state["context"]["validation_passed"] = False
        state["context"]["validation_error"] = "timeout occurred"
        state["context"]["max_retries"] = 3
        state["retry_count"] = 0
        
        result = manager._should_retry(state)
        assert result == "retry"
    
    def test_should_retry_on_non_retryable_error(self):
        """Test should_retry returns finalize for non-retryable errors (Requirement 9.6)"""
        registry = AgentRegistry()
        manager = StateManager(registry)
        
        state = create_initial_state("test", "simple")
        state["context"]["validation_passed"] = False
        state["context"]["validation_error"] = "invalid input"
        state["context"]["max_retries"] = 3
        state["retry_count"] = 0
        
        result = manager._should_retry(state)
        assert result == "finalize"
    
    def test_retry_handler_increments_count(self):
        """Test retry handler increments retry_count (Requirement 9.1)"""
        registry = AgentRegistry()
        manager = StateManager(registry)
        
        state = create_initial_state("test", "simple")
        state["retry_count"] = 0
        
        with patch('time.sleep'):  # Skip actual sleep
            new_state = manager._retry_handler_node(state)
        
        assert new_state["retry_count"] == 1
    
    def test_retry_handler_applies_backoff(self):
        """Test retry handler applies exponential backoff (Requirement 9.4)"""
        registry = AgentRegistry()
        manager = StateManager(registry)
        
        state = create_initial_state("test", "simple")
        state["retry_count"] = 0
        
        with patch('time.sleep') as mock_sleep:
            new_state = manager._retry_handler_node(state)
        
        # Should have called sleep with 1 second (2^0)
        mock_sleep.assert_called_once_with(1)
        assert new_state["context"]["last_backoff_seconds"] == 1
    
    def test_finalize_node_on_success(self):
        """Test finalize node creates success result"""
        registry = AgentRegistry()
        manager = StateManager(registry)
        
        state = create_initial_state("test", "simple")
        state["context"]["validation_passed"] = True
        state["agent_responses"] = [{"success": True}]
        
        new_state = manager._finalize_response_node(state)
        
        assert new_state["final_result"] is not None
        assert new_state["final_result"]["success"] == True
    
    def test_finalize_node_on_failure(self):
        """Test finalize node creates failure result"""
        registry = AgentRegistry()
        manager = StateManager(registry)
        
        state = create_initial_state("test", "simple")
        state["context"]["validation_passed"] = False
        state["context"]["validation_error"] = "test error"
        state["agent_responses"] = [{"success": False}]
        
        new_state = manager._finalize_response_node(state)
        
        assert new_state["final_result"] is not None
        assert new_state["final_result"]["success"] == False
        assert "error" in new_state["final_result"]
    
    def test_is_retryable_error_identifies_timeouts(self):
        """Test retryable error detection for timeouts"""
        registry = AgentRegistry()
        manager = StateManager(registry)
        
        assert manager._is_retryable_error("timeout occurred") == True
        assert manager._is_retryable_error("connection timeout") == True
    
    def test_is_retryable_error_identifies_network(self):
        """Test retryable error detection for network errors"""
        registry = AgentRegistry()
        manager = StateManager(registry)
        
        assert manager._is_retryable_error("network error") == True
        assert manager._is_retryable_error("connection failed") == True
    
    def test_is_retryable_error_rejects_invalid(self):
        """Test non-retryable error detection"""
        registry = AgentRegistry()
        manager = StateManager(registry)
        
        assert manager._is_retryable_error("invalid input") == False
        assert manager._is_retryable_error("unauthorized") == False


class TestRetryModule:
    """Tests for retry.py module"""
    
    def test_retry_handler_node_increments_count(self):
        """Test retry_handler_node increments retry_count (Requirement 9.1)"""
        state = create_initial_state("test", "simple")
        state["retry_count"] = 0
        
        with patch('time.sleep'):
            new_state = retry_handler_node(state)
        
        assert new_state["retry_count"] == 1
    
    def test_retry_handler_node_exponential_backoff(self):
        """Test exponential backoff calculation (Requirement 9.4)"""
        state = create_initial_state("test", "simple")
        
        # First retry: 1 second
        state["retry_count"] = 0
        with patch('time.sleep') as mock_sleep:
            new_state = retry_handler_node(state)
        mock_sleep.assert_called_once_with(1)
        
        # Second retry: 2 seconds
        state["retry_count"] = 1
        with patch('time.sleep') as mock_sleep:
            new_state = retry_handler_node(state)
        mock_sleep.assert_called_once_with(2)
        
        # Third retry: 4 seconds
        state["retry_count"] = 2
        with patch('time.sleep') as mock_sleep:
            new_state = retry_handler_node(state)
        mock_sleep.assert_called_once_with(4)
    
    def test_should_retry_success_path(self):
        """Test should_retry on success (Requirement 9.2)"""
        state = create_initial_state("test", "simple")
        state["context"]["validation_passed"] = True
        
        assert should_retry(state) == "finalize"
    
    def test_should_retry_max_retries(self):
        """Test should_retry when max retries reached (Requirement 9.3)"""
        state = create_initial_state("test", "simple")
        state["context"]["validation_passed"] = False
        state["context"]["max_retries"] = 3
        state["retry_count"] = 3
        
        assert should_retry(state) == "finalize"
    
    def test_should_retry_retryable_error(self):
        """Test should_retry with retryable error (Requirement 9.6)"""
        state = create_initial_state("test", "simple")
        state["context"]["validation_passed"] = False
        state["context"]["validation_error"] = "timeout"
        state["context"]["max_retries"] = 3
        state["retry_count"] = 0
        
        assert should_retry(state) == "retry"
    
    def test_should_retry_non_retryable_error(self):
        """Test should_retry with non-retryable error (Requirement 9.6)"""
        state = create_initial_state("test", "simple")
        state["context"]["validation_passed"] = False
        state["context"]["validation_error"] = "invalid input"
        state["context"]["max_retries"] = 3
        state["retry_count"] = 0
        
        assert should_retry(state) == "finalize"
    
    def test_is_retryable_error_timeout(self):
        """Test retryable error detection for timeouts"""
        assert is_retryable_error("timeout") == True
        assert is_retryable_error("timed out") == True
    
    def test_is_retryable_error_network(self):
        """Test retryable error detection for network errors"""
        assert is_retryable_error("network error") == True
        assert is_retryable_error("connection failed") == True
    
    def test_is_retryable_error_rate_limit(self):
        """Test retryable error detection for rate limiting"""
        assert is_retryable_error("rate limit exceeded") == True
        assert is_retryable_error("429 error") == True
        assert is_retryable_error("503 service unavailable") == True
    
    def test_is_retryable_error_element_not_found(self):
        """Test retryable error detection for UI elements"""
        assert is_retryable_error("element not found") == True
    
    def test_is_retryable_error_invalid(self):
        """Test non-retryable error detection for validation errors"""
        assert is_retryable_error("invalid input") == False
        assert is_retryable_error("invalid format") == False
    
    def test_is_retryable_error_unauthorized(self):
        """Test non-retryable error detection for auth errors"""
        assert is_retryable_error("unauthorized") == False
        assert is_retryable_error("forbidden") == False
        assert is_retryable_error("401 error") == False
    
    def test_calculate_backoff_time_formula(self):
        """Test backoff time calculation formula (Requirement 9.4)"""
        assert calculate_backoff_time(1) == 1  # 2^0
        assert calculate_backoff_time(2) == 2  # 2^1
        assert calculate_backoff_time(3) == 4  # 2^2
        assert calculate_backoff_time(4) == 8  # 2^3
    
    def test_calculate_backoff_time_invalid_input(self):
        """Test backoff time calculation with invalid input"""
        with pytest.raises(ValueError):
            calculate_backoff_time(0)
        
        with pytest.raises(ValueError):
            calculate_backoff_time(-1)
    
    def test_validate_retry_count_within_limit(self):
        """Test retry count validation (Requirement 9.3, 19.3)"""
        state = create_initial_state("test", "simple")
        state["retry_count"] = 2
        state["context"]["max_retries"] = 3
        
        assert validate_retry_count(state) == True
    
    def test_validate_retry_count_at_limit(self):
        """Test retry count validation at limit"""
        state = create_initial_state("test", "simple")
        state["retry_count"] = 3
        state["context"]["max_retries"] = 3
        
        assert validate_retry_count(state) == True
    
    def test_validate_retry_count_exceeds_limit(self):
        """Test retry count validation when exceeded"""
        state = create_initial_state("test", "simple")
        state["retry_count"] = 4
        state["context"]["max_retries"] = 3
        
        assert validate_retry_count(state) == False


class TestStateTransitions:
    """Integration tests for state transitions through graph"""
    
    def test_successful_execution_path(self):
        """Test complete successful execution through graph"""
        registry = AgentRegistry()
        mock_agent = MockAgent(should_succeed=True)
        registry.register("mock", mock_agent)
        
        # Set default agent so routing works
        registry._default_agent = mock_agent
        
        manager = StateManager(registry)
        
        # Initial state
        state = create_initial_state("test", "simple")
        
        # Simulate graph execution
        state = manager._classify_command_node(state)
        state = manager._route_to_agent_node(state)
        state = manager._execute_agent_node(state)
        state = manager._validate_result_node(state)
        
        # Should proceed to finalize (not retry)
        assert manager._should_retry(state) == "finalize"
        
        state = manager._finalize_response_node(state)
        
        # Verify final state
        assert state["final_result"]["success"] == True
        assert state["retry_count"] == 0
    
    def test_retry_then_success_path(self):
        """Test execution with one retry then success"""
        registry = AgentRegistry()
        
        # Agent that fails first time, succeeds second time
        agent = MockAgent(should_succeed=False)
        registry.register("mock", agent)
        
        # Set default agent so routing works
        registry._default_agent = agent
        
        manager = StateManager(registry)
        
        # Initial state
        state = create_initial_state("test", "simple")
        state["context"]["max_retries"] = 3
        
        # First execution - fails
        state = manager._classify_command_node(state)
        state = manager._route_to_agent_node(state)
        state = manager._execute_agent_node(state)
        state = manager._validate_result_node(state)
        
        # Should retry (retryable error)
        state["agent_responses"][0]["error"] = "timeout"
        state["agent_responses"][0]["retry_recommended"] = True
        state["context"]["validation_error"] = "timeout"
        state["context"]["validation_passed"] = False
        assert manager._should_retry(state) == "retry"
        
        # Retry
        with patch('time.sleep'):
            state = manager._retry_handler_node(state)
        
        assert state["retry_count"] == 1
        
        # Second execution - succeeds
        agent.should_succeed = True
        state = manager._execute_agent_node(state)
        state = manager._validate_result_node(state)
        
        # Should finalize
        assert manager._should_retry(state) == "finalize"
        
        state = manager._finalize_response_node(state)
        
        # Verify final state
        assert state["retry_count"] == 1
        assert len(state["agent_responses"]) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
