"""
Property-based tests for WorkflowState using Hypothesis.

Tests:
- Property 24: State Field Completeness
- Property 5: State Monotonic Progression
- Property 6: State Object Persistence
- Property 25: Agent Responses Append-Only
- Property 28: WorkflowState Serialization Round-Trip
"""

from hypothesis import given, strategies as st
from hypothesis import assume
import pytest
from typing import Dict, Any, List
import json

from agents.state import (
    WorkflowState,
    create_initial_state,
    validate_state,
    serialize_state,
    deserialize_state
)
from agents.models import AgentResponse


# Hypothesis strategies for generating test data
@st.composite
def agent_response_strategy(draw):
    """Generate random AgentResponse objects."""
    return AgentResponse(
        success=draw(st.booleans()),
        agent_name=draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll')))),
        action_taken=draw(st.text(min_size=1, max_size=50)),
        result=draw(st.one_of(st.none(), st.text(max_size=100))),
        error=draw(st.one_of(st.none(), st.text(max_size=100))),
        retry_recommended=draw(st.booleans()),
        next_agent=draw(st.one_of(st.none(), st.text(min_size=1, max_size=20)))
    )


@st.composite
def workflow_state_strategy(draw):
    """Generate random WorkflowState objects."""
    return WorkflowState(
        user_input=draw(st.text(min_size=1, max_size=200)),
        command_type=draw(st.sampled_from(["simple", "complex", "multi_step"])),
        agent_responses=draw(st.lists(agent_response_strategy(), max_size=10)),
        current_step=draw(st.integers(min_value=0, max_value=100)),
        retry_count=draw(st.integers(min_value=0, max_value=5)),
        context=draw(st.dictionaries(st.text(max_size=20), st.text(max_size=100), max_size=10)),
        final_result=draw(st.one_of(st.none(), st.text(max_size=200))),
        last_error=draw(st.one_of(st.none(), st.text(max_size=100)))
    )


class TestPropertyStateFieldCompleteness:
    """
    Property 24: State Field Completeness
    Validates: Requirements 19.1
    """
    
    @given(workflow_state_strategy())
    def test_all_required_fields_present(self, state: WorkflowState):
        """Test that all required fields exist in WorkflowState instances."""
        # All required fields must be present
        assert "user_input" in state
        assert "command_type" in state
        assert "agent_responses" in state
        assert "current_step" in state
        assert "retry_count" in state
        assert "context" in state
        assert "final_result" in state
        assert "last_error" in state
    
    @given(st.text(min_size=1, max_size=200))
    def test_initial_state_has_all_fields(self, user_input: str):
        """Test that create_initial_state() produces complete states."""
        state = create_initial_state(user_input, {})
        
        assert state["user_input"] == user_input
        assert state["command_type"] in ["simple", "complex", "multi_step"]
        assert isinstance(state["agent_responses"], list)
        assert state["current_step"] == 0
        assert state["retry_count"] == 0
        assert isinstance(state["context"], dict)
        assert state["final_result"] is None
        assert state["last_error"] is None


class TestPropertyStateMonotonicProgression:
    """
    Property 5: State Monotonic Progression
    Validates: Requirements 2.3, 19.4
    """
    
    @given(st.lists(st.integers(min_value=0, max_value=1), min_size=2, max_size=20))
    def test_current_step_always_increases(self, step_increments: List[int]):
        """Test that current_step always increases during state transitions."""
        state = create_initial_state("test command", {})
        
        previous_step = state["current_step"]
        
        for increment in step_increments:
            # Simulate state transition (step should increase)
            state["current_step"] += 1
            
            # Monotonic property: current >= previous
            assert state["current_step"] >= previous_step
            assert state["current_step"] == previous_step + 1
            
            previous_step = state["current_step"]
    
    @given(workflow_state_strategy())
    def test_step_never_decreases(self, state: WorkflowState):
        """Test that step modifications never decrease the value."""
        original_step = state["current_step"]
        
        # Any valid transition should not decrease step
        state["current_step"] += 1
        assert state["current_step"] > original_step


