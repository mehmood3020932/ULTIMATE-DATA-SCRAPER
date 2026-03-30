# app/agents/pattern_detector.py
# Pattern Detector Agent - Identifies data patterns

import json

from app.agents.base import AgentContext, AgentResult, BaseAgent
from app.llm.router import LLMRouter


class PatternDetectorAgent(BaseAgent):
    """
    Pattern Detector Agent: Identifies repeating patterns in web content.
    Detects list structures, tables, cards, and other data containers.
    """
    
    def __init__(self, llm_router: LLMRouter):
        super().__init__("pattern_detector", llm_router)
        self.llm = llm_router
    
    async def execute(self, context: AgentContext) -> AgentResult:
        """Detect patterns in page content."""
        self.logger.info("detecting_patterns", job_id=context.job_id)
        
        html_sample = context.data.get("html_sample", "")
        dom_analysis = context.data.get("dom_analysis", {})
        
        prompt = f"""
        Analyze this HTML and identify data patterns.
        
        HTML Sample: {html_sample[:6000]}
        DOM Analysis: {json.dumps(dom_analysis)}
        
        Identify:
        1. List patterns (product lists, article lists, etc.)
        2. Table structures
        3. Card/grid layouts
        4. Pagination patterns
        5. Detail page links
        
        Response (JSON):
        {{
            "patterns": [
                {{
                    "type": "list|table|cards",
                    "selector": ".product-list",
                    "item_selector": ".product-item",
                    "count": 10,
                    "confidence": 0.95
                }}
            ],
            "pagination": {{
                "type": "numbered|load_more|infinite",
                "selector": ".pagination"
            }},
            "detail_links": {{
                "selector": "a[href*='product']",
                "pattern": "/product/(\\d+)"
            }}
        }}
        """
        
        try:
            response = await self.llm.generate(prompt=prompt, temperature=0.2)
            patterns = json.loads(response)
            
            context.data["patterns"] = patterns
            
            return AgentResult(
                success=True,
                data=patterns,
                confidence=0.85,
                next_agent="extractor",
            )
            
        except Exception as e:
            return await self.on_error(context, e)