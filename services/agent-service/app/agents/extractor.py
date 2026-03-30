# services/agent-service/app/agents/extractor.py
# Extractor Agent - Extracts data from pages

import json

from app.agents.base import AgentContext, AgentResult, BaseAgent
from app.llm.router import LLMRouter


class ExtractorAgent(BaseAgent):
    """
    Extractor Agent: Extracts structured data from web pages.
    Uses LLM to understand unstructured data and extract according to schema.
    """
    
    def __init__(self, llm_router: LLMRouter):
        super().__init__("extractor", llm_router)
        self.llm = llm_router
    
    async def execute(self, context: AgentContext) -> AgentResult:
        """Extract data from page content."""
        self.logger.info("extracting_data", job_id=context.job_id)
        
        page_content = context.data.get("page_content", "")
        schema = context.data.get("output_schema", {})
        
        prompt = f"""
        Extract structured data from the following web content according to the schema.
        
        Schema: {json.dumps(schema, indent=2)}
        Content: {page_content[:10000]}...
        
        Extract all matching items. Return as JSON array.
        If a field is missing, use null.
        
        Response format:
        {{
            "items": [
                {{"field1": "value1", "field2": "value2"}},
                ...
            ],
            "total_items": 2,
            "confidence": 0.95
        }}
        """
        
        try:
            response = await self.llm.generate(prompt=prompt, temperature=0.1)
            extraction = json.loads(response)
            
            items = extraction.get("items", [])
            context.data["extracted_items"] = items
            context.data["items_count"] = len(items)
            
            return AgentResult(
                success=True,
                data=extraction,
                confidence=extraction.get("confidence", 0.8),
                next_agent="validator",
            )
            
        except Exception as e:
            return await self.on_error(context, e)