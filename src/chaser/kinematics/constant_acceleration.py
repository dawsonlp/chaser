"""Exact constant-acceleration 2D motion path."""

from __future__ import annotations

from dataclasses import dataclass

from chaser.kinematics.state import KinematicState


@dataclass(frozen=True, slots=True)
class ConstantAccelerationPath:
    """An exact 2D path valid while acceleration remains constant."""

    start_time: float
    initial: KinematicState

    def state_at(self, time: float) -> KinematicState:
        if time < self.start_time:
            raise ValueError("cannot evaluate a path before its start")
        elapsed = time - self.start_time
        return KinematicState(
            position=(
                self.initial.position
                + self.initial.velocity * elapsed
                + self.initial.acceleration * (0.5 * elapsed * elapsed)
            ),
            velocity=self.initial.velocity + self.initial.acceleration * elapsed,
            acceleration=self.initial.acceleration,
        )

