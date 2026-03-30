# app/orchestrator/agent_manager.py
# Agent Manager - Manages agent lifecycle

from typing import Dict, List, Optional, Type

from app.agents.base import BaseAgent


class AgentManager:
    """
    Manages agent registration, configuration, and lifecycle.
    """
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.agent_configs: Dict[str, dict] = {}
    
    def register_agent(self, name: str, agent: BaseAgent, config: dict = None):
        """Register an agent."""
        self.agents[name] = agent
        self.agent_configs[name] = config or {}
    
    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """Get agent by name."""
        return self.agents.get(name)
    
    def list_agents(self) -> List[str]:
        """List all registered agents."""
        return list(self.agents.keys())
    
    def get_agent_config(self, name: str) -> dict:
        """Get agent configuration."""
        return self.agent_configs.get(name, {})
    
    def update_agent_config(self, name: str, config: dict):
        """Update agent configuration."""
        if name in self.agent_configs:
            self.agent_configs[name].update(config)