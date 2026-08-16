"""
Configuration management for the agent system.

This module loads and manages configuration settings for the multi-agent system,
including feature flags, timeouts, and retry settings. Configuration is loaded
from environment variables defined in env.env.

Validates: Requirements 17.1, 17.2, 17.3, 17.4, 17.5
"""

import os
from typing import Optional
from dotenv import load_dotenv


# Load environment variables from env.env
load_dotenv("env.env")


class AgentSystemConfig:
    """
    Configuration manager for the agent system.
    
    Loads configuration from environment variables and provides easy access
    to settings throughout the agent system. Supports feature flags for
    enabling/disabling the agent system and kill switches for emergency rollback.
    
    Configuration Variables:
        - USE_AGENT_SYSTEM: Enable/disable multi-agent system (default: false)
        - DISABLE_AGENT_SYSTEM: Emergency kill switch (default: false)
        - MAX_AGENT_RETRIES: Maximum retry attempts (default: 3)
        - AGENT_EXECUTION_TIMEOUT: Agent execution timeout in seconds (default: 120)
        - GRAPH_EXECUTION_TIMEOUT: Graph execution timeout in seconds (default: 10)
    
    Validates: Requirements 17.1, 17.2, 17.3, 17.4, 17.5
    
    Examples:
        >>> config = AgentSystemConfig()
        >>> config.is_agent_system_enabled()
        False
        >>> config.max_retries
        3
        >>> config.graph_timeout
        10
    """
    
    def __init__(self):
        """
        Initialize configuration by loading from environment variables.
        
        Configuration is loaded once at initialization and cached. Changes to
        environment variables after initialization require creating a new
        AgentSystemConfig instance.
        """
        # Feature flags (Requirements 17.1, 17.2, 17.3)
        self.use_agent_system = self._get_bool_env("USE_AGENT_SYSTEM", False)
        self.disable_agent_system = self._get_bool_env("DISABLE_AGENT_SYSTEM", False)
        
        # Retry configuration (Requirement 9.3)
        self.max_retries = self._get_int_env("MAX_AGENT_RETRIES", 3)
        
        # Timeout configuration (Requirements 30.1, 30.2)
        self.agent_timeout = self._get_int_env("AGENT_EXECUTION_TIMEOUT", 120)
        self.graph_timeout = self._get_int_env("GRAPH_EXECUTION_TIMEOUT", 10)
    
    def is_agent_system_enabled(self) -> bool:
        """
        Check if agent system should be used for command processing.
        
        The agent system is enabled if:
        - USE_AGENT_SYSTEM is "true" AND
        - DISABLE_AGENT_SYSTEM is NOT "true"
        
        The DISABLE_AGENT_SYSTEM flag acts as a kill switch that overrides
        USE_AGENT_SYSTEM, allowing instant rollback to legacy mode.
        
        Returns:
            True if agent system should be used, False for legacy mode
            
        Validates: Requirements 17.1, 17.2, 17.3
        
        Examples:
            >>> config = AgentSystemConfig()
            >>> # Default: both false
            >>> config.is_agent_system_enabled()
            False
            
            >>> # Kill switch overrides enable flag
            >>> config.use_agent_system = True
            >>> config.disable_agent_system = True
            >>> config.is_agent_system_enabled()
            False
        """
        # Kill switch takes precedence (Requirement 17.3)
        if self.disable_agent_system:
            return False
        
        return self.use_agent_system
    
    def get_mode_description(self) -> str:
        """
        Get human-readable description of current configuration mode.
        
        Returns:
            String describing active mode (agent system or legacy)
            
        Examples:
            >>> config = AgentSystemConfig()
            >>> config.get_mode_description()
            'LEGACY MODE (agent system disabled)'
        """
        if self.disable_agent_system:
            return "LEGACY MODE (kill switch active)"
        elif self.use_agent_system:
            return "AGENT SYSTEM ENABLED"
        else:
            return "LEGACY MODE (agent system disabled)"
    
    def log_configuration(self, logger=None) -> None:
        """
        Log current configuration settings.
        
        Logs the active mode and key configuration parameters. Uses provided
        logger or prints to stdout if no logger provided.
        
        Args:
            logger: Optional logger instance (uses print if None)
            
        Validates: Requirement 17.5
        
        Examples:
            >>> config = AgentSystemConfig()
            >>> config.log_configuration()
            🤖 KYPZER AI - Agent System Configuration
            ==========================================
            Mode: LEGACY MODE (agent system disabled)
            Max Retries: 3
            Agent Timeout: 120s
            Graph Timeout: 10s
            ==========================================
        """
        log_func = logger.info if logger else print
        
        log_func("🤖 KYPZER AI - Agent System Configuration")
        log_func("=" * 42)
        log_func(f"Mode: {self.get_mode_description()}")
        log_func(f"Max Retries: {self.max_retries}")
        log_func(f"Agent Timeout: {self.agent_timeout}s")
        log_func(f"Graph Timeout: {self.graph_timeout}s")
        log_func("=" * 42)
    
    def _get_bool_env(self, key: str, default: bool) -> bool:
        """
        Get boolean value from environment variable.
        
        Accepts "true", "yes", "1" as True (case-insensitive).
        All other values are treated as False.
        
        Args:
            key: Environment variable name
            default: Default value if not set
            
        Returns:
            Boolean value
        """
        value = os.getenv(key)
        if value is None:
            return default
        return value.lower() in ("true", "yes", "1")
    
    def _get_int_env(self, key: str, default: int) -> int:
        """
        Get integer value from environment variable.
        
        Args:
            key: Environment variable name
            default: Default value if not set or invalid
            
        Returns:
            Integer value
        """
        value = os.getenv(key)
        if value is None:
            return default
        
        try:
            return int(value)
        except ValueError:
            return default
    
    def to_dict(self) -> dict:
        """
        Convert configuration to dictionary.
        
        Returns:
            Dictionary with all configuration values
            
        Examples:
            >>> config = AgentSystemConfig()
            >>> d = config.to_dict()
            >>> "use_agent_system" in d
            True
        """
        return {
            "use_agent_system": self.use_agent_system,
            "disable_agent_system": self.disable_agent_system,
            "is_enabled": self.is_agent_system_enabled(),
            "mode": self.get_mode_description(),
            "max_retries": self.max_retries,
            "agent_timeout": self.agent_timeout,
            "graph_timeout": self.graph_timeout
        }
    
    def __repr__(self) -> str:
        """String representation of configuration."""
        return (
            f"AgentSystemConfig("
            f"enabled={self.is_agent_system_enabled()}, "
            f"mode='{self.get_mode_description()}', "
            f"max_retries={self.max_retries})"
        )


