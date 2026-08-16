"""
StateManager for LangGraph workflow orchestration.

This module implements the StateManager class that builds and manages the LangGraph
workflow graph with all nodes, edges, and conditional routing logic. It coordinates
the execution flow through classification, routing, execution, validation, retry,
and finalization nodes.

The StateManager is the core orchestration engine for multi-agent workflows.

Validates: Requirements 2.1, 2.5, 2.6, 2.7, 9.2, 10.1, 10.2, 10.3, 10.4, 10.5
"""

from typing import Literal
from langgraph.graph import StateGraph, END
from agents.state import WorkflowState, increment_step, add_agent_response, set_final_result
from agents.models import AgentResponse, CommandClassification, error_response, success_response
from agents.registry import AgentRegistry


class StateManager:
    """
    Manages LangGraph workflow state graph with nodes and conditional edges.
    
    The StateManager builds a workflow graph that routes user commands through
    classification, agent selection, execution, validation, and optional retry
    with exponential backoff. It maintains state consistency throughout execution
    and ensures all paths lead to a terminal state.
    
    Graph Structure:
        START → classify → route → execute → validate → [retry|finalize] → END
        
    Attributes:
        agent_registry: Registry for discovering and accessing agents
        _graph: Compiled StateGraph instance (created by build_graph)
        
    Validates: Requirements 2.1, 2.5, 2.6, 2.7, 9.2
    
    Examples:
        >>> registry = AgentRegistry()
        >>> manager = StateManager(registry)
        >>> graph = manager.build_graph()
        >>> result = graph.invoke(initial_state)
    """
    
    def __init__(self, agent_registry: AgentRegistry):
        """
        Initialize StateManager with agent registry.
        
        Args:
            agent_registry: Registry for agent discovery and access
        """
        self.agent_registry = agent_registry
        self._graph = None
    
    def build_graph(self) -> StateGraph:
        """
        Build LangGraph workflow with all nodes and edges.
        
        Creates a StateGraph with:
        - classify node: Analyzes command type
        - route node: Selects appropriate agent
        - execute node: Runs agent task
        - validate node: Checks execution result
        - retry node: Handles failures with backoff
        - finalize node: Prepares final response
        
        The graph has a single entry point (classify) and all paths eventually
        reach the END node, ensuring no unreachable nodes exist.
        
        Returns:
            Compiled StateGraph ready for execution
            
        Validates: Requirements 2.1, 2.6, 2.7, 9.2
        
        Examples:
            >>> manager = StateManager(registry)
            >>> graph = manager.build_graph()
            >>> result = graph.invoke({"user_input": "test", ...})
        """
        # Create StateGraph with WorkflowState schema
        graph = StateGraph(WorkflowState)
        
        # Add all nodes
        graph.add_node("classify", self._classify_command_node)
        graph.add_node("route", self._route_to_agent_node)
        graph.add_node("execute", self._execute_agent_node)
        graph.add_node("validate", self._validate_result_node)
        graph.add_node("retry", self._retry_handler_node)
        graph.add_node("finalize", self._finalize_response_node)
        
        # Set entry point (Requirement 2.7)
        graph.set_entry_point("classify")
        
        # Add edges
        graph.add_edge("classify", "route")
        graph.add_edge("route", "execute")
        graph.add_edge("execute", "validate")
        
        # Conditional edge from validate (Requirement 2.5)
        graph.add_conditional_edges(
            "validate",
            self._should_retry,
            {
                "retry": "retry",
                "finalize": "finalize"
            }
        )
        
        # Retry loops back to execute
        graph.add_edge("retry", "execute")
        
        # Finalize terminates
        graph.add_edge("finalize", END)
        
        # Compile and cache
        self._graph = graph.compile()
        return self._graph
    
    def _classify_command_node(self, state: WorkflowState) -> WorkflowState:
        """
        Classify command node - analyzes user input.
        
        This is the entry point of the graph. It analyzes the user input
        to determine command type but does not change the classification
        if already set (to preserve orchestrator decisions).
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with incremented step
            
        Validates: Requirement 12.1 - Error handling with state capture
            
        Examples:
            >>> state = {"user_input": "test", "command_type": "simple", ...}
            >>> new_state = manager._classify_command_node(state)
            >>> new_state["current_step"]
            1
        """
        try:
            # Command type already set by orchestrator, just increment step
            new_state = increment_step(state)
            return new_state
        except Exception as e:
            # Capture error in state
            new_state = state.copy()
            new_state["context"] = state["context"].copy()
            new_state["context"]["last_error"] = f"classify_node_error: {str(e)}"
            new_state["context"]["error_node"] = "classify"
            # Still increment step to allow progression
            new_state = increment_step(new_state)
            return new_state
    
    def _route_to_agent_node(self, state: WorkflowState) -> WorkflowState:
        """
        Route to agent node - selects appropriate agent based on command.
        
        Uses the agent registry's intelligent routing to select the best agent
        for the user's command. Stores the selected agent type in state context
        for use by the execute node.
        
        Supports agent handoff: If previous agent specified next_agent in response,
        routes to that agent instead of performing new selection.
        
        Implements fallback to default agent if routing fails.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with selected agent stored in context
            
        Validates: Requirements 10.1, 10.2, 10.3, 10.4, 12.1, 12.3, 13.1, 13.2
        
        Examples:
            >>> state = {"user_input": "volume up", ...}
            >>> new_state = manager._route_to_agent_node(state)
            >>> new_state["context"]["assigned_agent"]
            'pc_control'
        """
        try:
            # Check for agent handoff (Requirement 13.1, 13.2)
            if state["agent_responses"]:
                last_response = state["agent_responses"][-1]
                next_agent = last_response.get("next_agent")
                
                if next_agent:
                    # Agent handoff requested
                    new_state = state.copy()
                    new_state["context"] = state["context"].copy()
                    new_state["context"]["assigned_agent"] = next_agent
                    new_state["context"]["handoff_from"] = last_response.get("agent_name")
                    new_state["context"]["is_handoff"] = True
                    
                    # Increment step
                    new_state = increment_step(new_state)
                    return new_state
            
            # Normal agent selection
            command = state["user_input"]
            
            # Use agent registry's intelligent selection
            agent = self.agent_registry.get_agent_for_command(command)
            
            # Store selected agent in context
            new_state = state.copy()
            new_state["context"] = state["context"].copy()
            new_state["context"]["assigned_agent"] = agent.agent_type
            new_state["context"]["is_handoff"] = False
            
            # Increment step
            new_state = increment_step(new_state)
            
            return new_state
            
        except Exception as e:
            # Fallback to default agent on routing failure (Requirement 12.3)
            new_state = state.copy()
            new_state["context"] = state["context"].copy()
            new_state["context"]["last_error"] = f"route_node_error: {str(e)}"
            new_state["context"]["error_node"] = "route"
            
            # Fallback to default agent
            try:
                default_agent = self.agent_registry.get_agent("default")
                new_state["context"]["assigned_agent"] = default_agent.agent_type
                new_state["context"]["used_fallback_agent"] = True
            except Exception as fallback_error:
                # If even fallback fails, mark for immediate finalization
                new_state["context"]["assigned_agent"] = None
                new_state["context"]["fallback_failed"] = True
                new_state["context"]["last_error"] = f"route_fallback_error: {str(fallback_error)}"
            
            # Increment step
            new_state = increment_step(new_state)
            
            return new_state
    
    def _execute_agent_node(self, state: WorkflowState) -> WorkflowState:
        """
        Execute agent node - runs the selected agent's task.
        
        Retrieves the agent from the registry and executes the user command.
        Captures the result in an AgentResponse and appends it to the state's
        agent_responses list.
        
        Implements comprehensive error handling with agent fallback support.
        
        Args:
            state: Current workflow state with assigned agent
            
        Returns:
            Updated state with agent response appended
            
        Validates: Requirements 10.5, 12.1, 12.3
        
        Examples:
            >>> state = {"context": {"assigned_agent": "pc_control"}, ...}
            >>> new_state = manager._execute_agent_node(state)
            >>> len(new_state["agent_responses"])
            1
        """
        agent_type = state["context"].get("assigned_agent", "default")
        command = state["user_input"]
        
        # Check if routing fallback failed
        if state["context"].get("fallback_failed", False):
            # Cannot execute without an agent
            response = error_response(
                agent_name="none",
                action_taken="execute_command",
                error="Agent routing failed and no fallback available",
                retry_recommended=False,
                metadata={"command": command}
            )
            
            new_state = add_agent_response(state, response.to_dict())
            new_state["context"] = state["context"].copy()
            new_state["context"]["last_error"] = "execution_failed: no agent available"
            new_state = increment_step(new_state)
            return new_state
        
        try:
            # Get agent from registry
            agent = self.agent_registry.get_agent(agent_type)
            
            # Execute agent task
            result = agent.execute_task(command)
            
            # Create success response
            response = success_response(
                agent_name=agent_type,
                action_taken=result.get("action", "execute_command"),
                result=result,
                metadata={"command": command}
            )
            
        except Exception as e:
            # Capture error in state (Requirement 12.1)
            error_str = str(e)
            
            # Create error response
            response = error_response(
                agent_name=agent_type,
                action_taken="execute_command",
                error=error_str,
                retry_recommended=self._is_retryable_error(error_str),
                metadata={"command": command, "exception_type": type(e).__name__}
            )
            
            # Store error in context for retry logic
            new_state = state.copy()
            new_state["context"] = state["context"].copy()
            new_state["context"]["last_error"] = f"execute_node_error: {error_str}"
            new_state["context"]["error_node"] = "execute"
            
            # Add response and return early
            new_state = add_agent_response(new_state, response.to_dict())
            new_state = increment_step(new_state)
            return new_state
        
        # Add successful response to state
        new_state = add_agent_response(state, response.to_dict())
        
        # Increment step
        new_state = increment_step(new_state)
        
        return new_state
    
    def _validate_result_node(self, state: WorkflowState) -> WorkflowState:
        """
        Validate result node - checks if execution succeeded.
        
        Examines the last agent response to determine if execution was successful.
        Updates context with validation status for use by should_retry conditional.
        
        Implements comprehensive error handling with graceful degradation.
        
        Args:
            state: Current workflow state with agent responses
            
        Returns:
            Updated state with validation status in context
            
        Validates: Requirement 12.1 - Error capture
            
        Examples:
            >>> state = {"agent_responses": [{"success": True}], ...}
            >>> new_state = manager._validate_result_node(state)
            >>> new_state["context"]["validation_passed"]
            True
        """
        try:
            # Get last agent response
            if not state["agent_responses"]:
                # No responses - validation fails
                new_state = state.copy()
                new_state["context"] = state["context"].copy()
                new_state["context"]["validation_passed"] = False
                new_state["context"]["validation_error"] = "No agent responses"
                new_state["context"]["last_error"] = "validate_node_error: no responses"
                return increment_step(new_state)
            
            last_response = state["agent_responses"][-1]
            success = last_response.get("success", False)
            
            # Update context with validation result
            new_state = state.copy()
            new_state["context"] = state["context"].copy()
            new_state["context"]["validation_passed"] = success
            
            if not success:
                error_msg = last_response.get("error", "Unknown error")
                new_state["context"]["validation_error"] = error_msg
                new_state["context"]["last_error"] = f"validation_failed: {error_msg}"
            
            # Increment step
            new_state = increment_step(new_state)
            
            return new_state
            
        except Exception as e:
            # Capture validation node error
            new_state = state.copy()
            new_state["context"] = state["context"].copy()
            new_state["context"]["validation_passed"] = False
            new_state["context"]["validation_error"] = f"Validation node error: {str(e)}"
            new_state["context"]["last_error"] = f"validate_node_error: {str(e)}"
            new_state["context"]["error_node"] = "validate"
            new_state = increment_step(new_state)
            return new_state
    
    def _should_retry(self, state: WorkflowState) -> Literal["retry", "finalize"]:
        """
        Conditional routing logic - determines if retry should occur.
        
        Checks:
        1. Was validation successful? → finalize
        2. Have we exceeded max_retries? → finalize
        3. Is the error retryable? → retry
        4. Otherwise → finalize
        
        Args:
            state: Current workflow state after validation
            
        Returns:
            "retry" to retry with backoff, "finalize" to complete
            
        Validates: Requirements 9.2
        
        Examples:
            >>> state = {"context": {"validation_passed": True}, ...}
            >>> manager._should_retry(state)
            'finalize'
            
            >>> state = {"context": {"validation_passed": False}, "retry_count": 0, ...}
            >>> manager._should_retry(state)
            'retry'
        """
        # Check if validation passed
        if state["context"].get("validation_passed", False):
            return "finalize"
        
        # Check retry count (default max_retries is 3)
        max_retries = state["context"].get("max_retries", 3)
        if state["retry_count"] >= max_retries:
            return "finalize"
        
        # Check if error is retryable
        error = state["context"].get("validation_error", "")
        if self._is_retryable_error(error):
            return "retry"
        
        # Not retryable, go to finalize
        return "finalize"
    
    def _retry_handler_node(self, state: WorkflowState) -> WorkflowState:
        """
        Retry handler node - implements exponential backoff.
        
        Increments retry_count and applies exponential backoff delay:
        - Retry 1: 2^0 = 1 second
        - Retry 2: 2^1 = 2 seconds
        - Retry 3: 2^2 = 4 seconds
        
        Implements comprehensive error handling to ensure retry logic always completes.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with incremented retry_count
            
        Validates: Requirements 9.3, 9.4, 9.5, 9.6, 12.1
        
        Examples:
            >>> state = {"retry_count": 0, ...}
            >>> new_state = manager._retry_handler_node(state)
            >>> new_state["retry_count"]
            1
        """
        try:
            import time
            
            # Increment retry count
            new_state = state.copy()
            new_state["retry_count"] = state["retry_count"] + 1
            
            # Exponential backoff: 2^(retry_count - 1)
            backoff_seconds = 2 ** (new_state["retry_count"] - 1)
            
            # Store backoff time in context for logging/monitoring
            new_state["context"] = state["context"].copy()
            new_state["context"]["last_backoff_seconds"] = backoff_seconds
            
            # Apply backoff delay
            time.sleep(backoff_seconds)
            
            # Increment step
            new_state = increment_step(new_state)
            
            return new_state
            
        except Exception as e:
            # Even if retry logic fails, increment retry count and continue
            new_state = state.copy()
            new_state["retry_count"] = state["retry_count"] + 1
            new_state["context"] = state["context"].copy()
            new_state["context"]["last_error"] = f"retry_node_error: {str(e)}"
            new_state["context"]["error_node"] = "retry"
            new_state = increment_step(new_state)
            return new_state
    
    def _finalize_response_node(self, state: WorkflowState) -> WorkflowState:
        """
        Finalize response node - prepares final result.
        
        Creates the final result dictionary based on execution outcome.
        Sets the final_result field to mark the state as terminal.
        
        Implements comprehensive error handling to ensure finalization always succeeds.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with final_result set (terminal state)
            
        Validates: Requirement 12.1 - Error capture
            
        Examples:
            >>> state = {"agent_responses": [{"success": True}], ...}
            >>> new_state = manager._finalize_response_node(state)
            >>> new_state["final_result"]["success"]
            True
        """
        try:
            # Determine overall success
            validation_passed = state["context"].get("validation_passed", False)
            
            # Build final result
            final_result = {
                "success": validation_passed,
                "agent_responses": state["agent_responses"],
                "total_steps": state["current_step"],
                "total_retries": state["retry_count"]
            }
            
            # Add error if failed
            if not validation_passed:
                final_result["error"] = state["context"].get("validation_error", "Unknown error")
                final_result["last_error"] = state["context"].get("last_error", "")
            
            # Add fallback info if used
            if state["context"].get("used_fallback_agent", False):
                final_result["used_fallback"] = True
            
            # Set final result (marks state as terminal)
            new_state = set_final_result(state, final_result)
            
            # Increment step
            new_state = increment_step(new_state)
            
            return new_state
            
        except Exception as e:
            # Finalization should never fail completely - create minimal result
            minimal_result = {
                "success": False,
                "error": f"Finalization error: {str(e)}",
                "agent_responses": state.get("agent_responses", []),
                "total_steps": state.get("current_step", 0),
                "total_retries": state.get("retry_count", 0)
            }
            
            new_state = set_final_result(state, minimal_result)
            new_state["context"] = state["context"].copy()
            new_state["context"]["last_error"] = f"finalize_node_error: {str(e)}"
            new_state = increment_step(new_state)
            return new_state
    
    def _is_retryable_error(self, error: str) -> bool:
        """
        Determine if an error is retryable.
        
        Retryable errors include:
        - Network timeouts
        - Rate limiting
        - Temporary unavailability
        - Element not found (UI automation)
        
        Args:
            error: Error message string
            
        Returns:
            True if error should be retried, False otherwise
            
        Examples:
            >>> manager._is_retryable_error("timeout")
            True
            >>> manager._is_retryable_error("invalid input")
            False
        """
        error_lower = error.lower()
        
        retryable_patterns = [
            "timeout",
            "network",
            "connection",
            "rate limit",
            "429",
            "503",
            "element not found",
            "not found",
            "temporarily unavailable"
        ]
        
        return any(pattern in error_lower for pattern in retryable_patterns)
    
    def get_compiled_graph(self) -> StateGraph:
        """
        Get the compiled graph, building it if necessary.
        
        Returns:
            Compiled StateGraph instance
            
        Examples:
            >>> graph = manager.get_compiled_graph()
            >>> result = graph.invoke(state)
        """
        if self._graph is None:
            return self.build_graph()
        return self._graph
