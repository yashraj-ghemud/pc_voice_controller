"""
Unit tests for AgentResponse and CommandClassification data models.

Tests validate:
- Model creation and validation
- Field constraints and invariants
- Serialization/deserialization
- Factory function behavior
"""

import pytest
from agents.models import (
    AgentResponse,
    CommandClassification,
    success_response,
    error_response,
    simple_classification,
    complex_classification,
    multi_step_classification,
)


class TestAgentResponse:
    """Test AgentResponse dataclass."""
    
    def test_valid_success_response(self):
        """Valid success response should pass validation."""
        response = AgentResponse(
            success=True,
            agent_name="TestAgent",
            action_taken="test_action",
            result={"key": "value"},
            error=None,
            retry_recommended=False
        )
        
        response.validate()  # Should not raise
    
    def test_valid_error_response(self):
        """Valid error response should pass validation."""
        response = AgentResponse(
            success=False,
            agent_name="TestAgent",
            action_taken="test_action",
            result=None,
            error="Something went wrong",
            retry_recommended=True
        )
        
        response.validate()  # Should not raise
    
    def test_empty_agent_name_fails(self):
        """Empty agent_name should fail validation."""
        response = AgentResponse(
            success=True,
            agent_name="",
            action_taken="test",
            error=None
        )
        
        with pytest.raises(ValueError, match="agent_name cannot be empty"):
            response.validate()
    
    def test_empty_action_taken_fails(self):
        """Empty action_taken should fail validation."""
        response = AgentResponse(
            success=True,
            agent_name="TestAgent",
            action_taken="",
            error=None
        )
        
        with pytest.raises(ValueError, match="action_taken cannot be empty"):
            response.validate()
    
    def test_success_with_error_fails(self):
        """success=True with error set should fail validation."""
        response = AgentResponse(
            success=True,
            agent_name="TestAgent",
            action_taken="test",
            error="This shouldn't be here"
        )
        
        with pytest.raises(ValueError, match="error should be None when success=True"):
            response.validate()
    
    def test_failure_without_error_fails(self):
        """success=False without error should fail validation."""
        response = AgentResponse(
            success=False,
            agent_name="TestAgent",
            action_taken="test",
            error=None
        )
        
        with pytest.raises(ValueError, match="error must be provided when success=False"):
            response.validate()
    
    def test_retry_recommended_on_success_fails(self):
        """retry_recommended=True with success=True should fail."""
        response = AgentResponse(
            success=True,
            agent_name="TestAgent",
            action_taken="test",
            error=None,
            retry_recommended=True
        )
        
        with pytest.raises(ValueError, match="retry_recommended=True is invalid when success=True"):
            response.validate()
    
    def test_metadata_includes_timestamp(self):
        """Response should automatically include timestamp in metadata."""
        response = AgentResponse(
            success=True,
            agent_name="TestAgent",
            action_taken="test",
            error=None
        )
        
        assert "timestamp" in response.metadata
    
    def test_to_dict(self):
        """Response should convert to dict correctly."""
        response = AgentResponse(
            success=True,
            agent_name="TestAgent",
            action_taken="test_action",
            result={"data": "value"},
            error=None,
            retry_recommended=False,
            next_agent="NextAgent",
            metadata={"custom": "field"}
        )
        
        d = response.to_dict()
        
        assert d["success"] is True
        assert d["agent_name"] == "TestAgent"
        assert d["action_taken"] == "test_action"
        assert d["result"] == {"data": "value"}
        assert d["error"] is None
        assert d["retry_recommended"] is False
        assert d["next_agent"] == "NextAgent"
        assert "custom" in d["metadata"]
    
    def test_from_dict(self):
        """Response should be created from dict correctly."""
        data = {
            "success": True,
            "agent_name": "TestAgent",
            "action_taken": "test_action",
            "result": {"key": "value"},
            "error": None,
            "retry_recommended": False,
            "next_agent": "NextAgent",
            "metadata": {"custom": "field"}
        }
        
        response = AgentResponse.from_dict(data)
        
        assert response.success is True
        assert response.agent_name == "TestAgent"
        assert response.action_taken == "test_action"
        assert response.result == {"key": "value"}
        assert response.error is None
        assert response.retry_recommended is False
        assert response.next_agent == "NextAgent"
    
    def test_round_trip_serialization(self):
        """Serialization and deserialization should be reversible."""
        original = AgentResponse(
            success=False,
            agent_name="TestAgent",
            action_taken="test",
            result=None,
            error="Error occurred",
            retry_recommended=True,
            metadata={"key": "value"}
        )
        
        data = original.to_dict()
        restored = AgentResponse.from_dict(data)
        
        assert restored.success == original.success
        assert restored.agent_name == original.agent_name
        assert restored.action_taken == original.action_taken
        assert restored.error == original.error
        assert restored.retry_recommended == original.retry_recommended


