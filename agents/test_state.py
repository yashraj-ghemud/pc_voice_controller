"""
Unit tests for WorkflowState and state management functions.

Tests validate:
- State creation and initialization
- State validation rules
- State transition functions
- Immutability guarantees
"""

import pytest
from agents.state import (
    WorkflowState,
    StateValidationError,
    validate_workflow_state,
    create_initial_state,
    is_terminal_state,
    increment_step,
    increment_retry,
    add_agent_response,
    set_final_result,
)


class TestWorkflowStateValidation:
    """Test state validation logic."""
    
    def test_valid_minimal_state(self):
        """Valid state with all required fields should pass validation."""
        state: WorkflowState = {
            "user_input": "test command",
            "command_type": "simple",
            "agent_responses": [],
            "current_step": 0,
            "retry_count": 0,
            "context": {}
        }
        
        # Should not raise
        validate_workflow_state(state)
    
    def test_valid_state_with_final_result(self):
        """Valid state with final_result should pass validation."""
        state: WorkflowState = {
            "user_input": "test command",
            "command_type": "complex",
            "agent_responses": [],
            "current_step": 5,
            "retry_count": 1,
            "context": {"key": "value"},
            "final_result": {"success": True}
        }
        
        validate_workflow_state(state)
    
    def test_missing_user_input(self):
        """State missing user_input should fail validation."""
        state = {
            "command_type": "simple",
            "agent_responses": [],
            "current_step": 0,
            "retry_count": 0,
            "context": {}
        }
        
        with pytest.raises(StateValidationError, match="Missing required field: user_input"):
            validate_workflow_state(state)
    
    def test_missing_command_type(self):
        """State missing command_type should fail validation."""
        state = {
            "user_input": "test",
            "agent_responses": [],
            "current_step": 0,
            "retry_count": 0,
            "context": {}
        }
        
        with pytest.raises(StateValidationError, match="Missing required field: command_type"):
            validate_workflow_state(state)
    
    def test_invalid_command_type(self):
        """State with invalid command_type should fail validation."""
        state: WorkflowState = {
            "user_input": "test",
            "command_type": "invalid",  # type: ignore
            "agent_responses": [],
            "current_step": 0,
            "retry_count": 0,
            "context": {}
        }
        
        with pytest.raises(StateValidationError, match="command_type must be one of"):
            validate_workflow_state(state)
    
    def test_negative_current_step(self):
        """State with negative current_step should fail validation."""
        state: WorkflowState = {
            "user_input": "test",
            "command_type": "simple",
            "agent_responses": [],
            "current_step": -1,
            "retry_count": 0,
            "context": {}
        }
        
        with pytest.raises(StateValidationError, match="current_step must be non-negative"):
            validate_workflow_state(state)
    
    def test_negative_retry_count(self):
        """State with negative retry_count should fail validation."""
        state: WorkflowState = {
            "user_input": "test",
            "command_type": "simple",
            "agent_responses": [],
            "current_step": 0,
            "retry_count": -1,
            "context": {}
        }
        
        with pytest.raises(StateValidationError, match="retry_count must be non-negative"):
            validate_workflow_state(state)
    
    def test_invalid_agent_responses_type(self):
        """State with non-list agent_responses should fail validation."""
        state: WorkflowState = {
            "user_input": "test",
            "command_type": "simple",
            "agent_responses": "not a list",  # type: ignore
            "current_step": 0,
            "retry_count": 0,
            "context": {}
        }
        
        with pytest.raises(StateValidationError, match="agent_responses must be list"):
            validate_workflow_state(state)
    
    def test_invalid_agent_response_element(self):
        """State with non-dict elements in agent_responses should fail."""
        state: WorkflowState = {
            "user_input": "test",
            "command_type": "simple",
            "agent_responses": ["not a dict"],  # type: ignore
            "current_step": 0,
            "retry_count": 0,
            "context": {}
        }
        
        with pytest.raises(StateValidationError, match="agent_responses\\[0\\] must be dict"):
            validate_workflow_state(state)
    
    def test_invalid_final_result_type(self):
        """State with non-dict final_result should fail validation."""
        state: WorkflowState = {
            "user_input": "test",
            "command_type": "simple",
            "agent_responses": [],
            "current_step": 0,
            "retry_count": 0,
            "context": {},
            "final_result": "not a dict"  # type: ignore
        }
        
        with pytest.raises(StateValidationError, match="final_result must be dict or None"):
            validate_workflow_state(state)


