"""3D spherical contact detection (3D readiness)."""

from __future__ import annotations

import math
from typing import Protocol

from chaser.kinematics.path import Path3D


class SphereContactDetector:
    """Finds earliest continuous contact between two 3D spherical paths."""

    def earliest_sphere_contact(
        self,
        first: Path3D,
        first_radius: float,
        second: Path3D,
        second_radius: float,
        *,
        from_time: float,
        through_time: float,
        interval_count: int = 16_384,
        time_tolerance: float = 1e-9,
    ) -> float | None:
        """Find earliest contact in 3D using interval bracketing and bisection."""
        contact_radius_squared = (first_radius + second_radius) ** 2

        def separation(t: float) -> float:
            offset = first.state_at(t).position - second.state_at(t).position
            return offset.magnitude_squared - contact_radius_squared

        left = from_time
        if separation(left) <= 0.0:
            return left

        dt = (through_time - from_time) / interval_count
        for i in range(1, interval_count + 1):
            right = from_time + dt * i
            if separation(right) <= 0.0:
                lo = left
                hi = right
                for _ in range(80):
                    if hi - lo <= time_tolerance:
                        break
                    mid = (lo + hi) * 0.5
                    if separation(mid) <= 0.0:
                        hi = mid
                    else:
                        lo = mid
                return (lo + hi) * 0.5
            left = right
        return None
