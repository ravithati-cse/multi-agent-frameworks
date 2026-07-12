"""
BaseAgent — foundation every AI agent in this system inherits from.

Concepts:
  - Tools: async callables decorated with @tool; registered in AgentToolRegistry
  - Events: agents can subscribe to domain events via bus.subscribe(...)
  - run(): override to implement agent logic (single shot or loop)
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from app.core.events import DomainEvent, EventBus, bus as default_bus

logger = logging.getLogger(__name__)


class AgentTool:
    """Wraps a callable as an agent-callable tool with metadata."""

    def __init__(self, fn, name: str, description: str, parameters: dict):
        self.fn = fn
        self.name = name
        self.description = description
        self.parameters = parameters  # JSON Schema

    async def __call__(self, **kwargs) -> Any:
        return await self.fn(**kwargs)

    def to_dict(self) -> dict:
        """Returns tool spec compatible with OpenAI / Anthropic tool_use format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters,
        }


def tool(name: str, description: str, parameters: dict):
    """Decorator to register a method as an agent tool."""
    def decorator(fn):
        fn._is_agent_tool = True
        fn._tool_name = name
        fn._tool_description = description
        fn._tool_parameters = parameters
        return fn
    return decorator


class BaseAgent(ABC):
    """
    All cloud-kitchen agents inherit from this.

    Usage:
        class MyAgent(BaseAgent):
            @tool("get_pending_orders", "List pending orders for a kitchen", {...})
            async def get_pending_orders(self, kitchen_id: str) -> list:
                ...

            async def run(self, input: dict) -> dict:
                ...
    """

    name: str = "base_agent"
    description: str = ""

    def __init__(self, bus: EventBus = default_bus):
        self.bus = bus
        self._tools: dict[str, AgentTool] = {}
        self._register_tools()

    def _register_tools(self) -> None:
        for attr_name in dir(self):
            method = getattr(self, attr_name, None)
            if callable(method) and getattr(method, "_is_agent_tool", False):
                t = AgentTool(
                    fn=method,
                    name=method._tool_name,
                    description=method._tool_description,
                    parameters=method._tool_parameters,
                )
                self._tools[t.name] = t
                logger.debug("agent %s registered tool: %s", self.name, t.name)

    def get_tools(self) -> list[dict]:
        """Return tool specs for LLM tool_use."""
        return [t.to_dict() for t in self._tools.values()]

    async def call_tool(self, tool_name: str, args: dict) -> Any:
        t = self._tools.get(tool_name)
        if not t:
            raise ValueError(f"Unknown tool: {tool_name}")
        return await t(**args)

    def subscribe(self, event_type: str):
        """Decorator: subscribe a method to a domain event."""
        def decorator(fn):
            self.bus.subscribe(event_type, fn)
            return fn
        return decorator

    @abstractmethod
    async def run(self, input: dict) -> dict:
        """Entry point for agent execution. Input/output are free-form dicts."""
        ...