class TestCommandClassification:
    """Test CommandClassification dataclass."""
    
    def test_valid_simple_classification(self):
        """Valid simple classification should pass validation."""
        classification = CommandClassification(
            command_type="simple",
            intent="volume_control",
            confidence=0.95,
            requires_agents=["PCControlAgent"],
            estimated_steps=1,
            use_fast_route=True
        )
        
        classification.validate()  # Should not raise
    
    def test_valid_complex_classification(self):
        """Valid complex classification should pass validation."""
        classification = CommandClassification(
            command_type="complex",
            intent="send_whatsapp",
            confidence=0.85,
            requires_agents=["WhatsAppAgent"],
            estimated_steps=3,
            use_fast_route=False
        )
        
        classification.validate()  # Should not raise
    
    def test_valid_multi_step_classification(self):
        """Valid multi-step classification should pass validation."""
        classification = CommandClassification(
            command_type="multi_step",
            intent="screenshot_and_send",
            confidence=0.8,
            requires_agents=["ScreenAIAgent", "WhatsAppAgent"],
            estimated_steps=5,
            use_fast_route=False
        )
        
        classification.validate()  # Should not raise
    
    def test_confidence_below_zero_fails(self):
        """Confidence below 0.0 should fail validation."""
        classification = CommandClassification(
            command_type="simple",
            intent="test",
            confidence=-0.1,
            requires_agents=[],
            estimated_steps=1
        )
        
        with pytest.raises(ValueError, match="confidence must be between 0.0 and 1.0"):
            classification.validate()
    
    def test_confidence_above_one_fails(self):
        """Confidence above 1.0 should fail validation."""
        classification = CommandClassification(
            command_type="simple",
            intent="test",
            confidence=1.5,
            requires_agents=[],
            estimated_steps=1
        )
        
        with pytest.raises(ValueError, match="confidence must be between 0.0 and 1.0"):
            classification.validate()
    
    def test_invalid_command_type_fails(self):
        """Invalid command_type should fail validation."""
        classification = CommandClassification(
            command_type="invalid",  # type: ignore
            intent="test",
            confidence=0.9,
            requires_agents=[],
            estimated_steps=1
        )
        
        with pytest.raises(ValueError, match="command_type must be one of"):
            classification.validate()
    
    def test_empty_intent_fails(self):
        """Empty intent should fail validation."""
        classification = CommandClassification(
            command_type="simple",
            intent="",
            confidence=0.9,
            requires_agents=[],
            estimated_steps=1
        )
        
        with pytest.raises(ValueError, match="intent cannot be empty"):
            classification.validate()
    
    def test_zero_estimated_steps_fails(self):
        """Zero estimated_steps should fail validation."""
        classification = CommandClassification(
            command_type="simple",
            intent="test",
            confidence=0.9,
            requires_agents=[],
            estimated_steps=0
        )
        
        with pytest.raises(ValueError, match="estimated_steps must be positive"):
            classification.validate()
    
    def test_fast_route_on_complex_fails(self):
        """use_fast_route=True on complex command should fail."""
        classification = CommandClassification(
            command_type="complex",
            intent="test",
            confidence=0.9,
            requires_agents=[],
            estimated_steps=1,
            use_fast_route=True
        )
        
        with pytest.raises(ValueError, match="use_fast_route=True is only valid for command_type='simple'"):
            classification.validate()
    
    def test_metadata_includes_timestamp(self):
        """Classification should automatically include timestamp in metadata."""
        classification = CommandClassification(
            command_type="simple",
            intent="test",
            confidence=0.9
        )
        
        assert "timestamp" in classification.metadata
    
    def test_to_dict(self):
        """Classification should convert to dict correctly."""
        classification = CommandClassification(
            command_type="simple",
            intent="test_intent",
            confidence=0.9,
            requires_agents=["Agent1", "Agent2"],
            estimated_steps=2,
            use_fast_route=True,
            metadata={"custom": "field"}
        )
        
        d = classification.to_dict()
        
        assert d["command_type"] == "simple"
        assert d["intent"] == "test_intent"
        assert d["confidence"] == 0.9
        assert d["requires_agents"] == ["Agent1", "Agent2"]
        assert d["estimated_steps"] == 2
        assert d["use_fast_route"] is True
        assert "custom" in d["metadata"]
    
    def test_from_dict(self):
        """Classification should be created from dict correctly."""
        data = {
            "command_type": "complex",
            "intent": "test_intent",
            "confidence": 0.85,
            "requires_agents": ["Agent1"],
            "estimated_steps": 3,
            "use_fast_route": False,
            "metadata": {"custom": "field"}
        }
        
        classification = CommandClassification.from_dict(data)
        
        assert classification.command_type == "complex"
        assert classification.intent == "test_intent"
        assert classification.confidence == 0.85
        assert classification.requires_agents == ["Agent1"]
        assert classification.estimated_steps == 3
        assert classification.use_fast_route is False
    
    def test_round_trip_serialization(self):
        """Serialization and deserialization should be reversible."""
        original = CommandClassification(
            command_type="multi_step",
            intent="complex_task",
            confidence=0.75,
            requires_agents=["Agent1", "Agent2", "Agent3"],
            estimated_steps=7,
            use_fast_route=False
        )
        
        data = original.to_dict()
        restored = CommandClassification.from_dict(data)
        
        assert restored.command_type == original.command_type
        assert restored.intent == original.intent
        assert restored.confidence == original.confidence
        assert restored.requires_agents == original.requires_agents
        assert restored.estimated_steps == original.estimated_steps
        assert restored.use_fast_route == original.use_fast_route


