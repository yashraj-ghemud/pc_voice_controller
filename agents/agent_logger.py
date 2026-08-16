"""
Comprehensive logging for the agent system.

This module provides structured logging for agent executions, graph workflows,
and system events. Logs include timestamps, execution times, success status,
and error tracebacks for debugging.

Validates: Requirements 18.1, 18.2, 18.3
"""

import logging
import json
import time
from typing import Optional, Any, Dict, List
from datetime import datetime
from pathlib import Path


# Configure logging
LOG_DIR = Path("logs/agents")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Create formatters
DETAILED_FORMAT = logging.Formatter(
    '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

JSON_FORMAT = logging.Formatter('%(message)s')


class AgentLogger:
    """
    Structured logger for agent system with multiple output formats.
    
    Provides logging for:
    - Individual agent executions
    - Complete graph workflows
    - State transitions
    - Retry attempts
    - Security events
    
    Logs are written to both file and console, with structured JSON format
    for machine parsing and human-readable format for debugging.
    
    Validates: Requirements 18.1, 18.2, 18.3
    
    Examples:
        >>> logger = AgentLogger("orchestrator")
        >>> logger.log_agent_execution(
        ...     agent_name="pc_control",
        ...     command="volume up",
        ...     success=True,
        ...     execution_time=0.5
        ... )
    """
    
    def __init__(self, component_name: str = "agent_system"):
        """
        Initialize logger for a specific component.
        
        Args:
            component_name: Name of component (orchestrator, state_manager, etc.)
        """
        self.component_name = component_name
        self.logger = logging.getLogger(f"kypzer.agents.{component_name}")
        self.logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # File handler for detailed logs
        file_handler = logging.FileHandler(
            LOG_DIR / f"{component_name}.log",
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(DETAILED_FORMAT)
        self.logger.addHandler(file_handler)
        
        # JSON handler for structured logs
        json_handler = logging.FileHandler(
            LOG_DIR / f"{component_name}_json.log",
            encoding='utf-8'
        )
        json_handler.setLevel(logging.INFO)
        json_handler.setFormatter(JSON_FORMAT)
        self.logger.addHandler(json_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(DETAILED_FORMAT)
        self.logger.addHandler(console_handler)
    
    def log_agent_execution(
        self,
        agent_name: str,
        command: str,
        success: bool,
        execution_time: float,
        result: Optional[Any] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Log individual agent execution.
        
        Records execution details including timing, success status, and results.
        
        Args:
            agent_name: Name of agent that executed
            command: User command processed
            success: Whether execution succeeded
            execution_time: Time taken in seconds
            result: Execution result data (optional)
            error: Error message if failed (optional)
            metadata: Additional metadata (optional)
            
        Validates: Requirement 18.1
        
        Examples:
            >>> logger = AgentLogger()
            >>> logger.log_agent_execution(
            ...     agent_name="pc_control",
            ...     command="volume up",
            ...     success=True,
            ...     execution_time=0.5
            ... )
        """
        log_data = {
            "event": "agent_execution",
            "timestamp": datetime.now().isoformat(),
            "agent_name": agent_name,
            "command": command,
            "success": success,
            "execution_time_seconds": round(execution_time, 3),
            "error": error,
            "metadata": metadata or {}
        }
        
        # Log human-readable message
        status = "✅ SUCCESS" if success else "❌ FAILED"
        msg = f"{status} | Agent: {agent_name} | Command: '{command}' | Time: {execution_time:.3f}s"
        
        if error:
            msg += f" | Error: {error}"
            self.logger.error(msg)
        else:
            self.logger.info(msg)
        
        # Log structured JSON
        self.logger.info(json.dumps(log_data))
    
    def log_graph_execution(
        self,
        user_input: str,
        total_steps: int,
        total_retries: int,
        agents_involved: List[str],
        success: bool,
        execution_time: float,
        final_result: Optional[Dict] = None,
        error: Optional[str] = None
    ) -> None:
        """
        Log complete graph workflow execution.
        
        Records high-level workflow information including agents involved,
        steps taken, retries, and overall outcome.
        
        Args:
            user_input: Original user command
            total_steps: Number of steps executed
            total_retries: Number of retry attempts
            agents_involved: List of agent names that participated
            success: Whether workflow succeeded
            execution_time: Total time taken in seconds
            final_result: Final workflow result (optional)
            error: Error message if failed (optional)
            
        Validates: Requirement 18.2
        
        Examples:
            >>> logger = AgentLogger()
            >>> logger.log_graph_execution(
            ...     user_input="volume up",
            ...     total_steps=3,
            ...     total_retries=0,
            ...     agents_involved=["pc_control"],
            ...     success=True,
            ...     execution_time=1.2
            ... )
        """
        log_data = {
            "event": "graph_execution",
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "total_steps": total_steps,
            "total_retries": total_retries,
            "agents_involved": agents_involved,
            "num_agents": len(agents_involved),
            "success": success,
            "execution_time_seconds": round(execution_time, 3),
            "error": error
        }
        
        # Log human-readable summary
        status = "✅ COMPLETED" if success else "❌ FAILED"
        msg = (
            f"{status} | Workflow: '{user_input}' | "
            f"Steps: {total_steps} | Retries: {total_retries} | "
            f"Agents: {', '.join(agents_involved)} | "
            f"Time: {execution_time:.3f}s"
        )
        
        if error:
            msg += f" | Error: {error}"
            self.logger.error(msg)
        else:
            self.logger.info(msg)
        
        # Log structured JSON
        self.logger.info(json.dumps(log_data))
    
    def log_state_transition(
        self,
        from_node: str,
        to_node: str,
        current_step: int,
        state_summary: Optional[Dict] = None
    ) -> None:
        """
        Log state graph node transition.
        
        Args:
            from_node: Source node name
            to_node: Destination node name
            current_step: Current step counter
            state_summary: Summary of state data (optional)
            
        Validates: Requirement 18.2
        """
        log_data = {
            "event": "state_transition",
            "timestamp": datetime.now().isoformat(),
            "from_node": from_node,
            "to_node": to_node,
            "current_step": current_step,
            "state_summary": state_summary or {}
        }
        
        self.logger.debug(f"Transition: {from_node} → {to_node} (step {current_step})")
        self.logger.debug(json.dumps(log_data))
    
    def log_retry_attempt(
        self,
        agent_name: str,
        retry_count: int,
        max_retries: int,
        backoff_seconds: float,
        reason: str
    ) -> None:
        """
        Log retry attempt with exponential backoff.
        
        Args:
            agent_name: Agent being retried
            retry_count: Current retry attempt number
            max_retries: Maximum retries allowed
            backoff_seconds: Backoff delay applied
            reason: Reason for retry (error message)
            
        Validates: Requirement 18.2
        """
        log_data = {
            "event": "retry_attempt",
            "timestamp": datetime.now().isoformat(),
            "agent_name": agent_name,
            "retry_count": retry_count,
            "max_retries": max_retries,
            "backoff_seconds": backoff_seconds,
            "reason": reason
        }
        
        self.logger.warning(
            f"🔄 RETRY {retry_count}/{max_retries} | Agent: {agent_name} | "
            f"Backoff: {backoff_seconds}s | Reason: {reason}"
        )
        self.logger.info(json.dumps(log_data))
    
    def log_security_event(
        self,
        event_type: str,
        agent_name: str,
        details: str,
        severity: str = "warning"
    ) -> None:
        """
        Log security-related events.
        
        Records unauthorized actions, injection attempts, and other
        security violations.
        
        Args:
            event_type: Type of security event (unauthorized_action, injection, etc.)
            agent_name: Agent involved
            details: Event details
            severity: Severity level (info, warning, error, critical)
            
        Validates: Requirement 18.3, Security NFR 5
        """
        log_data = {
            "event": "security_event",
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "agent_name": agent_name,
            "details": details,
            "severity": severity
        }
        
        msg = f"🔒 SECURITY | {event_type} | Agent: {agent_name} | {details}"
        
        if severity == "critical":
            self.logger.critical(msg)
        elif severity == "error":
            self.logger.error(msg)
        elif severity == "warning":
            self.logger.warning(msg)
        else:
            self.logger.info(msg)
        
        self.logger.info(json.dumps(log_data))
    
    def log_error_with_traceback(
        self,
        error: Exception,
        context: str,
        additional_info: Optional[Dict] = None
    ) -> None:
        """
        Log error with full traceback for debugging.
        
        Args:
            error: Exception object
            context: Context where error occurred
            additional_info: Additional debugging info (optional)
            
        Validates: Requirement 18.3
        """
        import traceback
        
        log_data = {
            "event": "error",
            "timestamp": datetime.now().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
            "traceback": traceback.format_exc(),
            "additional_info": additional_info or {}
        }
        
        self.logger.error(f"❌ ERROR in {context}: {type(error).__name__}: {error}")
        self.logger.error(json.dumps(log_data))
        self.logger.debug(traceback.format_exc())


# Global logger instance
_global_logger: Optional[AgentLogger] = None


def get_logger(component_name: str = "agent_system") -> AgentLogger:
    """
    Get logger instance for a component (singleton per component).
    
    Args:
        component_name: Component name
        
    Returns:
        AgentLogger instance
        
    Examples:
        >>> logger = get_logger("orchestrator")
        >>> logger.log_agent_execution(...)
    """
    global _global_logger
    
    if _global_logger is None or _global_logger.component_name != component_name:
        _global_logger = AgentLogger(component_name)
    
    return _global_logger
