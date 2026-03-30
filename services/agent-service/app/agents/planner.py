# services/agent-service/app/agents/planner.py
# Planner Agent - Strategizes scraping approach

import json
from typing import List

from app.agents.base import AgentContext, AgentResult, BaseAgent
from app.llm.router import LLMRouter


class PlannerAgent(BaseAgent):
    """
    Planner Agent: Analyzes the scraping task and creates a step-by-step plan.
    Determines which agents to use, in what order, and with what configuration.
    """
    
    def __init__(self, llm_router: LLMRouter):
        super().__init__("planner", llm_router)
        self.llm = llm_router
    
    async def execute(self, context: AgentContext) -> AgentResult:
        """Create scraping plan based on instructions."""
        self.logger.info("planning_job", job_id=context.job_id)
        
        prompt = f"""
        You are an expert web scraping strategist. Analyze the following task and create a detailed plan.
        
        Target URL: {context.target_url}
        Instructions: {context.instructions}
        
        Create a JSON plan with:
        1. "steps": List of agent execution steps with order and configuration
        2. "estimated_pages": Estimated number of pages to scrape
        3. "complexity": "simple", "medium", or "complex"
        4. "risks": Potential challenges and mitigation strategies
        5. "selectors": Suggested CSS selectors if apparent
        
        Available agents: browser, navigator, dom_analyzer, pattern_detector, 
        extractor, pagination, anti_block, validator, cleaner, output
        
        Response format (JSON only):
        {{
            "steps": [
                {{"agent": "browser", "config": {{}}, "reason": "..."}},
                {{"agent": "navigator", "config": {{}}, "reason": "..."}}
            ],
            "estimated_pages": 10,
            "complexity": "medium",
            "risks": ["pagination", "dynamic_content"],
            "selectors": {{"title": "h1", "items": ".item"}}
        }}
        """
        
        try:
            response = await self.llm.generate(
                prompt=prompt,
                temperature=0.2,
                max_tokens=2000,
            )
            
            plan = json.loads(response)
            
            # Store plan in context
            context.data["plan"] = plan
            context.data["estimated_pages"] = plan.get("estimated_pages", 10)
            context.data["complexity"] = plan.get("complexity", "medium")
            
            # Determine next agent from plan
            next_agent = plan["steps"][0]["agent"] if plan["steps"] else "browser"
            
            return AgentResult(
                success=True,
                data=plan,
                confidence=0.9,
                next_agent=next_agent,
                tokens_used=response.get("tokens_used", 0),
            )
            
        except Exception as e:
            return await self.on_error(context, e)