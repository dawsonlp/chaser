from __future__ import annotations

import math
import unittest

from chaser.math import ZERO_VEC2, ZERO_VEC3, Vec2, Vec3, heading_to_vec2, rotate_vec2


class MathTests(unittest.TestCase):
    def test_vec2_basic_operations(self) -> None:
        v1 = Vec2(3.0, 4.0)
        v2 = Vec2(1.0, 2.0)

        self.assertEqual(v1 + v2, Vec2(4.0, 6.0))
        self.assertEqual(v1 - v2, Vec2(2.0, 2.0))
        self.assertEqual(v1 * 2.0, Vec2(6.0, 8.0))
        self.assertEqual(2.0 * v1, Vec2(6.0, 8.0))
        self.assertEqual(v1 / 2.0, Vec2(1.5, 2.0))
        self.assertEqual(-v1, Vec2(-3.0, -4.0))

        self.assertAlmostEqual(v1.magnitude, 5.0)
        self.assertAlmostEqual(v1.magnitude_squared, 25.0)
        self.assertAlmostEqual(v1.dot(v2), 3.0 * 1.0 + 4.0 * 2.0)
        self.assertAlmostEqual(v1.cross_2d(v2), 3.0 * 2.0 - 4.0 * 1.0)
        self.assertAlmostEqual(v1.distance_to(v2), math.hypot(2.0, 2.0))

        norm = v1.normalized()
        self.assertAlmostEqual(norm.magnitude, 1.0)
        self.assertAlmostEqual(norm.x, 0.6)
        self.assertAlmostEqual(norm.y, 0.8)

    def test_vec2_polar(self) -> None:
        v = Vec2.from_polar(10.0, math.pi / 2.0)
        self.assertAlmostEqual(v.x, 0.0, places=9)
        self.assertAlmostEqual(v.y, 10.0, places=9)
        self.assertAlmostEqual(v.direction(), math.pi / 2.0)

    def test_vec3_operations(self) -> None:
        v1 = Vec3(1.0, 2.0, 3.0)
        v2 = Vec3(4.0, 5.0, 6.0)

        self.assertEqual(v1 + v2, Vec3(5.0, 7.0, 9.0))
        self.assertEqual(v1 - v2, Vec3(-3.0, -3.0, -3.0))
        self.assertEqual(v1 * 2.0, Vec3(2.0, 4.0, 6.0))
        self.assertEqual(v1 / 2.0, Vec3(0.5, 1.0, 1.5))
        self.assertEqual(-v1, Vec3(-1.0, -2.0, -3.0))

        self.assertAlmostEqual(v1.dot(v2), 1 * 4 + 2 * 5 + 3 * 6)
        cross = v1.cross(v2)
        self.assertEqual(cross, Vec3(-3.0, 6.0, -3.0))

        planar = v1.to_vec2_planar()
        self.assertEqual(planar, Vec2(1.0, 2.0))
        embed = Vec3.from_vec2(planar, z=3.0)
        self.assertEqual(embed, v1)

    def test_transforms(self) -> None:
        v = Vec2(1.0, 0.0)
        rotated = rotate_vec2(v, math.pi / 2.0)
        self.assertAlmostEqual(rotated.x, 0.0, places=9)
        self.assertAlmostEqual(rotated.y, 1.0, places=9)

        h = heading_to_vec2(math.pi)
        self.assertAlmostEqual(h.x, -1.0, places=9)
        self.assertAlmostEqual(h.y, 0.0, places=9)


if __name__ == "__main__":
    unittest.main()