class TestCreateInitialState:
    """Test initial state creation."""
    
    def test_minimal_creation(self):
        """Creating state with just user_input should work."""
        state = create_initial_state("test command")
        
        assert state["user_input"] == "test command"
        assert state["command_type"] == "simple"
        assert state["agent_responses"] == []
        assert state["current_step"] == 0
        assert state["retry_count"] == 0
        assert state["context"] == {}
        assert state["final_result"] is None
    
    def test_with_command_type(self):
        """Creating state with command_type should set it correctly."""
        state = create_initial_state("test", command_type="complex")
        
        assert state["command_type"] == "complex"
    
    def test_with_context(self):
        """Creating state with context should include it."""
        context = {"key": "value", "count": 42}
        state = create_initial_state("test", context=context)
        
        assert state["context"] == context
    
    def test_creates_valid_state(self):
        """Created state should pass validation."""
        state = create_initial_state("test")
        
        # Should not raise
        validate_workflow_state(state)


class TestIsTerminalState:
    """Test terminal state detection."""
    
    def test_initial_state_not_terminal(self):
        """Initial state should not be terminal."""
        state = create_initial_state("test")
        
        assert not is_terminal_state(state)
    
    def test_state_with_none_final_result_not_terminal(self):
        """State with final_result=None is not terminal."""
        state = create_initial_state("test")
        state["final_result"] = None
        
        assert not is_terminal_state(state)
    
    def test_state_with_final_result_is_terminal(self):
        """State with final_result set is terminal."""
        state = create_initial_state("test")
        state["final_result"] = {"success": True}
        
        assert is_terminal_state(state)


class TestIncrementStep:
    """Test step counter increment."""
    
    def test_increments_from_zero(self):
        """Incrementing from 0 should give 1."""
        state = create_initial_state("test")
        assert state["current_step"] == 0
        
        new_state = increment_step(state)
        
        assert new_state["current_step"] == 1
    
    def test_increments_multiple_times(self):
        """Multiple increments should work correctly."""
        state = create_initial_state("test")
        
        state = increment_step(state)
        assert state["current_step"] == 1
        
        state = increment_step(state)
        assert state["current_step"] == 2
        
        state = increment_step(state)
        assert state["current_step"] == 3
    
    def test_immutability(self):
        """Original state should not be modified."""
        state = create_initial_state("test")
        original_step = state["current_step"]
        
        new_state = increment_step(state)
        
        assert state["current_step"] == original_step
        assert new_state["current_step"] == original_step + 1


class TestIncrementRetry:
    """Test retry counter increment."""
    
    def test_increments_from_zero(self):
        """Incrementing from 0 should give 1."""
        state = create_initial_state("test")
        assert state["retry_count"] == 0
        
        new_state = increment_retry(state)
        
        assert new_state["retry_count"] == 1
    
    def test_increments_multiple_times(self):
        """Multiple increments should work correctly."""
        state = create_initial_state("test")
        
        state = increment_retry(state)
        assert state["retry_count"] == 1
        
        state = increment_retry(state)
        assert state["retry_count"] == 2
    
    def test_immutability(self):
        """Original state should not be modified."""
        state = create_initial_state("test")
        original_retry = state["retry_count"]
        
        new_state = increment_retry(state)
        
        assert state["retry_count"] == original_retry
        assert new_state["retry_count"] == original_retry + 1


