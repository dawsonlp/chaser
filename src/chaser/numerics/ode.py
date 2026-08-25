"""Adaptive Runge-Kutta ODE numerical integrator."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence
import math

from chaser.math.vec2 import Vec2


@dataclass(frozen=True, slots=True)
class IntegrationStep2D:
    time: float
    position: Vec2
    velocity: Vec2
    acceleration: Vec2


# Derivative function: (t, pos, vel) -> acceleration
DerivativeFunc2D = Callable[[float, Vec2, Vec2], Vec2]


def rk4_step_2d(
    func: DerivativeFunc2D,
    t: float,
    pos: Vec2,
    vel: Vec2,
    dt: float,
) -> tuple[Vec2, Vec2, Vec2]:
    """Single standard Runge-Kutta 4th order step.
    Returns (new_pos, new_vel, end_acc)."""
    k1_v = vel
    k1_a = func(t, pos, vel)

    k2_pos = pos + k1_v * (0.5 * dt)
    k2_vel = vel + k1_a * (0.5 * dt)
    k2_v = k2_vel
    k2_a = func(t + 0.5 * dt, k2_pos, k2_vel)

    k3_pos = pos + k2_v * (0.5 * dt)
    k3_vel = vel + k2_a * (0.5 * dt)
    k3_v = k3_vel
    k3_a = func(t + 0.5 * dt, k3_pos, k3_vel)

    k4_pos = pos + k3_v * dt
    k4_vel = vel + k3_a * dt
    k4_v = k4_vel
    k4_a = func(t + dt, k4_pos, k4_vel)

    next_pos = pos + (k1_v + 2.0 * k2_v + 2.0 * k3_v + k4_v) * (dt / 6.0)
    next_vel = vel + (k1_a + 2.0 * k2_a + 2.0 * k3_a + k4_a) * (dt / 6.0)
    next_acc = func(t + dt, next_pos, next_vel)

    return next_pos, next_vel, next_acc


def adaptive_step_2d(
    func: DerivativeFunc2D,
    t: float,
    pos: Vec2,
    vel: Vec2,
    dt: float,
    *,
    tolerance: float = 1e-6,
) -> tuple[float, Vec2, Vec2, Vec2, float]:
    """Take an adaptive step using step doubling error estimation.
    Returns (actual_dt, next_pos, next_vel, next_acc, suggested_next_dt)."""
    current_dt = dt

    for _ in range(20):
        # Full step of size current_dt
        pos_full, vel_full, _ = rk4_step_2d(func, t, pos, vel, current_dt)

        # Two half steps of size current_dt / 2
        half_dt = current_dt * 0.5
        pos_half, vel_half, _ = rk4_step_2d(func, t, pos, vel, half_dt)
        pos_two_half, vel_two_half, acc_two_half = rk4_step_2d(
            func, t + half_dt, pos_half, vel_half, half_dt
        )

        # Error estimation
        pos_err = (pos_two_half - pos_full).magnitude
        vel_err = (vel_two_half - vel_full).magnitude
        error = max(pos_err, vel_err)

        if error <= tolerance or current_dt <= 1e-8:
            # Richardson extrapolation for position and velocity
            extrapolated_pos = pos_two_half + (pos_two_half - pos_full) / 15.0
            extrapolated_vel = vel_two_half + (vel_two_half - vel_full) / 15.0
            next_acc = func(t + current_dt, extrapolated_pos, extrapolated_vel)

            factor = 0.9 * (tolerance / max(error, 1e-15)) ** 0.2
            suggested_dt = max(1e-6, min(current_dt * 2.0, current_dt * max(0.2, min(5.0, factor))))
            return current_dt, extrapolated_pos, extrapolated_vel, next_acc, suggested_dt
        else:
            # Reject step and decrease dt
            factor = max(0.1, 0.9 * (tolerance / error) ** 0.25)
            current_dt = max(1e-8, current_dt * factor)

    return current_dt, pos_two_half, vel_two_half, acc_two_half, current_dt

