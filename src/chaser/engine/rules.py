"""Simulation interaction rules, termination conditions, and scoring policies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping, Protocol

from chaser.core import EventRecord
from chaser.kinematics.path import Path2D


@dataclass(frozen=True, slots=True)
class InteractionRule:
    """Defines a contact check between two entities and resulting event kind / outcome."""

    entity_a: str
    entity_b: str
    event_kind: str
    outcome: str | None = None
    priority: int = 20


class ScoringPolicy(Protocol):
    """Calculates a numeric score from the final simulation state."""

    def calculate_score(
        self,
        final_time: float,
        outcome: str,
        events: tuple[EventRecord, ...],
        paths: Mapping[str, Path2D],
    ) -> float | None: ...
