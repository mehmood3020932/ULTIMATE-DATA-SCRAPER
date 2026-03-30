# app/agents/cleaner.py
# Cleaner Agent - Cleans and normalizes data

import re
from typing import Any, Dict, List

from app.agents.base import AgentContext, AgentResult, BaseAgent


class CleanerAgent(BaseAgent):
    """
    Cleaner Agent: Cleans and normalizes extracted data.
    Removes duplicates, fixes formatting, standardizes values.
    """
    
    def __init__(self):
        super().__init__("cleaner")
    
    async def execute(self, context: AgentContext) -> AgentResult:
        """Clean extracted data."""
        self.logger.info("cleaning_data", job_id=context.job_id)
        
        items = context.data.get("extracted_items", [])
        
        cleaned_items = []
        seen = set()
        
        for item in items:
            # Clean each field
            cleaned = self._clean_item(item)
            
            # Deduplication
            item_hash = hash(frozenset(cleaned.items()))
            if item_hash not in seen:
                seen.add(item_hash)
                cleaned_items.append(cleaned)
        
        context.data["cleaned_items"] = cleaned_items
        context.data["duplicates_removed"] = len(items) - len(cleaned_items)
        
        return AgentResult(
            success=True,
            data={"cleaned_count": len(cleaned_items)},
            confidence=0.95,
            next_agent="output",
        )
    
    def _clean_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Clean individual item."""
        cleaned = {}
        
        for key, value in item.items():
            if isinstance(value, str):
                # Remove extra whitespace
                value = " ".join(value.split())
                # Remove HTML tags
                value = re.sub(r'<[^>]+>', '', value)
                # Strip whitespace
                value = value.strip()
            
            cleaned[key] = value
        
        return cleaned
    
    def normalize_price(self, price_str: str) -> float:
        """Normalize price string to float."""
        # Remove currency symbols and whitespace
        cleaned = re.sub(r'[^\d.,]', '', price_str)
        # Handle European format (1.234,56)
        if ',' in cleaned and '.' in cleaned:
            if cleaned.rfind(',') > cleaned.rfind('.'):
                cleaned = cleaned.replace('.', '').replace(',', '.')
            else:
                cleaned = cleaned.replace(',', '')
        elif ',' in cleaned:
            cleaned = cleaned.replace(',', '.')
        
        try:
            return float(cleaned)
        except ValueError:
            return 0.0