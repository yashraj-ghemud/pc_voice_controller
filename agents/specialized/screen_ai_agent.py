"""
ScreenAIAgent - Specialized agent for vision-based UI interaction.

This module implements the ScreenAIAgent class that handles vision-based
UI interaction operations including element finding, clicking, typing,
waiting for conditions, and taking screenshots.

The agent extends BaseAgent and integrates with the existing screen_ai.py
module for vision-based element detection and interaction via pyautogui.

Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5
"""

from typing import Optional, Any
import os
import time
from datetime import datetime
from agents.base import BaseAgent
from agents.models import AgentResponse, success_response, error_response

# Import existing screen_ai module functions
import screen_ai


class ScreenAIAgent(BaseAgent):
    """
    Specialized agent for vision-based UI interaction.
    
    This agent handles:
    - Finding and clicking UI elements using vision
    - Finding input fields and typing text
    - Waiting for visual conditions to be met
    - Taking and saving screenshots
    
    The agent validates all actions against an allowed_actions list for
    security and uses the existing screen_ai module for execution.
    
    Attributes:
        allowed_actions: Set of permitted action types
        screen_ai_module: Reference to screen_ai module for vision operations
        
    Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5
    
    Examples:
        >>> agent = ScreenAIAgent()
        >>> result = agent.find_and_click("play button")
        >>> result.success
        True
        >>> result.action_taken
        'CLICK'
        
        >>> # Type in field
        >>> result = agent.type_in_field("hello world", "search bar")
        >>> result.success
        True
        
        >>> # Take screenshot
        >>> result = agent.screenshot("youtube_page")
        >>> result.success
        True
        >>> "file_path" in result.result
        True
    """
    
    # Define allowed actions for security (Requirement 15.1)
    ALLOWED_ACTIONS = {
        "CLICK",                # Find and click UI element
        "TYPE",                 # Find input field and type text
        "SCREENSHOT",           # Take and save screenshot
        "WAIT_FOR_CONDITION",   # Wait for visual condition to be met
    }
    
    def __init__(
        self,
        name: str = "ScreenAIAgent",
        screen_ai_module: Any = None
    ):
        """
        Initialize ScreenAIAgent.
        
        Args:
            name: Agent name (default: "ScreenAIAgent")
            screen_ai_module: Optional custom screen_ai module (defaults to screen_ai)
            
        Examples:
            >>> agent = ScreenAIAgent()
            >>> agent.name
            'ScreenAIAgent'
            >>> agent.agent_type
            'screen_ai'
        """
        super().__init__(
            name=name,
            agent_type="screen_ai",
            description="Specialized agent for vision-based UI interaction: click, type, wait, screenshot"
        )
        
        # Use existing screen_ai module for execution
        self.screen_ai_module = screen_ai_module or screen_ai
    
    def execute_task(
        self,
        task_description: str,
        context: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """
        Execute a vision-based UI interaction task.
        
        This method implements the BaseAgent interface. It parses the task
        description to extract action type and parameters, then delegates
        to the appropriate method.
        
        Args:
            task_description: Natural language task description or action name
            context: Optional context with parsed parameters
            
        Returns:
            Dictionary with execution result (converted from AgentResponse)
            
        Examples:
            >>> agent = ScreenAIAgent()
            >>> result = agent.execute_task("CLICK", {
            ...     "action": "CLICK",
            ...     "params": {"element": "play button"}
            ... })
            >>> result["success"]
            True
        """
        # Extract action from context if available
        action = context.get("action") if context else None
        params = context.get("params", {}) if context else {}
        
        # If action not in context, use task_description as action
        if not action:
            action = task_description.strip().upper()
        
        # Route to appropriate method based on action
        if action == "CLICK":
            element = params.get("element") or params.get("description") or params.get("target")
            response = self.find_and_click(element)
        
        elif action == "TYPE":
            text = params.get("text") or params.get("message") or params.get("content")
            field = params.get("field") or params.get("field_description") or "text input field"
            press_enter = params.get("press_enter", True)
            response = self.type_in_field(text, field, press_enter)
        
        elif action == "SCREENSHOT":
            filename = params.get("filename") or params.get("name")
            response = self.screenshot(filename)
        
        elif action == "WAIT_FOR_CONDITION":
            condition = params.get("condition") or params.get("description")
            timeout = params.get("timeout", 120)
            response = self.wait_for_condition(condition, timeout)
        
        else:
            response = error_response(
                agent_name=self.name,
                action_taken=action,
                error=f"Unknown action: {action}. Allowed: {', '.join(self.ALLOWED_ACTIONS)}",
                retry_recommended=False
            )
        
        # Convert AgentResponse to dict for BaseAgent interface
        return response.to_dict()
    
    def find_and_click(
        self,
        element_description: str
    ) -> AgentResponse:
        """
        Find and click a UI element using vision.
        
        This method:
        1. Takes a screenshot of the current screen
        2. Uses vision AI to locate the element
        3. Clicks on the element using pyautogui
        
        PRECONDITIONS:
        - element_description is non-empty
        - Screen AI vision model is configured
        - Display is accessible
        
        POSTCONDITIONS:
        - Returns AgentResponse with success status
        - If success=True, element was clicked
        - If success=False and element not found, retry_recommended=True
        
        Args:
            element_description: Natural language description of element to click
                Examples: "play button", "search icon", "first video thumbnail"
            
        Returns:
            AgentResponse with execution result
            
        Validates: Requirements 6.1, 6.4
        
        Examples:
            >>> agent = ScreenAIAgent()
            >>> response = agent.find_and_click("play button")
            >>> response.success
            True
            >>> response.action_taken
            'CLICK'
            >>> response.result["element"]
            'play button'
        """
        if not element_description or not element_description.strip():
            return error_response(
                agent_name=self.name,
                action_taken="CLICK",
                error="Element description cannot be empty",
                retry_recommended=False
            )
        
        try:
            # Use screen_ai to find and click element
            success = self.screen_ai_module.find_and_click_element(element_description)
            
            if success:
                return success_response(
                    agent_name=self.name,
                    action_taken="CLICK",
                    result={
                        "element": element_description,
                        "clicked": True
                    },
                    metadata={
                        "action_type": "screen_ai",
                        "interaction_type": "click"
                    }
                )
            else:
                # Element not found - recommend retry (Requirement 6.4)
                return error_response(
                    agent_name=self.name,
                    action_taken="CLICK",
                    error=f"Element not found: {element_description}",
                    retry_recommended=True,
                    metadata={
                        "action_type": "screen_ai",
                        "interaction_type": "click",
                        "element_searched": element_description
                    }
                )
        
        except Exception as e:
            # Vision model error or other exception
            return error_response(
                agent_name=self.name,
                action_taken="CLICK",
                error=f"Failed to click element: {str(e)}",
                retry_recommended=True,
                metadata={
                    "action_type": "screen_ai",
                    "error_type": type(e).__name__
                }
            )
    
    def type_in_field(
        self,
        text: str,
        field_description: str = "text input field or search bar",
        press_enter: bool = True
    ) -> AgentResponse:
        """
        Find an input field and type text into it.
        
        This method:
        1. Takes a screenshot of the current screen
        2. Uses vision AI to locate the input field
        3. Clicks on the field to focus it
        4. Types the text using pyautogui/clipboard
        5. Optionally presses Enter
        
        PRECONDITIONS:
        - text is non-empty
        - field_description is non-empty
        - Screen AI vision model is configured
        - Display is accessible
        
        POSTCONDITIONS:
        - Returns AgentResponse with success status
        - If success=True, text was typed into field
        - If success=False and field not found, retry_recommended=True
        
        Args:
            text: Text to type into the field
            field_description: Natural language description of input field
                Examples: "search bar", "text input field", "comment box"
            press_enter: Whether to press Enter after typing (default: True)
            
        Returns:
            AgentResponse with execution result
            
        Validates: Requirements 6.2, 6.4
        
        Examples:
            >>> agent = ScreenAIAgent()
            >>> response = agent.type_in_field("hello world", "search bar")
            >>> response.success
            True
            >>> response.result["text"]
            'hello world'
            >>> response.result["press_enter"]
            True
        """
        if not text or not text.strip():
            return error_response(
                agent_name=self.name,
                action_taken="TYPE",
                error="Text cannot be empty",
                retry_recommended=False
            )
        
        if not field_description or not field_description.strip():
            return error_response(
                agent_name=self.name,
                action_taken="TYPE",
                error="Field description cannot be empty",
                retry_recommended=False
            )
        
        try:
            # Use screen_ai to find field and type text
            success = self.screen_ai_module.find_and_type_in_field(
                text=text,
                field_description=field_description,
                press_enter=press_enter
            )
            
            if success:
                return success_response(
                    agent_name=self.name,
                    action_taken="TYPE",
                    result={
                        "text": text,
                        "field": field_description,
                        "press_enter": press_enter,
                        "typed": True
                    },
                    metadata={
                        "action_type": "screen_ai",
                        "interaction_type": "type"
                    }
                )
            else:
                # Field not found - recommend retry (Requirement 6.4)
                return error_response(
                    agent_name=self.name,
                    action_taken="TYPE",
                    error=f"Input field not found: {field_description}",
                    retry_recommended=True,
                    metadata={
                        "action_type": "screen_ai",
                        "interaction_type": "type",
                        "field_searched": field_description
                    }
                )
        
        except Exception as e:
            # Vision model error or other exception
            return error_response(
                agent_name=self.name,
                action_taken="TYPE",
                error=f"Failed to type in field: {str(e)}",
                retry_recommended=True,
                metadata={
                    "action_type": "screen_ai",
                    "error_type": type(e).__name__
                }
            )
    
    def wait_for_condition(
        self,
        condition_description: str,
        timeout: int = 120,
        interval: int = 4,
        stable_checks: int = 2
    ) -> AgentResponse:
        """
        Wait for a visual condition to be met on screen.
        
        This method:
        1. Polls the screen at regular intervals
        2. Uses vision AI to check if condition is met
        3. Requires condition to be stable for multiple checks
        4. Returns success when condition is met or timeout
        
        PRECONDITIONS:
        - condition_description is non-empty
        - timeout is positive
        - Screen AI vision model is configured
        - Display is accessible
        
        POSTCONDITIONS:
        - Returns AgentResponse with success status
        - If success=True, condition was met before timeout
        - If success=False, timeout occurred
        
        Args:
            condition_description: Natural language description of condition
                Examples: "video is playing", "page loaded", "button is visible"
            timeout: Maximum seconds to wait (default: 120)
            interval: Seconds between checks (default: 4)
            stable_checks: Number of consecutive checks required (default: 2)
            
        Returns:
            AgentResponse with execution result
            
        Validates: Requirements 6.3
        
        Examples:
            >>> agent = ScreenAIAgent()
            >>> response = agent.wait_for_condition("video is playing", timeout=30)
            >>> response.action_taken
            'WAIT_FOR_CONDITION'
            >>> "condition" in response.result
            True
        """
        if not condition_description or not condition_description.strip():
            return error_response(
                agent_name=self.name,
                action_taken="WAIT_FOR_CONDITION",
                error="Condition description cannot be empty",
                retry_recommended=False
            )
        
        if timeout <= 0:
            return error_response(
                agent_name=self.name,
                action_taken="WAIT_FOR_CONDITION",
                error=f"Timeout must be positive, got {timeout}",
                retry_recommended=False
            )
        
        try:
            # Use screen_ai to wait for visual condition
            start_time = time.time()
            met = self.screen_ai_module.wait_for_visual_condition(
                condition_description=condition_description,
                timeout=timeout,
                interval=interval,
                stable_checks=stable_checks
            )
            elapsed = time.time() - start_time
            
            if met:
                return success_response(
                    agent_name=self.name,
                    action_taken="WAIT_FOR_CONDITION",
                    result={
                        "condition": condition_description,
                        "met": True,
                        "elapsed_seconds": round(elapsed, 2)
                    },
                    metadata={
                        "action_type": "screen_ai",
                        "interaction_type": "wait"
                    }
                )
            else:
                # Timeout occurred
                return error_response(
                    agent_name=self.name,
                    action_taken="WAIT_FOR_CONDITION",
                    error=f"Timeout after {timeout}s waiting for: {condition_description}",
                    retry_recommended=False,
                    result={
                        "condition": condition_description,
                        "met": False,
                        "timeout": timeout
                    },
                    metadata={
                        "action_type": "screen_ai",
                        "interaction_type": "wait"
                    }
                )
        
        except Exception as e:
            # Vision model error or other exception
            return error_response(
                agent_name=self.name,
                action_taken="WAIT_FOR_CONDITION",
                error=f"Failed to check condition: {str(e)}",
                retry_recommended=True,
                metadata={
                    "action_type": "screen_ai",
                    "error_type": type(e).__name__
                }
            )
    
    def screenshot(
        self,
        filename: Optional[str] = None
    ) -> AgentResponse:
        """
        Take a screenshot and save it to a file.
        
        This method:
        1. Takes a screenshot using screen_ai module
        2. Saves it to the temp/ directory with timestamp
        3. Returns the file path in AgentResponse.result
        
        PRECONDITIONS:
        - Screen AI module is configured
        - Display is accessible
        - temp/ directory exists or can be created
        
        POSTCONDITIONS:
        - Returns AgentResponse with success status
        - If success=True, screenshot file is saved
        - result["file_path"] contains the saved file path
        
        Args:
            filename: Optional filename (without extension). If None, generates
                timestamp-based name: screenshot_YYYYMMDD_HHMMSS.jpg
            
        Returns:
            AgentResponse with execution result, including file_path in result
            
        Validates: Requirements 6.5
        
        Examples:
            >>> agent = ScreenAIAgent()
            >>> response = agent.screenshot("youtube_page")
            >>> response.success
            True
            >>> response.result["file_path"]
            'temp/youtube_page.jpg'
            >>> response.action_taken
            'SCREENSHOT'
        """
        try:
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}"
            
            # Remove extension if provided
            if filename.endswith(".jpg") or filename.endswith(".jpeg") or filename.endswith(".png"):
                filename = os.path.splitext(filename)[0]
            
            # Ensure temp directory exists
            os.makedirs("temp", exist_ok=True)
            
            # Build file path
            file_path = os.path.join("temp", f"{filename}.jpg")
            
            # Take screenshot using screen_ai
            screenshot_b64 = self.screen_ai_module.take_screenshot()
            
            # Decode and save the base64 image
            import base64
            import io
            from PIL import Image
            
            img_data = base64.b64decode(screenshot_b64)
            img = Image.open(io.BytesIO(img_data))
            img.save(file_path, format="JPEG", quality=85)
            
            # Get absolute path for result
            abs_path = os.path.abspath(file_path)
            
            return success_response(
                agent_name=self.name,
                action_taken="SCREENSHOT",
                result={
                    "file_path": file_path,
                    "absolute_path": abs_path,
                    "filename": f"{filename}.jpg",
                    "saved": True
                },
                metadata={
                    "action_type": "screen_ai",
                    "interaction_type": "screenshot"
                }
            )
        
        except Exception as e:
            # Screenshot failed
            return error_response(
                agent_name=self.name,
                action_taken="SCREENSHOT",
                error=f"Failed to take screenshot: {str(e)}",
                retry_recommended=True,
                metadata={
                    "action_type": "screen_ai",
                    "error_type": type(e).__name__
                }
            )
    
    def __repr__(self) -> str:
        """String representation of ScreenAIAgent."""
        return (
            f"ScreenAIAgent(name='{self.name}', "
            f"allowed_actions={len(self.ALLOWED_ACTIONS)})"
        )
