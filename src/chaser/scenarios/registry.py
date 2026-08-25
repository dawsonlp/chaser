"""Scenario registry for discovering and instantiating scenarios."""

from __future__ import annotations

from typing import Any, Callable, Dict

from chaser.scenarios.base import Scenario


class ScenarioRegistry:
    """Registry for scenario factories."""

    _factories: Dict[str, Callable[[], Scenario]] = {}

    @classmethod
    def register(cls, name: str, factory: Callable[[], Scenario]) -> None:
        cls._factories[name.lower()] = factory

    @classmethod
    def get(cls, name: str) -> Scenario:
        key = name.lower()
        if key not in cls._factories:
            available = sorted(cls._factories.keys())
            raise KeyError(f"scenario {name!r} not found. Available scenarios: {available}")
        return cls._factories[key]()

    @classmethod
    def list_scenarios(cls) -> list[str]:
        return sorted(cls._factories.keys())

