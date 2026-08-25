"""Two-dimensional geometry, paths, actuators, sensors, and contact finding (re-exports for backward compatibility)."""

from __future__ import annotations

from chaser.collision import (
    CircleContactDetector,
    earliest_circle_contact,
)
from chaser.collision.circle_contact import _earliest_circle_contact_by_bracketing
from chaser.components.actuators import (
    ActuatorDefinition,
    ActuatorResponse,
    ActuatorSet,
    PlanarThrustResponse,
)
from chaser.components.sensors import (
    DirectVisualSensor,
    Sensor,
    VisualObservation,
)
from chaser.kinematics import (
    ConstantAccelerationPath,
    DenseNumericalPath2D,
    KinematicState,
    Path,
    Path2D,
)
from chaser.math import (
    ZERO_VEC2,
    Vec2,
)
from chaser.numerics import (
    polynomial_value,
    real_polynomial_roots_in_interval,
)

__all__ = [
    "ZERO_VEC2",
    "ActuatorDefinition",
    "ActuatorResponse",
    "ActuatorSet",
    "CircleContactDetector",
    "ConstantAccelerationPath",
    "DenseNumericalPath2D",
    "DirectVisualSensor",
    "KinematicState",
    "Path",
    "Path2D",
    "PlanarThrustResponse",
    "Sensor",
    "Vec2",
    "VisualObservation",
    "_earliest_circle_contact_by_bracketing",
    "earliest_circle_contact",
    "polynomial_value",
    "real_polynomial_roots_in_interval",
]