class TestFactoryFunctions:
    """Test factory functions for creating responses and classifications."""
    
    def test_success_response_factory(self):
        """success_response factory should create valid response."""
        response = success_response(
            "TestAgent",
            "test_action",
            result={"data": "value"}
        )
        
        assert response.success is True
        assert response.agent_name == "TestAgent"
        assert response.action_taken == "test_action"
        assert response.result == {"data": "value"}
        assert response.error is None
        assert response.retry_recommended is False
        response.validate()
    
    def test_error_response_factory(self):
        """error_response factory should create valid error response."""
        response = error_response(
            "TestAgent",
            "test_action",
            "Something went wrong",
            retry_recommended=True
        )
        
        assert response.success is False
        assert response.agent_name == "TestAgent"
        assert response.error == "Something went wrong"
        assert response.retry_recommended is True
        response.validate()
    
    def test_simple_classification_factory(self):
        """simple_classification factory should create valid classification."""
        classification = simple_classification(
            "volume_control",
            confidence=0.95,
            use_fast_route=True
        )
        
        assert classification.command_type == "simple"
        assert classification.intent == "volume_control"
        assert classification.confidence == 0.95
        assert classification.use_fast_route is True
        assert classification.estimated_steps == 1
        classification.validate()
    
    def test_complex_classification_factory(self):
        """complex_classification factory should create valid classification."""
        classification = complex_classification(
            "send_message",
            0.85,
            ["WhatsAppAgent"],
            estimated_steps=3
        )
        
        assert classification.command_type == "complex"
        assert classification.intent == "send_message"
        assert classification.confidence == 0.85
        assert classification.requires_agents == ["WhatsAppAgent"]
        assert classification.estimated_steps == 3
        assert classification.use_fast_route is False
        classification.validate()
    
    def test_multi_step_classification_factory(self):
        """multi_step_classification factory should create valid classification."""
        classification = multi_step_classification(
            "screenshot_and_send",
            0.8,
            ["ScreenAIAgent", "WhatsAppAgent"],
            estimated_steps=5
        )
        
        assert classification.command_type == "multi_step"
        assert classification.intent == "screenshot_and_send"
        assert classification.confidence == 0.8
        assert classification.requires_agents == ["ScreenAIAgent", "WhatsAppAgent"]
        assert classification.estimated_steps == 5
        assert classification.use_fast_route is False
        classification.validate()


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_confidence_exactly_zero(self):
        """Confidence of exactly 0.0 should be valid."""
        classification = CommandClassification(
            command_type="simple",
            intent="test",
            confidence=0.0,
            requires_agents=[]
        )
        
        classification.validate()  # Should not raise
    
    def test_confidence_exactly_one(self):
        """Confidence of exactly 1.0 should be valid."""
        classification = CommandClassification(
            command_type="simple",
            intent="test",
            confidence=1.0,
            requires_agents=[]
        )
        
        classification.validate()  # Should not raise
    
    def test_large_estimated_steps(self):
        """Large estimated_steps value should be valid."""
        classification = CommandClassification(
            command_type="multi_step",
            intent="complex_task",
            confidence=0.7,
            requires_agents=["Agent1"],
            estimated_steps=100
        )
        
        classification.validate()  # Should not raise
    
    def test_empty_requires_agents(self):
        """Empty requires_agents list should be valid."""
        classification = CommandClassification(
            command_type="simple",
            intent="test",
            confidence=0.9,
            requires_agents=[]
        )
        
        classification.validate()  # Should not raise
    
    def test_many_required_agents(self):
        """Many required agents should be valid."""
        classification = CommandClassification(
            command_type="multi_step",
            intent="complex_task",
            confidence=0.8,
            requires_agents=[f"Agent{i}" for i in range(10)],
            estimated_steps=20
        )
        
        classification.validate()  # Should not raise
        assert len(classification.requires_agents) == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
