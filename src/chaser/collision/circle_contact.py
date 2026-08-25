"""Planar circular contact detection between moving paths."""

from __future__ import annotations

import math

from chaser.kinematics.constant_acceleration import ConstantAccelerationPath
from chaser.kinematics.path import Path2D
from chaser.numerics.roots import real_polynomial_roots_in_interval


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


class CircleContactDetector:
    """Contact detector implementation for circular paths."""

    def earliest_contact(
        self,
        first_path: Path2D,
        first_radius: float,
        second_path: Path2D,
        second_radius: float,
        *,
        from_time: float,
        through_time: float,
    ) -> float | None:
        return earliest_circle_contact(
            first_path,
            first_radius,
            second_path,
            second_radius,
            from_time=from_time,
            through_time=through_time,
        )

