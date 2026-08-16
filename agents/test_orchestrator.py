"""
Unit tests for OrchestratorAgent.

These tests verify the orchestrator's routing logic, command classification,
fast route detection, and workflow graph creation.

Validates: Requirements 1.1, 1.2, 1.3, 1.5 (partial - unit tests only)
"""

import pytest
from agents.orchestrator import OrchestratorAgent
from agents.registry import AgentRegistry
from agents.base import BaseAgent
from agents.models import CommandClassification


class MockAgent(BaseAgent):
    """Mock agent for testing."""
    
    def __init__(self, name: str, agent_type: str):
        super().__init__(name=name, agent_type=agent_type, description="Mock agent")
    
    def execute_task(self, task_description: str, context=None):
        return {
            "success": True,
            "action": "mock_action",
            "result": {"message": "Mock execution"}
        }


@pytest.fixture
def registry():
    """Create a registry with mock agents."""
    reg = AgentRegistry()
    reg.register("pc_control", MockAgent("PCControlAgent", "pc_control"))
    reg.register("whatsapp", MockAgent("WhatsAppAgent", "whatsapp"))
    reg.register("web", MockAgent("WebAgent", "web"))
    return reg


@pytest.fixture
def orchestrator(registry):
    """Create orchestrator with mock registry."""
    return OrchestratorAgent(registry=registry)


class TestFastRouteDetection:
    """Tests for fast route pattern matching."""
    
    def test_volume_up_matches_fast_route(self, orchestrator):
        """Test that 'volume up' matches fast route pattern."""
        assert orchestrator.should_use_fast_route("volume up") is True
    
    def test_brightness_up_matches_fast_route(self, orchestrator):
        """Test that brightness commands match fast route."""
        assert orchestrator.should_use_fast_route("brightness badha") is True
    
    def test_screenshot_matches_fast_route(self, orchestrator):
        """Test that screenshot matches fast route."""
        assert orchestrator.should_use_fast_route("screenshot") is True
    
    def test_complex_command_no_fast_route(self, orchestrator):
        """Test that complex commands don't match fast route."""
        assert orchestrator.should_use_fast_route("send a message to john") is False
    
    def test_unknown_command_no_fast_route(self, orchestrator):
        """Test that unknown commands don't match fast route."""
        assert orchestrator.should_use_fast_route("xyzabc random text") is False


class TestCommandClassification:
    """Tests for command classification logic."""
    
    def test_classify_volume_command(self, orchestrator):
        """Test classification of volume control command."""
        classification = orchestrator.classify_command("volume up", {})
        
        assert classification.command_type == "simple"
        assert classification.intent == "pc_control"
        assert 0.0 <= classification.confidence <= 1.0
        assert "pc_control" in classification.requires_agents
    
    def test_classify_whatsapp_message(self, orchestrator):
        """Test classification of WhatsApp message command."""
        classification = orchestrator.classify_command("send message to papa", {})
        
        assert classification.command_type == "simple"
        assert classification.intent == "send_whatsapp_message"
        assert classification.confidence >= 0.8
        assert "whatsapp" in classification.requires_agents
    
    def test_classify_whatsapp_file(self, orchestrator):
        """Test classification of WhatsApp file send command."""
        classification = orchestrator.classify_command("papa ko file bhejo", {})
        
        assert classification.command_type == "complex"
        assert classification.intent == "send_whatsapp_file"
        assert classification.estimated_steps > 1
        assert "whatsapp" in classification.requires_agents
    
    def test_classify_web_search(self, orchestrator):
        """Test classification of web search command."""
        classification = orchestrator.classify_command("search python tutorial", {})
        
        assert classification.command_type == "simple"
        assert classification.intent == "web_action"
        assert "web" in classification.requires_agents
    
    def test_classify_screen_interaction(self, orchestrator):
        """Test classification of screen interaction command."""
        classification = orchestrator.classify_command("click the button", {})
        
        assert classification.command_type == "simple"
        assert classification.intent == "screen_interaction"
        assert "screen_ai" in classification.requires_agents
    
    def test_classification_confidence_range(self, orchestrator):
        """Test that confidence is always between 0.0 and 1.0."""
        commands = [
            "volume up",
            "send message",
            "search google",
            "unknown random command"
        ]
        
        for cmd in commands:
            classification = orchestrator.classify_command(cmd, {})
            assert 0.0 <= classification.confidence <= 1.0, \
                f"Confidence {classification.confidence} out of range for: {cmd}"
    
    def test_classification_returns_valid_command_type(self, orchestrator):
        """Test that command_type is always valid."""
        valid_types = {"simple", "complex", "multi_step"}
        
        commands = [
            "volume up",
            "papa ko file bhejo",
            "search python"
        ]
        
        for cmd in commands:
            classification = orchestrator.classify_command(cmd, {})
            assert classification.command_type in valid_types, \
                f"Invalid command_type '{classification.command_type}' for: {cmd}"


