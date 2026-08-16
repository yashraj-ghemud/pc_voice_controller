"""
WebAgent - Specialized agent for web searches and URL opening.

This module implements the WebAgent class that handles web-related operations
including performing web searches and opening specific URLs in the default browser.

The agent extends BaseAgent and uses Python's webbrowser module for browser
control operations.

Validates: Requirements 7.1, 7.2, 7.3, 7.4
"""

from typing import Optional, Any
import webbrowser
import urllib.parse
from agents.base import BaseAgent
from agents.models import AgentResponse, success_response, error_response


class WebAgent(BaseAgent):
    """
    Specialized agent for web search and URL operations.
    
    This agent handles:
    - Web searches (opens search results in default browser)
    - Direct URL opening in default browser
    
    The agent validates all actions against an allowed_actions list for
    security and uses Python's webbrowser module for browser operations.
    
    Attributes:
        allowed_actions: Set of permitted action types
        search_engine: Default search engine URL pattern
        
    Validates: Requirements 7.1, 7.2, 7.3, 7.4
    
    Examples:
        >>> agent = WebAgent()
        >>> result = agent.search("Python programming")
        >>> result.success
        True
        >>> result.action_taken
        'SEARCH'
        
        >>> # Open URL
        >>> result = agent.open_url("https://www.python.org")
        >>> result.success
        True
        >>> result.action_taken
        'OPEN_URL'
    """
    
    # Define allowed actions for security (Requirement 15.1)
    ALLOWED_ACTIONS = {
        "SEARCH",      # Perform web search and open results
        "OPEN_URL",    # Open specific URL in browser
    }
    
    def __init__(
        self,
        name: str = "WebAgent",
        search_engine: str = "https://www.google.com/search?q={query}"
    ):
        """
        Initialize WebAgent.
        
        Args:
            name: Agent name (default: "WebAgent")
            search_engine: Search engine URL pattern with {query} placeholder
                (default: Google search)
            
        Examples:
            >>> agent = WebAgent()
            >>> agent.name
            'WebAgent'
            >>> agent.agent_type
            'web'
            
            >>> # Custom search engine
            >>> agent = WebAgent(search_engine="https://duckduckgo.com/?q={query}")
            >>> agent.search_engine
            'https://duckduckgo.com/?q={query}'
        """
        super().__init__(
            name=name,
            agent_type="web",
            description="Specialized agent for web searches and URL opening"
        )
        
        self.search_engine = search_engine
    
    def execute_task(
        self,
        task_description: str,
        context: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """
        Execute a web-related task.
        
        This method implements the BaseAgent interface. It parses the task
        description to extract action type and parameters, then delegates
        to the appropriate method.
        
        Args:
            task_description: Natural language task description or action name
            context: Optional context with parsed parameters
            
        Returns:
            Dictionary with execution result (converted from AgentResponse)
            
        Examples:
            >>> agent = WebAgent()
            >>> result = agent.execute_task("SEARCH", {
            ...     "action": "SEARCH",
            ...     "params": {"query": "Python tutorials"}
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
        if action == "SEARCH":
            query = params.get("query") or params.get("search_query") or params.get("text")
            response = self.search(query)
        
        elif action == "OPEN_URL":
            url = params.get("url") or params.get("link") or params.get("address")
            response = self.open_url(url)
        
        else:
            response = error_response(
                agent_name=self.name,
                action_taken=action,
                error=f"Unknown action: {action}. Allowed: {', '.join(self.ALLOWED_ACTIONS)}",
                retry_recommended=False
            )
        
        # Convert AgentResponse to dict for BaseAgent interface
        return response.to_dict()
    
    def search(
        self,
        query: str
    ) -> AgentResponse:
        """
        Perform a web search and open results in default browser.
        
        This method:
        1. Validates the search query
        2. URL-encodes the query
        3. Formats the search engine URL
        4. Opens the URL in the default browser
        
        PRECONDITIONS:
        - query is non-empty string
        - Default browser is configured on the system
        
        POSTCONDITIONS:
        - Returns AgentResponse with success status
        - If success=True, browser opened with search results
        - If success=False, error message explains why
        - Completes within 3 seconds (Requirement 7.3)
        
        Args:
            query: Search query string
            
        Returns:
            AgentResponse with execution result
            
        Validates: Requirements 7.1, 7.3, 7.4
        
        Examples:
            >>> agent = WebAgent()
            >>> response = agent.search("Python programming")
            >>> response.success
            True
            >>> response.action_taken
            'SEARCH'
            >>> response.result["query"]
            'Python programming'
            
            >>> # Empty query
            >>> response = agent.search("")
            >>> response.success
            False
            >>> "cannot be empty" in response.error.lower()
            True
        """
        if not query or not query.strip():
            return error_response(
                agent_name=self.name,
                action_taken="SEARCH",
                error="Search query cannot be empty",
                retry_recommended=False
            )
        
        try:
            # URL-encode the query
            encoded_query = urllib.parse.quote_plus(query.strip())
            
            # Format the search URL
            search_url = self.search_engine.format(query=encoded_query)
            
            # Open in default browser
            # webbrowser.open() returns True if browser opened successfully
            success = webbrowser.open(search_url)
            
            if success:
                return success_response(
                    agent_name=self.name,
                    action_taken="SEARCH",
                    result={
                        "query": query.strip(),
                        "search_url": search_url,
                        "browser_opened": True
                    },
                    metadata={
                        "action_type": "web",
                        "operation": "search"
                    }
                )
            else:
                return error_response(
                    agent_name=self.name,
                    action_taken="SEARCH",
                    error="Failed to open browser for search",
                    retry_recommended=True,
                    result={
                        "query": query.strip(),
                        "search_url": search_url
                    }
                )
        
        except Exception as e:
            return error_response(
                agent_name=self.name,
                action_taken="SEARCH",
                error=f"Search failed: {str(e)}",
                retry_recommended=True,
                metadata={
                    "action_type": "web",
                    "error_type": type(e).__name__
                }
            )
    
    def open_url(
        self,
        url: str
    ) -> AgentResponse:
        """
        Open a specific URL in the default browser.
        
        This method:
        1. Validates the URL
        2. Adds http:// prefix if no protocol specified
        3. Opens the URL in the default browser
        
        PRECONDITIONS:
        - url is non-empty string
        - Default browser is configured on the system
        
        POSTCONDITIONS:
        - Returns AgentResponse with success status
        - If success=True, browser opened with the URL
        - If success=False, error message explains why
        - Completes within 3 seconds (Requirement 7.3)
        
        Args:
            url: URL to open (with or without protocol)
                Examples: "https://www.python.org", "python.org"
            
        Returns:
            AgentResponse with execution result
            
        Validates: Requirements 7.2, 7.3, 7.4
        
        Examples:
            >>> agent = WebAgent()
            >>> response = agent.open_url("https://www.python.org")
            >>> response.success
            True
            >>> response.action_taken
            'OPEN_URL'
            >>> response.result["url"]
            'https://www.python.org'
            
            >>> # URL without protocol
            >>> response = agent.open_url("python.org")
            >>> response.success
            True
            >>> response.result["url"].startswith("http")
            True
            
            >>> # Empty URL
            >>> response = agent.open_url("")
            >>> response.success
            False
            >>> "cannot be empty" in response.error.lower()
            True
        """
        if not url or not url.strip():
            return error_response(
                agent_name=self.name,
                action_taken="OPEN_URL",
                error="URL cannot be empty",
                retry_recommended=False
            )
        
        try:
            url = url.strip()
            
            # Add http:// prefix if no protocol specified
            if not url.startswith(("http://", "https://", "file://", "ftp://")):
                url = "http://" + url
            
            # Open in default browser
            # webbrowser.open() returns True if browser opened successfully
            success = webbrowser.open(url)
            
            if success:
                return success_response(
                    agent_name=self.name,
                    action_taken="OPEN_URL",
                    result={
                        "url": url,
                        "browser_opened": True
                    },
                    metadata={
                        "action_type": "web",
                        "operation": "open_url"
                    }
                )
            else:
                return error_response(
                    agent_name=self.name,
                    action_taken="OPEN_URL",
                    error="Failed to open browser for URL",
                    retry_recommended=True,
                    result={
                        "url": url
                    }
                )
        
        except Exception as e:
            return error_response(
                agent_name=self.name,
                action_taken="OPEN_URL",
                error=f"Failed to open URL: {str(e)}",
                retry_recommended=True,
                metadata={
                    "action_type": "web",
                    "error_type": type(e).__name__
                }
            )
    
    def __repr__(self) -> str:
        """String representation of WebAgent."""
        return (
            f"WebAgent(name='{self.name}', "
            f"allowed_actions={len(self.ALLOWED_ACTIONS)})"
        )
