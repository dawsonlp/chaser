"""Cooperative dual-chaser guidance policy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from chaser.components.policies.intercept.quadratic_drag import (
    QuadraticDragInterceptDecision,
)
from chaser.components.sensors.base import VisualObservation
from chaser.physics.aerodynamics import SphereQuadraticDrag


@dataclass(frozen=True, slots=True)
class DualPincerPolicy:
    """Cooperative dual-chaser policy computing optimal intercept from each chaser's position."""

    role: str  # "lead" or "wing"
    maximum_acceleration: float
    deadline: float
    drag: SphereQuadraticDrag
    time_delay_offset_s: float = 0.0

    def choose_actuator_changes(
        self,
        observation: VisualObservation,
    ) -> Mapping[str, float]:
        base_decision = QuadraticDragInterceptDecision(
            maximum_acceleration=self.maximum_acceleration,
            deadline=max(0.1, self.deadline - self.time_delay_offset_s),
            drag=self.drag,
        )
        return base_decision.choose_actuator_changes(observation)
