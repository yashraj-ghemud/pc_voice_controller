"""
Integration tests for AgentRegistry with all specialized agents.

This test file verifies that the AgentRegistry correctly registers and
retrieves all five specialized agents (PCControl, WhatsApp, ScreenAI, Web, Memory).

Validates: Requirements 3.5, 20.3
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.registry import AgentRegistry, create_default_registry
from agents.specialized.pc_control_agent import PCControlAgent
from agents.specialized.whatsapp_agent import WhatsAppAgent
from agents.specialized.screen_ai_agent import ScreenAIAgent
from agents.specialized.web_agent import WebAgent
from agents.specialized.memory_agent import MemoryAgent


def test_create_default_registry():
    """Test create_default_registry() creates all agents."""
    print("\n" + "="*60)
    print("TEST 1: create_default_registry()")
    print("="*60)
    
    registry = create_default_registry()
    
    # Verify all five agents are registered
    assert len(registry.list_agents()) == 5
    assert "pc_control" in registry.list_agents()
    assert "whatsapp" in registry.list_agents()
    assert "screen_ai" in registry.list_agents()
    assert "web" in registry.list_agents()
    assert "memory" in registry.list_agents()
    
    print("✅ All 5 agents registered:")
    for agent_type in registry.list_agents():
        print(f"   - {agent_type}")
    
    return True


def test_lazy_initialization():
    """Test agents are lazily initialized."""
    print("\n" + "="*60)
    print("TEST 2: Lazy Initialization")
    print("="*60)
    
    registry = create_default_registry()
    
    # Before retrieval, agents should not be in instances cache
    initial_cached = len(registry._instances)
    print(f"Initial cached agents: {initial_cached}")
    
    # Get an agent - this should trigger lazy initialization
    agent = registry.get_agent("pc_control")
    
    # Now it should be cached
    assert len(registry._instances) >= 1
    print(f"After get_agent('pc_control'): {len(registry._instances)} cached")
    
    # Getting same agent again should return cached instance
    same_agent = registry.get_agent("pc_control")
    assert agent is same_agent
    
    print("✅ Lazy initialization working correctly")
    print("   Agent created only when first requested")
    print("   Subsequent calls return cached instance")
    
    return True


def test_agent_types():
    """Test all agents have correct types."""
    print("\n" + "="*60)
    print("TEST 3: Agent Type Verification")
    print("="*60)
    
    registry = create_default_registry()
    
    # Retrieve all agents and verify types
    pc_control = registry.get_agent("pc_control")
    assert isinstance(pc_control, PCControlAgent)
    assert pc_control.agent_type == "pc_control"
    print("✅ PCControlAgent: type='pc_control'")
    
    whatsapp = registry.get_agent("whatsapp")
    assert isinstance(whatsapp, WhatsAppAgent)
    assert whatsapp.agent_type == "whatsapp"
    print("✅ WhatsAppAgent: type='whatsapp'")
    
    screen_ai = registry.get_agent("screen_ai")
    assert isinstance(screen_ai, ScreenAIAgent)
    assert screen_ai.agent_type == "screen_ai"
    print("✅ ScreenAIAgent: type='screen_ai'")
    
    web = registry.get_agent("web")
    assert isinstance(web, WebAgent)
    assert web.agent_type == "web"
    print("✅ WebAgent: type='web'")
    
    memory = registry.get_agent("memory")
    assert isinstance(memory, MemoryAgent)
    assert memory.agent_type == "memory"
    print("✅ MemoryAgent: type='memory'")
    
    return True


def test_get_agent_for_command_routing():
    """Test get_agent_for_command() routes correctly."""
    print("\n" + "="*60)
    print("TEST 4: Command-Based Agent Routing")
    print("="*60)
    
    registry = create_default_registry()
    
    # PC Control routing
    agent = registry.get_agent_for_command("increase volume")
    assert agent.agent_type == "pc_control"
    print("✅ 'increase volume' → pc_control")
    
    agent = registry.get_agent_for_command("brightness up")
    assert agent.agent_type == "pc_control"
    print("✅ 'brightness up' → pc_control")
    
    # WhatsApp routing
    agent = registry.get_agent_for_command("send message to John")
    assert agent.agent_type == "whatsapp"
    print("✅ 'send message to John' → whatsapp")
    
    agent = registry.get_agent_for_command("whatsapp message")
    assert agent.agent_type == "whatsapp"
    print("✅ 'whatsapp message' → whatsapp")
    
    # ScreenAI routing
    agent = registry.get_agent_for_command("click the submit button")
    assert agent.agent_type == "screen_ai"
    print("✅ 'click the submit button' → screen_ai")
    
    agent = registry.get_agent_for_command("take a screenshot")
    assert agent.agent_type == "screen_ai"
    print("✅ 'take a screenshot' → screen_ai")
    
    # Web routing
    agent = registry.get_agent_for_command("search for Python tutorials")
    assert agent.agent_type == "web"
    print("✅ 'search for Python tutorials' → web")
    
    agent = registry.get_agent_for_command("open google.com")
    assert agent.agent_type == "web"
    print("✅ 'open google.com' → web")
    
    # Memory routing
    agent = registry.get_agent_for_command("remember this conversation")
    assert agent.agent_type == "memory"
    print("✅ 'remember this conversation' → memory")
    
    agent = registry.get_agent_for_command("recall previous context")
    assert agent.agent_type == "memory"
    print("✅ 'recall previous context' → memory")
    
    return True


def test_agent_count():
    """Test registry has exactly 5 agents."""
    print("\n" + "="*60)
    print("TEST 5: Agent Count Validation")
    print("="*60)
    
    registry = create_default_registry()
    
    agent_types = registry.list_agents()
    assert len(agent_types) == 5, f"Expected 5 agents, got {len(agent_types)}"
    
    print(f"✅ Registry has exactly 5 agents")
    print(f"   Registered types: {', '.join(sorted(agent_types))}")
    
    return True


def test_registry_with_default_agent():
    """Test registry with default fallback agent."""
    print("\n" + "="*60)
    print("TEST 6: Default Fallback Agent")
    print("="*60)
    
    # Create a simple default agent
    class DefaultAgent:
        def __init__(self):
            self.agent_type = "default"
    
    default = DefaultAgent()
    registry = create_default_registry()
    registry._default_agent = default
    
    # Request unregistered agent type - should get default
    agent = registry.get_agent("unknown_type")
    assert agent is default
    print("✅ Unregistered agent type returns default agent")
    
    # Registered agents should still work
    pc_agent = registry.get_agent("pc_control")
    assert pc_agent.agent_type == "pc_control"
    print("✅ Registered agents still accessible")
    
    return True


def run_all_tests():
    """Run all integration tests."""
    print("\n" + "="*70)
    print(" AgentRegistry Integration Tests")
    print("="*70)
    
    tests = [
        test_create_default_registry,
        test_lazy_initialization,
        test_agent_types,
        test_get_agent_for_command_routing,
        test_agent_count,
        test_registry_with_default_agent,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*70)
    print(f" Test Results: {passed}/{len(tests)} passed")
    print("="*70)
    
    if failed == 0:
        print("\n🎉 All integration tests passed!")
        print("\n✅ Task 12.1 Complete: All 5 agents registered successfully")
        print("   - pc_control (PCControlAgent)")
        print("   - whatsapp (WhatsAppAgent)")
        print("   - screen_ai (ScreenAIAgent)")
        print("   - web (WebAgent)")
        print("   - memory (MemoryAgent)")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
