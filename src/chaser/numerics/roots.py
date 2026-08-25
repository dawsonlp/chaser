"""Numerical root finding and polynomial algorithms."""

from __future__ import annotations

from typing import Callable, Iterable
import math


def polynomial_value(coefficients: Iterable[float], value: float) -> float:
    """Evaluate polynomial sum_{i} c_i * x^i using Horner's method."""
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


def bisection_root(
    func: Callable[[float], float],
    lower: float,
    upper: float,
    *,
    time_tolerance: float = 1e-9,
    max_iterations: int = 100,
) -> float | None:
    """Find a root of func in [lower, upper] using bisection."""
    if lower > upper:
        raise ValueError("lower bound must not exceed upper bound")
    
    f_lower = func(lower)
    f_upper = func(upper)

    if abs(f_lower) <= 1e-12:
        return lower
    if abs(f_upper) <= 1e-12:
        return upper
    if f_lower * f_upper > 0.0:
        return None

    lo, hi = lower, upper
    for _ in range(max_iterations):
        mid = (lo + hi) * 0.5
        f_mid = func(mid)
        if hi - lo <= time_tolerance or abs(f_mid) <= 1e-12:
            return mid
        if f_lower * f_mid <= 0.0:
            hi = mid
            f_upper = f_mid
        else:
            lo = mid
            f_lower = f_mid
    return (lo + hi) * 0.5