# Global configuration instance
# This can be imported and used throughout the agent system
_config_instance: Optional[AgentSystemConfig] = None


def get_config() -> AgentSystemConfig:
    """
    Get global configuration instance (singleton pattern).
    
    Creates configuration on first call and returns cached instance
    on subsequent calls. To reload configuration, call reload_config().
    
    Returns:
        AgentSystemConfig instance
        
    Examples:
        >>> config = get_config()
        >>> config.is_agent_system_enabled()
        False
        >>> # Same instance returned
        >>> config2 = get_config()
        >>> config is config2
        True
    """
    global _config_instance
    
    if _config_instance is None:
        _config_instance = AgentSystemConfig()
    
    return _config_instance


def reload_config() -> AgentSystemConfig:
    """
    Reload configuration from environment variables.
    
    Forces reload of configuration by creating a new AgentSystemConfig
    instance. Useful for testing or when environment variables change
    at runtime.
    
    Returns:
        New AgentSystemConfig instance
        
    Examples:
        >>> config1 = get_config()
        >>> # Change environment
        >>> os.environ["USE_AGENT_SYSTEM"] = "true"
        >>> config2 = reload_config()
        >>> config1 is config2
        False
    """
    global _config_instance
    
    # Reload .env file
    load_dotenv("env.env", override=True)
    
    # Create new instance
    _config_instance = AgentSystemConfig()
    
    return _config_instance


def is_agent_system_enabled() -> bool:
    """
    Convenience function to check if agent system is enabled.
    
    Returns:
        True if agent system enabled, False otherwise
        
    Examples:
        >>> is_agent_system_enabled()
        False
    """
    return get_config().is_agent_system_enabled()
