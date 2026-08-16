"""
test_memory_agent_verification.py - Verification tests for MemoryAgent

This test file verifies that MemoryAgent correctly integrates with the
existing memory.py module and provides the expected interface.

Run: python -m pytest agents/specialized/test_memory_agent_verification.py -v
"""

import os
import sys
import shutil
import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from agents.specialized.memory_agent import MemoryAgent
import memory


# --- Test Fixtures ---

@pytest.fixture(scope="function")
def test_memory_setup():
    """
    Setup test memory database, yield, then cleanup.
    """
    # Create a test database path
    test_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../chroma_db_test_agent")
    
    # Override memory module's DB path
    original_path = memory.CHROMA_DB_PATH
    memory.CHROMA_DB_PATH = test_db
    memory._chroma_client = None
    memory._collection = None
    
    # Force reinitialization
    memory._get_collection()
    
    yield test_db
    
    # Cleanup
    memory._collection = None
    memory._chroma_client = None
    try:
        shutil.rmtree(test_db, ignore_errors=True)
    except:
        pass
    
    # Restore original path
    memory.CHROMA_DB_PATH = original_path
    memory._chroma_client = None
    memory._collection = None


@pytest.fixture
def agent():
    """Create a MemoryAgent instance for testing."""
    return MemoryAgent()


# --- Test Cases ---

def test_memory_agent_initialization(agent):
    """Test MemoryAgent initializes correctly."""
    assert agent.name == "MemoryAgent"
    assert agent.agent_type == "memory"
    assert "SAVE_CONVERSATION" in agent.ALLOWED_ACTIONS
    assert "RETRIEVE_CONTEXT" in agent.ALLOWED_ACTIONS
    assert len(agent.ALLOWED_ACTIONS) == 2


def test_save_conversation_success(agent, test_memory_setup):
    """Test saving a conversation successfully."""
    response = agent.save_conversation(
        user_message="Hello, how are you?",
        assistant_response="I'm doing great, thank you!"
    )
    
    assert response.success is True
    assert response.agent_name == "MemoryAgent"
    assert response.action_taken == "SAVE_CONVERSATION"
    assert response.result["saved"] is True
    assert "user_message" in response.result
    assert "assistant_response" in response.result
    assert response.error is None


def test_save_conversation_empty_user_message(agent, test_memory_setup):
    """Test saving with empty user message fails."""
    response = agent.save_conversation(
        user_message="",
        assistant_response="I'm doing great!"
    )
    
    assert response.success is False
    assert response.action_taken == "SAVE_CONVERSATION"
    assert "cannot be empty" in response.error.lower()
    assert response.retry_recommended is False


def test_save_conversation_empty_assistant_response(agent, test_memory_setup):
    """Test saving with empty assistant response fails."""
    response = agent.save_conversation(
        user_message="Hello!",
        assistant_response=""
    )
    
    assert response.success is False
    assert response.action_taken == "SAVE_CONVERSATION"
    assert "cannot be empty" in response.error.lower()
    assert response.retry_recommended is False


def test_retrieve_context_success(agent, test_memory_setup):
    """Test retrieving context successfully."""
    # First save a conversation
    agent.save_conversation(
        user_message="What is Python?",
        assistant_response="Python is a programming language."
    )
    
    # Then retrieve context
    response = agent.retrieve_context(query="programming language")
    
    assert response.success is True
    assert response.agent_name == "MemoryAgent"
    assert response.action_taken == "RETRIEVE_CONTEXT"
    assert "context" in response.result
    assert isinstance(response.result["context"], str)
    assert "query" in response.result
    assert response.error is None


def test_retrieve_context_empty_query(agent, test_memory_setup):
    """Test retrieving context with empty query fails."""
    response = agent.retrieve_context(query="")
    
    assert response.success is False
    assert response.action_taken == "RETRIEVE_CONTEXT"
    assert "cannot be empty" in response.error.lower()
    assert response.retry_recommended is False


def test_retrieve_context_invalid_top_k(agent, test_memory_setup):
    """Test retrieving context with invalid top_k fails."""
    response = agent.retrieve_context(query="test", top_k=0)
    
    assert response.success is False
    assert response.action_taken == "RETRIEVE_CONTEXT"
    assert "must be positive" in response.error.lower()


def test_retrieve_context_no_results(agent, test_memory_setup):
    """Test retrieving context when no relevant results exist returns empty string."""
    response = agent.retrieve_context(query="nonexistent query about nothing")
    
    # Should succeed but return empty context
    assert response.success is True
    assert response.result["context"] == ""
    assert response.result["found_results"] is False


def test_execute_task_save_conversation(agent, test_memory_setup):
    """Test execute_task with SAVE_CONVERSATION action."""
    result = agent.execute_task(
        task_description="SAVE_CONVERSATION",
        context={
            "action": "SAVE_CONVERSATION",
            "params": {
                "user_message": "Test message",
                "assistant_response": "Test response"
            }
        }
    )
    
    assert result["success"] is True
    assert result["action_taken"] == "SAVE_CONVERSATION"


def test_execute_task_retrieve_context(agent, test_memory_setup):
    """Test execute_task with RETRIEVE_CONTEXT action."""
    # First save a conversation
    agent.save_conversation("Hello", "Hi there!")
    
    result = agent.execute_task(
        task_description="RETRIEVE_CONTEXT",
        context={
            "action": "RETRIEVE_CONTEXT",
            "params": {
                "query": "greeting"
            }
        }
    )
    
    assert result["success"] is True
    assert result["action_taken"] == "RETRIEVE_CONTEXT"
    assert "context" in result["result"]


def test_execute_task_unknown_action(agent, test_memory_setup):
    """Test execute_task with unknown action."""
    result = agent.execute_task(
        task_description="UNKNOWN_ACTION",
        context={"action": "UNKNOWN_ACTION"}
    )
    
    assert result["success"] is False
    assert "Unknown action" in result["error"]


def test_agent_response_validation(agent, test_memory_setup):
    """Test that AgentResponse objects are valid."""
    response = agent.save_conversation("Test", "Response")
    
    # Should not raise ValueError
    response.validate()
    
    # Check response structure
    assert hasattr(response, "success")
    assert hasattr(response, "agent_name")
    assert hasattr(response, "action_taken")
    assert hasattr(response, "result")
    assert hasattr(response, "error")
    assert hasattr(response, "metadata")


def test_memory_agent_repr(agent):
    """Test string representation."""
    repr_str = repr(agent)
    assert "MemoryAgent" in repr_str
    assert "name='MemoryAgent'" in repr_str
    assert "allowed_actions=2" in repr_str


def test_save_and_retrieve_integration(agent, test_memory_setup):
    """Test full integration: save multiple conversations and retrieve."""
    # Save multiple conversations
    conversations = [
        ("What is Python?", "Python is a programming language."),
        ("How do I learn Python?", "Start with the basics and practice coding."),
        ("What is machine learning?", "Machine learning is a subset of AI.")
    ]
    
    for user_msg, assistant_msg in conversations:
        response = agent.save_conversation(user_msg, assistant_msg)
        assert response.success is True
    
    # Retrieve context related to Python
    response = agent.retrieve_context("Python programming")
    
    assert response.success is True
    context = response.result["context"]
    
    # Context should contain at least one Python-related conversation
    # (depending on similarity threshold in memory.py)
    assert isinstance(context, str)
    # If context is not empty, it should be properly formatted
    if context:
        assert "Memory" in context or len(context) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
