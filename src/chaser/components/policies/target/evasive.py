"""Target policy with threat evasion and goal re-targeting."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping

from chaser.components.sensors.base import VisualObservation
from chaser.math.vec2 import Vec2


@dataclass
class EvasiveGoalSteeringPolicy:
    """Target policy that dodges incoming chasers sideways and re-steers toward the goal."""

    goal_position: Vec2
    evasion_acceleration_mps2: float = 350.0
    correction_acceleration_mps2: float = 300.0
    threat_distance_threshold_m: float = 4_500.0
    evasion_duration_s: float = 1.2
    nominal_speed_mps: float = 1_000.0
    _evade_until: float = -1.0
    _evade_direction_sign: float = 1.0

    def choose_actuator_changes(
        self,
        observation: VisualObservation,
    ) -> Mapping[str, float]:
        t = observation.observed_at
        is_threat = getattr(observation, "is_threat", False)
        dist = getattr(observation, "distance_m", observation.relative_position.magnitude)
        rel_pos = observation.relative_position  # Chaser relative to target

        # Check if active closing threat triggers new evasion
        if is_threat and t >= self._evade_until:
            self._evade_until = t + self.evasion_duration_s
            # If chaser is below target (rel_pos.y < 0), dodge UP (+Y). Otherwise dodge DOWN (-Y).
            self._evade_direction_sign = 1.0 if rel_pos.y < 0 else -1.0

        # Currently in active evasion window
        if t < self._evade_until:
            dodge_heading = math.pi / 2.0 if self._evade_direction_sign > 0 else -math.pi / 2.0
            return {
                "thrust_acceleration": self.evasion_acceleration_mps2,
                "thrust_direction": dodge_heading,
            }

        # Evasion complete: steer toward goal
        p_curr = observation.observer_position or Vec2(0.0, 0.0)
        v_curr = observation.observer_velocity or Vec2(self.nominal_speed_mps, 0.0)

        r_goal = self.goal_position - p_curr
        if r_goal.magnitude < 1e-3:
            return {"thrust_acceleration": 0.0, "thrust_direction": 0.0}

        v_des = r_goal.normalized() * self.nominal_speed_mps
        dv = v_des - v_curr

        if dv.magnitude > 5.0:
            return {
                "thrust_acceleration": min(self.correction_acceleration_mps2, dv.magnitude * 2.0),
                "thrust_direction": dv.direction(),
            }

        # Coast directly toward goal
        return {
            "thrust_acceleration": 0.0,
            "thrust_direction": r_goal.direction(),
        }
