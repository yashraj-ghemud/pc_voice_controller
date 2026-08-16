"""
Agent Registry for centralized agent management.

This module provides the AgentRegistry class that manages registration,
retrieval, and intelligent selection of specialized agents. It implements
lazy initialization patterns for optimal performance and provides a default
fallback mechanism.

The registry is the central hub for agent discovery and management in the
Kypzer AI multi-agent system.

Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 20.1, 20.2
"""

from typing import Optional, Dict, Callable
from agents.base import BaseAgent


def create_default_registry() -> 'AgentRegistry':
    """
    Create and initialize an AgentRegistry with all specialized agents.
    
    This factory function creates a fully configured AgentRegistry with all
    five specialized agents registered using lazy initialization. Agents are
    created only when first requested, optimizing startup time and memory usage.
    
    Registered agents:
    - pc_control: PCControlAgent for system control (volume, brightness, apps)
    - whatsapp: WhatsAppAgent for messaging and file sharing
    - screen_ai: ScreenAIAgent for vision-based UI interaction
    - web: WebAgent for web searches and browser automation
    - memory: MemoryAgent for conversation context management
    
    Returns:
        AgentRegistry instance with all specialized agents registered
        
    Validates: Requirements 3.5, 20.1, 20.3
    
    Examples:
        >>> registry = create_default_registry()
        >>> registry.list_agents()
        ['pc_control', 'whatsapp', 'screen_ai', 'web', 'memory']
        
        >>> # Get an agent (lazy initialization)
        >>> agent = registry.get_agent("whatsapp")
        >>> agent.agent_type
        'whatsapp'
    """
    from agents.specialized.pc_control_agent import PCControlAgent
    from agents.specialized.whatsapp_agent import WhatsAppAgent
    from agents.specialized.screen_ai_agent import ScreenAIAgent
    from agents.specialized.web_agent import WebAgent
    from agents.specialized.memory_agent import MemoryAgent
    
    registry = AgentRegistry()
    
    # Register all five specialized agents with lazy initialization
    # Agents will be created only when first requested (Requirement 20.1)
    
    registry.register("pc_control", lambda: PCControlAgent())
    registry.register("whatsapp", lambda: WhatsAppAgent())
    registry.register("screen_ai", lambda: ScreenAIAgent())
    registry.register("web", lambda: WebAgent())
    registry.register("memory", lambda: MemoryAgent())
    
    return registry


