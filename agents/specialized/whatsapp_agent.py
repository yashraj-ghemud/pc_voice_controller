"""
WhatsAppAgent - Specialized agent for WhatsApp messaging commands.

This module implements the WhatsAppAgent class that handles WhatsApp messaging
operations including text messages, voice notes, and smart file sending with
voice-based selection.

The agent extends BaseAgent and integrates with the existing whatsapp_module
for WhatsApp Desktop automation, TTS, file search, and voice interaction.

Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 5.6
"""

from typing import Optional, Any
from agents.base import BaseAgent
from agents.models import AgentResponse, success_response, error_response

# Import existing WhatsApp module functions
from whatsapp_module.handler import send_voice_note as wa_send_voice_note
from whatsapp_module.handler import handle_send_command as wa_handle_send_command
from whatsapp_module.wa_controller import open_whatsapp_chat, paste_and_send
from whatsapp_module.clipboard import copy_file_to_clipboard
import pyperclip


class WhatsAppAgent(BaseAgent):
    """
    Specialized agent for WhatsApp messaging operations.
    
    This agent handles:
    - Text message sending to contacts
    - Voice note generation and sending (text-to-speech)
    - Smart file sending with voice-based file selection
    - Integration with existing WhatsApp Desktop automation
    
    The agent validates all actions against an allowed_actions list for
    security and uses the existing whatsapp_module for execution.
    
    Attributes:
        allowed_actions: Set of permitted action types
        
    Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 5.6
    
    Examples:
        >>> agent = WhatsAppAgent()
        >>> result = agent.execute_task("send message to papa: hello")
        >>> result["success"]
        True
        >>> result["action_taken"]
        'SEND_MESSAGE'
        
        >>> # Voice note
        >>> result = agent.send_voice_note("papa", "Testing voice note")
        >>> result.success
        True
        
        >>> # File sending with smart search
        >>> result = agent.send_file_smart("papa ko resume bhejo")
        >>> result.success
        True
    """
    
    # Define allowed actions for security (Requirement 15.1)
    ALLOWED_ACTIONS = {
        "SEND_MESSAGE",      # Send text message to contact
        "SEND_VOICE_NOTE",   # Convert text to speech and send as voice note
        "SEND_FILE",         # Search, select, and send file to contact
    }
    
    def __init__(
        self,
        name: str = "WhatsAppAgent",
    ):
        """
        Initialize WhatsAppAgent.
        
        Args:
            name: Agent name (default: "WhatsAppAgent")
            
        Examples:
            >>> agent = WhatsAppAgent()
            >>> agent.name
            'WhatsAppAgent'
            >>> agent.agent_type
            'whatsapp'
        """
        super().__init__(
            name=name,
            agent_type="whatsapp",
            description="Specialized agent for WhatsApp: messages, voice notes, file sending"
        )
    
    def execute_task(
        self,
        task_description: str,
        context: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """
        Execute a WhatsApp task.
        
        This method implements the BaseAgent interface. It parses the task
        description to extract action type and parameters, then delegates
        to the appropriate method.
        
        Args:
            task_description: Natural language task description or action name
            context: Optional context with parsed parameters
            
        Returns:
            Dictionary with execution result (converted from AgentResponse)
            
        Examples:
            >>> agent = WhatsAppAgent()
            >>> result = agent.execute_task("SEND_MESSAGE", {
            ...     "action": "SEND_MESSAGE",
            ...     "params": {"contact": "papa", "message": "hello"}
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
        if action == "SEND_MESSAGE":
            contact = params.get("contact") or params.get("contact_name")
            message = params.get("message") or params.get("text")
            response = self.send_message(contact, message)
        
        elif action == "SEND_VOICE_NOTE":
            contact = params.get("contact") or params.get("contact_name")
            text = params.get("text") or params.get("message")
            response = self.send_voice_note(contact, text)
        
        elif action == "SEND_FILE":
            command = params.get("command") or task_description
            response = self.send_file_smart(command)
        
        else:
            response = error_response(
                agent_name=self.name,
                action_taken=action,
                error=f"Unknown action: {action}. Allowed: {', '.join(self.ALLOWED_ACTIONS)}",
                retry_recommended=False
            )
        
        # Convert AgentResponse to dict for BaseAgent interface
        return response.to_dict()
    
    def send_message(
        self,
        contact_name: str,
        message: str
    ) -> AgentResponse:
        """
        Send a text message to a WhatsApp contact.
        
        This method:
        1. Opens WhatsApp Desktop and navigates to contact
        2. Copies message to clipboard
        3. Pastes and sends the message
        
        PRECONDITIONS:
        - contact_name is non-empty
        - message is non-empty
        - WhatsApp Desktop is installed
        
        POSTCONDITIONS:
        - Returns AgentResponse with success status
        - If success=True, message was sent
        - If success=False, error message explains why
        
        Args:
            contact_name: Name of WhatsApp contact
            message: Text message to send
            
        Returns:
            AgentResponse with execution result
            
        Validates: Requirements 5.1, 5.6
        
        Examples:
            >>> agent = WhatsAppAgent()
            >>> response = agent.send_message("papa", "Hello!")
            >>> response.success
            True
            >>> response.action_taken
            'SEND_MESSAGE'
        """
        if not contact_name or not contact_name.strip():
            return error_response(
                agent_name=self.name,
                action_taken="SEND_MESSAGE",
                error="Contact name cannot be empty",
                retry_recommended=False
            )
        
        if not message or not message.strip():
            return error_response(
                agent_name=self.name,
                action_taken="SEND_MESSAGE",
                error="Message cannot be empty",
                retry_recommended=False
            )
        
        try:
            # Open WhatsApp chat
            if not open_whatsapp_chat(contact_name):
                return error_response(
                    agent_name=self.name,
                    action_taken="SEND_MESSAGE",
                    error=f"Failed to open chat with {contact_name}",
                    retry_recommended=True
                )
            
            # Copy message to clipboard and send
            pyperclip.copy(message)
            paste_and_send()
            
            return success_response(
                agent_name=self.name,
                action_taken="SEND_MESSAGE",
                result={
                    "contact": contact_name,
                    "message": message,
                    "sent": True
                },
                metadata={
                    "action_type": "whatsapp",
                    "message_type": "text"
                }
            )
        
        except Exception as e:
            return error_response(
                agent_name=self.name,
                action_taken="SEND_MESSAGE",
                error=f"Failed to send message: {str(e)}",
                retry_recommended=True,
                metadata={
                    "action_type": "whatsapp",
                    "error_type": type(e).__name__
                }
            )
    
    def send_voice_note(
        self,
        contact_name: str,
        text: str
    ) -> AgentResponse:
        """
        Convert text to speech and send as WhatsApp voice note.
        
        This method:
        1. Converts text to MP3 using TTS
        2. Copies MP3 file to clipboard
        3. Opens WhatsApp chat with contact
        4. Pastes and sends the voice note
        5. Cleans up temporary MP3 file
        
        PRECONDITIONS:
        - contact_name is non-empty
        - text is non-empty
        - TTS module is configured
        - WhatsApp Desktop is installed
        
        POSTCONDITIONS:
        - Returns AgentResponse with success status
        - If success=True, voice note was sent
        - Temporary MP3 file is deleted after sending
        
        Args:
            contact_name: Name of WhatsApp contact
            text: Text to convert to speech and send
            
        Returns:
            AgentResponse with execution result
            
        Validates: Requirements 5.2, 5.4, 5.6
        
        Examples:
            >>> agent = WhatsAppAgent()
            >>> response = agent.send_voice_note("papa", "This is a voice note")
            >>> response.success
            True
            >>> response.metadata["message_type"]
            'voice_note'
        """
        if not contact_name or not contact_name.strip():
            return error_response(
                agent_name=self.name,
                action_taken="SEND_VOICE_NOTE",
                error="Contact name cannot be empty",
                retry_recommended=False
            )
        
        if not text or not text.strip():
            return error_response(
                agent_name=self.name,
                action_taken="SEND_VOICE_NOTE",
                error="Text cannot be empty",
                retry_recommended=False
            )
        
        try:
            # Use existing handler from whatsapp_module
            # This handles: TTS -> mp3 -> clipboard -> send -> cleanup
            success = wa_send_voice_note(contact_name, text)
            
            if success:
                return success_response(
                    agent_name=self.name,
                    action_taken="SEND_VOICE_NOTE",
                    result={
                        "contact": contact_name,
                        "text": text,
                        "sent": True
                    },
                    metadata={
                        "action_type": "whatsapp",
                        "message_type": "voice_note"
                    }
                )
            else:
                return error_response(
                    agent_name=self.name,
                    action_taken="SEND_VOICE_NOTE",
                    error="Voice note sending failed",
                    retry_recommended=True
                )
        
        except Exception as e:
            return error_response(
                agent_name=self.name,
                action_taken="SEND_VOICE_NOTE",
                error=f"Failed to send voice note: {str(e)}",
                retry_recommended=True,
                metadata={
                    "action_type": "whatsapp",
                    "error_type": type(e).__name__
                }
            )
    
    def send_file_smart(
        self,
        command: str
    ) -> AgentResponse:
        """
        Search for file, use voice selection, and send to WhatsApp contact.
        
        This method implements the full smart file sending pipeline:
        1. Parse command to extract contact and search keyword
        2. Search for files matching keyword
        3. Present results via voice
        4. Listen for user's voice selection
        5. Send selected file to contact
        
        Command format examples:
        - "papa ko resume bhejo"
        - "send photo to mama"
        
        PRECONDITIONS:
        - command contains contact name and file keyword
        - File search module is configured
        - Voice interaction (TTS/STT) is available
        - WhatsApp Desktop is installed
        
        POSTCONDITIONS:
        - Returns AgentResponse with success status
        - If success=True, file was sent to contact
        - If success=False, explains what went wrong
        
        Args:
            command: Natural language command with contact and file keyword
            
        Returns:
            AgentResponse with execution result
            
        Validates: Requirements 5.3, 5.4, 5.5, 5.6
        
        Examples:
            >>> agent = WhatsAppAgent()
            >>> response = agent.send_file_smart("papa ko resume bhejo")
            >>> response.action_taken
            'SEND_FILE'
        """
        if not command or not command.strip():
            return error_response(
                agent_name=self.name,
                action_taken="SEND_FILE",
                error="Command cannot be empty",
                retry_recommended=False
            )
        
        try:
            # Use existing handler from whatsapp_module
            # This handles: parse -> search -> voice selection -> send
            wa_handle_send_command(command)
            
            # Note: handle_send_command doesn't return success/failure
            # It speaks the result to user. We assume success if no exception.
            return success_response(
                agent_name=self.name,
                action_taken="SEND_FILE",
                result={
                    "command": command,
                    "executed": True
                },
                metadata={
                    "action_type": "whatsapp",
                    "message_type": "file",
                    "interaction_mode": "voice_selection"
                }
            )
        
        except Exception as e:
            return error_response(
                agent_name=self.name,
                action_taken="SEND_FILE",
                error=f"Failed to send file: {str(e)}",
                retry_recommended=True,
                metadata={
                    "action_type": "whatsapp",
                    "error_type": type(e).__name__
                }
            )
    
    def __repr__(self) -> str:
        """String representation of WhatsAppAgent."""
        return (
            f"WhatsAppAgent(name='{self.name}', "
            f"allowed_actions={len(self.ALLOWED_ACTIONS)})"
        )
