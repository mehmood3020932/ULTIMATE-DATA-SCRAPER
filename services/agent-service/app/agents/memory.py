# app/agents/memory.py
# Memory Agent - Manages context and learned patterns

from typing import Any, Dict, List, Optional

from app.agents.base import AgentContext, AgentResult, BaseAgent


class MemoryAgent(BaseAgent):
    """
    Memory Agent: Manages long-term memory and learned patterns.
    Stores successful strategies for future reuse.
    """
    
    def __init__(self):
        super().__init__("memory")
        self.short_term: Dict[str, Any] = {}
        self.long_term: Dict[str, Any] = {}
    
    async def execute(self, context: AgentContext) -> AgentResult:
        """Manage memory for current job."""
        self.logger.info("managing_memory", job_id=context.job_id)
        
        # Store job context
        memory_key = f"job:{context.job_id}"
        
        self.short_term[memory_key] = {
            "url": context.target_url,
            "instructions": context.instructions,
            "patterns_found": context.data.get("patterns", {}),
            "successful_selectors": context.data.get("dom_analysis", {}).get("selectors", {}),
        }
        
        # Check for similar past jobs
        similar_jobs = self._find_similar_jobs(context)
        
        if similar_jobs:
            context.data["similar_jobs"] = similar_jobs
            context.data["suggested_selectors"] = similar_jobs[0].get("successful_selectors", {})
        
        return AgentResult(
            success=True,
            data={"memory_stored": True, "similar_jobs_found": len(similar_jobs)},
            confidence=0.9,
            next_agent="planner",
        )
    
    def _find_similar_jobs(self, context: AgentContext) -> List[Dict]:
        """Find similar past jobs."""
        # In production, this would query vector database
        current_domain = context.target_url.split("/")[2]
        
        similar = []
        for key, mem in self.long_term.items():
            if mem.get("domain") == current_domain:
                similar.append(mem)
        
        return similar[:3]  # Return top 3
    
    async def persist_memory(self, job_id: str):
        """Persist short-term to long-term memory."""
        memory_key = f"job:{job_id}"
        if memory_key in self.short_term:
            self.long_term[memory_key] = self.short_term[memory_key]
            del self.short_term[memory_key]