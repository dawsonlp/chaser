"""Collision and contact detection protocols."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from chaser.kinematics.path import Path2D


@dataclass(frozen=True, slots=True)
class ContactEventRecord:
    time: float
    participant_a: str
    participant_b: str


class ContactDetector(Protocol):
    """Protocol for finding earliest contact between two time-addressable paths."""

    def earliest_contact(
        self,
        first_path: Path2D,
        first_radius: float,
        second_path: Path2D,
        second_radius: float,
        *,
        from_time: float,
        through_time: float,
    ) -> float | None: ...