class AgentRegistry:
    """
    Centralized registry for managing and discovering agents.
    
    The AgentRegistry implements lazy initialization patterns to optimize
    performance by only creating agent instances when they're first requested.
    It provides intelligent agent selection based on command analysis and
    includes a default fallback mechanism.
    
    Attributes:
        _agents: Dictionary mapping agent_type to agent instances or factories
        _instances: Cache of initialized agent instances (lazy initialization)
        _default_agent: Fallback agent when no specific agent is registered
        
    Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 20.1, 20.2
    
    Examples:
        >>> registry = AgentRegistry()
        >>> registry.register("pc_control", pc_control_agent)
        >>> agent = registry.get_agent("pc_control")
        >>> agent.agent_type
        'pc_control'
        
        >>> # With lazy initialization
        >>> registry = AgentRegistry()
        >>> registry.register("whatsapp", lambda: create_whatsapp_agent())
        >>> agent = registry.get_agent("whatsapp")  # Factory called here
    """
    
    def __init__(self, default_agent: Optional[BaseAgent] = None):
        """
        Initialize the AgentRegistry.
        
        Args:
            default_agent: Optional default agent to return when requested
                agent type is not registered. If None, a RuntimeError will
                be raised when accessing unregistered agents without a default.
                
        Examples:
            >>> registry = AgentRegistry()
            >>> registry = AgentRegistry(default_agent=orchestrator_agent)
        """
        self._agents: Dict[str, BaseAgent | Callable[[], BaseAgent]] = {}
        self._instances: Dict[str, BaseAgent] = {}
        self._default_agent = default_agent
    
    def register(
        self, 
        agent_type: str, 
        agent: BaseAgent | Callable[[], BaseAgent]
    ) -> None:
        """
        Register an agent with a unique agent_type identifier.
        
        Supports both direct agent instances and factory functions for lazy
        initialization. When a factory function is provided, the agent will
        be created only when first requested via get_agent().
        
        Args:
            agent_type: Unique identifier for the agent (e.g., "pc_control",
                "whatsapp", "screen_ai", "web", "memory")
            agent: Either a BaseAgent instance or a factory function that
                returns a BaseAgent instance
                
        Raises:
            ValueError: If agent_type is empty or agent is None
            
        Validates: Requirement 3.1
        
        Examples:
            >>> # Direct registration
            >>> registry.register("pc_control", pc_control_agent)
            
            >>> # Lazy registration with factory
            >>> registry.register("whatsapp", lambda: WhatsAppAgent(...))
            
            >>> # Registration validates input
            >>> registry.register("", agent)
            Traceback (most recent call last):
            ...
            ValueError: agent_type cannot be empty
        """
        if not agent_type:
            raise ValueError("agent_type cannot be empty")
        
        if agent is None:
            raise ValueError("agent cannot be None")
        
        # Store the agent or factory
        self._agents[agent_type] = agent
        
        # If it's an instance (not a factory), cache it immediately
        if isinstance(agent, BaseAgent):
            self._instances[agent_type] = agent
    
    def get_agent(self, agent_type: str) -> BaseAgent:
        """
        Retrieve an agent by its type identifier.
        
        Implements lazy initialization - if the agent was registered as a
        factory function, it will be created on first access and cached for
        subsequent calls. If the agent type is not registered, returns the
        default agent if one was provided during initialization.
        
        Args:
            agent_type: The agent type identifier to retrieve
            
        Returns:
            BaseAgent instance for the requested type, or the default agent
            if the type is not registered and a default was provided
            
        Raises:
            ValueError: If agent_type is empty
            RuntimeError: If agent_type is not registered and no default
                agent was provided
                
        Validates: Requirements 3.2, 3.3, 20.1
        
        Examples:
            >>> agent = registry.get_agent("pc_control")
            >>> agent.agent_type
            'pc_control'
            
            >>> # Lazy initialization
            >>> registry.register("whatsapp", lambda: WhatsAppAgent(...))
            >>> agent = registry.get_agent("whatsapp")  # Factory called here
            >>> same_agent = registry.get_agent("whatsapp")  # Cached, not recreated
            >>> agent is same_agent
            True
            
            >>> # Default fallback
            >>> registry = AgentRegistry(default_agent=orchestrator)
            >>> agent = registry.get_agent("unknown_type")
            >>> agent is orchestrator
            True
        """
        if not agent_type:
            raise ValueError("agent_type cannot be empty")
        
        # Check if already initialized (cached)
        if agent_type in self._instances:
            return self._instances[agent_type]
        
        # Check if registered
        if agent_type in self._agents:
            agent_or_factory = self._agents[agent_type]
            
            # If it's a factory function, call it to create the agent
            if callable(agent_or_factory) and not isinstance(agent_or_factory, BaseAgent):
                agent = agent_or_factory()
                # Cache the instance for subsequent calls (Requirement 20.2)
                self._instances[agent_type] = agent
                return agent
            
            # Otherwise it's already an instance
            return agent_or_factory
        
        # Not registered - use default agent if available (Requirement 3.3)
        if self._default_agent is not None:
            return self._default_agent
        
        # No default available
        raise RuntimeError(
            f"Agent type '{agent_type}' is not registered and no default "
            f"agent was provided. Available types: {list(self._agents.keys())}"
        )
    
    def get_agent_for_command(self, command: str) -> BaseAgent:
        """
        Intelligently select the most suitable agent for a command.
        
        Analyzes the command text to determine which specialized agent should
        handle it. Uses keyword matching and pattern recognition to route
        commands to the appropriate domain expert.
        
        Command routing logic:
        - Volume/brightness/app control → pc_control
        - WhatsApp/message/contact → whatsapp
        - Screen/click/type/wait → screen_ai
        - Search/browse/open URL → web
        - Remember/recall/context → memory
        - Default → fallback to default agent
        
        Args:
            command: User command text to analyze
            
        Returns:
            BaseAgent instance best suited for the command
            
        Raises:
            ValueError: If command is empty or None
            RuntimeError: If no suitable agent is found and no default exists
            
        Validates: Requirements 3.4, 3.5
        
        Examples:
            >>> agent = registry.get_agent_for_command("increase volume")
            >>> agent.agent_type
            'pc_control'
            
            >>> agent = registry.get_agent_for_command("send message to John")
            >>> agent.agent_type
            'whatsapp'
            
            >>> agent = registry.get_agent_for_command("click the submit button")
            >>> agent.agent_type
            'screen_ai'
        """
        if not command:
            raise ValueError("command cannot be empty or None")
        
        # Normalize command for analysis
        command_lower = command.lower()
        
        # WhatsApp patterns (check first to avoid keyword conflicts)
        whatsapp_keywords = [
            "whatsapp", "send message", "send file", "contact", "chat",
            "voice note", "bhejo", "message to"
        ]
        if any(keyword in command_lower for keyword in whatsapp_keywords):
            if "whatsapp" in self._agents:
                return self.get_agent("whatsapp")
        
        # Web patterns (check before PC control to handle URLs)
        web_keywords = [
            "search", "google", "browse", "website", "url", ".com", ".org",
            "internet", "online", "lookup", "find online", "web"
        ]
        if any(keyword in command_lower for keyword in web_keywords):
            if "web" in self._agents:
                return self.get_agent("web")
        
        # PC Control patterns (more specific, avoid URL conflicts)
        pc_control_keywords = [
            "volume", "brightness", "launch app", "open app", "close app",
            "application", "wifi", "bluetooth", "display",
            "window", "minimize", "maximize"
        ]
        if any(keyword in command_lower for keyword in pc_control_keywords):
            if "pc_control" in self._agents:
                return self.get_agent("pc_control")
        
        # Screen AI patterns (more specific patterns to avoid false matches)
        screen_ai_keywords = [
            "click", "type", "wait", "screenshot", "button",
            "input", "field", "element", "ui", "interface"
        ]
        if any(keyword in command_lower for keyword in screen_ai_keywords):
            if "screen_ai" in self._agents:
                return self.get_agent("screen_ai")
        
        # Web patterns
        web_keywords = [
            "search", "google", "browse", "website", "url", "web",
            "internet", "online", "lookup", "find"
        ]
        if any(keyword in command_lower for keyword in web_keywords):
            if "web" in self._agents:
                return self.get_agent("web")
        
        # Memory patterns
        memory_keywords = [
            "remember", "recall", "memory", "context", "history",
            "previous", "before", "earlier", "save", "store"
        ]
        if any(keyword in command_lower for keyword in memory_keywords):
            if "memory" in self._agents:
                return self.get_agent("memory")
        
        # Default fallback (Requirement 3.3)
        if self._default_agent is not None:
            return self._default_agent
        
        # No suitable agent found
        raise RuntimeError(
            f"No suitable agent found for command: '{command}'. "
            f"Available agent types: {list(self._agents.keys())}"
        )
    
    def list_agents(self) -> list[str]:
        """
        List all registered agent types.
        
        Returns:
            List of agent_type identifiers currently registered
            
        Examples:
            >>> registry.register("pc_control", agent1)
            >>> registry.register("whatsapp", agent2)
            >>> registry.list_agents()
            ['pc_control', 'whatsapp']
        """
        return list(self._agents.keys())
    
    def is_registered(self, agent_type: str) -> bool:
        """
        Check if an agent type is registered.
        
        Args:
            agent_type: The agent type to check
            
        Returns:
            True if the agent type is registered, False otherwise
            
        Examples:
            >>> registry.register("pc_control", agent)
            >>> registry.is_registered("pc_control")
            True
            >>> registry.is_registered("unknown")
            False
        """
        return agent_type in self._agents
    
    def unregister(self, agent_type: str) -> None:
        """
        Unregister an agent type.
        
        Removes both the agent/factory and any cached instance.
        
        Args:
            agent_type: The agent type to unregister
            
        Raises:
            ValueError: If agent_type is not registered
            
        Examples:
            >>> registry.register("test", agent)
            >>> registry.unregister("test")
            >>> registry.is_registered("test")
            False
        """
        if agent_type not in self._agents:
            raise ValueError(
                f"Agent type '{agent_type}' is not registered. "
                f"Available types: {list(self._agents.keys())}"
            )
        
        # Remove from both dictionaries
        del self._agents[agent_type]
        if agent_type in self._instances:
            del self._instances[agent_type]
    
    def clear(self) -> None:
        """
        Clear all registered agents and cached instances.
        
        Examples:
            >>> registry.register("test1", agent1)
            >>> registry.register("test2", agent2)
            >>> registry.clear()
            >>> registry.list_agents()
            []
        """
        self._agents.clear()
        self._instances.clear()
    
    def __repr__(self) -> str:
        """String representation of the registry."""
        agent_count = len(self._agents)
        cached_count = len(self._instances)
        return (
            f"AgentRegistry(agents={agent_count}, "
            f"cached={cached_count}, "
            f"default={'set' if self._default_agent else 'None'})"
        )
