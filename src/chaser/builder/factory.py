"""Dynamic factory assembling configured scenario components into ComposableArenaModel."""

from __future__ import annotations

import math
from typing import Mapping

from chaser.builder.config import ScenarioConfig
from chaser.catalog.registry import PolicyCatalog, SensorCatalog
from chaser.components.actuators.base import ActuatorDefinition, ActuatorSet
from chaser.components.actuators.responses import PlanarThrustResponse
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
    GOAL_COLOR,
    GOAL_TRAIL_COLOR,
    PURPLE_COLOR,
    PURPLE_TRAIL_COLOR,
    RED_COLOR,
    RED_TRAIL_COLOR,
    YELLOW_COLOR,
    YELLOW_TRAIL_COLOR,
    CircleShape,
    Color,
    VisualStyle,
)
from chaser.kinematics.constant_acceleration import ConstantAccelerationPath
from chaser.kinematics.numerical_path import DenseNumericalPath2D
from chaser.kinematics.path import Path2D
from chaser.kinematics.state import KinematicState
from chaser.math.vec2 import Vec2, ZERO_VEC2
from chaser.physics.aerodynamics import SphereQuadraticDrag
from chaser.physics.atmosphere import UniformAtmosphere
from chaser.physics.bodies import SphereBody
from chaser.physics.drag_paths import ConstantThrustQuadraticDragPath


def _resolve_color_theme(theme_name: str) -> VisualStyle:
    themes: dict[str, tuple[Color, Color]] = {
        "blue": (BLUE_COLOR, BLUE_TRAIL_COLOR),
        "cyan": (CYAN_COLOR, CYAN_TRAIL_COLOR),
        "purple": (PURPLE_COLOR, PURPLE_TRAIL_COLOR),
        "yellow": (YELLOW_COLOR, YELLOW_TRAIL_COLOR),
        "red": (RED_COLOR, RED_TRAIL_COLOR),
        "goal": (GOAL_COLOR, GOAL_TRAIL_COLOR),
    }
    main_c, trail_c = themes.get(theme_name, (BLUE_COLOR, BLUE_TRAIL_COLOR))
    return VisualStyle(color=main_c, trail_color=trail_c)


class StandardPursuitScoringPolicy(ScoringPolicy):
    def __init__(self, target_radius_m: float, goal_radius_m: float) -> None:
        self.target_radius_m = target_radius_m
        self.goal_radius_m = goal_radius_m

    def calculate_score(
        self,
        final_time: float,
        outcome: str,
        events: tuple[EventRecord, ...],
        paths: Mapping[str, Path2D],
    ) -> float | None:
        if "intercept" in outcome and "red" in paths and "goal" in paths:
            target_pos = paths["red"].state_at(final_time).position
            goal_pos = paths["goal"].state_at(final_time).position
            distance = (goal_pos - target_pos).magnitude
            return distance - (self.target_radius_m + self.goal_radius_m)
        return None


