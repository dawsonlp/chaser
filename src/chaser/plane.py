"""Two-dimensional geometry, paths, actuators, sensors, and contact finding."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable, Mapping, Protocol


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

    def dot(self, other: Vec2) -> float:
        return self.x * other.x + self.y * other.y

    @property
    def magnitude(self) -> float:
        return math.hypot(self.x, self.y)

    def direction(self) -> float:
        return math.atan2(self.y, self.x)

    @classmethod
    def from_polar(cls, magnitude: float, direction: float) -> Vec2:
        return cls(
            magnitude * math.cos(direction),
            magnitude * math.sin(direction),
        )


ZERO_VEC2 = Vec2(0.0, 0.0)


@dataclass(frozen=True, slots=True)
class KinematicState:
    position: Vec2
    velocity: Vec2
    acceleration: Vec2 = ZERO_VEC2


class Path2D(Protocol):
    """A time-addressable path in the first model set."""

    start_time: float

    def state_at(self, time: float) -> KinematicState: ...


@dataclass(frozen=True, slots=True)
class ConstantAccelerationPath:
    """An exact path valid while acceleration remains constant."""

    start_time: float
    initial: KinematicState

    def state_at(self, time: float) -> KinematicState:
        if time < self.start_time:
            raise ValueError("cannot evaluate a path before its start")
        elapsed = time - self.start_time
        return KinematicState(
            position=(
                self.initial.position
                + self.initial.velocity * elapsed
                + self.initial.acceleration * (0.5 * elapsed * elapsed)
            ),
            velocity=self.initial.velocity + self.initial.acceleration * elapsed,
            acceleration=self.initial.acceleration,
        )


@dataclass(frozen=True, slots=True)
class ActuatorDefinition:
    name: str
    minimum: float
    maximum: float

    def validate(self, value: float) -> None:
        if not math.isfinite(value):
            raise ValueError(f"{self.name} must be finite")
        if value < self.minimum or value > self.maximum:
            raise ValueError(
                f"{self.name}={value} is outside [{self.minimum}, {self.maximum}]"
            )


@dataclass(frozen=True, slots=True)
class ActuatorSet:
    """The current values of the actuators belonging to one object."""

    definitions: Mapping[str, ActuatorDefinition]
    values: Mapping[str, float]

    def __post_init__(self) -> None:
        if set(self.definitions) != set(self.values):
            raise ValueError("every actuator must have exactly one current value")
        for name, value in self.values.items():
            self.definitions[name].validate(value)

    def with_changes(self, changes: Mapping[str, float]) -> ActuatorSet:
        unknown = set(changes) - set(self.definitions)
        if unknown:
            raise ValueError(f"unknown actuators: {sorted(unknown)!r}")

        updated = dict(self.values)
        for name, value in changes.items():
            self.definitions[name].validate(value)
            updated[name] = value
        return ActuatorSet(self.definitions, updated)


@dataclass(frozen=True, slots=True)
class PlanarThrustResponse:
    """Scenario-specific interpretation of two actuator values."""

    magnitude_actuator: str = "thrust_acceleration"
    direction_actuator: str = "thrust_direction"

    def acceleration(self, actuators: ActuatorSet) -> Vec2:
        return Vec2.from_polar(
            actuators.values[self.magnitude_actuator],
            actuators.values[self.direction_actuator],
        )


@dataclass(frozen=True, slots=True)
class VisualObservation:
    observed_at: float
    observer_id: str
    target_id: str
    relative_position: Vec2
    relative_velocity: Vec2


@dataclass(frozen=True, slots=True)
class DirectVisualSensor:
    """Initial ideal sensor: reports exact visible target motion at an event time."""

    def observe(
        self,
        *,
        time: float,
        observer_id: str,
        target_id: str,
        observer_path: Path2D,
        target_path: Path2D,
    ) -> VisualObservation:
        observer_state = observer_path.state_at(time)
        target_state = target_path.state_at(time)
        return VisualObservation(
            observed_at=time,
            observer_id=observer_id,
            target_id=target_id,
            relative_position=target_state.position - observer_state.position,
            relative_velocity=target_state.velocity - observer_state.velocity,
        )


def polynomial_value(coefficients: Iterable[float], value: float) -> float:
    result = 0.0
    for coefficient in reversed(tuple(coefficients)):
        result = result * value + coefficient
    return result


def real_polynomial_roots_in_interval(
    coefficients: Iterable[float],
    lower: float,
    upper: float,
    *,
    time_tolerance: float = 1e-10,
) -> tuple[float, ...]:
    """Isolate real roots recursively using derivative critical points."""

    if lower > upper:
        raise ValueError("lower bound must not exceed upper bound")

    original = list(coefficients)
    if not original:
        return ()
    scale = max(1.0, *(abs(value) for value in original))
    coefficient_tolerance = 1e-14 * scale
    while len(original) > 1 and abs(original[-1]) <= coefficient_tolerance:
        original.pop()

    degree = len(original) - 1
    if degree == 0:
        return ()
    if degree == 1:
        root = -original[0] / original[1]
        if lower - time_tolerance <= root <= upper + time_tolerance:
            return (min(upper, max(lower, root)),)
        return ()

    derivative = [index * original[index] for index in range(1, len(original))]
    critical = real_polynomial_roots_in_interval(
        derivative,
        lower,
        upper,
        time_tolerance=time_tolerance,
    )
    points = [lower, *critical, upper]
    value_scale = max(
        1.0,
        sum(abs(coefficient) * max(1.0, abs(upper)) ** index for index, coefficient in enumerate(original)),
    )
    value_tolerance = 1e-10 * value_scale
    roots: list[float] = []

    def add_root(root: float) -> None:
        if not roots or abs(root - roots[-1]) > time_tolerance * 10.0:
            roots.append(root)

    for point in points:
        if abs(polynomial_value(original, point)) <= value_tolerance:
            add_root(point)

    for left, right in zip(points, points[1:]):
        left_value = polynomial_value(original, left)
        right_value = polynomial_value(original, right)
        if left_value == 0.0 or right_value == 0.0 or left_value * right_value > 0.0:
            continue
        lo = left
        hi = right
        for _ in range(100):
            mid = (lo + hi) * 0.5
            mid_value = polynomial_value(original, mid)
            if hi - lo <= time_tolerance:
                break
            if left_value * mid_value <= 0.0:
                hi = mid
                right_value = mid_value
            else:
                lo = mid
                left_value = mid_value
        add_root((lo + hi) * 0.5)

    return tuple(sorted(roots))


def earliest_circle_contact(
    first: Path2D,
    first_radius: float,
    second: Path2D,
    second_radius: float,
    *,
    from_time: float,
    through_time: float,
) -> float | None:
    """Return the first contact time for two circular paths.

    Constant-acceleration pairs use an exact polynomial. Other compatible paths
    use interval bracketing followed by bisection. That search locates the next
    event; its intervals are not simulation time steps.
    """

    if first_radius < 0.0 or second_radius < 0.0:
        raise ValueError("circle radii must be non-negative")
    if from_time > through_time:
        return None
    if math.isclose(from_time, through_time):
        offset = first.state_at(from_time).position - second.state_at(from_time).position
        if offset.dot(offset) <= (first_radius + second_radius) ** 2:
            return from_time
        return None

    if not isinstance(first, ConstantAccelerationPath) or not isinstance(
        second, ConstantAccelerationPath
    ):
        return _earliest_circle_contact_by_bracketing(
            first,
            first_radius,
            second,
            second_radius,
            from_time=from_time,
            through_time=through_time,
        )

    first_state = first.state_at(from_time)
    second_state = second.state_at(from_time)
    relative_position = first_state.position - second_state.position
    relative_velocity = first_state.velocity - second_state.velocity
    half_relative_acceleration = (
        first_state.acceleration - second_state.acceleration
    ) * 0.5
    contact_radius = first_radius + second_radius

    if relative_position.dot(relative_position) <= contact_radius * contact_radius:
        return from_time

    coefficients = (
        relative_position.dot(relative_position) - contact_radius * contact_radius,
        2.0 * relative_position.dot(relative_velocity),
        relative_velocity.dot(relative_velocity)
        + 2.0 * relative_position.dot(half_relative_acceleration),
        2.0 * relative_velocity.dot(half_relative_acceleration),
        half_relative_acceleration.dot(half_relative_acceleration),
    )
    duration = through_time - from_time
    roots = real_polynomial_roots_in_interval(coefficients, 0.0, duration)
    for root in roots:
        if root >= -1e-9:
            return from_time + max(0.0, root)
    return None


def _earliest_circle_contact_by_bracketing(
    first: Path2D,
    first_radius: float,
    second: Path2D,
    second_radius: float,
    *,
    from_time: float,
    through_time: float,
    interval_count: int = 16_384,
    time_tolerance: float = 1e-9,
) -> float | None:
    contact_radius_squared = (first_radius + second_radius) ** 2

    def separation(time: float) -> float:
        offset = first.state_at(time).position - second.state_at(time).position
        return offset.dot(offset) - contact_radius_squared

    left = from_time
    if separation(left) <= 0.0:
        return left

    interval_width = (through_time - from_time) / interval_count
    for index in range(1, interval_count + 1):
        right = from_time + interval_width * index
        right_value = separation(right)
        if right_value <= 0.0:
            for _ in range(80):
                if right - left <= time_tolerance:
                    break
                middle = (left + right) * 0.5
                if separation(middle) <= 0.0:
                    right = middle
                else:
                    left = middle
            return (left + right) * 0.5
        left = right
    return None
