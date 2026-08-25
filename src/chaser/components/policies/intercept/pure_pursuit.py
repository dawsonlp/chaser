"""Pure pursuit guidance policy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from chaser.components.sensors.base import VisualObservation


@dataclass(frozen=True, slots=True)
class PurePursuitPolicy:
    """Direct line-of-sight acceleration towards the observed target."""

    maximum_acceleration: float

    def choose_actuator_changes(
        self,
        observation: VisualObservation,
    ) -> Mapping[str, float]:
        return {
            "thrust_acceleration": self.maximum_acceleration,
            "thrust_direction": observation.relative_position.direction(),
        }

