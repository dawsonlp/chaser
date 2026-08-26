"""Augmented Proportional Navigation (APN) guidance policy."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping

from chaser.components.sensors.base import VisualObservation
from chaser.math.vec2 import Vec2


@dataclass(frozen=True, slots=True)
class ProportionalNavigationGuidancePolicy:
    """Proportional Navigation guidance driving Line-of-Sight (LOS) angular rate to zero."""

    navigation_gain: float = 3.5
    maximum_acceleration: float = 500.0

    def choose_actuator_changes(
        self,
        observation: VisualObservation,
    ) -> Mapping[str, float]:
        r = observation.relative_position  # p_target - p_chaser
        v = observation.relative_velocity  # v_target - v_chaser

        dist_sq = r.magnitude_squared
        dist = math.sqrt(dist_sq)

        if dist < 1e-3:
            return {"thrust_acceleration": 0.0, "thrust_direction": 0.0}

        # Line-of-sight rotation rate: (r_x * v_y - r_y * v_x) / dist^2
        los_rate = r.cross_2d(v) / dist_sq

        # Closing velocity: - (r . v) / dist
        closing_speed = -r.dot(v) / dist

        # Commanded normal acceleration perpendicular to line of sight
        los_heading = r.direction()
        normal_heading = los_heading + math.pi / 2.0
        normal_dir = Vec2.from_polar(1.0, normal_heading)

        # Lateral acceleration command: a_n = N * V_c * lambda_dot
        acc_cmd_normal = self.navigation_gain * max(10.0, closing_speed) * los_rate

        # Forward closing acceleration along LOS to maintain closing velocity
        acc_cmd_forward = max(0.0, self.maximum_acceleration - abs(acc_cmd_normal))
        forward_dir = Vec2.from_polar(1.0, los_heading)

        total_acc = normal_dir * acc_cmd_normal + forward_dir * acc_cmd_forward

        return {
            "thrust_acceleration": min(self.maximum_acceleration, max(50.0, total_acc.magnitude)),
            "thrust_direction": total_acc.direction(),
        }
