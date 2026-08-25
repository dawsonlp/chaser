"""Atmospheric density models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UniformAtmosphere:
    """Uniform still-air atmospheric model."""

    density_kg_m3: float = 1.225

    def __post_init__(self) -> None:
        if self.density_kg_m3 < 0.0:
            raise ValueError("air density must be non-negative")

    def density_at(self, altitude_m: float = 0.0) -> float:
        return self.density_kg_m3

