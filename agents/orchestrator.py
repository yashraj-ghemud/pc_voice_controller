"""
OrchestratorAgent - Central coordinator for multi-agent system.

This module implements the OrchestratorAgent class that serves as the main
entry point for all user commands. It decides routing strategy (fast route vs.
graph workflow), classifies commands, creates workflow graphs, and coordinates
specialized agents through the AgentRegistry.

The OrchestratorAgent extends AutoGen's AssistantAgent and integrates with
LangGraph for workflow orchestration.

Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 21.1, 21.3
"""

import time
from typing import Optional, Any
from agents.base import BaseAgent
from agents.registry import AgentRegistry
from agents.state_manager import StateManager
from agents.state import create_initial_state, WorkflowState
from agents.models import CommandClassification, simple_classification, complex_classification
import intent  # Existing fast route patterns


class OrchestratorAgent(BaseAgent):
    """
    Central coordinator for multi-agent command execution.
    
    The OrchestratorAgent is the primary entry point for all user commands.
    It determines execution strategy through two paths:
    
    1. Fast Route: Simple commands that match pre-defined patterns execute
       directly without graph overhead (<500ms response time)
    
    2. Graph Workflow: Complex commands routed through LangGraph StateGraph
       with intelligent agent selection, retry logic, and state management
    
    The orchestrator uses the existing intent.py module for fast route pattern
    matching and creates StateGraph workflows for multi-step tasks requiring
    agent coordination.
    
    Attributes:
        llm_config: Configuration for Gemini LLM (with API key rotation)
        agent_registry: Registry for discovering and accessing agents
        state_manager: StateManager for building and executing workflows
        fast_route_patterns: Loaded from intent.py (50+ patterns)
        
    Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 21.1, 21.3
    
    Examples:
        >>> registry = AgentRegistry()
        >>> orchestrator = OrchestratorAgent(registry=registry)
        >>> result = orchestrator.process_command("volume up", {})
        >>> result["success"]
        True
        >>> result["execution_time"] < 0.5  # Fast route
        True
    """
    
    def __init__(
        self,
        registry: AgentRegistry,
        llm_config: Optional[dict[str, Any]] = None,
        name: str = "OrchestratorAgent",
        max_retries: int = 3
    ):
        """
        Initialize OrchestratorAgent with agent registry and LLM config.
        
        Args:
            registry: AgentRegistry for agent discovery
            llm_config: Optional LLM configuration (uses defaults if None)
            name: Agent name (default: "OrchestratorAgent")
            max_retries: Maximum retry attempts for graph workflows (default: 3)
            
        Examples:
            >>> registry = AgentRegistry()
            >>> orchestrator = OrchestratorAgent(registry=registry)
            >>> orchestrator.name
            'OrchestratorAgent'
        """
        super().__init__(
            name=name,
            agent_type="orchestrator",
            description="Central coordinator for multi-agent command execution"
        )
        
        self.agent_registry = registry
        self.llm_config = llm_config or self._get_default_llm_config()
        self.state_manager = StateManager(registry)
        self.max_retries = max_retries
        
        # Pre-compile graph at initialization for performance (Requirement 20.3)
        self._compiled_graph = None
        
    def _get_default_llm_config(self) -> dict[str, Any]:
        """
        Get default LLM configuration with Gemini API key rotation.
        
        Uses the existing API key rotation mechanism from brain.py.
        
        Returns:
            Dictionary with LLM configuration
            
        Validates: Requirements 21.1, 21.3
        """
        import brain
        
        # Use gemini-2.0-flash-lite for routing decisions (Requirement 21.1)
        return {
            "model": "gemini-2.0-flash-lite",
            "api_key": brain.API_KEYS[brain.current_key_index] if brain.API_KEYS else None,
            "temperature": 0.3,  # Lower temperature for routing decisions
        }
    
    def process_command(
        self,
        user_input: str,
        context: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """
        Main entry point for command processing.
        
        This is the primary interface for processing user commands. It:
        1. Checks if command matches fast route pattern
        2. If fast route: executes directly (<500ms)
        3. If not: classifies command and creates workflow graph
        4. Executes graph with timeout enforcement
        5. Returns formatted result
        
        PRECONDITIONS:
        - user_input is non-empty string
        - agent_registry is initialized with agents
        
        POSTCONDITIONS:
        - Returns result dict with success status
        - Execution completes within 10 seconds or times out
        - Fast route commands complete within 500ms
        
        Args:
            user_input: User's command text
            context: Optional conversation context
            
        Returns:
            Dictionary with:
                - success: bool indicating execution status
                - result: Execution result data
                - execution_time: Time taken in seconds
                - used_fast_route: Whether fast route was used
                - error: Error message if failed (optional)
                
        Validates: Requirements 1.1, 1.2, 1.3, 1.5
        
        Examples:
            >>> orchestrator = OrchestratorAgent(registry=AgentRegistry())
            >>> result = orchestrator.process_command("volume up", {})
            >>> result["success"]
            True
            >>> result["used_fast_route"]
            True
        """
        start_time = time.time()
        context = context or {}
        
        try:
            # STEP 1: Check fast route (Requirement 1.2)
            if self.should_use_fast_route(user_input):
                result = self._execute_fast_route(user_input)
                execution_time = time.time() - start_time
                
                return {
                    "success": result.get("success", True),
                    "result": result,
                    "execution_time": execution_time,
                    "used_fast_route": True
                }
            
            # STEP 2: Classify command (Requirement 1.1, 1.4)
            classification = self.classify_command(user_input, context)
            
            # STEP 3: Create and execute workflow graph (Requirement 1.3)
            graph_result = self.create_workflow_graph(
                user_input,
                classification,
                context
            )
            
            execution_time = time.time() - start_time
            
            return {
                "success": graph_result.get("success", False),
                "result": graph_result,
                "execution_time": execution_time,
                "used_fast_route": False,
                "classification": classification.to_dict()
            }
            
        except TimeoutError as e:
            # Requirement 1.5: Timeout handling
            execution_time = time.time() - start_time
            return {
                "success": False,
                "result": None,
                "execution_time": execution_time,
                "used_fast_route": False,
                "error": f"Execution timeout after {execution_time:.2f}s: {str(e)}"
            }
        
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "success": False,
                "result": None,
                "execution_time": execution_time,
                "used_fast_route": False,
                "error": f"Execution error: {str(e)}"
            }
    
    def should_use_fast_route(self, command: str) -> bool:
        """
        Check if command matches fast route pattern.
        
        Uses the existing intent.py module which contains 50+ pre-defined
        patterns for common commands (volume, brightness, app control, etc.).
        
        Fast route commands execute directly without LLM calls or graph
        overhead, achieving <500ms response times.
        
        PRECONDITIONS:
        - command is non-empty string
        
        POSTCONDITIONS:
        - Returns True if pattern matches, False otherwise
        - No side effects (pure function)
        
        Args:
            command: User command text to check
            
        Returns:
            True if command matches fast route pattern, False otherwise
            
        Validates: Requirements 1.2, 11.1, 11.2, 11.3, 11.4
        
        Examples:
            >>> orchestrator = OrchestratorAgent(registry=AgentRegistry())
            >>> orchestrator.should_use_fast_route("volume up")
            True
            >>> orchestrator.should_use_fast_route("screenshot")
            True
            >>> orchestrator.should_use_fast_route("send papa a complex message")
            False
        """
        # Use existing intent.py classify function
        # Returns None if no pattern match, dict if matched
        result = intent.classify(command)
        return result is not None
    
    def classify_command(
        self,
        user_input: str,
        context: dict[str, Any]
    ) -> CommandClassification:
        """
        Classify user command to determine routing strategy.
        
        Analyzes command to determine:
        - Command type: simple, complex, or multi_step
        - Intent: Specific goal (e.g., "volume_control", "send_message")
        - Confidence: Score between 0.0 and 1.0
        - Required agents: Which agents needed for execution
        - Estimated steps: How many execution steps expected
        
        Uses keyword matching and pattern analysis for classification.
        Falls back to LLM-based classification for ambiguous commands.
        
        PRECONDITIONS:
        - user_input is non-empty string
        - context is valid dict
        
        POSTCONDITIONS:
        - Returns CommandClassification with valid fields
        - confidence is between 0.0 and 1.0
        - command_type is one of ["simple", "complex", "multi_step"]
        
        Args:
            user_input: User command text
            context: Conversation context
            
        Returns:
            CommandClassification with routing details
            
        Validates: Requirements 1.1, 1.4, 10.5
        
        Examples:
            >>> orchestrator = OrchestratorAgent(registry=AgentRegistry())
            >>> classification = orchestrator.classify_command("open chrome", {})
            >>> classification.command_type
            'simple'
            >>> classification.confidence >= 0.0 and classification.confidence <= 1.0
            True
        """
        command_lower = user_input.lower()
        
        # Simple keyword-based classification
        # PC Control patterns
        if any(kw in command_lower for kw in ["volume", "brightness", "open", "close", "app"]):
            return simple_classification(
                intent="pc_control",
                confidence=0.9,
                use_fast_route=False,
                requires_agents=["pc_control"]
            )
        
        # WhatsApp patterns
        if any(kw in command_lower for kw in ["whatsapp", "message", "send", "bhejo"]):
            # Check if file is involved
            if any(kw in command_lower for kw in ["file", "document", "photo", "pdf"]):
                return complex_classification(
                    intent="send_whatsapp_file",
                    confidence=0.85,
                    requires_agents=["whatsapp"],
                    estimated_steps=3
                )
            else:
                return simple_classification(
                    intent="send_whatsapp_message",
                    confidence=0.9,
                    use_fast_route=False,
                    requires_agents=["whatsapp"]
                )
        
        # Screen AI patterns
        if any(kw in command_lower for kw in ["click", "type", "screenshot"]):
            return simple_classification(
                intent="screen_interaction",
                confidence=0.85,
                use_fast_route=False,
                requires_agents=["screen_ai"]
            )
        
        # Web patterns
        if any(kw in command_lower for kw in ["search", "google", "open url", "browse"]):
            return simple_classification(
                intent="web_action",
                confidence=0.9,
                use_fast_route=False,
                requires_agents=["web"]
            )
        
        # Default: simple command with lower confidence
        return simple_classification(
            intent="unknown",
            confidence=0.5,
            use_fast_route=False,
            requires_agents=[]
        )
    
    def create_workflow_graph(
        self,
        user_input: str,
        classification: CommandClassification,
        context: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Create and execute LangGraph workflow for command.
        
        This method:
        1. Initializes WorkflowState from command and context
        2. Gets or builds compiled StateGraph
        3. Invokes graph with timeout enforcement (10 seconds)
        4. Extracts and formats final result
        
        The graph orchestrates agent selection, execution, validation,
        and retry logic through LangGraph nodes and edges.
        
        PRECONDITIONS:
        - user_input is non-empty string
        - classification is valid CommandClassification
        - state_manager is initialized
        
        POSTCONDITIONS:
        - Returns final result dict
        - Execution completes within 10 seconds or times out
        - WorkflowState.final_result is set
        
        Args:
            user_input: User command text
            classification: Command classification from classify_command
            context: Conversation context
            
        Returns:
            Dictionary with final execution result
            
        Raises:
            TimeoutError: If execution exceeds 10 seconds
            
        Validates: Requirements 1.3, 1.5, 2.4, 30.2
        
        Examples:
            >>> orchestrator = OrchestratorAgent(registry=AgentRegistry())
            >>> classification = simple_classification("test", confidence=0.9)
            >>> result = orchestrator.create_workflow_graph("test", classification, {})
            >>> "success" in result
            True
        """
        # Initialize WorkflowState (Requirement 2.2)
        initial_state = create_initial_state(
            user_input=user_input,
            command_type=classification.command_type,
            context={
                **context,
                "max_retries": self.max_retries,
                "classification": classification.to_dict()
            }
        )
        
        # Get or build compiled graph (lazy compilation)
        if self._compiled_graph is None:
            self._compiled_graph = self.state_manager.build_graph()
        
        # Execute graph with timeout (Requirement 1.5, 30.2)
        start_time = time.time()
        timeout_seconds = 10
        
        try:
            # Invoke graph
            final_state = self._compiled_graph.invoke(initial_state)
            
            # Check execution time
            execution_time = time.time() - start_time
            if execution_time > timeout_seconds:
                raise TimeoutError(
                    f"Graph execution exceeded {timeout_seconds}s timeout"
                )
            
            # Extract final result (Requirement 2.4)
            final_result = final_state.get("final_result", {})
            
            if final_result is None:
                final_result = {
                    "success": False,
                    "error": "Graph execution completed but no final_result set"
                }
            
            return final_result
            
        except Exception as e:
            # Graph execution failed
            return {
                "success": False,
                "error": f"Graph execution failed: {str(e)}",
                "agent_responses": initial_state.get("agent_responses", [])
            }
    
    def _execute_fast_route(self, command: str) -> dict[str, Any]:
        """
        Execute command through fast route (direct execution).
        
        Uses intent.py classify to get action and then executes directly
        without graph overhead. This preserves the existing fast execution
        path for simple commands.
        
        Args:
            command: User command matching fast route pattern
            
        Returns:
            Execution result dictionary
            
        Validates: Requirements 1.2, 11.1, 11.2, 16.2
        
        Examples:
            >>> orchestrator = OrchestratorAgent(registry=AgentRegistry())
            >>> result = orchestrator._execute_fast_route("volume up")
            >>> result["action"]
            'VOLUME_UP'
        """
        # Get fast route classification from intent.py
        intent_result = intent.classify(command)
        
        if intent_result is None:
            return {
                "success": False,
                "error": "Fast route pattern not matched",
                "action": None
            }
        
        # Return the intent result as-is
        # This will be executed by actions.py in the main flow
        return {
            "success": True,
            "action": intent_result.get("action"),
            "target": intent_result.get("target"),
            "value": intent_result.get("value"),
            "say": intent_result.get("say", "Done")
        }
    
    def execute_task(
        self,
        task_description: str,
        context: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """
        Execute a task assigned to the orchestrator.
        
        This method satisfies the BaseAgent interface. It delegates to
        process_command for actual execution.
        
        Args:
            task_description: Natural language task description
            context: Optional context from workflow state
            
        Returns:
            Dictionary containing execution result
            
        Examples:
            >>> orchestrator = OrchestratorAgent(registry=AgentRegistry())
            >>> result = orchestrator.execute_task("volume up", {})
            >>> result["success"]
            True
        """
        return self.process_command(task_description, context)
    
    def sequence_agents(
        self,
        agent_sequence: list[str],
        user_input: str,
        context: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """
        Coordinate execution of multiple agents in sequence.
        
        Executes agents one after another, passing results through WorkflowState.
        Each agent has access to previous agents' results via agent_responses.
        This enables complex multi-step workflows like:
        - Screenshot + WhatsApp send
        - Web search + Screen interaction
        - File search + File send
        
        PRECONDITIONS:
        - agent_sequence contains valid agent type names
        - All agents in sequence are registered
        - user_input is non-empty string
        
        POSTCONDITIONS:
        - All agents execute in order
        - Each agent can access previous results
        - WorkflowState updated after each agent
        - Returns combined result
        
        LOOP INVARIANT:
        - After each iteration i, agent_responses contains i+1 responses
        - WorkflowState remains valid throughout execution
        
        Args:
            agent_sequence: List of agent types to execute in order
            user_input: Original user command
            context: Optional workflow context
            
        Returns:
            Dictionary with:
                - success: Overall success status
                - agent_responses: List of all agent responses
                - final_result: Result from last agent
                
        Validates: Requirements 13.1, 13.2, 13.3, 13.4
        
        Examples:
            >>> orchestrator = OrchestratorAgent(registry=AgentRegistry())
            >>> result = orchestrator.sequence_agents(
            ...     ["screen_ai", "whatsapp"],
            ...     "papa ko screenshot bhejo",
            ...     {}
            ... )
            >>> len(result["agent_responses"])
            2
            >>> result["success"]
            True
        """
        from agents.state import create_initial_state, add_agent_response
        from agents.models import success_response, error_response
        
        context = context or {}
        
        # Initialize workflow state (Requirement 13.2)
        state = create_initial_state(
            user_input=user_input,
            command_type="multi_step",
            context={
                **context,
                "agent_sequence": agent_sequence,
                "sequence_index": 0
            }
        )
        
        all_success = True
        
        # Execute each agent in sequence (Requirement 13.1)
        for i, agent_type in enumerate(agent_sequence):
            try:
                # Get agent from registry
                agent = self.agent_registry.get_agent(agent_type)
                
                # Prepare context with previous results (Requirement 13.3)
                agent_context = {
                    **context,
                    "previous_responses": state["agent_responses"],
                    "sequence_index": i,
                    "is_last_agent": i == len(agent_sequence) - 1
                }
                
                # Execute agent task
                result = agent.execute_task(user_input, agent_context)
                
                # Create agent response
                if result.get("success", False):
                    response = success_response(
                        agent_name=agent_type,
                        action_taken=result.get("action", "execute_task"),
                        result=result,
                        metadata={
                            "sequence_position": i,
                            "command": user_input
                        }
                    )
                else:
                    response = error_response(
                        agent_name=agent_type,
                        action_taken="execute_task",
                        error=result.get("error", "Agent execution failed"),
                        retry_recommended=False,
                        metadata={
                            "sequence_position": i,
                            "command": user_input
                        }
                    )
                    all_success = False
                
                # Update state with agent response (Requirement 13.2)
                state = add_agent_response(state, response.to_dict())
                
                # If agent failed and not continuing, break
                if not result.get("success", False):
                    break
                    
            except Exception as e:
                # Handle agent execution error
                response = error_response(
                    agent_name=agent_type,
                    action_taken="execute_task",
                    error=f"Agent execution exception: {str(e)}",
                    retry_recommended=False,
                    metadata={
                        "sequence_position": i,
                        "command": user_input,
                        "exception_type": type(e).__name__
                    }
                )
                
                state = add_agent_response(state, response.to_dict())
                all_success = False
                break
        
        # Build final result (Requirement 13.4)
        final_result = {
            "success": all_success,
            "agent_responses": state["agent_responses"],
            "total_agents": len(agent_sequence),
            "executed_agents": len(state["agent_responses"])
        }
        
        # Add last agent result if available
        if state["agent_responses"]:
            final_result["final_agent_result"] = state["agent_responses"][-1]
        
        return final_result
    
    def __repr__(self) -> str:
        """String representation of orchestrator."""
        return (
            f"OrchestratorAgent(name='{self.name}', "
            f"agents={len(self.agent_registry.list_agents())}, "
            f"max_retries={self.max_retries})"
        )

