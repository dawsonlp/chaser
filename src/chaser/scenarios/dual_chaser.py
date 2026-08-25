"""Comparative scenario: two cooperative blue chasers vs one red target and a goal."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping

from chaser.components.actuators.base import ActuatorDefinition, ActuatorSet
from chaser.components.actuators.responses import PlanarThrustResponse
from chaser.components.policies.cooperative.dual_pincer import DualPincerPolicy
from chaser.components.sensors.visual import DirectVisualSensor
from chaser.core import EventDrivenRuntime, EventRecord
from chaser.engine.arena import ComposableArenaModel
from chaser.engine.record import SimulationRecord
from chaser.engine.rules import InteractionRule, ScoringPolicy
from chaser.entities.agent import Agent
from chaser.entities.visual_style import (
    BLUE_COLOR,
    BLUE_TRAIL_COLOR,
    CYAN_COLOR,
    CYAN_TRAIL_COLOR,
    CircleShape,
    GOAL_COLOR,
    RED_COLOR,
    RED_TRAIL_COLOR,
    VisualStyle,
)
from chaser.kinematics.constant_acceleration import ConstantAccelerationPath
from chaser.kinematics.path import Path2D
from chaser.kinematics.state import KinematicState
from chaser.math.vec2 import ZERO_VEC2, Vec2
from chaser.physics.aerodynamics import SphereQuadraticDrag
from chaser.physics.atmosphere import UniformAtmosphere
from chaser.physics.bodies import SphereBody
from chaser.physics.drag_paths import ConstantThrustQuadraticDragPath

BLUE_1_ID = "blue_1"
BLUE_2_ID = "blue_2"
RED_ID = "red"
GOAL_ID = "goal"


@dataclass(frozen=True, slots=True)
class DualChaserSettings:
    """Settings for two-chaser comparative pursuit."""

    red_goal_clearance_m: float = 10_000.0
    red_speed_mps: float = 1_000.0
    red_radius_m: float = 100.0
    goal_radius_m: float = 100.0
    blue_diameter_m: float = 0.1
    blue_material_density_kg_m3: float = 7_850.0
    blue_1_start: Vec2 = Vec2(4_000.0, -2_500.0)
    blue_2_start: Vec2 = Vec2(3_000.0, 2_000.0)
    blue_max_acceleration_mps2: float = 500.0
    air_density_kg_m3: float = 1.225
    sphere_drag_coefficient: float = 0.47

    @property
    def blue_body(self) -> SphereBody:
        return SphereBody(self.blue_diameter_m, self.blue_material_density_kg_m3)

    @property
    def blue_radius_m(self) -> float:
        return self.blue_body.radius_m

    @property
    def red_start(self) -> Vec2:
        return Vec2(0.0, 0.0)

    @property
    def goal_position(self) -> Vec2:
        center_dist = self.red_goal_clearance_m + self.red_radius_m + self.goal_radius_m
        return Vec2(center_dist, 0.0)

    @property
    def uninterrupted_goal_time(self) -> float:
        return self.red_goal_clearance_m / self.red_speed_mps


class DualChaserScoringPolicy:
    def __init__(self, settings: DualChaserSettings) -> None:
        self.settings = settings

    def calculate_score(
        self,
        final_time: float,
        outcome: str,
        events: tuple[EventRecord, ...],
        paths: Mapping[str, Path2D],
    ) -> float | None:
        if "intercept" in outcome:
            red_pos = paths[RED_ID].state_at(final_time).position
            center_dist = (self.settings.goal_position - red_pos).magnitude
            return max(
                0.0,
                center_dist - self.settings.red_radius_m - self.settings.goal_radius_m,
            )
        return None


class DualChaserScenario:
    """Two blue chasers (lead and wing/flank) pursuing a red target."""

    name = "dual_chaser"
    description = "Two cooperative blue chasers intercepting a red target before it scores."

    def run(self, settings: DualChaserSettings | None = None) -> SimulationRecord:
        cfg = settings or DualChaserSettings()
        drag = SphereQuadraticDrag(
            cfg.blue_body,
            UniformAtmosphere(cfg.air_density_kg_m3),
            cfg.sphere_drag_coefficient,
        )

        def make_actuators() -> ActuatorSet:
            return ActuatorSet(
                definitions={
                    "thrust_acceleration": ActuatorDefinition(
                        "thrust_acceleration", 0.0, cfg.blue_max_acceleration_mps2
                    ),
                    "thrust_direction": ActuatorDefinition(
                        "thrust_direction", -math.pi, math.pi
                    ),
                },
                values={"thrust_acceleration": 0.0, "thrust_direction": 0.0},
            )

        def build_drag_path(
            agent: Agent,
            t: float,
            state: KinematicState,
            actuators: ActuatorSet,
        ) -> Path2D:
            response = PlanarThrustResponse()
            return ConstantThrustQuadraticDragPath(
                start_time=t,
                initial_position=state.position,
                thrust_acceleration=response.acceleration(actuators),
                drag=drag,
            )

        agents: dict[str, Agent] = {
            BLUE_1_ID: Agent(
                id=BLUE_1_ID,
                display_name="Blue Lead",
                shape=CircleShape(cfg.blue_radius_m),
                initial_path=ConstantAccelerationPath(
                    0.0, KinematicState(cfg.blue_1_start, ZERO_VEC2, ZERO_VEC2)
                ),
                body=cfg.blue_body,
                sensors=(DirectVisualSensor(),),
                policy=DualPincerPolicy(
                    role="lead",
                    maximum_acceleration=cfg.blue_max_acceleration_mps2,
                    deadline=cfg.uninterrupted_goal_time,
                    drag=drag,
                ),
                actuators=make_actuators(),
                actuator_response=PlanarThrustResponse(),
                path_builder=build_drag_path,
                target_id=RED_ID,
                style=VisualStyle(color=BLUE_COLOR, trail_color=BLUE_TRAIL_COLOR),
            ),
            BLUE_2_ID: Agent(
                id=BLUE_2_ID,
                display_name="Blue Wing",
                shape=CircleShape(cfg.blue_radius_m),
                initial_path=ConstantAccelerationPath(
                    0.0, KinematicState(cfg.blue_2_start, ZERO_VEC2, ZERO_VEC2)
                ),
                body=cfg.blue_body,
                sensors=(DirectVisualSensor(),),
                policy=DualPincerPolicy(
                    role="wing",
                    maximum_acceleration=cfg.blue_max_acceleration_mps2,
                    deadline=cfg.uninterrupted_goal_time,
                    drag=drag,
                ),
                actuators=make_actuators(),
                actuator_response=PlanarThrustResponse(),
                path_builder=build_drag_path,
                target_id=RED_ID,
                style=VisualStyle(color=CYAN_COLOR, trail_color=CYAN_TRAIL_COLOR),
            ),
            RED_ID: Agent(
                id=RED_ID,
                display_name="Red Target",
                shape=CircleShape(cfg.red_radius_m),
                initial_path=ConstantAccelerationPath(
                    0.0,
                    KinematicState(
                        cfg.red_start, Vec2(cfg.red_speed_mps, 0.0), ZERO_VEC2
                    ),
                ),
                style=VisualStyle(color=RED_COLOR, trail_color=RED_TRAIL_COLOR),
            ),
            GOAL_ID: Agent(
                id=GOAL_ID,
                display_name="Goal Post",
                shape=CircleShape(cfg.goal_radius_m),
                initial_path=ConstantAccelerationPath(
                    0.0, KinematicState(cfg.goal_position, ZERO_VEC2, ZERO_VEC2)
                ),
                style=VisualStyle(color=GOAL_COLOR, show_trail=False),
            ),
        }

        rules = (
            InteractionRule(BLUE_1_ID, RED_ID, "blue_1_intercept", outcome="blue_1_intercepted", priority=20),
            InteractionRule(BLUE_2_ID, RED_ID, "blue_2_intercept", outcome="blue_2_intercepted", priority=20),
            InteractionRule(RED_ID, GOAL_ID, "red_goal_contact", outcome="red_scored", priority=10),
        )

        model = ComposableArenaModel(
            scenario_id="dual_chaser",
            agents=agents,
            interaction_rules=rules,
            scoring_policy=DualChaserScoringPolicy(cfg),
            horizon_time=cfg.uninterrupted_goal_time + 1.0,
        )

        return EventDrivenRuntime().run(model)
