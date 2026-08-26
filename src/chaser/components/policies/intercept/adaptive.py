"""Adaptive intercept policy that continuously recomputes lead trajectories when target maneuvers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from chaser.components.policies.intercept.quadratic_drag import (
    QuadraticDragInterceptDecision,
)
from chaser.components.sensors.base import VisualObservation
from chaser.physics.aerodynamics import SphereQuadraticDrag


@dataclass(frozen=True, slots=True)
class AdaptiveInterceptPolicy:
    """Guidance policy that recalculates optimal drag-compensated intercept at every observation."""

    maximum_acceleration: float
    deadline: float
    drag: SphereQuadraticDrag

    def choose_actuator_changes(
        self,
        observation: VisualObservation,
    ) -> Mapping[str, float]:
        decision = QuadraticDragInterceptDecision(
            maximum_acceleration=self.maximum_acceleration,
            deadline=max(0.1, self.deadline - observation.observed_at),
            drag=self.drag,
        )
        return decision.choose_actuator_changes(observation)

