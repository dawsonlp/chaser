"""Three-dimensional vector mathematics and 3D readiness stubs."""

from __future__ import annotations

from dataclasses import dataclass
import math

from chaser.math.vec2 import Vec2


@dataclass(frozen=True, slots=True)
class Vec3:
    x: float
    y: float
    z: float

    def __add__(self, other: Vec3) -> Vec3:
        return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: Vec3) -> Vec3:
        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float) -> Vec3:
        return Vec3(self.x * scalar, self.y * scalar, self.z * scalar)

    __rmul__ = __mul__

    def __truediv__(self, scalar: float) -> Vec3:
        return Vec3(self.x / scalar, self.y / scalar, self.z / scalar)

    def __neg__(self) -> Vec3:
        return Vec3(-self.x, -self.y, -self.z)

    def dot(self, other: Vec3) -> float:
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other: Vec3) -> Vec3:
        return Vec3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x,
        )

    @property
    def magnitude(self) -> float:
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)

    @property
    def magnitude_squared(self) -> float:
        return self.x * self.x + self.y * self.y + self.z * self.z

    def normalized(self) -> Vec3:
        mag = self.magnitude
        if mag == 0.0:
            raise ValueError("cannot normalize zero-length vector")
        return self / mag

    def distance_to(self, other: Vec3) -> float:
        return (self - other).magnitude

    def to_vec2_planar(self) -> Vec2:
        """Project onto the 2D XY plane (discarding Z altitude)."""
        return Vec2(self.x, self.y)

    @classmethod
    def from_vec2(cls, vec: Vec2, z: float = 0.0) -> Vec3:
        """Embed a 2D planar vector into 3D space with a specified altitude."""
        return cls(vec.x, vec.y, z)

    @classmethod
    def from_spherical(cls, radius: float, azimuth_rad: float, elevation_rad: float) -> Vec3:
        """Construct from spherical coordinates (radius, azimuth in XY, elevation from XY)."""
        cos_el = math.cos(elevation_rad)
        return cls(
            radius * cos_el * math.cos(azimuth_rad),
            radius * cos_el * math.sin(azimuth_rad),
            radius * math.sin(elevation_rad),
        )


ZERO_VEC3 = Vec3(0.0, 0.0, 0.0)

