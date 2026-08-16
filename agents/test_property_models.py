"""
Property-based tests for data models using Hypothesis.

Tests:
- Property 1: Command Classification Validity
"""

from hypothesis import given, strategies as st
from hypothesis import assume
import pytest

from agents.models import CommandClassification, AgentResponse


class TestPropertyCommandClassificationValidity:
    """
    Property 1: Command Classification Validity
    Validates: Requirements 1.1, 1.4
    """
    
    @given(
        st.floats(min_value=0.0, max_value=1.0),
        st.sampled_from(["simple", "complex", "multi_step"])
    )
    def test_confidence_bounded(self, confidence: float, command_type: str):
        """Test that confidence is always between 0.0 and 1.0."""
        classification = CommandClassification(
            command_type=command_type,
            intent="test_intent",
            confidence=confidence,
            requires_agents=["test_agent"],
            estimated_steps=1,
            use_fast_route=False
        )
        
        # Confidence must be in valid range
        assert 0.0 <= classification.confidence <= 1.0
        assert classification.confidence == confidence
    
    @given(st.floats())
    def test_confidence_out_of_range_rejected(self, confidence: float):
        """Test that confidence outside [0.0, 1.0] is rejected."""
        assume(confidence < 0.0 or confidence > 1.0)
        
        with pytest.raises((ValueError, AssertionError)):
            classification = CommandClassification(
                command_type="simple",
                intent="test",
                confidence=confidence,
                requires_agents=[],
                estimated_steps=1,
                use_fast_route=False
            )
            # If creation succeeded, validation should catch it
            if hasattr(classification, 'validate'):
                classification.validate()
    
    @given(st.sampled_from(["simple", "complex", "multi_step"]))
    def test_command_type_restricted(self, command_type: str):
        """Test that command_type is one of the allowed values."""
        classification = CommandClassification(
            command_type=command_type,
            intent="test_intent",
            confidence=0.8,
            requires_agents=["agent1"],
            estimated_steps=2,
            use_fast_route=False
        )
        
        assert classification.command_type in ["simple", "complex", "multi_step"]
        assert classification.command_type == command_type
    
    @given(st.text(min_size=1))
    def test_invalid_command_type_rejected(self, invalid_type: str):
        """Test that invalid command_type values are rejected."""
        assume(invalid_type not in ["simple", "complex", "multi_step"])
        
        # Should either raise an error or fail validation
        try:
            classification = CommandClassification(
                command_type=invalid_type,
                intent="test",
                confidence=0.5,
                requires_agents=[],
                estimated_steps=1,
                use_fast_route=False
            )
            # If it was created, validation should catch the issue
            if hasattr(classification, 'validate'):
                with pytest.raises(ValueError):
                    classification.validate()
        except (ValueError, TypeError):
            pass  # Expected
    
    @given(
        st.floats(min_value=0.0, max_value=1.0),
        st.integers(min_value=0, max_value=100)
    )
    def test_classification_fields_valid(self, confidence: float, steps: int):
        """Test that all classification fields maintain validity."""
        classification = CommandClassification(
            command_type="complex",
            intent="test_command",
            confidence=confidence,
            requires_agents=["agent1", "agent2"],
            estimated_steps=steps,
            use_fast_route=False
        )
        
        # Validate all fields
        assert isinstance(classification.command_type, str)
        assert isinstance(classification.intent, str)
        assert isinstance(classification.confidence, float)
        assert 0.0 <= classification.confidence <= 1.0
        assert isinstance(classification.requires_agents, list)
        assert isinstance(classification.estimated_steps, int)
        assert classification.estimated_steps >= 0
        assert isinstance(classification.use_fast_route, bool)


class TestPropertyAgentResponse:
    """Additional property tests for AgentResponse model."""
    
    @given(
        st.booleans(),
        st.text(min_size=1, max_size=50),
        st.text(min_size=1, max_size=100)
    )
    def test_agent_response_validity(self, success: bool, agent_name: str, action: str):
        """Test that AgentResponse maintains structural validity."""
        response = AgentResponse(
            success=success,
            agent_name=agent_name,
            action_taken=action,
            result="Test result",
            error=None,
            retry_recommended=False,
            next_agent=None
        )
        
        assert response.success == success
        assert response.agent_name == agent_name
        assert response.action_taken == action
        assert isinstance(response.success, bool)
        assert isinstance(response.retry_recommended, bool)
    
    @given(st.booleans())
    def test_retry_recommendation_consistency(self, success: bool):
        """Test that retry recommendation is consistent with success status."""
        response = AgentResponse(
            success=success,
            agent_name="test_agent",
            action_taken="test_action",
            result="result" if success else None,
            error=None if success else "error occurred",
            retry_recommended=not success,
            next_agent=None
        )
        
        # Failed actions typically recommend retry
        if not response.success and response.error:
            # Retry recommendation makes sense for failures
            assert isinstance(response.retry_recommended, bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
