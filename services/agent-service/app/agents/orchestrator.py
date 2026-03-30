# services/agent-service/app/agents/orchestrator.py
# Agent Orchestrator - Manages multi-agent execution

import asyncio
from typing import Dict, List, Optional

import structlog

from app.agents.base import AgentContext
from app.agents.browser import BrowserAgent
from app.agents.cleaner import CleanerAgent
from app.agents.dom_analyzer import DOMAnalyzerAgent
from app.agents.extractor import ExtractorAgent
from app.agents.navigator import NavigatorAgent
from app.agents.output import OutputAgent
from app.agents.pagination import PaginationAgent
from app.agents.pattern_detector import PatternDetectorAgent
from app.agents.planner import PlannerAgent
from app.agents.validator import ValidatorAgent
from app.config import settings
from app.events.producer import KafkaEventProducer
from app.llm.router import LLMRouter

logger = structlog.get_logger()


class AgentOrchestrator:
    """
    Orchestrates the execution of multiple AI agents.
    Implements parallel execution, consensus building, and error recovery.
    """
    
    def __init__(self, event_producer: KafkaEventProducer):
        self.event_producer = event_producer
        self.llm_router = LLMRouter()
        self.agents = self._initialize_agents()
        self.logger = logger.bind(component="orchestrator")
    
    def _initialize_agents(self) -> Dict[str, any]:
        """Initialize all available agents."""
        return {
            "planner": PlannerAgent(self.llm_router),
            "browser": BrowserAgent(),
            "navigator": NavigatorAgent(),
            "dom_analyzer": DOMAnalyzerAgent(self.llm_router),
            "pattern_detector": PatternDetectorAgent(self.llm_router),
            "extractor": ExtractorAgent(self.llm_router),
            "pagination": PaginationAgent(),
            "validator": ValidatorAgent(self.llm_router),
            "cleaner": CleanerAgent(),
            "output": OutputAgent(),
        }
    
    async def execute_job(self, job_id: str, job_data: dict) -> dict:
        """
        Execute a scraping job using the multi-agent system.
        """
        self.logger.info("starting_job_execution", job_id=job_id)
        
        # Initialize context
        context = AgentContext(
            job_id=job_id,
            user_id=job_data.get("user_id"),
            target_url=job_data.get("target_url"),
            instructions=job_data.get("instructions", ""),
            config=job_data.get("config", {}),
            data={},
            memory={},
            errors=[],
            metadata={"start_time": asyncio.get_event_loop().time()},
        )
        
        try:
            # Phase 1: Planning
            plan_result = await self._execute_agent("planner", context)
            if not plan_result.success:
                raise Exception(f"Planning failed: {plan_result.error}")
            
            # Phase 2: Execution loop
            current_agent = plan_result.next_agent
            iteration = 0
            max_iterations = settings.MAX_AGENT_ITERATIONS
            
            while current_agent and iteration < max_iterations:
                self.logger.info(
                    "agent_execution",
                    job_id=job_id,
                    agent=current_agent,
                    iteration=iteration,
                )
                
                # Execute agent
                result = await self._execute_agent(current_agent, context)
                
                # Publish event
                await self.event_producer.send_event(
                    topic="scraping.events",
                    event={
                        "job_id": job_id,
                        "agent": current_agent,
                        "success": result.success,
                        "confidence": result.confidence,
                        "timestamp": asyncio.get_event_loop().time(),
                    },
                )
                
                if not result.success:
                    # Error recovery
                    recovery = await self._handle_agent_error(
                        current_agent, context, result
                    )
                    if not recovery:
                        break
                    current_agent = recovery
                else:
                    current_agent = result.next_agent
                
                iteration += 1
            
            # Phase 3: Finalize
            final_result = await self._finalize_job(context)
            return final_result
            
        except Exception as e:
            self.logger.error("job_execution_failed", job_id=job_id, error=str(e))
            await self._handle_job_failure(job_id, str(e))
            raise
    
    async def _execute_agent(self, agent_name: str, context: AgentContext):
        """Execute a single agent."""
        agent = self.agents.get(agent_name)
        if not agent:
            raise ValueError(f"Unknown agent: {agent_name}")
        
        return await agent.execute(context)
    
    async def _handle_agent_error(
        self,
        agent_name: str,
        context: AgentContext,
        result,
    ) -> Optional[str]:
        """Handle agent execution error."""
        self.logger.warning(
            "agent_error",
            job_id=context.job_id,
            agent=agent_name,
            error=result.error,
        )
        
        # Simple retry logic - could be more sophisticated
        retry_count = context.memory.get(f"{agent_name}.retries", 0)
        if retry_count < 3:
            context.memory[f"{agent_name}.retries"] = retry_count + 1
            return agent_name  # Retry same agent
        
        # Try fallback
        return "validator" if agent_name != "validator" else None
    
    async def _finalize_job(self, context: AgentContext) -> dict:
        """Finalize job and prepare results."""
        duration = asyncio.get_event_loop().time() - context.metadata["start_time"]
        
        return {
            "job_id": context.job_id,
            "status": "completed",
            "data": context.data.get("extracted_items", []),
            "pages_scraped": context.data.get("pages_scraped", 0),
            "items_extracted": context.data.get("items_count", 0),
            "confidence": context.data.get("validation_confidence", 0),
            "duration_seconds": duration,
            "agents_used": list(context.memory.keys()),
        }
    
    async def _handle_job_failure(self, job_id: str, error: str):
        """Handle complete job failure."""
        await self.event_producer.send_event(
            topic="scraping.events",
            event={
                "job_id": job_id,
                "event": "job_failed",
                "error": error,
                "timestamp": asyncio.get_event_loop().time(),
            },
        )
    
    async def execute_parallel(
        self,
        agent_names: List[str],
        context: AgentContext,
    ) -> List[dict]:
        """
        Execute multiple agents in parallel.
        Used for consensus building.
        """
        tasks = [
            self._execute_agent(name, context)
            for name in agent_names
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [
            r if not isinstance(r, Exception) else {"success": False, "error": str(r)}
            for r in results
        ]