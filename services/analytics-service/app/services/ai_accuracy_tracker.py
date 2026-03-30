# app/services/ai_accuracy_tracker.py
# Track AI agent accuracy metrics

from datetime import datetime, timezone
from typing import Dict, List

import structlog

logger = structlog.get_logger()


class AIAccuracyTracker:
    """Tracks accuracy metrics for AI agents and LLM providers."""
    
    def __init__(self):
        self.metrics = {
            "agents": {},
            "providers": {},
        }
    
    async def record_agent_result(
        self,
        agent_name: str,
        success: bool,
        confidence: float,
        latency_ms: int,
    ):
        """Record agent execution result."""
        if agent_name not in self.metrics["agents"]:
            self.metrics["agents"][agent_name] = {
                "total": 0,
                "successes": 0,
                "total_confidence": 0,
                "total_latency": 0,
            }
        
        m = self.metrics["agents"][agent_name]
        m["total"] += 1
        if success:
            m["successes"] += 1
        m["total_confidence"] += confidence
        m["total_latency"] += latency_ms
        
        logger.debug(
            "agent_metric_recorded",
            agent=agent_name,
            success=success,
            confidence=confidence,
        )
    
    async def record_llm_usage(
        self,
        provider: str,
        model: str,
        tokens_used: int,
        cost_usd: float,
        success: bool,
        latency_ms: int,
    ):
        """Record LLM API usage."""
        key = f"{provider}/{model}"
        if key not in self.metrics["providers"]:
            self.metrics["providers"][key] = {
                "calls": 0,
                "total_tokens": 0,
                "total_cost": 0,
                "successes": 0,
                "total_latency": 0,
            }
        
        m = self.metrics["providers"][key]
        m["calls"] += 1
        m["total_tokens"] += tokens_used
        m["total_cost"] += cost_usd
        if success:
            m["successes"] += 1
        m["total_latency"] += latency_ms
    
    def get_agent_accuracy(self, agent_name: str) -> Dict:
        """Get accuracy stats for agent."""
        m = self.metrics["agents"].get(agent_name, {})
        if not m or m["total"] == 0:
            return {"success_rate": 0, "avg_confidence": 0, "avg_latency_ms": 0}
        
        return {
            "success_rate": m["successes"] / m["total"],
            "avg_confidence": m["total_confidence"] / m["total"],
            "avg_latency_ms": m["total_latency"] / m["total"],
            "total_calls": m["total"],
        }
    
    def get_provider_stats(self, provider: str) -> Dict:
        """Get stats for LLM provider."""
        m = self.metrics["providers"].get(provider, {})
        if not m or m["calls"] == 0:
            return {}
        
        return {
            "success_rate": m["successes"] / m["calls"],
            "avg_cost_per_call": m["total_cost"] / m["calls"],
            "avg_tokens_per_call": m["total_tokens"] / m["calls"],
            "avg_latency_ms": m["total_latency"] / m["calls"],
            "total_calls": m["calls"],
        }