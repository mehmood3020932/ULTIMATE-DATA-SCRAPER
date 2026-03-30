# app/orchestrator/parallel_executor.py
# Parallel Executor - Executes agents in parallel

import asyncio
from typing import Any, Dict, List

from app.agents.base import AgentContext, BaseAgent


class ParallelExecutor:
    """
    Executes multiple agents in parallel for consensus building.
    """
    
    def __init__(self, max_concurrent: int = 5):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def execute_parallel(
        self,
        agents: List[BaseAgent],
        context: AgentContext,
    ) -> List[Dict[str, Any]]:
        """
        Execute multiple agents in parallel.
        
        Args:
            agents: List of agents to execute
            context: Shared context
        
        Returns:
            List of results
        """
        tasks = [
            self._execute_with_semaphore(agent, context)
            for agent in agents
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        successful = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                successful.append({
                    "agent": agents[i].name,
                    "success": False,
                    "error": str(result),
                })
            else:
                successful.append({
                    "agent": agents[i].name,
                    "success": True,
                    "result": result,
                })
        
        return successful
    
    async def _execute_with_semaphore(
        self,
        agent: BaseAgent,
        context: AgentContext,
    ):
        """Execute agent with concurrency limit."""
        async with self.semaphore:
            return await agent.execute(context)