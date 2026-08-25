"""Physical body definitions and mass properties."""

from __future__ import annotations

from dataclasses import dataclass
import math


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
class RigidBody:
    """General rigid body mass and aerodynamic properties (3D readiness)."""

    mass_kg: float
    reference_area_m2: float
    collision_radius_m: float

    def __post_init__(self) -> None:
        if self.mass_kg <= 0.0 or self.reference_area_m2 <= 0.0 or self.collision_radius_m <= 0.0:
            raise ValueError("mass, area, and collision radius must be positive")

