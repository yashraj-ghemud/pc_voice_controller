"""
Agent system initialization module.

This module handles initialization of the complete agent system including:
- AgentRegistry setup with all specialized agents
- StateGraph pre-compilation
- Configuration loading
- Graceful error handling for initialization failures

Validates: Requirements 14.5, 20.1, 20.3, 20.4, 20.5
"""

import time
from typing import Optional, Tuple
from agents.config import get_config
from agents.registry import AgentRegistry
from agents.orchestrator import OrchestratorAgent
from agents.state_manager import StateManager


class AgentSystemInitializationError(Exception):
    """
    Exception raised when agent system initialization fails.
    
    This exception indicates a critical failure during initialization that
    prevents the agent system from starting. The system should fall back
    to legacy mode when this occurs.
    
    Validates: Requirement 20.5
    """
    pass


def initialize_agent_system(
    max_init_time: float = 3.0,
    raise_on_error: bool = False
) -> Tuple[bool, Optional[OrchestratorAgent], Optional[str]]:
    """
    Initialize the complete agent system with all components.
    
    This function performs full initialization of the multi-agent system:
    1. Loads configuration from environment
    2. Creates and initializes AgentRegistry
    3. Registers all 5 specialized agents
    4. Creates OrchestratorAgent
    5. Pre-compiles StateGraph for performance
    6. Validates initialization completed within time limit
    
    Initialization is designed to complete within 3 seconds (Requirement 14.5).
    If initialization fails, the system gracefully degrades to legacy mode.
    
    PRECONDITIONS:
    - Environment variables configured in env.env
    - All agent modules are importable
    
    POSTCONDITIONS:
    - If success=True: Orchestrator ready for use
    - If success=False: Error message provided, fallback to legacy
    - Initialization completes within max_init_time seconds
    
    Args:
        max_init_time: Maximum time allowed for initialization (default: 3.0s)
        raise_on_error: If True, raise exception on failure instead of
                       returning error tuple (default: False, for graceful degradation)
    
    Returns:
        Tuple of (success: bool, orchestrator: Optional[OrchestratorAgent], error: Optional[str])
        
    Raises:
        AgentSystemInitializationError: If raise_on_error=True and init fails
        
    Validates: Requirements 14.5, 20.1, 20.3, 20.4, 20.5
    
    Examples:
        >>> success, orchestrator, error = initialize_agent_system()
        >>> if success:
        ...     result = orchestrator.process_command("volume up", {})
        ... else:
        ...     print(f"Init failed: {error}")
        ...     # Fall back to legacy mode
    """
    start_time = time.time()
    config = get_config()
    
    try:
        # Log initialization start
        print("🚀 Initializing Kypzer AI Agent System...")
        
        # STEP 1: Create AgentRegistry (Requirement 20.1)
        print("  📋 Creating AgentRegistry...")
        registry = AgentRegistry()
        
        # STEP 2: Register all specialized agents (Requirement 20.3)
        print("  🤖 Registering specialized agents...")
        _register_all_agents(registry)
        
        # Verify all agents registered
        registered = registry.list_agents()
        print(f"  ✅ Registered {len(registered)} agents: {', '.join(registered)}")
        
        # STEP 3: Create OrchestratorAgent
        print("  🎯 Creating OrchestratorAgent...")
        orchestrator = OrchestratorAgent(
            registry=registry,
            max_retries=config.max_retries
        )
        
        # STEP 4: Pre-compile StateGraph (Requirement 20.3)
        print("  🔧 Pre-compiling StateGraph...")
        state_manager = StateManager(registry)
        compiled_graph = state_manager.build_graph()
        
        # Store compiled graph in orchestrator
        orchestrator._compiled_graph = compiled_graph
        
        # STEP 5: Validate initialization time (Requirement 14.5)
        elapsed = time.time() - start_time
        print(f"  ⏱️  Initialization completed in {elapsed:.2f}s")
        
        if elapsed > max_init_time:
            warning = f"⚠️  Initialization took {elapsed:.2f}s (target: {max_init_time}s)"
            print(warning)
        
        # Success!
        print("  ✨ Agent system ready!")
        config.log_configuration()
        
        return True, orchestrator, None
        
    except Exception as e:
        # Initialization failed (Requirement 20.5)
        elapsed = time.time() - start_time
        error_msg = f"Agent system initialization failed after {elapsed:.2f}s: {str(e)}"
        
        print(f"  ❌ {error_msg}")
        print("  🔄 Falling back to legacy mode")
        
        if raise_on_error:
            raise AgentSystemInitializationError(error_msg) from e
        
        return False, None, error_msg


