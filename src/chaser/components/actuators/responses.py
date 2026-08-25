"""Actuator response converters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from chaser.components.actuators.base import ActuatorSet
from chaser.math.vec2 import Vec2


class ActuatorResponse(Protocol):
    """Translates an ActuatorSet into an effective kinematic/force effect."""

    def acceleration(self, actuators: ActuatorSet) -> Vec2: ...


@dataclass(frozen=True, slots=True)
class PlanarThrustResponse:
    """Interpretation of magnitude and direction actuator values as 2D thrust acceleration."""

    magnitude_actuator: str = "thrust_acceleration"
    direction_actuator: str = "thrust_direction"

    def acceleration(self, actuators: ActuatorSet) -> Vec2:
        return Vec2.from_polar(
            actuators.values[self.magnitude_actuator],
            actuators.values[self.direction_actuator],
        )

