from __future__ import annotations

import math
import unittest

from chaser.kinematics import (
    ConstantAccelerationPath,
    DenseNumericalPath2D,
    KinematicState,
)
from chaser.math import ZERO_VEC2, Vec2
from chaser.physics import (
    ConstantThrustQuadraticDragPath,
    SphereBody,
    SphereQuadraticDrag,
    UniformAtmosphere,
)


class DenseNumericalPathTests(unittest.TestCase):
    def test_numerical_path_matches_constant_acceleration(self) -> None:
        initial = KinematicState(
            position=Vec2(100.0, 200.0),
            velocity=Vec2(10.0, -5.0),
            acceleration=Vec2(2.0, 3.0),
        )
        analytic = ConstantAccelerationPath(0.0, initial)

        def const_acc_func(t: float, pos: Vec2, vel: Vec2) -> Vec2:
            return Vec2(2.0, 3.0)

        numerical = DenseNumericalPath2D(0.0, initial, const_acc_func)

        for t in [0.0, 0.5, 1.0, 2.5, 5.0]:
            state_a = analytic.state_at(t)
            state_n = numerical.state_at(t)
            self.assertAlmostEqual(state_a.position.x, state_n.position.x, places=4)
            self.assertAlmostEqual(state_a.position.y, state_n.position.y, places=4)
            self.assertAlmostEqual(state_a.velocity.x, state_n.velocity.x, places=4)
            self.assertAlmostEqual(state_a.velocity.y, state_n.velocity.y, places=4)

    def test_numerical_path_matches_drag_path(self) -> None:
        body = SphereBody(0.1, 7850.0)
        drag = SphereQuadraticDrag(body, UniformAtmosphere(1.225), 0.47)
        thrust = Vec2(500.0, 0.0)

        analytic = ConstantThrustQuadraticDragPath(
            start_time=0.0,
            initial_position=ZERO_VEC2,
            thrust_acceleration=thrust,
            drag=drag,
        )

        k = drag.drag_factor_per_m

        def drag_acc_func(t: float, pos: Vec2, vel: Vec2) -> Vec2:
            speed = vel.magnitude
            drag_decel = vel * (k * speed)
            return thrust - drag_decel

        numerical = DenseNumericalPath2D(
            0.0,
            KinematicState(ZERO_VEC2, ZERO_VEC2, thrust),
            drag_acc_func,
            tolerance=1e-7,
        )

        for t in [0.1, 0.5, 1.0, 2.0, 4.0]:
            state_a = analytic.state_at(t)
            state_n = numerical.state_at(t)
            self.assertAlmostEqual(state_a.position.x, state_n.position.x, delta=0.05)
            self.assertAlmostEqual(state_a.velocity.x, state_n.velocity.x, delta=0.05)


if __name__ == "__main__":
    unittest.main()

