"""Kinematic state representations in 2D and 3D."""

from __future__ import annotations

from dataclasses import dataclass

from chaser.math.vec2 import ZERO_VEC2, Vec2
from chaser.math.vec3 import ZERO_VEC3, Vec3


@dataclass(frozen=True, slots=True)
class KinematicState:
    """2D Kinematic state (position, velocity, acceleration)."""

    position: Vec2
    velocity: Vec2
    acceleration: Vec2 = ZERO_VEC2


@dataclass(frozen=True, slots=True)
class KinematicState3D:
    """3D Kinematic state (position, velocity, acceleration)."""

    position: Vec3
    velocity: Vec3
    acceleration: Vec3 = ZERO_VEC3

    def to_2d_planar(self) -> KinematicState:
        return KinematicState(
            position=self.position.to_vec2_planar(),
            velocity=self.velocity.to_vec2_planar(),
            acceleration=self.acceleration.to_vec2_planar(),
        )
