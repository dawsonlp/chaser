"""Dense interpolation utilities for continuous trajectory evaluation."""

from __future__ import annotations

from dataclasses import dataclass
import math

from chaser.math.vec2 import Vec2


@dataclass(frozen=True, slots=True)
class CubicHermiteSegment2D:
    """Cubic Hermite polynomial interpolating between two 2D kinematic states."""

    t0: float
    t1: float
    p0: Vec2
    p1: Vec2
    v0: Vec2
    v1: Vec2

    def __post_init__(self) -> None:
        if self.t1 <= self.t0:
            raise ValueError("t1 must be strictly greater than t0")

    @property
    def duration(self) -> float:
        return self.t1 - self.t0

    def evaluate_position(self, t: float) -> Vec2:
        """Evaluate interpolated position at time t."""
        dt = self.duration
        u = (t - self.t0) / dt
        u2 = u * u
        u3 = u2 * u

        h00 = 2.0 * u3 - 3.0 * u2 + 1.0
        h10 = u3 - 2.0 * u2 + u
        h01 = -2.0 * u3 + 3.0 * u2
        h11 = u3 - u2

        return self.p0 * h00 + self.v0 * (dt * h10) + self.p1 * h01 + self.v1 * (dt * h11)

    def evaluate_velocity(self, t: float) -> Vec2:
        """Evaluate interpolated velocity at time t (derivative of position)."""
        dt = self.duration
        u = (t - self.t0) / dt
        u2 = u * u

        # Derivatives of Hermite basis with respect to u
        dh00 = 6.0 * u2 - 6.0 * u
        dh10 = 3.0 * u2 - 4.0 * u + 1.0
        dh01 = -6.0 * u2 + 6.0 * u
        dh11 = 3.0 * u2 - 2.0 * u

        # du/dt = 1 / dt
        return (
            self.p0 * (dh00 / dt)
            + self.v0 * dh10
            + self.p1 * (dh01 / dt)
            + self.v1 * dh11
        )

    def evaluate_acceleration(self, t: float) -> Vec2:
        """Evaluate interpolated acceleration at time t (second derivative)."""
        dt = self.duration
        u = (t - self.t0) / dt

        # Second derivatives with respect to u
        d2h00 = 12.0 * u - 6.0
        d2h10 = 6.0 * u - 4.0
        d2h01 = -12.0 * u + 6.0
        d2h11 = 6.0 * u - 2.0

        dt2 = dt * dt
        return (
            self.p0 * (d2h00 / dt2)
            + self.v0 * (d2h10 / dt)
            + self.p1 * (d2h01 / dt2)
            + self.v1 * (d2h11 / dt)
        )

