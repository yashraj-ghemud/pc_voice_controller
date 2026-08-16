"""
Basic verification tests for WhatsAppAgent implementation.

This test file verifies that the WhatsAppAgent is correctly implemented
with all required methods and proper integration with existing modules.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


def test_whatsapp_agent_initialization():
    """Test that WhatsAppAgent can be initialized correctly."""
    from agents.specialized.whatsapp_agent import WhatsAppAgent
    
    agent = WhatsAppAgent()
    
    assert agent.name == "WhatsAppAgent"
    assert agent.agent_type == "whatsapp"
    assert hasattr(agent, "ALLOWED_ACTIONS")
    assert len(agent.ALLOWED_ACTIONS) == 3
    assert "SEND_MESSAGE" in agent.ALLOWED_ACTIONS
    assert "SEND_VOICE_NOTE" in agent.ALLOWED_ACTIONS
    assert "SEND_FILE" in agent.ALLOWED_ACTIONS
    
    print("✅ WhatsAppAgent initialization test passed")


def test_whatsapp_agent_has_required_methods():
    """Test that WhatsAppAgent has all required methods."""
    from agents.specialized.whatsapp_agent import WhatsAppAgent
    
    agent = WhatsAppAgent()
    
    # Check required methods exist
    assert hasattr(agent, "execute_task")
    assert hasattr(agent, "send_message")
    assert hasattr(agent, "send_voice_note")
    assert hasattr(agent, "send_file_smart")
    assert hasattr(agent, "__repr__")
    
    # Check methods are callable
    assert callable(agent.execute_task)
    assert callable(agent.send_message)
    assert callable(agent.send_voice_note)
    assert callable(agent.send_file_smart)
    
    print("✅ WhatsAppAgent methods test passed")


def test_whatsapp_agent_validation():
    """Test that WhatsAppAgent validates inputs correctly."""
    from agents.specialized.whatsapp_agent import WhatsAppAgent
    
    agent = WhatsAppAgent()
    
    # Test empty contact validation
    response = agent.send_message("", "test message")
    assert response.success is False
    assert "contact" in response.error.lower() or "empty" in response.error.lower()
    
    # Test empty message validation
    response = agent.send_message("test_contact", "")
    assert response.success is False
    assert "message" in response.error.lower() or "empty" in response.error.lower()
    
    # Test empty contact for voice note
    response = agent.send_voice_note("", "test text")
    assert response.success is False
    
    # Test empty text for voice note
    response = agent.send_voice_note("test_contact", "")
    assert response.success is False
    
    # Test empty command for file send
    response = agent.send_file_smart("")
    assert response.success is False
    
    print("✅ WhatsAppAgent validation test passed")


def test_whatsapp_agent_response_structure():
    """Test that WhatsAppAgent returns proper AgentResponse objects."""
    from agents.specialized.whatsapp_agent import WhatsAppAgent
    from agents.models import AgentResponse
    
    agent = WhatsAppAgent()
    
    # Test send_message returns AgentResponse
    response = agent.send_message("", "test")
    assert isinstance(response, AgentResponse)
    assert hasattr(response, "success")
    assert hasattr(response, "agent_name")
    assert hasattr(response, "action_taken")
    assert hasattr(response, "error")
    assert response.agent_name == "WhatsAppAgent"
    
    # Test send_voice_note returns AgentResponse
    response = agent.send_voice_note("", "test")
    assert isinstance(response, AgentResponse)
    assert response.agent_name == "WhatsAppAgent"
    
    # Test send_file_smart returns AgentResponse
    response = agent.send_file_smart("")
    assert isinstance(response, AgentResponse)
    assert response.agent_name == "WhatsAppAgent"
    
    print("✅ WhatsAppAgent response structure test passed")


def test_whatsapp_agent_execute_task_routing():
    """Test that execute_task routes to correct methods."""
    from agents.specialized.whatsapp_agent import WhatsAppAgent
    
    agent = WhatsAppAgent()
    
    # Test SEND_MESSAGE routing
    result = agent.execute_task("SEND_MESSAGE", {
        "action": "SEND_MESSAGE",
        "params": {"contact": "", "message": "test"}
    })
    assert result["action_taken"] == "SEND_MESSAGE"
    
    # Test SEND_VOICE_NOTE routing
    result = agent.execute_task("SEND_VOICE_NOTE", {
        "action": "SEND_VOICE_NOTE",
        "params": {"contact": "", "text": "test"}
    })
    assert result["action_taken"] == "SEND_VOICE_NOTE"
    
    # Test SEND_FILE routing
    result = agent.execute_task("SEND_FILE", {
        "action": "SEND_FILE",
        "params": {"command": ""}
    })
    assert result["action_taken"] == "SEND_FILE"
    
    # Test unknown action
    result = agent.execute_task("UNKNOWN_ACTION", {
        "action": "UNKNOWN_ACTION",
        "params": {}
    })
    assert result["success"] is False
    assert "unknown" in result["error"].lower()
    
    print("✅ WhatsAppAgent execute_task routing test passed")


def test_whatsapp_agent_repr():
    """Test WhatsAppAgent string representation."""
    from agents.specialized.whatsapp_agent import WhatsAppAgent
    
    agent = WhatsAppAgent()
    
    repr_str = repr(agent)
    assert "WhatsAppAgent" in repr_str
    assert "allowed_actions" in repr_str
    
    print("✅ WhatsAppAgent repr test passed")


def run_all_tests():
    """Run all WhatsAppAgent verification tests."""
    print("\n" + "="*60)
    print("Running WhatsAppAgent Verification Tests")
    print("="*60 + "\n")
    
    try:
        test_whatsapp_agent_initialization()
        test_whatsapp_agent_has_required_methods()
        test_whatsapp_agent_validation()
        test_whatsapp_agent_response_structure()
        test_whatsapp_agent_execute_task_routing()
        test_whatsapp_agent_repr()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60 + "\n")
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
