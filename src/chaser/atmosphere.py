"""First-order atmosphere and spherical-drag models (re-exports for backward compatibility)."""

from __future__ import annotations

from chaser.kinematics import KinematicState
from chaser.math import ZERO_VEC2, Vec2
from chaser.physics import (
    ConstantThrustQuadraticDragPath,
    DragModel,
    RigidBody,
    SphereBody,
    SphereQuadraticDrag,
    UniformAtmosphere,
)
from chaser.physics.drag_paths import _log_cosh

__all__ = [
    "ConstantThrustQuadraticDragPath",
    "DragModel",
    "KinematicState",
    "RigidBody",
    "SphereBody",
    "SphereQuadraticDrag",
    "UniformAtmosphere",
    "Vec2",
    "ZERO_VEC2",
    "_log_cosh",
]
