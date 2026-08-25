"""Two-dimensional vector mathematics."""

from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True, slots=True)
class Vec2:
    x: float
    y: float

    def __add__(self, other: Vec2) -> Vec2:
        return Vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Vec2) -> Vec2:
        return Vec2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> Vec2:
        return Vec2(self.x * scalar, self.y * scalar)

    __rmul__ = __mul__

    def __truediv__(self, scalar: float) -> Vec2:
        return Vec2(self.x / scalar, self.y / scalar)

    def __neg__(self) -> Vec2:
        return Vec2(-self.x, -self.y)

    def dot(self, other: Vec2) -> float:
        return self.x * other.x + self.y * other.y

    def cross_2d(self, other: Vec2) -> float:
        """2D cross product: x1*y2 - y1*x2 (perpendicular scalar)."""
        return self.x * other.y - self.y * other.x

    @property
    def magnitude(self) -> float:
        return math.hypot(self.x, self.y)

    @property
    def magnitude_squared(self) -> float:
        return self.x * self.x + self.y * self.y

    def direction(self) -> float:
        return math.atan2(self.y, self.x)

    def normalized(self) -> Vec2:
        mag = self.magnitude
        if mag == 0.0:
            raise ValueError("cannot normalize zero-length vector")
        return self / mag

    def distance_to(self, other: Vec2) -> float:
        return (self - other).magnitude

    @classmethod
    def from_polar(cls, magnitude: float, direction: float) -> Vec2:
        return cls(
            magnitude * math.cos(direction),
            magnitude * math.sin(direction),
        )


ZERO_VEC2 = Vec2(0.0, 0.0)

