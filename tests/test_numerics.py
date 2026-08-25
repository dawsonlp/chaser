from __future__ import annotations

import math
import unittest

from chaser.math import Vec2
from chaser.numerics import (
    CubicHermiteSegment2D,
    bisection_root,
    polynomial_value,
    real_polynomial_roots_in_interval,
    rk4_step_2d,
)


class NumericsTests(unittest.TestCase):
    def test_polynomial_roots(self) -> None:
        # P(x) = (x - 2)(x - 5) = x^2 - 7x + 10 -> coeffs: (10, -7, 1)
        coeffs = (10.0, -7.0, 1.0)
        self.assertAlmostEqual(polynomial_value(coeffs, 2.0), 0.0)
        self.assertAlmostEqual(polynomial_value(coeffs, 5.0), 0.0)

        roots = real_polynomial_roots_in_interval(coeffs, 0.0, 10.0)
        self.assertEqual(len(roots), 2)
        self.assertAlmostEqual(roots[0], 2.0, places=6)
        self.assertAlmostEqual(roots[1], 5.0, places=6)

    def test_bisection_root(self) -> None:
        # f(x) = x^3 - 8 = 0 -> root = 2.0
        root = bisection_root(lambda x: x**3 - 8.0, 0.0, 4.0)
        self.assertIsNotNone(root)
        self.assertAlmostEqual(root or 0.0, 2.0, places=6)

    def test_hermite_interpolation(self) -> None:
        seg = CubicHermiteSegment2D(
            t0=0.0,
            t1=2.0,
            p0=Vec2(0.0, 0.0),
            p1=Vec2(10.0, 20.0),
            v0=Vec2(5.0, 10.0),
            v1=Vec2(5.0, 10.0),
        )
        # Endpoints
        self.assertEqual(seg.evaluate_position(0.0), Vec2(0.0, 0.0))
        self.assertEqual(seg.evaluate_position(2.0), Vec2(10.0, 20.0))
        self.assertEqual(seg.evaluate_velocity(0.0), Vec2(5.0, 10.0))
        self.assertEqual(seg.evaluate_velocity(2.0), Vec2(5.0, 10.0))

        # Midpoint for constant velocity should be exact midpoint
        p_mid = seg.evaluate_position(1.0)
        self.assertAlmostEqual(p_mid.x, 5.0)
        self.assertAlmostEqual(p_mid.y, 10.0)


if __name__ == "__main__":
    unittest.main()

