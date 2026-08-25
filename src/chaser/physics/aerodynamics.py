"""Aerodynamic drag models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from chaser.physics.atmosphere import UniformAtmosphere
from chaser.physics.bodies import SphereBody


class DragModel(Protocol):
    @property
    def drag_factor_per_m(self) -> float: ...

    def drag_force_n(self, speed_mps: float) -> float: ...


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

