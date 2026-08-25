"""Actuator definitions and values."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping


@dataclass(frozen=True, slots=True)
class ActuatorDefinition:
    name: str
    minimum: float
    maximum: float

    def validate(self, value: float) -> None:
        if not math.isfinite(value):
            raise ValueError(f"{self.name} must be finite")
        if value < self.minimum or value > self.maximum:
            raise ValueError(
                f"{self.name}={value} is outside [{self.minimum}, {self.maximum}]"
            )


@dataclass(frozen=True, slots=True)
class ActuatorSet:
    """The current values of the actuators belonging to one object."""

    definitions: Mapping[str, ActuatorDefinition]
    values: Mapping[str, float]

    def __post_init__(self) -> None:
        if set(self.definitions) != set(self.values):
            raise ValueError("every actuator must have exactly one current value")
        for name, value in self.values.items():
            self.definitions[name].validate(value)

    def with_changes(self, changes: Mapping[str, float]) -> ActuatorSet:
        unknown = set(changes) - set(self.definitions)
        if unknown:
            raise ValueError(f"unknown actuators: {sorted(unknown)!r}")

        updated = dict(self.values)
        for name, value in changes.items():
            self.definitions[name].validate(value)
            updated[name] = value
        return ActuatorSet(self.definitions, updated)
