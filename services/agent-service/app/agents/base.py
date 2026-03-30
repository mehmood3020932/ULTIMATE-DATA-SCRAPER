# services/agent-service/app/agents/base.py
# Base Agent Class

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger()


@dataclass
class AgentContext:
    """Context passed between agents."""
    job_id: str
    user_id: str
    target_url: str
    instructions: str
    config: Dict[str, Any] = field(default_factory=dict)
    data: Dict[str, Any] = field(default_factory=dict)
    memory: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult:
    """Result from agent execution."""
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    next_agent: Optional[str] = None
    error: Optional[str] = None
    tokens_used: int = 0
    latency_ms: int = 0


class BaseAgent(ABC):
    """Base class for all AI agents."""
    
    def __init__(self, name: str, llm_provider=None):
        self.name = name
        self.llm_provider = llm_provider
        self.logger = logger.bind(agent=name)
    
    @abstractmethod
    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute agent logic."""
        pass
    
    async def on_error(self, context: AgentContext, error: Exception) -> AgentResult:
        """Handle agent error."""
        self.logger.error("agent_error", error=str(error), job_id=context.job_id)
        return AgentResult(
            success=False,
            error=str(error),
            confidence=0.0,
        )
    
    def update_memory(self, context: AgentContext, key: str, value: Any):
        """Update agent memory."""
        context.memory[f"{self.name}.{key}"] = value
    
    def get_memory(self, context: AgentContext, key: str) -> Any:
        """Get from agent memory."""
        return context.memory.get(f"{self.name}.{key}")