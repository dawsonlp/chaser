"""Numerical algorithms, root-finding, interpolation, and integration."""

from chaser.numerics.interpolation import CubicHermiteSegment2D
from chaser.numerics.ode import (
    DerivativeFunc2D,
    IntegrationStep2D,
    adaptive_step_2d,
    rk4_step_2d,
)
from chaser.numerics.roots import (
    bisection_root,
    polynomial_value,
    real_polynomial_roots_in_interval,
)

__all__ = [
    "CubicHermiteSegment2D",
    "DerivativeFunc2D",
    "IntegrationStep2D",
    "adaptive_step_2d",
    "bisection_root",
    "polynomial_value",
    "real_polynomial_roots_in_interval",
    "rk4_step_2d",
]

