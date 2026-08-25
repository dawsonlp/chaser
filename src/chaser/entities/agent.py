"""Composable agent representation with explicit component slots."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Sequence

from chaser.components.actuators.base import ActuatorSet
from chaser.components.actuators.responses import ActuatorResponse
from chaser.components.policies.base import DecisionPolicy
from chaser.components.sensors.base import Sensor
from chaser.entities.visual_style import BLUE_COLOR, BLUE_TRAIL_COLOR, CircleShape, VisualStyle
from chaser.kinematics.path import Path2D
from chaser.kinematics.state import KinematicState
from chaser.physics.bodies import RigidBody, SphereBody

PathBuilderFunc = Callable[["Agent", float, KinematicState, ActuatorSet], Path2D]


@dataclass(frozen=True, slots=True)
class Agent:
    """A simulation participant composed of typed physical, cognitive, and actuator components."""

    id: str
    display_name: str
    shape: CircleShape
    initial_path: Path2D
    body: SphereBody | RigidBody | None = None
    sensors: tuple[Sensor, ...] = ()
    policy: DecisionPolicy | None = None
    actuators: ActuatorSet | None = None
    actuator_response: ActuatorResponse | None = None
    path_builder: PathBuilderFunc | None = None
    target_id: str | None = None
    style: VisualStyle = field(
        default_factory=lambda: VisualStyle(color=BLUE_COLOR, trail_color=BLUE_TRAIL_COLOR)
    )

    @property
    def radius_m(self) -> float:
        return self.shape.radius_m

    def with_actuators(self, actuators: ActuatorSet) -> Agent:
        """Return a copy of the agent with updated actuator values."""
        return Agent(
            id=self.id,
            display_name=self.display_name,
            shape=self.shape,
            initial_path=self.initial_path,
            body=self.body,
            sensors=self.sensors,
            policy=self.policy,
            actuators=actuators,
            actuator_response=self.actuator_response,
            path_builder=self.path_builder,
            target_id=self.target_id,
            style=self.style,
        )
