"""
Demo script to test PCControlAgent functionality.

This script demonstrates the PCControlAgent capabilities including:
- Volume control operations
- Brightness control operations
- Application management
- Media controls
- Desktop switching
- System actions
- Error handling
- Authorization validation
"""

from agents.specialized import PCControlAgent


def print_section(title):
    """Print a section header."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def test_volume_controls():
    """Test volume control operations."""
    print_section("Volume Controls")
    
    agent = PCControlAgent()
    
    # Test volume up
    print("\n1. Volume Up:")
    response = agent.execute_system_command("VOLUME_UP", {})
    print(f"   Success: {response.success}")
    print(f"   Action: {response.action_taken}")
    
    # Test volume down
    print("\n2. Volume Down:")
    response = agent.execute_system_command("VOLUME_DOWN", {})
    print(f"   Success: {response.success}")
    
    # Test set volume
    print("\n3. Set Volume to 50%:")
    response = agent.execute_system_command("SET_VOLUME", {"value": 50})
    print(f"   Success: {response.success}")
    print(f"   Result: {response.result}")
    
    # Test mute
    print("\n4. Mute:")
    response = agent.execute_system_command("MUTE", {})
    print(f"   Success: {response.success}")
    
    # Test unmute
    print("\n5. Unmute:")
    response = agent.execute_system_command("UNMUTE", {})
    print(f"   Success: {response.success}")


def test_brightness_controls():
    """Test brightness control operations."""
    print_section("Brightness Controls")
    
    agent = PCControlAgent()
    
    # Test brightness up
    print("\n1. Brightness Up:")
    response = agent.execute_system_command("BRIGHTNESS_UP", {})
    print(f"   Success: {response.success}")
    
    # Test brightness down
    print("\n2. Brightness Down:")
    response = agent.execute_system_command("BRIGHTNESS_DOWN", {})
    print(f"   Success: {response.success}")
    
    # Test set brightness
    print("\n3. Set Brightness to 70%:")
    response = agent.execute_system_command("SET_BRIGHTNESS", {"value": 70})
    print(f"   Success: {response.success}")


def test_application_management():
    """Test application management operations."""
    print_section("Application Management")
    
    agent = PCControlAgent()
    
    # Test open app
    print("\n1. Open Notepad:")
    response = agent.execute_system_command("OPEN_APP", {"target": "notepad"})
    print(f"   Success: {response.success}")
    print(f"   Action: {response.action_taken}")
    
    # Wait a moment
    import time
    time.sleep(2)
    
    # Test close app
    print("\n2. Close Notepad:")
    response = agent.execute_system_command("CLOSE_APP", {"target": "notepad"})
    print(f"   Success: {response.success}")


def test_media_controls():
    """Test media control operations."""
    print_section("Media Controls")
    
    agent = PCControlAgent()
    
    print("\n1. Play Media:")
    response = agent.execute_system_command("PLAY_MEDIA", {})
    print(f"   Success: {response.success}")
    
    print("\n2. Pause Media:")
    response = agent.execute_system_command("PAUSE_MEDIA", {})
    print(f"   Success: {response.success}")
    
    print("\n3. Next Track:")
    response = agent.execute_system_command("NEXT_TRACK", {})
    print(f"   Success: {response.success}")
    
    print("\n4. Previous Track:")
    response = agent.execute_system_command("PREV_TRACK", {})
    print(f"   Success: {response.success}")


def test_desktop_switching():
    """Test virtual desktop switching."""
    print_section("Virtual Desktop Switching")
    
    agent = PCControlAgent()
    
    print("\n1. Switch Desktop Right:")
    response = agent.execute_system_command("SWITCH_DESKTOP_RIGHT", {})
    print(f"   Success: {response.success}")
    
    import time
    time.sleep(1)
    
    print("\n2. Switch Desktop Left:")
    response = agent.execute_system_command("SWITCH_DESKTOP_LEFT", {})
    print(f"   Success: {response.success}")


def test_system_actions():
    """Test system actions."""
    print_section("System Actions")
    
    agent = PCControlAgent()
    
    print("\n1. Take Screenshot:")
    response = agent.execute_system_command("SCREENSHOT", {})
    print(f"   Success: {response.success}")
    print(f"   Result: {response.result}")
    
    # Note: LOCK and SLEEP are available but not tested in demo
    print("\n2. LOCK and SLEEP actions available but not tested in demo")


def test_error_handling():
    """Test error handling and validation."""
    print_section("Error Handling & Validation")
    
    agent = PCControlAgent()
    
    # Test unauthorized action
    print("\n1. Unauthorized Action (HACK_SYSTEM):")
    response = agent.execute_system_command("HACK_SYSTEM", {})
    print(f"   Success: {response.success}")
    print(f"   Error: {response.error}")
    print(f"   Contains 'not authorized': {'not authorized' in response.error.lower()}")
    
    # Test missing parameter
    print("\n2. Missing Parameter (SET_VOLUME without value):")
    response = agent.execute_system_command("SET_VOLUME", {})
    print(f"   Success: {response.success}")
    print(f"   Error: {response.error}")
    print(f"   Retry Recommended: {response.retry_recommended}")
    
    # Test missing target
    print("\n3. Missing Target (OPEN_APP without target):")
    response = agent.execute_system_command("OPEN_APP", {})
    print(f"   Success: {response.success}")
    print(f"   Error: {response.error}")


def test_agent_response_validation():
    """Test AgentResponse validation."""
    print_section("AgentResponse Validation")
    
    agent = PCControlAgent()
    
    print("\n1. Valid Response Structure:")
    response = agent.execute_system_command("VOLUME_UP", {})
    print(f"   Has agent_name: {response.agent_name == 'PCControlAgent'}")
    print(f"   Has action_taken: {len(response.action_taken) > 0}")
    print(f"   Has metadata: {'timestamp' in response.metadata}")
    print(f"   Has action_category: {'action_category' in response.metadata}")
    
    print("\n2. Response Validation:")
    try:
        response.validate()
        print("   ✅ Validation passed")
    except ValueError as e:
        print(f"   ❌ Validation failed: {e}")
    
    print("\n3. Response to Dict Conversion:")
    response_dict = response.to_dict()
    print(f"   Dict keys: {list(response_dict.keys())}")
    print(f"   Success in dict: {response_dict['success']}")


def test_integration_with_registry():
    """Test integration with AgentRegistry."""
    print_section("Integration with AgentRegistry")
    
    from agents.registry import AgentRegistry
    
    print("\n1. Creating registry and agent:")
    registry = AgentRegistry()
    pc_agent = PCControlAgent()
    
    print("\n2. Registering agent:")
    registry.register("pc_control", pc_agent)
    print("   ✅ Agent registered")
    
    print("\n3. Retrieving agent:")
    retrieved = registry.get_agent("pc_control")
    print(f"   Retrieved: {retrieved.name}")
    print(f"   Type: {retrieved.agent_type}")
    print(f"   Same instance: {retrieved is pc_agent}")
    
    print("\n4. Executing via registry:")
    response = retrieved.execute_system_command("VOLUME_UP", {})
    print(f"   Success: {response.success}")


def main():
    """Run all tests."""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "PCControlAgent Demo & Test Suite" + " "*21 + "║")
    print("╚" + "="*68 + "╝")
    
    try:
        test_volume_controls()
        test_brightness_controls()
        test_application_management()
        test_media_controls()
        test_desktop_switching()
        test_system_actions()
        test_error_handling()
        test_agent_response_validation()
        test_integration_with_registry()
        
        print("\n" + "="*70)
        print("  ✅ All tests completed successfully!")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

