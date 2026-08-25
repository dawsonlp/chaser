from __future__ import annotations

import math
import unittest

from chaser.atmosphere import (
    ConstantThrustQuadraticDragPath,
    SphereBody,
    SphereQuadraticDrag,
    UniformAtmosphere,
)
from chaser.plane import Vec2


class AtmosphericDragTests(unittest.TestCase):
    def setUp(self) -> None:
        self.body = SphereBody(0.1, 7_850.0)
        self.drag = SphereQuadraticDrag(self.body, UniformAtmosphere(1.225), 0.47)

    def test_ten_centimeter_steel_sphere_properties_are_derived(self) -> None:
        self.assertTrue(math.isclose(self.body.radius_m, 0.05))
        self.assertTrue(math.isclose(self.body.frontal_area_m2, math.pi * 0.05**2))
        self.assertTrue(math.isclose(self.body.mass_kg, 4.110250388, rel_tol=1e-9))

    def test_quadratic_drag_quadruples_when_speed_doubles(self) -> None:
        force_at_500 = self.drag.drag_force_n(500.0)
        force_at_1000 = self.drag.drag_force_n(1_000.0)

        self.assertTrue(math.isclose(force_at_1000, 4.0 * force_at_500))

    def test_thrust_produces_configured_acceleration_only_at_low_speed(self) -> None:
        path = ConstantThrustQuadraticDragPath(
            0.0,
            Vec2(0.0, 0.0),
            Vec2(500.0, 0.0),
            self.drag,
        )

        initial = path.state_at(0.0)
        later = path.state_at(2.0)

        self.assertTrue(math.isclose(initial.acceleration.x, 500.0))
        self.assertLess(later.acceleration.magnitude, initial.acceleration.magnitude)
        self.assertLess(later.position.x, 0.5 * 500.0 * 2.0**2)


if __name__ == "__main__":
    unittest.main()
