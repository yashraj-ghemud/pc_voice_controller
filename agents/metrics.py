"""
Performance metrics collection for the agent system.

This module tracks execution times, agent usage frequency, retry rates, and
other performance metrics. Provides aggregation and export capabilities for
monitoring dashboards.

Validates: Requirements 18.4, 18.5, 29.1, 29.2, 29.3, 29.4, 29.5
"""

import time
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class ExecutionMetric:
    """Single execution metric record."""
    timestamp: str
    command_type: str
    agent_name: str
    execution_time: float
    success: bool
    retry_count: int = 0


class MetricsCollector:
    """
    Collects and aggregates performance metrics for the agent system.
    
    Tracks:
    - Execution times by command type
    - Agent usage frequency
    - Retry rates per agent
    - Success/failure rates
    - Performance trends over time
    
    Metrics are stored in memory with a rolling window (default 1000 records)
    and can be exported to JSON for external monitoring tools.
    
    Validates: Requirements 18.4, 18.5, 29.1, 29.2, 29.3, 29.4, 29.5
    
    Examples:
        >>> collector = MetricsCollector()
        >>> collector.record_execution(
        ...     command_type="simple",
        ...     agent_name="pc_control",
        ...     execution_time=0.5,
        ...     success=True
        ... )
        >>> stats = collector.get_stats()
        >>> stats["total_executions"]
        1
    """
    
    def __init__(self, max_records: int = 1000):
        """
        Initialize metrics collector.
        
        Args:
            max_records: Maximum records to keep in memory (rolling window)
        """
        self.max_records = max_records
        
        # Rolling window of execution metrics
        self.executions: deque[ExecutionMetric] = deque(maxlen=max_records)
        
        # Aggregated counters
        self.total_executions = 0
        self.total_successes = 0
        self.total_failures = 0
        
        # Per-command-type metrics
        self.execution_times_by_type: Dict[str, List[float]] = defaultdict(list)
        self.success_count_by_type: Dict[str, int] = defaultdict(int)
        self.failure_count_by_type: Dict[str, int] = defaultdict(int)
        
        # Per-agent metrics
        self.agent_usage_count: Dict[str, int] = defaultdict(int)
        self.agent_success_count: Dict[str, int] = defaultdict(int)
        self.agent_failure_count: Dict[str, int] = defaultdict(int)
        self.agent_retry_count: Dict[str, int] = defaultdict(int)
        self.agent_total_retries: Dict[str, int] = defaultdict(int)
        
        # Initialization time
        self.start_time = time.time()
    
    def record_execution(
        self,
        command_type: str,
        agent_name: str,
        execution_time: float,
        success: bool,
        retry_count: int = 0
    ) -> None:
        """
        Record a single execution metric.
        
        Args:
            command_type: Type of command (simple, complex, multi_step)
            agent_name: Name of agent that executed
            execution_time: Time taken in seconds
            success: Whether execution succeeded
            retry_count: Number of retry attempts
            
        Validates: Requirements 29.1, 29.2, 29.3
        
        Examples:
            >>> collector = MetricsCollector()
            >>> collector.record_execution(
            ...     command_type="simple",
            ...     agent_name="pc_control",
            ...     execution_time=0.5,
            ...     success=True
            ... )
        """
        # Create metric record
        metric = ExecutionMetric(
            timestamp=datetime.now().isoformat(),
            command_type=command_type,
            agent_name=agent_name,
            execution_time=execution_time,
            success=success,
            retry_count=retry_count
        )
        
        # Add to rolling window
        self.executions.append(metric)
        
        # Update counters
        self.total_executions += 1
        if success:
            self.total_successes += 1
        else:
            self.total_failures += 1
        
        # Update per-command-type metrics (Requirement 29.1)
        self.execution_times_by_type[command_type].append(execution_time)
        if success:
            self.success_count_by_type[command_type] += 1
        else:
            self.failure_count_by_type[command_type] += 1
        
        # Update per-agent metrics (Requirement 29.2, 29.3)
        self.agent_usage_count[agent_name] += 1
        if success:
            self.agent_success_count[agent_name] += 1
        else:
            self.agent_failure_count[agent_name] += 1
        
        if retry_count > 0:
            self.agent_retry_count[agent_name] += 1
            self.agent_total_retries[agent_name] += retry_count
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get aggregated statistics for all metrics.
        
        Returns comprehensive metrics including:
        - Total executions, successes, failures
        - Average execution time per command type
        - Agent usage frequency
        - Retry rates per agent
        - Success rates
        
        Returns:
            Dictionary with aggregated statistics
            
        Validates: Requirement 29.4
        
        Examples:
            >>> collector = MetricsCollector()
            >>> collector.record_execution("simple", "pc_control", 0.5, True)
            >>> stats = collector.get_stats()
            >>> stats["total_executions"]
            1
            >>> stats["overall_success_rate"]
            1.0
        """
        uptime = time.time() - self.start_time
        
        # Calculate success rate
        success_rate = (
            self.total_successes / self.total_executions
            if self.total_executions > 0
            else 0.0
        )
        
        # Calculate average execution times by command type
        avg_times_by_type = {}
        for cmd_type, times in self.execution_times_by_type.items():
            if times:
                avg_times_by_type[cmd_type] = {
                    "average": sum(times) / len(times),
                    "min": min(times),
                    "max": max(times),
                    "count": len(times)
                }
        
        # Calculate agent metrics
        agent_metrics = {}
        for agent_name in self.agent_usage_count:
            total_uses = self.agent_usage_count[agent_name]
            successes = self.agent_success_count.get(agent_name, 0)
            failures = self.agent_failure_count.get(agent_name, 0)
            retries = self.agent_retry_count.get(agent_name, 0)
            total_retry_attempts = self.agent_total_retries.get(agent_name, 0)
            
            agent_metrics[agent_name] = {
                "total_uses": total_uses,
                "success_count": successes,
                "failure_count": failures,
                "success_rate": successes / total_uses if total_uses > 0 else 0.0,
                "retry_count": retries,
                "total_retry_attempts": total_retry_attempts,
                "retry_rate": retries / total_uses if total_uses > 0 else 0.0,
                "avg_retries_when_retried": (
                    total_retry_attempts / retries if retries > 0 else 0.0
                )
            }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": round(uptime, 2),
            
            # Overall metrics
            "total_executions": self.total_executions,
            "total_successes": self.total_successes,
            "total_failures": self.total_failures,
            "overall_success_rate": round(success_rate, 3),
            
            # Command type metrics (Requirement 29.1)
            "execution_times_by_command_type": avg_times_by_type,
            "success_count_by_type": dict(self.success_count_by_type),
            "failure_count_by_type": dict(self.failure_count_by_type),
            
            # Agent metrics (Requirements 29.2, 29.3)
            "agent_metrics": agent_metrics,
            
            # Agent usage ranking
            "most_used_agents": sorted(
                self.agent_usage_count.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5],
            
            # Highest retry rates
            "highest_retry_rates": sorted(
                [
                    (agent, metrics["retry_rate"])
                    for agent, metrics in agent_metrics.items()
                ],
                key=lambda x: x[1],
                reverse=True
            )[:5]
        }
    
    def get_recent_executions(self, limit: int = 10) -> List[Dict]:
        """
        Get most recent execution records.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of recent execution metric dicts
        """
        recent = list(self.executions)[-limit:]
        return [asdict(metric) for metric in recent]
    
    def export_to_json(self, filepath: str) -> None:
        """
        Export metrics to JSON file for external monitoring.
        
        Args:
            filepath: Path to output JSON file
            
        Validates: Requirement 29.5
        
        Examples:
            >>> collector = MetricsCollector()
            >>> collector.export_to_json("metrics.json")
        """
        stats = self.get_stats()
        stats["recent_executions"] = self.get_recent_executions(50)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
    
    def reset(self) -> None:
        """
        Reset all metrics (useful for testing).
        """
        self.executions.clear()
        self.total_executions = 0
        self.total_successes = 0
        self.total_failures = 0
        self.execution_times_by_type.clear()
        self.success_count_by_type.clear()
        self.failure_count_by_type.clear()
        self.agent_usage_count.clear()
        self.agent_success_count.clear()
        self.agent_failure_count.clear()
        self.agent_retry_count.clear()
        self.agent_total_retries.clear()
        self.start_time = time.time()
    
    def __repr__(self) -> str:
        """String representation of metrics collector."""
        return (
            f"MetricsCollector("
            f"executions={self.total_executions}, "
            f"success_rate={self.total_successes/self.total_executions if self.total_executions > 0 else 0:.2%})"
        )


# Global metrics collector instance
_global_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """
    Get global metrics collector instance (singleton).
    
    Returns:
        MetricsCollector instance
        
    Examples:
        >>> collector = get_metrics_collector()
        >>> collector.record_execution(...)
    """
    global _global_collector
    
    if _global_collector is None:
        _global_collector = MetricsCollector()
    
    return _global_collector


def reset_metrics() -> None:
    """
    Reset global metrics collector (useful for testing).
    """
    global _global_collector
    _global_collector = None