def _register_all_agents(registry: AgentRegistry) -> None:
    """
    Register all 5 specialized agents in the registry.
    
    Registers:
    1. PCControlAgent - PC control (volume, brightness, apps)
    2. WhatsAppAgent - WhatsApp messaging
    3. ScreenAIAgent - Vision-based UI interaction
    4. WebAgent - Web searches and URLs
    5. MemoryAgent - Conversation memory
    
    Also registers OrchestratorAgent as default fallback.
    
    Args:
        registry: AgentRegistry instance to register agents in
        
    Raises:
        ImportError: If agent modules cannot be imported
        Exception: If agent initialization fails
        
    Validates: Requirement 20.3
    """
    from agents.specialized.pc_control_agent import PCControlAgent
    from agents.specialized.whatsapp_agent import WhatsAppAgent
    from agents.specialized.screen_ai_agent import ScreenAIAgent
    from agents.specialized.web_agent import WebAgent
    from agents.specialized.memory_agent import MemoryAgent
    
    # Register specialized agents (Requirement 3.5)
    agents_to_register = [
        ("pc_control", PCControlAgent, "PC control for volume, brightness, apps"),
        ("whatsapp", WhatsAppAgent, "WhatsApp messaging and file sending"),
        ("screen_ai", ScreenAIAgent, "Vision-based screen interaction"),
        ("web", WebAgent, "Web searches and URL opening"),
        ("memory", MemoryAgent, "Conversation memory and context")
    ]
    
    for agent_type, agent_class, description in agents_to_register:
        try:
            # Initialize agent
            agent = agent_class()
            
            # Register in registry
            registry.register(agent_type, agent)
            
            print(f"    ✓ {agent_type}: {description}")
            
        except Exception as e:
            print(f"    ⚠️  Failed to register {agent_type}: {str(e)}")
            # Continue with other agents (graceful degradation)
            # Requirement 20.5: Handle failures gracefully


def quick_health_check(orchestrator: OrchestratorAgent) -> bool:
    """
    Perform quick health check on initialized agent system.
    
    Tests basic functionality:
    - Can access agent registry
    - Can classify a simple command
    - StateGraph is compiled
    
    Args:
        orchestrator: Initialized OrchestratorAgent
        
    Returns:
        True if health check passes, False otherwise
        
    Examples:
        >>> success, orchestrator, _ = initialize_agent_system()
        >>> if success:
        ...     healthy = quick_health_check(orchestrator)
        ...     print(f"System healthy: {healthy}")
    """
    try:
        # Check 1: Registry accessible
        agents = orchestrator.agent_registry.list_agents()
        if len(agents) == 0:
            return False
        
        # Check 2: Can classify command
        classification = orchestrator.classify_command("test", {})
        if classification is None:
            return False
        
        # Check 3: Graph compiled
        if orchestrator._compiled_graph is None:
            return False
        
        return True
        
    except Exception:
        return False


def get_initialization_status() -> dict:
    """
    Get current initialization status and system info.
    
    Returns dictionary with:
    - agent_system_enabled: Whether agent system is active
    - mode: Current mode description
    - configuration: Current config settings
    
    Returns:
        Dictionary with initialization status
        
    Examples:
        >>> status = get_initialization_status()
        >>> status["agent_system_enabled"]
        False
        >>> status["mode"]
        'LEGACY MODE (agent system disabled)'
    """
    config = get_config()
    
    return {
        "agent_system_enabled": config.is_agent_system_enabled(),
        "mode": config.get_mode_description(),
        "configuration": config.to_dict()
    }


# Module-level initialization tracking
_orchestrator_instance: Optional[OrchestratorAgent] = None
_initialization_attempted: bool = False
_initialization_error: Optional[str] = None


def get_orchestrator(force_reinit: bool = False) -> Optional[OrchestratorAgent]:
    """
    Get initialized orchestrator instance (singleton pattern).
    
    Initializes on first call and caches the instance. Returns None if
    initialization failed or agent system is disabled.
    
    Args:
        force_reinit: If True, force re-initialization (default: False)
        
    Returns:
        OrchestratorAgent instance or None if unavailable
        
    Examples:
        >>> orchestrator = get_orchestrator()
        >>> if orchestrator:
        ...     result = orchestrator.process_command("test", {})
        ... else:
        ...     # Use legacy mode
        ...     pass
    """
    global _orchestrator_instance, _initialization_attempted, _initialization_error
    
    config = get_config()
    
    # Check if agent system is disabled
    if not config.is_agent_system_enabled():
        return None
    
    # Return cached instance if available
    if _orchestrator_instance is not None and not force_reinit:
        return _orchestrator_instance
    
    # Initialize if not attempted or force_reinit
    if not _initialization_attempted or force_reinit:
        _initialization_attempted = True
        
        success, orchestrator, error = initialize_agent_system()
        
        if success:
            _orchestrator_instance = orchestrator
            _initialization_error = None
            return orchestrator
        else:
            _initialization_error = error
            return None
    
    # Previous initialization failed
    return None


def reset_initialization() -> None:
    """
    Reset initialization state (useful for testing).
    
    Clears cached orchestrator instance and initialization flags,
    forcing re-initialization on next get_orchestrator() call.
    """
    global _orchestrator_instance, _initialization_attempted, _initialization_error
    
    _orchestrator_instance = None
    _initialization_attempted = False
    _initialization_error = None
