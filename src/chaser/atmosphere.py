"""Explicit first-order atmosphere and spherical-drag models."""

from __future__ import annotations

from dataclasses import dataclass
import math

from chaser.plane import KinematicState, Vec2, ZERO_VEC2


@dataclass(frozen=True, slots=True)
class SphereBody:
    diameter_m: float
    material_density_kg_m3: float

    def __post_init__(self) -> None:
        if self.diameter_m <= 0.0 or self.material_density_kg_m3 <= 0.0:
            raise ValueError("sphere diameter and material density must be positive")

    @property
    def radius_m(self) -> float:
        return self.diameter_m * 0.5

    @property
    def volume_m3(self) -> float:
        return (4.0 / 3.0) * math.pi * self.radius_m**3

    @property
    def mass_kg(self) -> float:
        return self.volume_m3 * self.material_density_kg_m3

    @property
    def frontal_area_m2(self) -> float:
        return math.pi * self.radius_m**2


@dataclass(frozen=True, slots=True)
class UniformAtmosphere:
    density_kg_m3: float = 1.225

    def __post_init__(self) -> None:
        if self.density_kg_m3 < 0.0:
            raise ValueError("air density must be non-negative")


@dataclass(frozen=True, slots=True)
class SphereQuadraticDrag:
    """D = 1/2 rho Cd A v^2 for a sphere in still, uniform air."""

    body: SphereBody
    atmosphere: UniformAtmosphere
    drag_coefficient: float = 0.47

    def __post_init__(self) -> None:
        if self.drag_coefficient < 0.0:
            raise ValueError("drag coefficient must be non-negative")

    @property
    def drag_factor_per_m(self) -> float:
        """Return k in dv/dt = thrust_acceleration - k*v^2."""

        return (
            0.5
            * self.atmosphere.density_kg_m3
            * self.drag_coefficient
            * self.body.frontal_area_m2
            / self.body.mass_kg
        )

    def drag_force_n(self, speed_mps: float) -> float:
        if speed_mps < 0.0:
            raise ValueError("speed must be non-negative")
        return (
            0.5
            * self.atmosphere.density_kg_m3
            * self.drag_coefficient
            * self.body.frontal_area_m2
            * speed_mps**2
        )


@dataclass(frozen=True, slots=True)
class ConstantThrustQuadraticDragPath:
    """Analytic path from rest under constant thrust and quadratic drag.

    Thrust direction, air density, and drag coefficient remain fixed for the
    lifetime of this path. Gravity is outside this horizontal-plane model.
    """

    start_time: float
    initial_position: Vec2
    thrust_acceleration: Vec2
    drag: SphereQuadraticDrag

    def state_at(self, time: float) -> KinematicState:
        if time < self.start_time:
            raise ValueError("cannot evaluate a path before its start")
        elapsed = time - self.start_time
        thrust = self.thrust_acceleration.magnitude
        if thrust == 0.0:
            return KinematicState(self.initial_position, ZERO_VEC2, ZERO_VEC2)

        direction = self.thrust_acceleration / thrust
        drag_factor = self.drag.drag_factor_per_m
        if drag_factor == 0.0:
            return KinematicState(
                self.initial_position + direction * (0.5 * thrust * elapsed**2),
                direction * (thrust * elapsed),
                self.thrust_acceleration,
            )

        rate = math.sqrt(thrust * drag_factor)
        terminal_speed = math.sqrt(thrust / drag_factor)
        scaled_time = rate * elapsed
        speed = terminal_speed * math.tanh(scaled_time)
        distance = _log_cosh(scaled_time) / drag_factor
        net_acceleration = thrust * (1.0 - math.tanh(scaled_time) ** 2)
        return KinematicState(
            self.initial_position + direction * distance,
            direction * speed,
            direction * net_acceleration,
        )

    def distance_after(self, elapsed: float) -> float:
        if elapsed < 0.0:
            raise ValueError("elapsed time must be non-negative")
        return (
            self.state_at(self.start_time + elapsed).position - self.initial_position
        ).magnitude


def _log_cosh(value: float) -> float:
    absolute = abs(value)
    return absolute + math.log1p(math.exp(-2.0 * absolute)) - math.log(2.0)