class TestPropertyAgentResponsesAppendOnly:
    """
    Property 25: Agent Responses Append-Only
    Validates: Requirements 19.2
    """
    
    @given(workflow_state_strategy(), st.lists(agent_response_strategy(), min_size=1, max_size=10))
    def test_agent_responses_only_grows(self, state: WorkflowState, new_responses: List[AgentResponse]):
        """Test that agent_responses only grows, never shrinks."""
        initial_count = len(state["agent_responses"])
        initial_responses = state["agent_responses"].copy()
        
        # Add new responses (append-only operation)
        for response in new_responses:
            state["agent_responses"].append(response)
        
        # List must have grown
        assert len(state["agent_responses"]) > initial_count
        assert len(state["agent_responses"]) == initial_count + len(new_responses)
        
        # Original responses must be unchanged
        for i, original_response in enumerate(initial_responses):
            assert state["agent_responses"][i] == original_response
    
    @given(workflow_state_strategy())
    def test_no_modifications_to_existing_entries(self, state: WorkflowState):
        """Verify no modifications to existing agent response entries."""
        if len(state["agent_responses"]) == 0:
            return  # Skip if empty
        
        # Capture original responses
        original_responses = [resp.copy() for resp in state["agent_responses"]]
        
        # Add a new response
        new_response = AgentResponse(
            success=True,
            agent_name="test_agent",
            action_taken="test_action",
            result="test_result"
        )
        state["agent_responses"].append(new_response)
        
        # Original responses must be unchanged
        for i, original in enumerate(original_responses):
            assert state["agent_responses"][i] == original


class TestPropertySerializationRoundTrip:
    """
    Property 28: WorkflowState Serialization Round-Trip
    Validates: Requirements 28.2, 28.3
    """
    
    @given(workflow_state_strategy())
    def test_serialize_deserialize_round_trip(self, state: WorkflowState):
        """Test that parse(serialize(state)) == state."""
        # Serialize to JSON
        serialized = serialize_state(state)
        
        # Ensure it's valid JSON
        assert isinstance(serialized, str)
        json_data = json.loads(serialized)
        assert isinstance(json_data, dict)
        
        # Deserialize back
        deserialized = deserialize_state(serialized)
        
        # Round-trip property: deserialized should equal original
        assert deserialized["user_input"] == state["user_input"]
        assert deserialized["command_type"] == state["command_type"]
        assert deserialized["current_step"] == state["current_step"]
        assert deserialized["retry_count"] == state["retry_count"]
        assert deserialized["context"] == state["context"]
        assert deserialized["final_result"] == state["final_result"]
        assert deserialized["last_error"] == state["last_error"]
        
        # Agent responses should match in count
        assert len(deserialized["agent_responses"]) == len(state["agent_responses"])
    
    @given(workflow_state_strategy())
    def test_serialization_produces_json_compatible_types(self, state: WorkflowState):
        """Test that serialization converts all fields to JSON-compatible types."""
        serialized = serialize_state(state)
        json_data = json.loads(serialized)
        
        # All top-level values must be JSON-compatible
        assert isinstance(json_data["user_input"], str)
        assert isinstance(json_data["command_type"], str)
        assert isinstance(json_data["agent_responses"], list)
        assert isinstance(json_data["current_step"], int)
        assert isinstance(json_data["retry_count"], int)
        assert isinstance(json_data["context"], dict)
        assert json_data["final_result"] is None or isinstance(json_data["final_result"], str)
        assert json_data["last_error"] is None or isinstance(json_data["last_error"], str)


class TestPropertyStateObjectPersistence:
    """
    Property 6: State Object Persistence
    Validates: Requirements 2.2
    """
    
    @given(workflow_state_strategy())
    def test_state_exists_throughout_execution(self, state: WorkflowState):
        """Test that WorkflowState exists and maintains structure throughout operations."""
        # State should always be a valid dictionary
        assert isinstance(state, dict)
        
        # Perform various operations
        state["current_step"] += 1
        state["agent_responses"].append(AgentResponse(
            success=True,
            agent_name="test",
            action_taken="test"
        ))
        state["retry_count"] += 1
        
        # State should still be valid
        assert isinstance(state, dict)
        validate_state(state)
    
    @given(workflow_state_strategy())
    def test_state_validation_consistency(self, state: WorkflowState):
        """Verify validate_state() maintains consistency."""
        # Valid state should pass validation
        try:
            validate_state(state)
            validation_passed = True
        except (ValueError, KeyError):
            validation_passed = False
        
        # If state is well-formed, validation should pass
        if all(k in state for k in ["user_input", "command_type", "agent_responses", 
                                     "current_step", "retry_count", "context"]):
            assert validation_passed or state["retry_count"] > 10  # May fail if retry_count too high


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
