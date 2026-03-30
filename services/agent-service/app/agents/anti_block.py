# app/agents/anti_block.py
# Anti-Block Agent - Avoids detection and blocking

import random
import time

from app.agents.base import AgentContext, AgentResult, BaseAgent


class AntiBlockAgent(BaseAgent):
    """
    Anti-Block Agent: Implements strategies to avoid detection.
    Manages request delays, user agents, proxies, and behavior mimicry.
    """
    
    def __init__(self):
        super().__init__("anti_block")
        self.request_count = 0
    
    async def execute(self, context: AgentContext) -> AgentResult:
        """Apply anti-blocking measures."""
        self.logger.info("applying_anti_block", job_id=context.job_id)
        
        config = context.config
        
        anti_block_config = {
            "delay_ms": config.get("delay_ms", 1000),
            "user_agent_rotation": True,
            "proxy_rotation": config.get("proxy_country") is not None,
            "randomize_viewport": True,
            "mouse_movements": True,
            "scroll_behavior": "natural",
        }
        
        # Calculate adaptive delay
        base_delay = anti_block_config["delay_ms"]
        jitter = random.randint(-200, 200)
        actual_delay = max(100, base_delay + jitter)
        
        # Simulate human behavior
        if self.request_count > 0:
            time.sleep(actual_delay / 1000)  # Convert to seconds
        
        self.request_count += 1
        
        # Rotate user agent periodically
        if self.request_count % 10 == 0:
            anti_block_config["new_user_agent"] = self._get_random_ua()
        
        context.data["anti_block"] = anti_block_config
        
        return AgentResult(
            success=True,
            data=anti_block_config,
            confidence=0.9,
            next_agent="navigator",
        )
    
    def _get_random_ua(self) -> str:
        """Get random user agent."""
        uas = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        ]
        return random.choice(uas)
    
    async def detect_blocking(self, response: dict) -> bool:
        """Detect if we've been blocked."""
        indicators = [
            "captcha",
            "access denied",
            "blocked",
            "403",
            "429",
        ]
        content = response.get("content", "").lower()
        return any(indicator in content for indicator in indicators)