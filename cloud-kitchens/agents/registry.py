"""Central registry — maps agent names to classes. Used by the /agents API."""
from __future__ import annotations
from typing import Type
from agents.base import BaseAgent

_registry: dict[str, Type[BaseAgent]] = {}


def register(cls: Type[BaseAgent]) -> Type[BaseAgent]:
    _registry[cls.name] = cls
    return cls


def get(name: str) -> Type[BaseAgent] | None:
    return _registry.get(name)


def list_agents() -> list[dict]:
    return [{"name": cls.name, "description": cls.description} for cls in _registry.values()]