def build_scenario_model(config: ScenarioConfig) -> ComposableArenaModel:
    """Instantiate all agents, components, sensors, policies, and interaction rules."""
    atmo = UniformAtmosphere(config.environment.air_density_kg_m3)
    agents: dict[str, Agent] = {}
    rules: list[InteractionRule] = []

    # 1. Target Agent
    target_spec = config.target
    target_sensors = ()
    if target_spec.sensor_name:
        target_sensors = (
            SensorCatalog.create(
                target_spec.sensor_name,
                **target_spec.sensor_params,
            ),
        )

    target_policy = PolicyCatalog.create(
        target_spec.policy_name,
        **target_spec.policy_params,
    )

    def make_target_actuators() -> ActuatorSet:
        evade_acc = target_spec.policy_params.get("evasion_acceleration_mps2", 350.0)
        return ActuatorSet(
            definitions={
                "thrust_acceleration": ActuatorDefinition(
                    "thrust_acceleration", 0.0, evade_acc
                ),
                "thrust_direction": ActuatorDefinition(
                    "thrust_direction", -math.pi, math.pi
                ),
            },
            values={"thrust_acceleration": 0.0, "thrust_direction": 0.0},
        )

    def build_target_path(
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

    # Primary target pursuer (first chaser)
    primary_chaser_id = config.chasers[0].id if config.chasers else "blue"

    agents[target_spec.id] = Agent(
        id=target_spec.id,
        display_name=target_spec.name,
        shape=CircleShape(target_spec.radius_m),
        initial_path=ConstantAccelerationPath(
            0.0, KinematicState(target_spec.start, target_spec.velocity, ZERO_VEC2)
        ),
        sensors=target_sensors,
        policy=target_policy,
        actuators=make_target_actuators(),
        actuator_response=PlanarThrustResponse(),
        path_builder=build_target_path,
        target_id=primary_chaser_id,
        style=_resolve_color_theme(target_spec.color_theme),
    )

    # 2. Chaser Agents
    for chaser_spec in config.chasers:
        body = SphereBody(chaser_spec.radius_m * 2.0, 7850.0)
        drag = SphereQuadraticDrag(
            body,
            atmo,
            config.environment.drag_coefficient,
        )

        sensor = SensorCatalog.create(
            chaser_spec.sensor_name,
            **chaser_spec.sensor_params,
        )

        policy_params = dict(chaser_spec.policy_params)
        policy_params.setdefault("maximum_acceleration", chaser_spec.max_acceleration_mps2)
        policy_params.setdefault("drag", drag)

        policy = PolicyCatalog.create(
            chaser_spec.policy_name,
            **policy_params,
        )

        def make_chaser_actuators(max_acc: float = chaser_spec.max_acceleration_mps2) -> ActuatorSet:
            return ActuatorSet(
                definitions={
                    "thrust_acceleration": ActuatorDefinition(
                        "thrust_acceleration", 0.0, max_acc
                    ),
                    "thrust_direction": ActuatorDefinition(
                        "thrust_direction", -math.pi, math.pi
                    ),
                },
                values={"thrust_acceleration": 0.0, "thrust_direction": 0.0},
            )

        def build_chaser_drag_path(
            agent: Agent,
            t: float,
            state: KinematicState,
            actuators: ActuatorSet,
            chaser_drag: SphereQuadraticDrag = drag,
        ) -> Path2D:
            response = PlanarThrustResponse()
            thrust_acc = response.acceleration(actuators)
            if t == 0.0 and state.velocity.magnitude < 1e-6:
                return ConstantThrustQuadraticDragPath(
                    start_time=t,
                    initial_position=state.position,
                    thrust_acceleration=thrust_acc,
                    drag=chaser_drag,
                )

            def total_accel(time_val: float, pos: Vec2, vel: Vec2) -> Vec2:
                return thrust_acc + chaser_drag.drag_acceleration(vel)

            return DenseNumericalPath2D(
                start_time=t,
                initial_state=KinematicState(
                    position=state.position,
                    velocity=state.velocity,
                    acceleration=thrust_acc,
                ),
                acceleration_func=total_accel,
            )

        agents[chaser_spec.id] = Agent(
            id=chaser_spec.id,
            display_name=chaser_spec.name,
            shape=CircleShape(chaser_spec.radius_m),
            initial_path=ConstantAccelerationPath(
                0.0, KinematicState(chaser_spec.start, ZERO_VEC2, ZERO_VEC2)
            ),
            body=body,
            sensors=(sensor,),
            policy=policy,
            actuators=make_chaser_actuators(),
            actuator_response=PlanarThrustResponse(),
            path_builder=build_chaser_drag_path,
            target_id=target_spec.id,
            style=_resolve_color_theme(chaser_spec.color_theme),
        )

        # Chaser vs Target collision rule
        rules.append(
            InteractionRule(
                entity_a=chaser_spec.id,
                entity_b=target_spec.id,
                event_kind=f"{chaser_spec.id}_intercept",
                outcome=f"{chaser_spec.id}_intercepted",
                priority=20,
            )
        )

    # 3. Goal Agent & Scoring
    goal_spec = config.goal
    agents[goal_spec.id] = Agent(
        id=goal_spec.id,
        display_name=goal_spec.name,
        shape=CircleShape(goal_spec.radius_m),
        initial_path=ConstantAccelerationPath(
            0.0, KinematicState(goal_spec.center, ZERO_VEC2, ZERO_VEC2)
        ),
        style=_resolve_color_theme("goal"),
    )

    rules.append(
        InteractionRule(
            entity_a=target_spec.id,
            entity_b=goal_spec.id,
            event_kind="target_goal_contact",
            outcome="target_scored",
            priority=10,
        )
    )

    return ComposableArenaModel(
        scenario_id=config.scenario_id,
        agents=agents,
        interaction_rules=rules,
        scoring_policy=StandardPursuitScoringPolicy(target_spec.radius_m, goal_spec.radius_m),
        horizon_time=config.environment.horizon_time,
    )


def run_composed_scenario(config: ScenarioConfig) -> SimulationRecord:
    """Execute a declarative scenario configuration and return its simulation record."""
    model = build_scenario_model(config)
    return EventDrivenRuntime().run(model)

