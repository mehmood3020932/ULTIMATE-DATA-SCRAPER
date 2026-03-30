# services/agent-service/app/agents/browser.py
# Browser Agent - Manages browser initialization and configuration

from app.agents.base import AgentContext, AgentResult, BaseAgent


class BrowserAgent(BaseAgent):
    """
    Browser Agent: Configures and initializes browser sessions.
    Determines optimal browser settings based on target site characteristics.
    """
    
    def __init__(self):
        super().__init__("browser")
    
    async def execute(self, context: AgentContext) -> AgentResult:
        """Configure browser settings."""
        self.logger.info("configuring_browser", job_id=context.job_id)
        
        config = context.config
        
        browser_config = {
            "headless": True,
            "viewport": {"width": 1920, "height": 1080},
            "user_agent": config.get("user_agent", self._get_rotating_ua()),
            "javascript_enabled": config.get("javascript_enabled", True),
            "cookies": config.get("cookies", []),
            "proxy": config.get("proxy_country"),
            "stealth_mode": True,
            "anti_detection": {
                "webdriver": False,
                "plugins": True,
                "languages": ["en-US", "en"],
                "timezone": "America/New_York",
            },
            "timeouts": {
                "navigation": config.get("timeout_seconds", 30) * 1000,
                "wait_for": config.get("wait_for_selector"),
            }
        }
        
        context.data["browser_config"] = browser_config
        
        return AgentResult(
            success=True,
            data=browser_config,
            confidence=0.95,
            next_agent="navigator",
        )
    
    def _get_rotating_ua(self) -> str:
        """Get rotating user agent."""
        import random
        uas = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWeb0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.0",
        ]
        return random.choice(uas)