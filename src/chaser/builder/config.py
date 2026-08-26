"""Declarative configuration models for assembling custom pursuit scenarios."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence

from chaser.math.vec2 import Vec2


@dataclass(frozen=True, slots=True)
class ChaserSpec:
    """Specification for a single chaser interceptor."""

    id: str = "blue_1"
    name: str = "Blue Interceptor"
    start: Vec2 = Vec2(4_000.0, -2_500.0)
    max_acceleration_mps2: float = 500.0
    policy_name: str = "quadratic_drag"
    policy_params: dict[str, Any] = field(default_factory=dict)
    sensor_name: str = "direct_visual"
    sensor_params: dict[str, Any] = field(default_factory=dict)
    radius_m: float = 0.05
    mass_kg: float = 32.882194
    color_theme: str = "blue"


@dataclass(frozen=True, slots=True)
class TargetSpec:
    """Specification for the pursued target."""

    id: str = "red"
    name: str = "Target"
    start: Vec2 = Vec2(0.0, 0.0)
    velocity: Vec2 = Vec2(1_000.0, 0.0)
    radius_m: float = 100.0
    policy_name: str = "straight_line"
    policy_params: dict[str, Any] = field(default_factory=dict)
    sensor_name: str | None = None
    sensor_params: dict[str, Any] = field(default_factory=dict)
    color_theme: str = "red"


@dataclass(frozen=True, slots=True)
class GoalSpec:
    """Specification for the target destination / goal post."""

    id: str = "goal"
    name: str = "Goal"
    center: Vec2 = Vec2(10_200.0, 0.0)
    radius_m: float = 100.0


@dataclass(frozen=True, slots=True)
class EnvironmentSpec:
    """Physical environment parameters."""

    air_density_kg_m3: float = 1.225
    drag_coefficient: float = 0.47
    horizon_time: float = 25.0


@dataclass(frozen=True, slots=True)
class ScenarioConfig:
    """Complete declarative scenario specification."""

    scenario_id: str = "custom_composed"
    chasers: tuple[ChaserSpec, ...] = (ChaserSpec(),)
    target: TargetSpec = TargetSpec()
    goal: GoalSpec = GoalSpec()
    environment: EnvironmentSpec = EnvironmentSpec()

    @classmethod
    def create(
        cls,
        *,
        scenario_id: str = "custom_composed",
        chaser_count: int = 1,
        chaser_policy: str = "quadratic_drag",
        chaser_acc: float = 500.0,
        chaser_starts: Sequence[Vec2] | None = None,
        target_policy: str = "straight_line",
        target_sensor: str | None = None,
        target_evade_acc: float = 350.0,
        goal_center: Vec2 = Vec2(10_200.0, 0.0),
    ) -> ScenarioConfig:
        """Helper to create standard 1-to-N chaser configurations quickly."""
        default_starts = [
            Vec2(4_000.0, -2_500.0),
            Vec2(3_000.0, 2_000.0),
            Vec2(6_000.0, -3_000.0),
            Vec2(5_000.0, 3_000.0),
        ]
        starts = list(chaser_starts) if chaser_starts else default_starts[:chaser_count]
        while len(starts) < chaser_count:
            starts.append(Vec2(4_000.0 + len(starts) * 1000.0, -2_500.0))

        themes = ["blue", "cyan", "purple", "yellow"]
        chasers: list[ChaserSpec] = []
        for i in range(chaser_count):
            cid = f"blue_{i+1}" if chaser_count > 1 else "blue"
            role = "lead" if i == 0 else "wing"
            chasers.append(
                ChaserSpec(
                    id=cid,
                    name=f"Blue {i+1}" if chaser_count > 1 else "Blue Interceptor",
                    start=starts[i],
                    max_acceleration_mps2=chaser_acc,
                    policy_name=chaser_policy,
                    policy_params={"role": role} if chaser_policy == "dual_pincer" else {},
                    color_theme=themes[i % len(themes)],
                )
            )

        # Target sensor setup
        target_sensor_name = target_sensor
        if target_sensor_name is None and target_policy == "evasive_goal_steering":
            target_sensor_name = "periodic_threat"

        target_policy_params: dict[str, Any] = {"goal_position": goal_center}
        if target_policy == "evasive_goal_steering":
            target_policy_params["evasion_acceleration_mps2"] = target_evade_acc

        target = TargetSpec(
            policy_name=target_policy,
            policy_params=target_policy_params,
            sensor_name=target_sensor_name,
        )

        return cls(
            scenario_id=scenario_id,
            chasers=tuple(chasers),
            target=target,
            goal=GoalSpec(center=goal_center),
        )
