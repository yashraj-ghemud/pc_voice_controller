"""
PCControlAgent - Specialized agent for system control commands.

This module implements the PCControlAgent class that handles system-level
control operations including volume, brightness, application management,
media controls, and desktop switching.

The agent extends AutoGen's AssistantAgent pattern but is implemented as
a BaseAgent to integrate with the existing actions.py infrastructure.

Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 15.1, 15.2
"""

from typing import Optional, Any
from agents.base import BaseAgent
from agents.models import AgentResponse, success_response, error_response
import actions


class PCControlAgent(BaseAgent):
    """
    Specialized agent for PC system control operations.
    
    This agent handles:
    - Volume control (up, down, set, mute, unmute)
    - Brightness control (up, down, set)
    - Application management (open, close)
    - Media controls (play, pause, stop, next, previous)
    - Desktop switching (left, right)
    - System actions (screenshot, lock, shutdown, restart, sleep)
    
    The agent validates all actions against an allowed_actions list for
    security and uses the existing actions.py module for execution.
    
    Attributes:
        allowed_actions: Set of permitted action types
        action_executor: Reference to actions module for execution
        
    Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 15.1
    
    Examples:
        >>> agent = PCControlAgent()
        >>> result = agent.execute_system_command("VOLUME_UP", {})
        >>> result.success
        True
        >>> result.action_taken
        'VOLUME_UP'
        
        >>> # Unauthorized action
        >>> result = agent.execute_system_command("HACK_SYSTEM", {})
        >>> result.success
        False
        >>> "not authorized" in result.error.lower()
        True
    """
    
    # Define allowed actions for security (Requirement 15.1)
    ALLOWED_ACTIONS = {
        # Volume control
        "VOLUME_UP",
        "VOLUME_DOWN",
        "SET_VOLUME",
        "MUTE",
        "UNMUTE",
        
        # Brightness control
        "BRIGHTNESS_UP",
        "BRIGHTNESS_DOWN",
        "SET_BRIGHTNESS",
        
        # Application management
        "OPEN_APP",
        "CLOSE_APP",
        
        # Media controls
        "PLAY_MEDIA",
        "PAUSE_MEDIA",
        "STOP_MEDIA",
        "NEXT_TRACK",
        "PREV_TRACK",
        
        # Desktop switching
        "SWITCH_DESKTOP_LEFT",
        "SWITCH_DESKTOP_RIGHT",
        
        # System actions
        "SCREENSHOT",
        "LOCK",
        "SLEEP",
        # Note: SHUTDOWN and RESTART are intentionally excluded for safety
        # They should require explicit confirmation in higher-level orchestration
    }
    
    def __init__(
        self,
        name: str = "PCControlAgent",
        action_executor: Any = None
    ):
        """
        Initialize PCControlAgent.
        
        Args:
            name: Agent name (default: "PCControlAgent")
            action_executor: Optional custom executor (defaults to actions module)
            
        Examples:
            >>> agent = PCControlAgent()
            >>> agent.name
            'PCControlAgent'
            >>> agent.agent_type
            'pc_control'
        """
        super().__init__(
            name=name,
            agent_type="pc_control",
            description="Specialized agent for system control: volume, brightness, apps, media"
        )
        
        # Use existing actions.py module for execution
        self.action_executor = action_executor or actions
    
    def execute_task(
        self,
        task_description: str,
        context: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """
        Execute a PC control task.
        
        This method implements the BaseAgent interface. It parses the task
        description to extract action type and parameters, then delegates
        to execute_system_command.
        
        Args:
            task_description: Natural language task description or action name
            context: Optional context with parsed parameters
            
        Returns:
            Dictionary with execution result (converted from AgentResponse)
            
        Examples:
            >>> agent = PCControlAgent()
            >>> result = agent.execute_task("VOLUME_UP")
            >>> result["success"]
            True
        """
        # Extract action from context if available
        action = context.get("action") if context else None
        params = context.get("params", {}) if context else {}
        
        # If action not in context, use task_description as action
        if not action:
            action = task_description.strip().upper()
        
        # Execute system command
        response = self.execute_system_command(action, params)
        
        # Convert AgentResponse to dict for BaseAgent interface
        return response.to_dict()
    
    def execute_system_command(
        self,
        action: str,
        params: Optional[dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Execute a system control command.
        
        This is the main execution method for PC control operations. It:
        1. Validates action is in allowed_actions list (Requirement 15.1)
        2. Extracts parameters (target, value)
        3. Calls appropriate actions.py function
        4. Returns AgentResponse with result
        
        PRECONDITIONS:
        - action is non-empty string
        - If action requires parameters, params contains them
        
        POSTCONDITIONS:
        - Returns AgentResponse with success status
        - If success=False, error message is provided
        - If action fails transiently, retry_recommended=True
        
        Args:
            action: Action type (e.g., "VOLUME_UP", "OPEN_APP")
            params: Optional parameters dict with:
                - target: Target for action (e.g., app name)
                - value: Value for action (e.g., volume level)
                
        Returns:
            AgentResponse with execution result
            
        Raises:
            ValueError: If action is not authorized (Requirement 15.2)
            
        Validates: Requirements 4.3, 4.4, 4.5, 15.1, 15.2
        
        Examples:
            >>> agent = PCControlAgent()
            >>> response = agent.execute_system_command("VOLUME_UP", {})
            >>> response.success
            True
            >>> response.agent_name
            'PCControlAgent'
            
            >>> # Action with parameters
            >>> response = agent.execute_system_command(
            ...     "SET_VOLUME",
            ...     {"value": 50}
            ... )
            >>> response.success
            True
            
            >>> # Open application
            >>> response = agent.execute_system_command(
            ...     "OPEN_APP",
            ...     {"target": "chrome"}
            ... )
            >>> response.success
            True
        """
        params = params or {}
        action = action.strip().upper()
        
        # Requirement 15.1: Validate action is authorized
        if action not in self.ALLOWED_ACTIONS:
            return error_response(
                agent_name=self.name,
                action_taken=action,
                error=f"Action '{action}' is not authorized for PCControlAgent. "
                      f"Allowed actions: {', '.join(sorted(self.ALLOWED_ACTIONS))}",
                retry_recommended=False
            )
        
        # Extract parameters
        target = params.get("target")
        value = params.get("value")
        
        try:
            # Execute action through actions.py
            # Requirement 4.3: Call appropriate actions.py function
            self._execute_action_internal(action, target, value)
            
            # Requirement 4.4: Return AgentResponse with success status
            return success_response(
                agent_name=self.name,
                action_taken=action,
                result={
                    "action": action,
                    "target": target,
                    "value": value,
                    "executed": True
                },
                metadata={
                    "action_type": "pc_control",
                    "action_category": self._get_action_category(action)
                }
            )
            
        except Exception as e:
            # Requirement 4.5: Handle errors and set retry_recommended flag
            error_msg = str(e)
            
            # Determine if error is retryable
            retry_recommended = self._is_retryable_error(error_msg)
            
            return error_response(
                agent_name=self.name,
                action_taken=action,
                error=f"Execution failed: {error_msg}",
                retry_recommended=retry_recommended,
                metadata={
                    "action_type": "pc_control",
                    "error_type": type(e).__name__
                }
            )
    
    def _execute_action_internal(
        self,
        action: str,
        target: Optional[Any],
        value: Optional[Any]
    ) -> None:
        """
        Internal method to execute action via actions.py.
        
        Maps action types to appropriate actions.py functions.
        
        Args:
            action: Action type (already validated)
            target: Target parameter
            value: Value parameter
            
        Raises:
            Exception: If action execution fails
        """
        # Volume controls (Requirement 4.1)
        if action == "VOLUME_UP":
            self.action_executor.change_volume(10)
        
        elif action == "VOLUME_DOWN":
            self.action_executor.change_volume(-10)
        
        elif action == "SET_VOLUME":
            if value is None:
                raise ValueError("SET_VOLUME requires 'value' parameter")
            self.action_executor.set_volume(value)
        
        elif action == "MUTE":
            self.action_executor.mute_volume()
        
        elif action == "UNMUTE":
            self.action_executor.unmute_volume()
        
        # Brightness controls (Requirement 4.2)
        elif action == "BRIGHTNESS_UP":
            self.action_executor.change_brightness(10)
        
        elif action == "BRIGHTNESS_DOWN":
            self.action_executor.change_brightness(-10)
        
        elif action == "SET_BRIGHTNESS":
            if value is None:
                raise ValueError("SET_BRIGHTNESS requires 'value' parameter")
            self.action_executor.set_brightness(int(value))
        
        # Application management (Requirement 4.3)
        elif action == "OPEN_APP":
            if not target:
                raise ValueError("OPEN_APP requires 'target' parameter (app name)")
            self.action_executor.open_application(str(target))
        
        elif action == "CLOSE_APP":
            if not target:
                raise ValueError("CLOSE_APP requires 'target' parameter (app name)")
            self.action_executor.close_application(str(target))
        
        # Media controls
        elif action == "PLAY_MEDIA":
            self.action_executor.play_media()
        
        elif action == "PAUSE_MEDIA":
            self.action_executor.pause_media()
        
        elif action == "STOP_MEDIA":
            self.action_executor.stop_media()
        
        elif action == "NEXT_TRACK":
            self.action_executor.next_track()
        
        elif action == "PREV_TRACK":
            self.action_executor.prev_track()
        
        # Desktop switching
        elif action == "SWITCH_DESKTOP_LEFT":
            self.action_executor.switch_desktop_left()
        
        elif action == "SWITCH_DESKTOP_RIGHT":
            self.action_executor.switch_desktop_right()
        
        # System actions
        elif action == "SCREENSHOT":
            self.action_executor.system_action("SCREENSHOT")
        
        elif action == "LOCK":
            self.action_executor.system_action("LOCK")
        
        elif action == "SLEEP":
            self.action_executor.system_action("SLEEP")
        
        else:
            # Should never reach here due to allowed_actions validation
            raise ValueError(f"Unhandled action: {action}")
    
    def _get_action_category(self, action: str) -> str:
        """
        Get category for an action.
        
        Args:
            action: Action type
            
        Returns:
            Category string (e.g., "volume", "brightness", "app")
        """
        if action in ("VOLUME_UP", "VOLUME_DOWN", "SET_VOLUME", "MUTE", "UNMUTE"):
            return "volume"
        elif action in ("BRIGHTNESS_UP", "BRIGHTNESS_DOWN", "SET_BRIGHTNESS"):
            return "brightness"
        elif action in ("OPEN_APP", "CLOSE_APP"):
            return "application"
        elif action in ("PLAY_MEDIA", "PAUSE_MEDIA", "STOP_MEDIA", "NEXT_TRACK", "PREV_TRACK"):
            return "media"
        elif action in ("SWITCH_DESKTOP_LEFT", "SWITCH_DESKTOP_RIGHT"):
            return "desktop"
        elif action in ("SCREENSHOT", "LOCK", "SLEEP"):
            return "system"
        else:
            return "unknown"
    
    def _is_retryable_error(self, error_msg: str) -> bool:
        """
        Determine if an error is retryable.
        
        Transient errors (timeouts, network issues, temporary resource
        unavailability) should recommend retry. Permanent errors
        (invalid parameters, missing resources) should not.
        
        Args:
            error_msg: Error message string
            
        Returns:
            True if error is retryable, False otherwise
            
        Validates: Requirement 4.5
        """
        error_lower = error_msg.lower()
        
        # Retryable error patterns
        retryable_patterns = [
            "timeout",
            "network",
            "connection",
            "temporary",
            "unavailable",
            "busy",
            "rate limit"
        ]
        
        # Non-retryable error patterns
        non_retryable_patterns = [
            "not found",
            "invalid",
            "permission denied",
            "not authorized",
            "missing",
            "requires"
        ]
        
        # Check non-retryable first (more specific)
        if any(pattern in error_lower for pattern in non_retryable_patterns):
            return False
        
        # Then check retryable
        if any(pattern in error_lower for pattern in retryable_patterns):
            return True
        
        # Default: assume non-retryable for safety
        return False
    
    def __repr__(self) -> str:
        """String representation of PCControlAgent."""
        return (
            f"PCControlAgent(name='{self.name}', "
            f"allowed_actions={len(self.ALLOWED_ACTIONS)})"
        )


