"""Scenario where the target periodically detects approaching chasers and executes lateral evasion."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping

from chaser.components.actuators.base import ActuatorDefinition, ActuatorSet
from chaser.components.actuators.responses import PlanarThrustResponse
from chaser.components.policies.intercept.quadratic_drag import (
    QuadraticDragInterceptDecision,
)
from chaser.components.policies.target.evasive import EvasiveGoalSteeringPolicy
from chaser.components.sensors.periodic import PeriodicThreatSensor
from chaser.components.sensors.visual import DirectVisualSensor
from chaser.core import EventDrivenRuntime, EventRecord
from chaser.engine.arena import ComposableArenaModel
from chaser.engine.record import SimulationRecord
from chaser.engine.rules import InteractionRule, ScoringPolicy
from chaser.entities.agent import Agent
from chaser.entities.visual_style import (
    BLUE_COLOR,
    BLUE_TRAIL_COLOR,
    GOAL_COLOR,
    GOAL_TRAIL_COLOR,
    RED_COLOR,
    RED_TRAIL_COLOR,
    CircleShape,
    VisualStyle,
)
from chaser.kinematics.constant_acceleration import ConstantAccelerationPath
from chaser.kinematics.path import Path2D
from chaser.kinematics.state import KinematicState
from chaser.math.vec2 import Vec2, ZERO_VEC2
from chaser.physics.aerodynamics import SphereQuadraticDrag
from chaser.physics.atmosphere import UniformAtmosphere
from chaser.physics.bodies import SphereBody
from chaser.physics.drag_paths import ConstantThrustQuadraticDragPath
from chaser.scenarios.base import Scenario

BLUE_ID = "blue"
RED_ID = "red"
GOAL_ID = "goal"


@dataclass(frozen=True, slots=True)
class EvasiveTargetSettings:
    red_start: Vec2 = Vec2(0.0, 0.0)
    red_velocity: Vec2 = Vec2(1_000.0, 0.0)
    red_radius_m: float = 100.0
    red_scan_interval_s: float = 0.25
    red_evasion_acceleration_mps2: float = 350.0

    goal_center: Vec2 = Vec2(10_200.0, 0.0)
    goal_radius_m: float = 100.0

    blue_start: Vec2 = Vec2(4_000.0, -2_500.0)
    blue_radius_m: float = 0.05
    blue_mass_kg: float = 32.882194
    blue_max_acceleration_mps2: float = 500.0

    air_density_kg_m3: float = 1.225
    sphere_drag_coefficient: float = 0.47
    uninterrupted_goal_time: float = 10.0


class EvasiveTargetScoringPolicy(ScoringPolicy):
    def __init__(self, red_radius_m: float, goal_radius_m: float) -> None:
        self.red_radius_m = red_radius_m
        self.goal_radius_m = goal_radius_m

    def calculate_score(
        self,
        final_time: float,
        outcome: str,
        events: tuple[EventRecord, ...],
        paths: Mapping[str, Path2D],
    ) -> float | None:
        if "intercept" in outcome and "red" in paths and "goal" in paths:
            red_pos = paths["red"].state_at(final_time).position
            goal_pos = paths["goal"].state_at(final_time).position
            distance = (goal_pos - red_pos).magnitude
            return distance - (self.red_radius_m + self.goal_radius_m)
        return None


class EvasiveTargetScenario:
    name = "evasive_target"
    description = "A target that periodically senses pursuers, evades sideways, and re-steers toward the goal."

    def run(self, settings: EvasiveTargetSettings | None = None) -> SimulationRecord:
        cfg = settings or EvasiveTargetSettings()
        blue_body = SphereBody(cfg.blue_radius_m * 2.0, 7850.0)
        drag = SphereQuadraticDrag(
            blue_body,
            UniformAtmosphere(cfg.air_density_kg_m3),
            cfg.sphere_drag_coefficient,
        )

        def make_blue_actuators() -> ActuatorSet:
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

        def make_red_actuators() -> ActuatorSet:
            return ActuatorSet(
                definitions={
                    "thrust_acceleration": ActuatorDefinition(
                        "thrust_acceleration", 0.0, cfg.red_evasion_acceleration_mps2
                    ),
                    "thrust_direction": ActuatorDefinition(
                        "thrust_direction", -math.pi, math.pi
                    ),
                },
                values={"thrust_acceleration": 0.0, "thrust_direction": 0.0},
            )

        def build_blue_drag_path(
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

        def build_red_path(
            agent: Agent,
            t: float,
            state: KinematicState,
            actuators: ActuatorSet,
        ) -> Path2D:
            response = PlanarThrustResponse()
            thrust_acc = response.acceleration(actuators)
            return ConstantAccelerationPath(
                start_time=t,
                initial=KinematicState(
                    position=state.position,
                    velocity=state.velocity,
                    acceleration=thrust_acc,
                ),
            )

        agents: dict[str, Agent] = {
            BLUE_ID: Agent(
                id=BLUE_ID,
                display_name="Blue Interceptor",
                shape=CircleShape(cfg.blue_radius_m),
                initial_path=ConstantAccelerationPath(
                    0.0, KinematicState(cfg.blue_start, ZERO_VEC2, ZERO_VEC2)
                ),
                body=blue_body,
                sensors=(DirectVisualSensor(),),
                policy=QuadraticDragInterceptDecision(
                    maximum_acceleration=cfg.blue_max_acceleration_mps2,
                    deadline=cfg.uninterrupted_goal_time,
                    drag=drag,
                ),
                actuators=make_blue_actuators(),
                actuator_response=PlanarThrustResponse(),
                path_builder=build_blue_drag_path,
                target_id=RED_ID,
                style=VisualStyle(color=BLUE_COLOR, trail_color=BLUE_TRAIL_COLOR),
            ),
            RED_ID: Agent(
                id=RED_ID,
                display_name="Evasive Red Target",
                shape=CircleShape(cfg.red_radius_m),
                initial_path=ConstantAccelerationPath(
                    0.0, KinematicState(cfg.red_start, cfg.red_velocity, ZERO_VEC2)
                ),
                sensors=(
                    PeriodicThreatSensor(
                        scan_interval_s=cfg.red_scan_interval_s,
                        detection_range_m=6_000.0,
                    ),
                ),
                policy=EvasiveGoalSteeringPolicy(
                    goal_position=cfg.goal_center,
                    evasion_acceleration_mps2=cfg.red_evasion_acceleration_mps2,
                ),
                actuators=make_red_actuators(),
                actuator_response=PlanarThrustResponse(),
                path_builder=build_red_path,
                target_id=BLUE_ID,
                style=VisualStyle(color=RED_COLOR, trail_color=RED_TRAIL_COLOR),
            ),
            GOAL_ID: Agent(
                id=GOAL_ID,
                display_name="Goal",
                shape=CircleShape(cfg.goal_radius_m),
                initial_path=ConstantAccelerationPath(
                    0.0, KinematicState(cfg.goal_center, ZERO_VEC2, ZERO_VEC2)
                ),
                style=VisualStyle(color=GOAL_COLOR, trail_color=GOAL_TRAIL_COLOR),
            ),
        }

        rules = [
            InteractionRule(
                entity_a=BLUE_ID,
                entity_b=RED_ID,
                event_kind="blue_intercept",
                outcome="blue_intercepted",
                priority=20,
            ),
            InteractionRule(
                entity_a=RED_ID,
                entity_b=GOAL_ID,
                event_kind="red_goal_contact",
                outcome="red_scored",
                priority=10,
            ),
        ]

        model = ComposableArenaModel(
            scenario_id=self.name,
            agents=agents,
            interaction_rules=rules,
            scoring_policy=EvasiveTargetScoringPolicy(cfg.red_radius_m, cfg.goal_radius_m),
            horizon_time=cfg.uninterrupted_goal_time * 2.0,
        )
        return EventDrivenRuntime().run(model)