class TestAddAgentResponse:
    """Test adding agent responses to state."""
    
    def test_adds_to_empty_list(self):
        """Adding to empty agent_responses should work."""
        state = create_initial_state("test")
        response = {"agent": "TestAgent", "success": True}
        
        new_state = add_agent_response(state, response)
        
        assert len(new_state["agent_responses"]) == 1
        assert new_state["agent_responses"][0] == response
    
    def test_appends_to_existing_list(self):
        """Adding to non-empty agent_responses should append."""
        state = create_initial_state("test")
        response1 = {"agent": "Agent1", "success": True}
        response2 = {"agent": "Agent2", "success": False}
        
        state = add_agent_response(state, response1)
        state = add_agent_response(state, response2)
        
        assert len(state["agent_responses"]) == 2
        assert state["agent_responses"][0] == response1
        assert state["agent_responses"][1] == response2
    
    def test_immutability(self):
        """Original state should not be modified."""
        state = create_initial_state("test")
        response = {"agent": "TestAgent", "success": True}
        original_length = len(state["agent_responses"])
        
        new_state = add_agent_response(state, response)
        
        assert len(state["agent_responses"]) == original_length
        assert len(new_state["agent_responses"]) == original_length + 1
    
    def test_preserves_order(self):
        """Responses should be added in order."""
        state = create_initial_state("test")
        
        for i in range(5):
            response = {"index": i}
            state = add_agent_response(state, response)
        
        for i in range(5):
            assert state["agent_responses"][i]["index"] == i


class TestSetFinalResult:
    """Test setting final result."""
    
    def test_sets_final_result(self):
        """Setting final_result should work."""
        state = create_initial_state("test")
        result = {"success": True, "message": "Done"}
        
        new_state = set_final_result(state, result)
        
        assert new_state["final_result"] == result
    
    def test_makes_state_terminal(self):
        """Setting final_result should make state terminal."""
        state = create_initial_state("test")
        assert not is_terminal_state(state)
        
        new_state = set_final_result(state, {"success": True})
        
        assert is_terminal_state(new_state)
    
    def test_immutability(self):
        """Original state should not be modified."""
        state = create_initial_state("test")
        result = {"success": True}
        
        new_state = set_final_result(state, result)
        
        assert "final_result" not in state or state["final_result"] is None
        assert new_state["final_result"] == result


class TestStateTransitions:
    """Test complex state transition scenarios."""
    
    def test_typical_workflow(self):
        """Test a typical state progression."""
        # Initial state
        state = create_initial_state("volume up", command_type="simple")
        assert state["current_step"] == 0
        assert len(state["agent_responses"]) == 0
        
        # Step 1: Classify command
        state = increment_step(state)
        assert state["current_step"] == 1
        
        # Step 2: Execute with agent
        state = increment_step(state)
        response = {"agent": "PCControlAgent", "success": True, "action": "VOLUME_UP"}
        state = add_agent_response(state, response)
        assert len(state["agent_responses"]) == 1
        
        # Step 3: Finalize
        state = increment_step(state)
        state = set_final_result(state, {"success": True, "message": "Volume increased"})
        
        assert is_terminal_state(state)
        assert state["current_step"] == 3
    
    def test_retry_workflow(self):
        """Test a workflow with retries."""
        state = create_initial_state("send message")
        
        # First attempt fails
        state = increment_step(state)
        response1 = {"agent": "WhatsAppAgent", "success": False, "error": "Network error"}
        state = add_agent_response(state, response1)
        state = increment_retry(state)
        assert state["retry_count"] == 1
        
        # Second attempt succeeds
        state = increment_step(state)
        response2 = {"agent": "WhatsAppAgent", "success": True}
        state = add_agent_response(state, response2)
        
        assert len(state["agent_responses"]) == 2
        assert state["retry_count"] == 1
        assert state["current_step"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
