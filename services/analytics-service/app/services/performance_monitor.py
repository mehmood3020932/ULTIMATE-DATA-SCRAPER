# app/services/performance_monitor.py
# System performance monitoring

import time
from collections import deque
from typing import Deque, Dict

import structlog

logger = structlog.get_logger()


class PerformanceMonitor:
    """Monitors system performance metrics."""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.metrics: Dict[str, Deque] = {
            "response_time": deque(maxlen=max_history),
            "queue_depth": deque(maxlen=max_history),
            "active_jobs": deque(maxlen=max_history),
            "error_rate": deque(maxlen=max_history),
        }
        self.start_time = time.time()
    
    def record_response_time(self, duration_ms: float):
        """Record API response time."""
        self.metrics["response_time"].append({
            "timestamp": time.time(),
            "value": duration_ms,
        })
    
    def record_queue_depth(self, depth: int):
        """Record job queue depth."""
        self.metrics["queue_depth"].append({
            "timestamp": time.time(),
            "value": depth,
        })
    
    def record_active_jobs(self, count: int):
        """Record number of active jobs."""
        self.metrics["active_jobs"].append({
            "timestamp": time.time(),
            "value": count,
        })
    
    def record_error(self):
        """Record an error occurrence."""
        self.metrics["error_rate"].append({
            "timestamp": time.time(),
            "value": 1,
        })
    
    def get_stats(self) -> Dict:
        """Get current performance stats."""
        stats = {}
        
        for metric_name, values in self.metrics.items():
            if not values:
                stats[metric_name] = {
                    "current": 0,
                    "avg": 0,
                    "min": 0,
                    "max": 0,
                }
                continue
            
            recent = list(values)[-100:]  # Last 100 samples
            vals = [v["value"] for v in recent]
            
            stats[metric_name] = {
                "current": vals[-1],
                "avg": sum(vals) / len(vals),
                "min": min(vals),
                "max": max(vals),
            }
        
        stats["uptime_seconds"] = time.time() - self.start_time
        return stats
    
    def get_health_status(self) -> str:
        """Determine system health status."""
        stats = self.get_stats()
        
        # Simple health check logic
        if stats["error_rate"]["avg"] > 0.1:  # >10% error rate
            return "unhealthy"
        elif stats["response_time"]["avg"] > 5000:  # >5s avg response
            return "degraded"
        elif stats["queue_depth"]["current"] > 1000:
            return "overloaded"
        
        return "healthy"