class TestProcessCommand:
    """Tests for main command processing flow."""
    
    def test_process_fast_route_command(self, orchestrator):
        """Test processing of fast route command."""
        result = orchestrator.process_command("volume up", {})
        
        assert result["success"] is True
        assert result["used_fast_route"] is True
        assert result["execution_time"] < 1.0  # Should be very fast
    
    def test_process_non_fast_route_command(self, orchestrator):
        """Test processing of non-fast route command."""
        # Use a command that definitely won't match fast route
        result = orchestrator.process_command("tell me about quantum physics", {})
        
        # Should not use fast route
        assert result["used_fast_route"] is False
        assert "classification" in result
    
    def test_process_command_returns_success_status(self, orchestrator):
        """Test that result always has success field."""
        commands = ["volume up", "search google"]
        
        for cmd in commands:
            result = orchestrator.process_command(cmd, {})
            assert "success" in result
            assert isinstance(result["success"], bool)
    
    def test_process_command_returns_execution_time(self, orchestrator):
        """Test that result includes execution time."""
        result = orchestrator.process_command("volume up", {})
        
        assert "execution_time" in result
        assert isinstance(result["execution_time"], (int, float))
        assert result["execution_time"] >= 0
    
    def test_process_command_handles_empty_context(self, orchestrator):
        """Test processing with empty context."""
        result = orchestrator.process_command("volume up", None)
        
        assert result["success"] is True
    
    def test_process_command_with_context(self, orchestrator):
        """Test processing with conversation context."""
        context = {
            "conversation_history": [
                {"user": "hello", "response": "hi"}
            ]
        }
        
        result = orchestrator.process_command("volume up", context)
        assert result["success"] is True


class TestExecuteTask:
    """Tests for BaseAgent interface compliance."""
    
    def test_execute_task_delegates_to_process_command(self, orchestrator):
        """Test that execute_task calls process_command."""
        result = orchestrator.execute_task("volume up", {})
        
        assert "success" in result
        assert isinstance(result, dict)
    
    def test_execute_task_with_none_context(self, orchestrator):
        """Test execute_task with None context."""
        result = orchestrator.execute_task("volume up", None)
        
        assert result["success"] is True


class TestOrchestratorInitialization:
    """Tests for orchestrator initialization."""
    
    def test_orchestrator_initializes_with_registry(self, registry):
        """Test that orchestrator initializes correctly."""
        orchestrator = OrchestratorAgent(registry=registry)
        
        assert orchestrator.name == "OrchestratorAgent"
        assert orchestrator.agent_type == "orchestrator"
        assert orchestrator.agent_registry is registry
    
    def test_orchestrator_has_default_llm_config(self, registry):
        """Test that orchestrator has LLM config."""
        orchestrator = OrchestratorAgent(registry=registry)
        
        assert orchestrator.llm_config is not None
        assert isinstance(orchestrator.llm_config, dict)
    
    def test_orchestrator_custom_max_retries(self, registry):
        """Test setting custom max_retries."""
        orchestrator = OrchestratorAgent(registry=registry, max_retries=5)
        
        assert orchestrator.max_retries == 5
    
    def test_orchestrator_repr(self, registry):
        """Test string representation."""
        orchestrator = OrchestratorAgent(registry=registry)
        repr_str = repr(orchestrator)
        
        assert "OrchestratorAgent" in repr_str
        assert "agents=" in repr_str


class TestFastRouteExecution:
    """Tests for fast route execution path."""
    
    def test_fast_route_preserves_action(self, orchestrator):
        """Test that fast route returns correct action."""
        result = orchestrator._execute_fast_route("volume up")
        
        assert result["success"] is True
        assert result["action"] is not None
    
    def test_fast_route_returns_say_message(self, orchestrator):
        """Test that fast route includes response message."""
        result = orchestrator._execute_fast_route("volume badha")
        
        assert "say" in result
        assert isinstance(result["say"], str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

