"""
Circular dependency detection for agent workflows.

This module provides functions to detect circular dependencies in agent
collaboration graphs before workflow execution. It prevents infinite loops
caused by agents calling each other in a cycle.

Validates: Requirement 12.4
"""

from typing import Dict, Set, List, Optional


class CircularDependencyError(Exception):
    """
    Exception raised when a circular dependency is detected in the agent graph.
    
    Circular dependencies occur when agents have a cycle in their collaboration,
    such as: Agent A → Agent B → Agent C → Agent A
    
    This would cause infinite loops during execution, so the graph must be
    validated before compilation.
    
    Validates: Requirement 12.4
    
    Examples:
        >>> raise CircularDependencyError("Cycle: A → B → C → A")
        Traceback (most recent call last):
        ...
        CircularDependencyError: Cycle: A → B → C → A
    """
    pass


def validate_agent_dependencies(
    agent_dependencies: Dict[str, List[str]]
) -> None:
    """
    Validate that agent collaboration graph has no circular dependencies.
    
    Uses Depth-First Search (DFS) to detect cycles in the agent dependency graph.
    If a cycle is detected, raises CircularDependencyError with the cycle path.
    
    The agent_dependencies dict maps each agent type to a list of other agent
    types it may invoke or hand off to during execution.
    
    Args:
        agent_dependencies: Dict mapping agent_type → List[dependent_agent_types]
        
    Raises:
        CircularDependencyError: If a cycle is detected in the graph
        
    Validates: Requirement 12.4
    
    Examples:
        >>> # Valid graph (no cycles)
        >>> deps = {
        ...     "orchestrator": ["pc_control", "whatsapp"],
        ...     "pc_control": [],
        ...     "whatsapp": []
        ... }
        >>> validate_agent_dependencies(deps)  # No exception
        
        >>> # Invalid graph (cycle detected)
        >>> deps = {
        ...     "agent_a": ["agent_b"],
        ...     "agent_b": ["agent_c"],
        ...     "agent_c": ["agent_a"]
        ... }
        >>> validate_agent_dependencies(deps)
        Traceback (most recent call last):
        ...
        CircularDependencyError: Circular dependency detected: agent_a → agent_b → agent_c → agent_a
        
        >>> # Self-loop
        >>> deps = {"agent_a": ["agent_a"]}
        >>> validate_agent_dependencies(deps)
        Traceback (most recent call last):
        ...
        CircularDependencyError: Circular dependency detected: agent_a → agent_a
    """
    # Track visited nodes and nodes in current path
    visited: Set[str] = set()
    rec_stack: Set[str] = set()
    path: List[str] = []
    
    def dfs(agent: str) -> Optional[List[str]]:
        """
        Perform DFS to detect cycles.
        
        Args:
            agent: Current agent being visited
            
        Returns:
            List representing the cycle path if cycle found, None otherwise
        """
        # Mark current node as visited and add to recursion stack
        visited.add(agent)
        rec_stack.add(agent)
        path.append(agent)
        
        # Recur for all dependencies
        for dependent in agent_dependencies.get(agent, []):
            # If dependent not visited, recurse
            if dependent not in visited:
                cycle = dfs(dependent)
                if cycle:
                    return cycle
            # If dependent is in recursion stack, cycle found
            elif dependent in rec_stack:
                # Build cycle path
                cycle_start_idx = path.index(dependent)
                cycle_path = path[cycle_start_idx:] + [dependent]
                return cycle_path
        
        # Remove from recursion stack before backtracking
        rec_stack.remove(agent)
        path.pop()
        
        return None
    
    # Check each agent as potential cycle start
    for agent in agent_dependencies:
        if agent not in visited:
            cycle = dfs(agent)
            if cycle:
                cycle_str = " → ".join(cycle)
                raise CircularDependencyError(
                    f"Circular dependency detected: {cycle_str}"
                )


def build_agent_dependency_graph(
    agent_responses: List[dict]
) -> Dict[str, List[str]]:
    """
    Build agent dependency graph from agent responses.
    
    Extracts the "next_agent" field from AgentResponse objects to construct
    a graph showing which agents invoke which other agents.
    
    Args:
        agent_responses: List of AgentResponse dicts from workflow execution
        
    Returns:
        Dict mapping agent_type → List[dependent_agent_types]
        
    Examples:
        >>> responses = [
        ...     {"agent_name": "orchestrator", "next_agent": "pc_control"},
        ...     {"agent_name": "pc_control", "next_agent": None}
        ... ]
        >>> build_agent_dependency_graph(responses)
        {'orchestrator': ['pc_control'], 'pc_control': []}
    """
    dependencies: Dict[str, List[str]] = {}
    
    for response in agent_responses:
        agent_name = response.get("agent_name")
        next_agent = response.get("next_agent")
        
        if agent_name:
            # Initialize agent in graph if not present
            if agent_name not in dependencies:
                dependencies[agent_name] = []
            
            # Add dependency if next_agent specified
            if next_agent and next_agent not in dependencies[agent_name]:
                dependencies[agent_name].append(next_agent)
    
    return dependencies


def validate_workflow_state(state: dict) -> None:
    """
    Validate that a workflow state has no circular dependencies.
    
    Convenience function that extracts agent_responses from a WorkflowState
    dict, builds the dependency graph, and validates it for cycles.
    
    Args:
        state: WorkflowState dict with agent_responses field
        
    Raises:
        CircularDependencyError: If circular dependency detected
        
    Examples:
        >>> state = {
        ...     "agent_responses": [
        ...         {"agent_name": "a", "next_agent": "b"},
        ...         {"agent_name": "b", "next_agent": None}
        ...     ]
        ... }
        >>> validate_workflow_state(state)  # No exception
    """
    agent_responses = state.get("agent_responses", [])
    
    if not agent_responses:
        # No responses yet, nothing to validate
        return
    
    # Build and validate dependency graph
    dependencies = build_agent_dependency_graph(agent_responses)
    validate_agent_dependencies(dependencies)
