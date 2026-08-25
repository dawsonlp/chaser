"""Sensor protocols and observation types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from chaser.kinematics.path import Path2D
from chaser.math.vec2 import Vec2


@dataclass(frozen=True, slots=True)
class VisualObservation:
    observed_at: float
    observer_id: str
    target_id: str
    relative_position: Vec2
    relative_velocity: Vec2


class Sensor(Protocol):
    """Protocol for an object-owned sensing device."""

    def observe(
        self,
        *,
        time: float,
        observer_id: str,
        target_id: str,
        observer_path: Path2D,
        target_path: Path2D,
    ) -> VisualObservation: ...

