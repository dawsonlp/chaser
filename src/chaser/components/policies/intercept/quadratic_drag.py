"""Quadratic drag intercept guidance decision policy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping

from chaser.components.sensors.base import VisualObservation
from chaser.math.vec2 import ZERO_VEC2, Vec2
from chaser.physics.aerodynamics import SphereQuadraticDrag
from chaser.physics.drag_paths import ConstantThrustQuadraticDragPath


@dataclass(frozen=True, slots=True)
class QuadraticDragInterceptDecision:
    """Calculates lead intercept heading under aerodynamic drag."""

    maximum_acceleration: float
    deadline: float
    drag: SphereQuadraticDrag

    def choose_actuator_changes(
        self,
        observation: VisualObservation,
    ) -> Mapping[str, float]:
        relative = observation.relative_position
        relative_velocity = observation.relative_velocity
        full_thrust_path = ConstantThrustQuadraticDragPath(
            start_time=0.0,
            initial_position=ZERO_VEC2,
            thrust_acceleration=Vec2(self.maximum_acceleration, 0.0),
            drag=self.drag,
        )

        def reach_margin(time: float) -> float:
            target_distance = (relative + relative_velocity * time).magnitude
            return full_thrust_path.distance_after(time) - target_distance

        intercept_time = self._first_reachable_time(reach_margin)
        if intercept_time is None:
            intercept_time = self.deadline

        displacement = relative + relative_velocity * intercept_time
        return {
            "thrust_acceleration": self.maximum_acceleration,
            "thrust_direction": displacement.direction(),
        }

    def _first_reachable_time(
        self,
        evaluate: Callable[[float], float],
    ) -> float | None:
        left = 1e-8
        left_value = evaluate(left)
        for index in range(1, 1_025):
            right = self.deadline * index / 1_024
            right_value = evaluate(right)
            if right_value >= 0.0 and left_value < 0.0:
                for _ in range(80):
                    middle = (left + right) * 0.5
                    if right - left <= 1e-9:
                        break
                    if evaluate(middle) >= 0.0:
                        right = middle
                    else:
                        left = middle
                return (left + right) * 0.5
            left = right
            left_value = right_value
        return None
