"""Dynamic lead intercept policy accounting for velocity vector updates, drag, and maneuvers."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping

from chaser.components.sensors.base import VisualObservation
from chaser.math.vec2 import Vec2
from chaser.physics.aerodynamics import SphereQuadraticDrag


@dataclass(frozen=True, slots=True)
class DynamicLeadInterceptPolicy:
    """Computes required thrust vector accounting for non-zero chaser velocity and aerodynamic drag."""

    maximum_acceleration: float = 500.0
    deadline: float = 15.0
    drag: SphereQuadraticDrag | None = None

    def choose_actuator_changes(
        self,
        observation: VisualObservation,
    ) -> Mapping[str, float]:
        r = observation.relative_position  # p_target - p_chaser
        v_target = observation.observer_velocity + observation.relative_velocity
        v_chaser = observation.observer_velocity

        k = self.drag.drag_factor_per_m if self.drag else 0.000305
        a_max = self.maximum_acceleration
        alpha = math.sqrt(k * a_max)

        def reachable_distance(tau: float) -> float:
            if v_chaser.magnitude < 1e-4:
                # Analytic exact distance under drag from rest: s(tau) = (1/k) * ln(cosh(tau * alpha))
                x = tau * alpha
                if x > 20.0:
                    return (x - math.log(2.0)) / k
                return math.log(math.cosh(x)) / k

            # With non-zero initial speed:
            v0_proj = v_chaser.dot((r + v_target * tau).normalized()) if (r + v_target * tau).magnitude > 1e-3 else 0.0
            # Numerical integration of 1D reach: dv/dt = a_max - k*v^2
            # v(tau) = v_term * tanh(alpha * tau + arctanh(v0/v_term))
            v_term = math.sqrt(a_max / k)
            v0_clamped = max(-0.99 * v_term, min(0.99 * v_term, v0_proj))
            c0 = math.atanh(v0_clamped / v_term)
            x0 = c0
            x1 = alpha * tau + c0
            # Integral of v_term * tanh(x) dx / alpha = (v_term / alpha) * [ln(cosh(x1)) - ln(cosh(x0))] = (1/k) * ln(cosh(x1)/cosh(x0))
            if x1 > 20.0:
                ln_cosh_x1 = x1 - math.log(2.0)
            else:
                ln_cosh_x1 = math.log(math.cosh(x1))
            ln_cosh_x0 = math.log(math.cosh(x0))
            return (ln_cosh_x1 - ln_cosh_x0) / k

        # Solve reachable_distance(tau) == |r + v_target * tau|
        best_tau = None
        t_prev = 0.05
        f_prev = reachable_distance(t_prev) - (r + v_target * t_prev).magnitude
        steps = 200
        dt = (self.deadline - 0.05) / steps

        for i in range(1, steps + 1):
            t_curr = 0.05 + i * dt
            f_curr = reachable_distance(t_curr) - (r + v_target * t_curr).magnitude
            if f_prev * f_curr <= 0.0 or f_curr >= 0.0:
                lo, hi = t_prev, t_curr
                for _ in range(25):
                    mid = (lo + hi) / 2.0
                    f_mid = reachable_distance(mid) - (r + v_target * mid).magnitude
                    if f_mid >= 0.0:
                        hi = mid
                    else:
                        lo = mid
                best_tau = (lo + hi) / 2.0
                break
            t_prev, f_prev = t_curr, f_curr

        if best_tau is not None:
            future_target_rel = r + v_target * best_tau
            if v_chaser.magnitude < 1e-4:
                thrust_dir = future_target_rel.direction()
            else:
                # Desired velocity vector to intercept at future_target_rel in best_tau
                desired_vel = future_target_rel * (1.0 / best_tau)
                delta_v = desired_vel - v_chaser
                thrust_dir = delta_v.direction() if delta_v.magnitude > 1e-3 else future_target_rel.direction()

            return {
                "thrust_acceleration": a_max,
                "thrust_direction": thrust_dir,
            }

        # Fallback: direct thrust toward relative position + lead
        fallback_dir = (r + v_target * min(2.0, self.deadline)).direction()
        return {
            "thrust_acceleration": a_max,
            "thrust_direction": fallback_dir,
        }

