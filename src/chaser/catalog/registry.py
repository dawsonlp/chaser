"""Component catalog for dynamic discovery and construction of policies, sensors, and physical bodies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from chaser.components.policies.base import DecisionPolicy
from chaser.components.policies.cooperative.dual_pincer import DualPincerPolicy
from chaser.components.policies.intercept.adaptive import AdaptiveInterceptPolicy
from chaser.components.policies.intercept.pure_pursuit import PurePursuitPolicy
from chaser.components.policies.intercept.quadratic_drag import (
    QuadraticDragInterceptDecision,
)
from chaser.components.policies.target.evasive import EvasiveGoalSteeringPolicy
from chaser.components.sensors.base import Sensor
from chaser.components.sensors.periodic import PeriodicThreatSensor
from chaser.components.sensors.visual import DirectVisualSensor
from chaser.math.vec2 import Vec2
from chaser.physics.aerodynamics import SphereQuadraticDrag
from chaser.physics.atmosphere import UniformAtmosphere
from chaser.physics.bodies import SphereBody


@dataclass(frozen=True, slots=True)
class StraightLinePolicy:
    """Passive policy that maintains constant heading with zero thrust."""

    def choose_actuator_changes(self, observation: Any) -> Mapping[str, float]:
        return {"thrust_acceleration": 0.0, "thrust_direction": 0.0}


class PolicyCatalog:
    _factories: dict[str, tuple[str, Callable[..., DecisionPolicy]]] = {}

    @classmethod
    def register(
        cls,
        name: str,
        description: str,
        factory: Callable[..., DecisionPolicy],
    ) -> None:
        cls._factories[name] = (description, factory)

    @classmethod
    def list_policies(cls) -> dict[str, str]:
        return {name: desc for name, (desc, _) in cls._factories.items()}

    @classmethod
    def create(cls, name: str, **kwargs: Any) -> DecisionPolicy:
        if name not in cls._factories:
            raise KeyError(
                f"Unknown policy {name!r}. Available: {list(cls._factories.keys())}"
            )
        _, factory = cls._factories[name]
        return factory(**kwargs)


class SensorCatalog:
    _factories: dict[str, tuple[str, Callable[..., Sensor]]] = {}

    @classmethod
    def register(
        cls,
        name: str,
        description: str,
        factory: Callable[..., Sensor],
    ) -> None:
        cls._factories[name] = (description, factory)

    @classmethod
    def list_sensors(cls) -> dict[str, str]:
        return {name: desc for name, (desc, _) in cls._factories.items()}

    @classmethod
    def create(cls, name: str, **kwargs: Any) -> Sensor:
        if name not in cls._factories:
            raise KeyError(
                f"Unknown sensor {name!r}. Available: {list(cls._factories.keys())}"
            )
        _, factory = cls._factories[name]
        return factory(**kwargs)


# Register default policies
PolicyCatalog.register(
    "straight_line",
    "Passive target maintaining constant velocity without maneuvers.",
    lambda **kwargs: StraightLinePolicy(),
)

PolicyCatalog.register(
    "quadratic_drag",
    "Drag-compensated optimal lead intercept guidance.",
    lambda maximum_acceleration=500.0, deadline=10.0, drag=None, **kwargs: (
        QuadraticDragInterceptDecision(
            maximum_acceleration=maximum_acceleration,
            deadline=deadline,
            drag=drag
            or SphereQuadraticDrag(
                SphereBody(0.1, 7850.0), UniformAtmosphere(1.225), 0.47
            ),
        )
    ),
)

PolicyCatalog.register(
    "pure_pursuit",
    "Direct pure pursuit steering directly at the target's current position.",
    lambda maximum_acceleration=500.0, **kwargs: PurePursuitPolicy(
        maximum_acceleration=maximum_acceleration
    ),
)

PolicyCatalog.register(
    "dual_pincer",
    "Cooperative pincer guidance calculating independent lead intercepts from each flank.",
    lambda role="lead", maximum_acceleration=500.0, deadline=10.0, drag=None, time_delay_offset_s=0.0, **kwargs: (
        DualPincerPolicy(
            role=role,
            maximum_acceleration=maximum_acceleration,
            deadline=deadline,
            drag=drag
            or SphereQuadraticDrag(
                SphereBody(0.1, 7850.0), UniformAtmosphere(1.225), 0.47
            ),
            time_delay_offset_s=time_delay_offset_s,
        )
    ),
)

PolicyCatalog.register(
    "adaptive_intercept",
    "Recalculates optimal drag-compensated intercept whenever target maneuvers.",
    lambda maximum_acceleration=500.0, deadline=10.0, drag=None, **kwargs: (
        AdaptiveInterceptPolicy(
            maximum_acceleration=maximum_acceleration,
            deadline=deadline,
            drag=drag
            or SphereQuadraticDrag(
                SphereBody(0.1, 7850.0), UniformAtmosphere(1.225), 0.47
            ),
        )
    ),
)

PolicyCatalog.register(
    "evasive_goal_steering",
    "Active threat detection, lateral dodge burst, and corrective goal re-targeting.",
    lambda goal_position=Vec2(10_200.0, 0.0), evasion_acceleration_mps2=350.0, correction_acceleration_mps2=300.0, threat_distance_threshold_m=4500.0, evasion_duration_s=1.2, nominal_speed_mps=1000.0, **kwargs: (
        EvasiveGoalSteeringPolicy(
            goal_position=goal_position,
            evasion_acceleration_mps2=evasion_acceleration_mps2,
            correction_acceleration_mps2=correction_acceleration_mps2,
            threat_distance_threshold_m=threat_distance_threshold_m,
            evasion_duration_s=evasion_duration_s,
            nominal_speed_mps=nominal_speed_mps,
        )
    ),
)

# Register default sensors
SensorCatalog.register(
    "direct_visual",
    "Continuous direct observation of target position and relative velocity.",
    lambda **kwargs: DirectVisualSensor(),
)

SensorCatalog.register(
    "periodic_threat",
    "Periodic scanning sensor measuring threat closing speed and distance.",
    lambda scan_interval_s=0.25, detection_range_m=6000.0, threat_closing_speed_threshold_mps=100.0, **kwargs: (
        PeriodicThreatSensor(
            scan_interval_s=scan_interval_s,
            detection_range_m=detection_range_m,
            threat_closing_speed_threshold_mps=threat_closing_speed_threshold_mps,
        )
    ),
)
