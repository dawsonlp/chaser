"""Coordinate transforms and projection utilities."""

from __future__ import annotations

import math
from chaser.math.vec2 import Vec2
from chaser.math.vec3 import Vec3


def rotate_vec2(vec: Vec2, angle_rad: float) -> Vec2:
    """Rotate a 2D vector by angle_rad counterclockwise."""
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    return Vec2(vec.x * cos_a - vec.y * sin_a, vec.x * sin_a + vec.y * cos_a)


def heading_to_vec2(heading_rad: float) -> Vec2:
    """Convert heading angle (radians) to unit direction vector."""
    return Vec2(math.cos(heading_rad), math.sin(heading_rad))

