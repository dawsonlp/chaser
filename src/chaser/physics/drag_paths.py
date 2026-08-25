"""Analytic motion paths under aerodynamic drag."""

from __future__ import annotations

from dataclasses import dataclass
import math

from chaser.kinematics.state import KinematicState
from chaser.math.vec2 import ZERO_VEC2, Vec2
from chaser.physics.aerodynamics import SphereQuadraticDrag


@dataclass(frozen=True, slots=True)
class ConstantThrustQuadraticDragPath:
    """Analytic path from rest under constant thrust and quadratic drag.

    Thrust direction, air density, and drag coefficient remain fixed for the
    lifetime of this path. Gravity is outside this horizontal-plane model.
    """

    start_time: float
    initial_position: Vec2
    thrust_acceleration: Vec2
    drag: SphereQuadraticDrag

    def state_at(self, time: float) -> KinematicState:
        if time < self.start_time:
            raise ValueError("cannot evaluate a path before its start")
        elapsed = time - self.start_time
        thrust = self.thrust_acceleration.magnitude
        if thrust == 0.0:
            return KinematicState(self.initial_position, ZERO_VEC2, ZERO_VEC2)

        direction = self.thrust_acceleration / thrust
        drag_factor = self.drag.drag_factor_per_m
        if drag_factor == 0.0:
            return KinematicState(
                self.initial_position + direction * (0.5 * thrust * elapsed**2),
                direction * (thrust * elapsed),
                self.thrust_acceleration,
            )

        rate = math.sqrt(thrust * drag_factor)
        terminal_speed = math.sqrt(thrust / drag_factor)
        scaled_time = rate * elapsed
        speed = terminal_speed * math.tanh(scaled_time)
        distance = _log_cosh(scaled_time) / drag_factor
        net_acceleration = thrust * (1.0 - math.tanh(scaled_time) ** 2)
        return KinematicState(
            self.initial_position + direction * distance,
            direction * speed,
            direction * net_acceleration,
        )

    def distance_after(self, elapsed: float) -> float:
        if elapsed < 0.0:
            raise ValueError("elapsed time must be non-negative")
        return (
            self.state_at(self.start_time + elapsed).position - self.initial_position
        ).magnitude


def _log_cosh(value: float) -> float:
    absolute = abs(value)
    return absolute + math.log1p(math.exp(-2.0 * absolute)) - math.log(2.0)

