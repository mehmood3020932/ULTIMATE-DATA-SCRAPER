# services/agent-service/app/agents/dom_analyzer.py
# DOM Analyzer Agent - Analyzes page structure

import json

from app.agents.base import AgentContext, AgentResult, BaseAgent
from app.llm.router import LLMRouter


class DOMAnalyzerAgent(BaseAgent):
    """
    DOM Analyzer Agent: Analyzes HTML structure to identify data patterns.
    Uses LLM to understand page layout and suggest extraction strategies.
    """
    
    def __init__(self, llm_router: LLMRouter):
        super().__init__("dom_analyzer", llm_router)
        self.llm = llm_router
    
    async def execute(self, context: AgentContext) -> AgentResult:
        """Analyze DOM structure."""
        self.logger.info("analyzing_dom", job_id=context.job_id)
        
        # In real implementation, this would receive HTML from worker service
        html_sample = context.data.get("html_sample", "")
        
        if not html_sample:
            # Request HTML from worker
            return AgentResult(
                success=True,
                data={"action": "request_html"},
                confidence=0.8,
                next_agent="worker_fetch",
            )
        
        prompt = f"""
        Analyze this HTML structure and identify data extraction opportunities.
        
        Instructions: {context.instructions}
        HTML Sample: {html_sample[:8000]}...
        
        Provide:
        1. Main content containers
        2. List/item patterns
        3. Data fields and their selectors
        4. Pagination elements
        5. Dynamic content indicators
        
        Response (JSON):
        {{
            "content_selector": "main .content",
            "item_selector": ".product-item",
            "fields": {{
                "title": ".title::text",
                "price": ".price::text",
                "image": "img::src"
            }},
            "pagination": {{
                "type": "button|link|infinite",
                "selector": ".next-page"
            }},
            "is_dynamic": true
        }}
        """
        
        try:
            response = await self.llm.generate(prompt=prompt, temperature=0.2)
            analysis = json.loads(response)
            
            context.data["dom_analysis"] = analysis
            
            return AgentResult(
                success=True,
                data=analysis,
                confidence=0.85,
                next_agent="pattern_detector",
            )
            
        except Exception as e:
            return await self.on_error(context, e)