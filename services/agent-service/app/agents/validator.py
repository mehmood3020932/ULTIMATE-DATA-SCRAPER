# services/agent-service/app/agents/validator.py
# Validator Agent - Validates extracted data quality

import json

from app.agents.base import AgentContext, AgentResult, BaseAgent
from app.llm.router import LLMRouter


class ValidatorAgent(BaseAgent):
    """
    Validator Agent: Validates extracted data for completeness and accuracy.
    Checks for missing fields, data quality issues, and schema compliance.
    """
    
    def __init__(self, llm_router: LLMRouter):
        super().__init__("validator", llm_router)
        self.llm = llm_router
    
    async def execute(self, context: AgentContext) -> AgentResult:
        """Validate extracted data."""
        self.logger.info("validating_data", job_id=context.job_id)
        
        items = context.data.get("extracted_items", [])
        schema = context.data.get("output_schema", {})
        
        validation_results = []
        total_confidence = 0
        
        for idx, item in enumerate(items):
            # Check schema compliance
            missing_fields = [
                field for field in schema.get("required", [])
                if field not in item or item[field] is None
            ]
            
            # LLM validation for data quality
            prompt = f"""
            Validate this data item for quality and completeness:
            {json.dumps(item, indent=2)}
            
            Check for:
            1. Missing or null required fields
            2. Data format issues
            3. Suspicious values
            4. Completeness score (0-1)
            
            Response (JSON):
            {{
                "is_valid": true,
                "issues": [],
                "confidence": 0.95,
                "suggestions": []
            }}
            """
            
            try:
                response = await self.llm.generate(prompt=prompt, temperature=0.1)
                validation = json.loads(response)
                validation["item_index"] = idx
                validation["missing_fields"] = missing_fields
                validation_results.append(validation)
                total_confidence += validation.get("confidence", 0.5)
                
            except Exception as e:
                validation_results.append({
                    "item_index": idx,
                    "is_valid": False,
                    "error": str(e),
                    "confidence": 0,
                })
        
        avg_confidence = total_confidence / len(items) if items else 0
        
        context.data["validation_results"] = validation_results
        context.data["validation_confidence"] = avg_confidence
        
        # Determine if re-extraction needed
        needs_retry = avg_confidence < 0.7
        
        return AgentResult(
            success=True,
            data={
                "valid_items": len([r for r in validation_results if r.get("is_valid")]),
                "invalid_items": len([r for r in validation_results if not r.get("is_valid")]),
                "average_confidence": avg_confidence,
            },
            confidence=avg_confidence,
            next_agent="cleaner" if not needs_retry else "extractor",
        )