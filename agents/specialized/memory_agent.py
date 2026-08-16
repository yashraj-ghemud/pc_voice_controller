"""
MemoryAgent - Specialized agent for conversation context management.

This module implements the MemoryAgent class that handles conversation memory
operations including saving conversations to ChromaDB and retrieving relevant
context for contextual responses.

The agent extends BaseAgent and integrates with the existing memory.py module
for ChromaDB-based vector storage and semantic search.

Validates: Requirements 8.1, 8.2, 8.3, 8.4
"""

from typing import Optional, Any
from agents.base import BaseAgent
from agents.models import AgentResponse, success_response, error_response

# Import existing memory module functions
import memory


class MemoryAgent(BaseAgent):
    """
    Specialized agent for conversation context management.
    
    This agent handles:
    - Saving user messages and assistant responses to ChromaDB
    - Retrieving relevant conversation context based on semantic similarity
    - Integration with existing memory.py ChromaDB implementation
    
    The agent validates all actions against an allowed_actions list for
    security and uses the existing memory module for vector storage operations.
    
    Attributes:
        allowed_actions: Set of permitted action types
        memory_module: Reference to memory module for ChromaDB operations
        
    Validates: Requirements 8.1, 8.2, 8.3, 8.4
    
    Examples:
        >>> agent = MemoryAgent()
        >>> result = agent.save_conversation(
        ...     "What is the weather?",
        ...     "The weather is sunny today."
        ... )
        >>> result.success
        True
        >>> result.action_taken
        'SAVE_CONVERSATION'
        
        >>> # Retrieve context
        >>> result = agent.retrieve_context("weather forecast")
        >>> result.success
        True
        >>> isinstance(result.result["context"], str)
        True
    """
    
    # Define allowed actions for security (Requirement 15.1)
    ALLOWED_ACTIONS = {
        "SAVE_CONVERSATION",     # Save user message and response to ChromaDB
        "RETRIEVE_CONTEXT",      # Query ChromaDB for relevant past conversations
    }
    
    def __init__(
        self,
        name: str = "MemoryAgent",
        memory_module: Any = None
    ):
        """
        Initialize MemoryAgent.
        
        Args:
            name: Agent name (default: "MemoryAgent")
            memory_module: Optional custom memory module (defaults to memory)
            
        Examples:
            >>> agent = MemoryAgent()
            >>> agent.name
            'MemoryAgent'
            >>> agent.agent_type
            'memory'
        """
        super().__init__(
            name=name,
            agent_type="memory",
            description="Specialized agent for conversation context: save and retrieve past conversations"
        )
        
        # Use existing memory.py module for ChromaDB operations
        self.memory_module = memory_module or memory
    
    def execute_task(
        self,
        task_description: str,
        context: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """
        Execute a memory management task.
        
        This method implements the BaseAgent interface. It parses the task
        description to extract action type and parameters, then delegates
        to the appropriate method.
        
        Args:
            task_description: Natural language task description or action name
            context: Optional context with parsed parameters
            
        Returns:
            Dictionary with execution result (converted from AgentResponse)
            
        Examples:
            >>> agent = MemoryAgent()
            >>> result = agent.execute_task("SAVE_CONVERSATION", {
            ...     "action": "SAVE_CONVERSATION",
            ...     "params": {
            ...         "user_message": "Hello",
            ...         "assistant_response": "Hi there!"
            ...     }
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
        if action == "SAVE_CONVERSATION":
            user_message = params.get("user_message") or params.get("user_msg") or params.get("message")
            assistant_response = params.get("assistant_response") or params.get("assistant_reply") or params.get("response")
            response = self.save_conversation(user_message, assistant_response)
        
        elif action == "RETRIEVE_CONTEXT":
            query = params.get("query") or params.get("message") or params.get("text")
            top_k = params.get("top_k", 3)
            response = self.retrieve_context(query, top_k)
        
        else:
            response = error_response(
                agent_name=self.name,
                action_taken=action,
                error=f"Unknown action: {action}. Allowed: {', '.join(self.ALLOWED_ACTIONS)}",
                retry_recommended=False
            )
        
        # Convert AgentResponse to dict for BaseAgent interface
        return response.to_dict()
    
    def save_conversation(
        self,
        user_message: str,
        assistant_response: str
    ) -> AgentResponse:
        """
        Save a conversation exchange to ChromaDB with timestamp metadata.
        
        This method:
        1. Validates inputs are non-empty
        2. Calls memory.save_conversation to store in ChromaDB
        3. Includes timestamp metadata automatically (handled by memory module)
        4. Returns success/failure status
        
        PRECONDITIONS:
        - user_message is non-empty string
        - assistant_response is non-empty string
        - ChromaDB is initialized and accessible
        
        POSTCONDITIONS:
        - Returns AgentResponse with success status
        - If success=True, conversation is stored in ChromaDB with timestamp
        - If success=False, error message explains why
        
        Args:
            user_message: User's message text
            assistant_response: Assistant's response text
            
        Returns:
            AgentResponse with execution result
            
        Validates: Requirements 8.1, 8.2
        
        Examples:
            >>> agent = MemoryAgent()
            >>> response = agent.save_conversation(
            ...     "What is Python?",
            ...     "Python is a programming language."
            ... )
            >>> response.success
            True
            >>> response.action_taken
            'SAVE_CONVERSATION'
            >>> response.result["saved"]
            True
            
            >>> # Empty message
            >>> response = agent.save_conversation("", "response")
            >>> response.success
            False
            >>> "cannot be empty" in response.error.lower()
            True
        """
        if not user_message or not user_message.strip():
            return error_response(
                agent_name=self.name,
                action_taken="SAVE_CONVERSATION",
                error="User message cannot be empty",
                retry_recommended=False
            )
        
        if not assistant_response or not assistant_response.strip():
            return error_response(
                agent_name=self.name,
                action_taken="SAVE_CONVERSATION",
                error="Assistant response cannot be empty",
                retry_recommended=False
            )
        
        try:
            # Use memory module to save conversation
            # memory.save_conversation automatically includes timestamp metadata
            saved = self.memory_module.save_conversation(
                user_msg=user_message,
                assistant_reply=assistant_response
            )
            
            if saved:
                return success_response(
                    agent_name=self.name,
                    action_taken="SAVE_CONVERSATION",
                    result={
                        "user_message": user_message[:100] + "..." if len(user_message) > 100 else user_message,
                        "assistant_response": assistant_response[:100] + "..." if len(assistant_response) > 100 else assistant_response,
                        "saved": True
                    },
                    metadata={
                        "action_type": "memory",
                        "operation": "save",
                        "user_message_length": len(user_message),
                        "assistant_response_length": len(assistant_response)
                    }
                )
            else:
                # ChromaDB save failed (e.g., connection issue)
                return error_response(
                    agent_name=self.name,
                    action_taken="SAVE_CONVERSATION",
                    error="Failed to save conversation to memory store",
                    retry_recommended=True,
                    metadata={
                        "action_type": "memory",
                        "operation": "save"
                    }
                )
        
        except Exception as e:
            # Unexpected error
            return error_response(
                agent_name=self.name,
                action_taken="SAVE_CONVERSATION",
                error=f"Failed to save conversation: {str(e)}",
                retry_recommended=True,
                metadata={
                    "action_type": "memory",
                    "error_type": type(e).__name__
                }
            )
    
    def retrieve_context(
        self,
        query: str,
        top_k: int = 3
    ) -> AgentResponse:
        """
        Query ChromaDB for relevant past conversations.
        
        This method:
        1. Validates query is non-empty
        2. Uses semantic similarity search to find relevant conversations
        3. Returns formatted context string with most relevant snippets
        4. Returns empty string when no relevant context exists
        
        PRECONDITIONS:
        - query is non-empty string
        - top_k is positive integer
        - ChromaDB is initialized and accessible
        
        POSTCONDITIONS:
        - Returns AgentResponse with success status
        - If success=True, result["context"] contains formatted context string
        - If no relevant context found, result["context"] is empty string
        - Never fails due to no results (returns empty string instead)
        
        Args:
            query: Search query to find relevant conversations
            top_k: Maximum number of relevant conversations to retrieve (default: 3)
            
        Returns:
            AgentResponse with execution result
            
        Validates: Requirements 8.3, 8.4
        
        Examples:
            >>> agent = MemoryAgent()
            >>> response = agent.retrieve_context("weather forecast")
            >>> response.success
            True
            >>> response.action_taken
            'RETRIEVE_CONTEXT'
            >>> isinstance(response.result["context"], str)
            True
            >>> response.result["found_results"]
            True
            
            >>> # Empty query
            >>> response = agent.retrieve_context("")
            >>> response.success
            False
            >>> "cannot be empty" in response.error.lower()
            True
        """
        if not query or not query.strip():
            return error_response(
                agent_name=self.name,
                action_taken="RETRIEVE_CONTEXT",
                error="Query cannot be empty",
                retry_recommended=False
            )
        
        if top_k < 1:
            return error_response(
                agent_name=self.name,
                action_taken="RETRIEVE_CONTEXT",
                error=f"top_k must be positive, got {top_k}",
                retry_recommended=False
            )
        
        try:
            # Use memory module to retrieve relevant context
            # Returns formatted string or empty string if no results
            context = self.memory_module.get_relevant_context(
                query=query,
                top_k=top_k
            )
            
            # Success regardless of whether context was found
            # Empty context means no relevant past conversations
            found_results = len(context) > 0
            
            return success_response(
                agent_name=self.name,
                action_taken="RETRIEVE_CONTEXT",
                result={
                    "query": query,
                    "context": context,
                    "found_results": found_results,
                    "context_length": len(context),
                    "top_k": top_k
                },
                metadata={
                    "action_type": "memory",
                    "operation": "retrieve",
                    "query_length": len(query)
                }
            )
        
        except Exception as e:
            # Unexpected error (e.g., ChromaDB connection issue)
            return error_response(
                agent_name=self.name,
                action_taken="RETRIEVE_CONTEXT",
                error=f"Failed to retrieve context: {str(e)}",
                retry_recommended=True,
                result={
                    "query": query,
                    "context": "",  # Return empty context on error
                    "found_results": False
                },
                metadata={
                    "action_type": "memory",
                    "error_type": type(e).__name__
                }
            )
    
    def __repr__(self) -> str:
        """String representation of MemoryAgent."""
        return (
            f"MemoryAgent(name='{self.name}', "
            f"allowed_actions={len(self.ALLOWED_ACTIONS)})"
        )
