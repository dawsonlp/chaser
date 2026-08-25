"""Cooperative dual-chaser pincer / flanking guidance policy."""

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
    """Cooperative policy that biases the intercept point based on role (lead vs wing/flank)."""

    role: str  # "lead" or "flank"
    maximum_acceleration: float
    deadline: float
    drag: SphereQuadraticDrag
    flank_offset_rad: float = 0.15

    def choose_actuator_changes(
        self,
        observation: VisualObservation,
    ) -> Mapping[str, float]:
        base_decision = QuadraticDragInterceptDecision(
            maximum_acceleration=self.maximum_acceleration,
            deadline=self.deadline,
            drag=self.drag,
        )
        base_changes = dict(base_decision.choose_actuator_changes(observation))

        if self.role == "flank":
            # Bias direction slightly to envelope the target
            base_dir = base_changes["thrust_direction"]
            base_changes["thrust_direction"] = base_dir + self.flank_offset_rad

        return base_changes
