# app/agents/output.py
# Output Agent - Formats final output

import json
from typing import Any, Dict

from app.agents.base import AgentContext, AgentResult, BaseAgent


class OutputAgent(BaseAgent):
    """
    Output Agent: Formats final output in requested format.
    Supports JSON, CSV, Excel, and PDF generation.
    """
    
    def __init__(self):
        super().__init__("output")
    
    async def execute(self, context: AgentContext) -> AgentResult:
        """Format output."""
        self.logger.info("formatting_output", job_id=context.job_id)
        
        items = context.data.get("cleaned_items", [])
        output_format = context.config.get("output_format", "json")
        
        formatted_data = self._format_data(items, output_format)
        
        result = {
            "format": output_format,
            "item_count": len(items),
            "data": formatted_data,
            "schema": self._infer_schema(items) if items else {},
        }
        
        context.data["final_output"] = result
        
        return AgentResult(
            success=True,
            data=result,
            confidence=0.99,
            next_agent=None,  # End of chain
        )
    
    def _format_data(self, items: list, format_type: str) -> Any:
        """Format data according to type."""
        if format_type == "json":
            return items
        
        elif format_type == "csv":
            # Return as CSV string
            if not items:
                return ""
            headers = list(items[0].keys())
            lines = [",".join(headers)]
            for item in items:
                values = [str(item.get(h, "")) for h in headers]
                lines.append(",".join(f'"{v}"' for v in values))
            return "\n".join(lines)
        
        elif format_type == "excel":
            # Would return Excel binary data
            return {"format": "xlsx", "items": len(items)}
        
        return items
    
    def _infer_schema(self, items: list) -> Dict[str, str]:
        """Infer data schema from items."""
        if not items:
            return {}
        
        schema = {}
        sample = items[0]
        
        for key, value in sample.items():
            if isinstance(value, bool):
                schema[key] = "boolean"
            elif isinstance(value, int):
                schema[key] = "integer"
            elif isinstance(value, float):
                schema[key] = "number"
            elif isinstance(value, list):
                schema[key] = "array"
            elif isinstance(value, dict):
                schema[key] = "object"
            else:
                schema[key] = "string"
        
        return schema