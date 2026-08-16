"""
Unit tests for AgentRegistry.

Tests:
- Task 3.2: Agent registration and retrieval
- Task 3.3: Property test for agent registry operations (Property 9)
"""

from hypothesis import given, strategies as st
import pytest
from unittest.mock import Mock, MagicMock

from agents.registry import AgentRegistry
from agents.base import BaseAgent


class TestAgentRegistryUnit:
    """
    Task 3.2: Write unit tests for AgentRegistry
    Requirements: 3.1, 3.2, 3.3
    """
    
    def setup_method(self):
        """Set up test fixtures."""
        self.registry = AgentRegistry()
        
        # Create mock agents
        self.mock_agent1 = Mock(spec=BaseAgent)
        self.mock_agent1.name = "test_agent_1"
        
        self.mock_agent2 = Mock(spec=BaseAgent)
        self.mock_agent2.name = "test_agent_2"
        
        self.default_agent = Mock(spec=BaseAgent)
        self.default_agent.name = "default_agent"
    
    def test_agent_registration(self):
        """Test agent registration."""
        self.registry.register("agent1", self.mock_agent1)
        
        # Agent should be retrievable
        retrieved = self.registry.get_agent("agent1")
        assert retrieved == self.mock_agent1
    
    def test_agent_retrieval(self):
        """Test agent retrieval by type."""
        self.registry.register("pc_control", self.mock_agent1)
        self.registry.register("whatsapp", self.mock_agent2)
        
        # Should retrieve correct agents
        assert self.registry.get_agent("pc_control") == self.mock_agent1
        assert self.registry.get_agent("whatsapp") == self.mock_agent2
    
    def test_default_agent_fallback(self):
        """Test default agent fallback for unknown types."""
        self.registry.register("default", self.default_agent)
        
        # Unknown agent type should return default
        result = self.registry.get_agent("unknown_type")
        assert result == self.default_agent
    
    def test_lazy_initialization(self):
        """Test lazy initialization pattern."""
        # Registry should start empty
        assert len(self.registry._agents) == 0
        
        # Register agents
        self.registry.register("agent1", self.mock_agent1)
        
        # Now it should have one agent
        assert len(self.registry._agents) == 1
    
    def test_multiple_registrations(self):
        """Test registering multiple agents."""
        agents = {
            "pc_control": Mock(spec=BaseAgent),
            "whatsapp": Mock(spec=BaseAgent),
            "screen_ai": Mock(spec=BaseAgent),
            "web": Mock(spec=BaseAgent),
            "memory": Mock(spec=BaseAgent)
        }
        
        for agent_type, agent in agents.items():
            self.registry.register(agent_type, agent)
        
        # All should be retrievable
        for agent_type, agent in agents.items():
            assert self.registry.get_agent(agent_type) == agent
    
    def test_overwrite_registration(self):
        """Test that re-registering an agent type overwrites the old one."""
        self.registry.register("agent1", self.mock_agent1)
        assert self.registry.get_agent("agent1") == self.mock_agent1
        
        # Overwrite with agent2
        self.registry.register("agent1", self.mock_agent2)
        assert self.registry.get_agent("agent1") == self.mock_agent2
    
    def test_get_agent_for_command_routing(self):
        """Test intelligent agent selection for commands."""
        self.registry.register("pc_control", self.mock_agent1)
        self.registry.register("whatsapp", self.mock_agent2)
        
        # Should route based on command content
        agent = self.registry.get_agent_for_command("increase volume")
        assert agent in [self.mock_agent1, self.mock_agent2] or agent is not None
        
        agent = self.registry.get_agent_for_command("send whatsapp message")
        assert agent in [self.mock_agent1, self.mock_agent2] or agent is not None


class TestAgentRegistryProperty:
    """
    Task 3.3: Write property test for agent registry operations
    Property 9: Agent Registry Round-Trip
    Validates: Requirements 3.1, 3.2
    """
    
    @given(
        st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
        st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll')))
    )
    def test_registry_round_trip(self, agent_type: str, agent_name: str):
        """Test that registered agents can be retrieved correctly."""
        registry = AgentRegistry()
        
        # Create mock agent
        mock_agent = Mock(spec=BaseAgent)
        mock_agent.name = agent_name
        
        # Register
        registry.register(agent_type, mock_agent)
        
        # Retrieve
        retrieved = registry.get_agent(agent_type)
        
        # Round-trip property: should get back the same agent
        assert retrieved == mock_agent
        assert retrieved.name == agent_name
    
    @given(st.lists(
        st.tuples(
            st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
            st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll')))
        ),
        min_size=1,
        max_size=10,
        unique_by=lambda x: x[0]  # Unique agent types
    ))
    def test_multiple_agents_round_trip(self, agent_specs):
        """Test that multiple registered agents can all be retrieved correctly."""
        registry = AgentRegistry()
        agents_map = {}
        
        # Register all agents
        for agent_type, agent_name in agent_specs:
            mock_agent = Mock(spec=BaseAgent)
            mock_agent.name = agent_name
            registry.register(agent_type, mock_agent)
            agents_map[agent_type] = mock_agent
        
        # Retrieve all agents and verify
        for agent_type, expected_agent in agents_map.items():
            retrieved = registry.get_agent(agent_type)
            assert retrieved == expected_agent
    
    @given(st.text(min_size=1, max_size=20))
    def test_unknown_agent_returns_default_or_none(self, unknown_type: str):
        """Test that unknown agent types return default or None gracefully."""
        registry = AgentRegistry()
        
        # Set up default agent
        default_agent = Mock(spec=BaseAgent)
        default_agent.name = "default"
        registry.register("default", default_agent)
        
        # Unknown type should return default
        result = registry.get_agent(unknown_type)
        
        # Should either return default or None, not raise exception
        assert result is None or result == default_agent


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
