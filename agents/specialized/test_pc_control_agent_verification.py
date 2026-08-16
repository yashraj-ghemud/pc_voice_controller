"""
Quick verification test for PCControlAgent implementation.
This test verifies that Task 7 (7.1 and 7.2) has been completed successfully.
"""

from agents.specialized.pc_control_agent import PCControlAgent
from agents.models import AgentResponse


def test_pc_control_agent_initialization():
    """Test that PCControlAgent can be initialized."""
    agent = PCControlAgent()
    assert agent.name == "PCControlAgent"
    assert agent.agent_type == "pc_control"
    assert len(agent.ALLOWED_ACTIONS) > 0
    print("✅ PCControlAgent initialization test passed")


def test_allowed_actions():
    """Test that allowed actions are properly defined."""
    agent = PCControlAgent()
    
    # Check required actions from Requirements 4.1, 4.2
    required_actions = {
        "VOLUME_UP", "VOLUME_DOWN", "SET_VOLUME",
        "BRIGHTNESS_UP", "BRIGHTNESS_DOWN", "SET_BRIGHTNESS",
        "OPEN_APP", "CLOSE_APP",
        "PLAY_MEDIA", "PAUSE_MEDIA", "STOP_MEDIA"
    }
    
    for action in required_actions:
        assert action in agent.ALLOWED_ACTIONS, f"Missing required action: {action}"
    
    print(f"✅ Allowed actions test passed ({len(agent.ALLOWED_ACTIONS)} actions)")


def test_unauthorized_action():
    """Test that unauthorized actions are rejected (Requirement 15.1, 15.2)."""
    agent = PCControlAgent()
    
    response = agent.execute_system_command("HACK_SYSTEM", {})
    
    assert isinstance(response, AgentResponse)
    assert response.success == False
    assert "not authorized" in response.error.lower()
    assert response.retry_recommended == False
    print("✅ Unauthorized action rejection test passed")


def test_volume_up_action():
    """Test VOLUME_UP action execution structure."""
    agent = PCControlAgent()
    
    # We'll mock the action executor to avoid actually changing volume
    class MockExecutor:
        def change_volume(self, change):
            if change != 10:
                raise ValueError(f"Expected change=10, got {change}")
    
    agent.action_executor = MockExecutor()
    
    response = agent.execute_system_command("VOLUME_UP", {})
    
    assert isinstance(response, AgentResponse)
    assert response.success == True
    assert response.agent_name == "PCControlAgent"
    assert response.action_taken == "VOLUME_UP"
    assert response.error is None
    print("✅ VOLUME_UP action test passed")


def test_set_volume_with_value():
    """Test SET_VOLUME action with value parameter."""
    agent = PCControlAgent()
    
    class MockExecutor:
        def set_volume(self, level):
            if level != 50:
                raise ValueError(f"Expected level=50, got {level}")
    
    agent.action_executor = MockExecutor()
    
    response = agent.execute_system_command("SET_VOLUME", {"value": 50})
    
    assert response.success == True
    assert response.action_taken == "SET_VOLUME"
    assert response.result["value"] == 50
    print("✅ SET_VOLUME with value test passed")


def test_open_app_with_target():
    """Test OPEN_APP action with target parameter."""
    agent = PCControlAgent()
    
    class MockExecutor:
        def open_application(self, app_name):
            if app_name != "chrome":
                raise ValueError(f"Expected app_name='chrome', got {app_name}")
    
    agent.action_executor = MockExecutor()
    
    response = agent.execute_system_command("OPEN_APP", {"target": "chrome"})
    
    assert response.success == True
    assert response.action_taken == "OPEN_APP"
    assert response.result["target"] == "chrome"
    print("✅ OPEN_APP with target test passed")


def test_error_handling_with_missing_parameter():
    """Test error handling when required parameter is missing (Requirement 4.5)."""
    agent = PCControlAgent()
    
    # SET_VOLUME requires 'value' parameter
    response = agent.execute_system_command("SET_VOLUME", {})
    
    assert response.success == False
    assert "requires" in response.error.lower()
    # Missing parameter is not retryable
    assert response.retry_recommended == False
    print("✅ Error handling for missing parameter test passed")


def test_execute_task_interface():
    """Test that execute_task interface works (BaseAgent requirement)."""
    agent = PCControlAgent()
    
    class MockExecutor:
        def change_volume(self, change):
            pass
    
    agent.action_executor = MockExecutor()
    
    # Test via execute_task interface
    result = agent.execute_task("VOLUME_UP")
    
    assert isinstance(result, dict)
    assert result["success"] == True
    assert result["agent_name"] == "PCControlAgent"
    print("✅ execute_task interface test passed")


def run_all_tests():
    """Run all verification tests."""
    print("\n" + "=" * 70)
    print("PCControlAgent Verification Tests (Task 7.1 and 7.2)")
    print("=" * 70 + "\n")
    
    try:
        test_pc_control_agent_initialization()
        test_allowed_actions()
        test_unauthorized_action()
        test_volume_up_action()
        test_set_volume_with_value()
        test_open_app_with_target()
        test_error_handling_with_missing_parameter()
        test_execute_task_interface()
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED - Task 7 (7.1, 7.2) Successfully Completed!")
        print("=" * 70 + "\n")
        
        print("Summary:")
        print("  ✅ 7.1: PCControlAgent class created with BaseAgent extension")
        print("  ✅ 7.2: execute_system_command method implemented")
        print("  ✅ Requirements 4.1, 4.2: Volume and brightness actions defined")
        print("  ✅ Requirements 4.3, 4.4, 4.5: Execution, response, error handling")
        print("  ✅ Requirements 15.1, 15.2: Action validation and security")
        print()
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
