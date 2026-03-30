# app/agents/pagination.py
# Pagination Agent - Handles multi-page scraping

from typing import List

from app.agents.base import AgentContext, AgentResult, BaseAgent


class PaginationAgent(BaseAgent):
    """
    Pagination Agent: Handles pagination strategies.
    Supports numbered pages, load more buttons, and infinite scroll.
    """
    
    def __init__(self):
        super().__init__("pagination")
    
    async def execute(self, context: AgentContext) -> AgentResult:
        """Handle pagination."""
        self.logger.info("handling_pagination", job_id=context.job_id)
        
        patterns = context.data.get("patterns", {})
        pagination = patterns.get("pagination", {})
        
        strategy = pagination.get("type", "none")
        
        pagination_config = {
            "strategy": strategy,
            "selector": pagination.get("selector"),
            "max_pages": context.config.get("max_pages", 100),
            "current_page": 1,
            "urls": [context.target_url],
        }
        
        if strategy == "numbered":
            pagination_config["page_param"] = "page"
            pagination_config["url_template"] = f"{context.target_url}?page={{page}}"
        elif strategy == "load_more":
            pagination_config["button_selector"] = pagination.get("selector", ".load-more")
        
        context.data["pagination"] = pagination_config
        
        # Check if we need to scrape more pages
        current_count = context.data.get("items_count", 0)
        max_items = context.config.get("max_items", 1000)
        
        if current_count < max_items and strategy != "none":
            return AgentResult(
                success=True,
                data=pagination_config,
                confidence=0.9,
                next_agent="navigator",  # Loop back to get next page
            )
        
        return AgentResult(
            success=True,
            data=pagination_config,
            confidence=0.9,
            next_agent="cleaner",
        )
    
    def generate_page_urls(self, base_url: str, total_pages: int) -> List[str]:
        """Generate URLs for all pages."""
        urls = []
        for page in range(1, total_pages + 1):
            if "?" in base_url:
                urls.append(f"{base_url}&page={page}")
            else:
                urls.append(f"{base_url}?page={page}")
        return urls