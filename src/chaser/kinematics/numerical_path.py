"""Continuous adaptive numerical path with memoized dense output."""

from __future__ import annotations

import bisect
from typing import Callable, Sequence

from chaser.kinematics.state import KinematicState
from chaser.math.vec2 import Vec2
from chaser.numerics.interpolation import CubicHermiteSegment2D
from chaser.numerics.ode import DerivativeFunc2D, IntegrationStep2D, adaptive_step_2d


class DenseNumericalPath2D:
    """A time-addressable 2D path evaluated by continuous adaptive numerical integration.

    Implements memoized forward stepping and Hermite spline dense output so root-finding
    algorithms can sample state_at(t) in O(1) without re-integrating.
    """

    def __init__(
        self,
        start_time: float,
        initial_state: KinematicState,
        acceleration_func: DerivativeFunc2D,
        *,
        initial_dt: float = 0.05,
        tolerance: float = 1e-6,
    ) -> None:
        self.start_time = start_time
        self._acc_func = acceleration_func
        self._dt = initial_dt
        self._tolerance = tolerance

        init_acc = initial_state.acceleration
        if init_acc.magnitude == 0.0:
            init_acc = self._acc_func(start_time, initial_state.position, initial_state.velocity)

        first_step = IntegrationStep2D(
            time=start_time,
            position=initial_state.position,
            velocity=initial_state.velocity,
            acceleration=init_acc,
        )

        self._steps: list[IntegrationStep2D] = [first_step]
        self._step_times: list[float] = [start_time]
        self._segments: list[CubicHermiteSegment2D] = []

    def state_at(self, time: float) -> KinematicState:
        if time < self.start_time:
            raise ValueError(f"cannot evaluate path at {time} before start_time {self.start_time}")

        # Integrate forward if requested time is beyond our cached steps
        while self._step_times[-1] < time:
            self._advance_step()

        if math_isclose(time, self.start_time):
            step = self._steps[0]
            return KinematicState(step.position, step.velocity, step.acceleration)

        # Locate interval [t_i, t_{i+1}] containing time
        idx = bisect.bisect_right(self._step_times, time) - 1
        idx = max(0, min(len(self._segments) - 1, idx))
        segment = self._segments[idx]

        return KinematicState(
            position=segment.evaluate_position(time),
            velocity=segment.evaluate_velocity(time),
            acceleration=segment.evaluate_acceleration(time),
        )

    def _advance_step(self) -> None:
        last = self._steps[-1]
        actual_dt, next_pos, next_vel, next_acc, next_dt = adaptive_step_2d(
            self._acc_func,
            last.time,
            last.position,
            last.velocity,
            self._dt,
            tolerance=self._tolerance,
        )
        self._dt = next_dt
        next_time = last.time + actual_dt

        new_step = IntegrationStep2D(
            time=next_time,
            position=next_pos,
            velocity=next_vel,
            acceleration=next_acc,
        )
        segment = CubicHermiteSegment2D(
            t0=last.time,
            t1=next_time,
            p0=last.position,
            p1=next_pos,
            v0=last.velocity,
            v1=next_vel,
        )

        self._steps.append(new_step)
        self._step_times.append(next_time)
        self._segments.append(segment)


def math_isclose(a: float, b: float, tol: float = 1e-12) -> bool:
    return abs(a - b) <= tol

