from __future__ import annotations

import math
import unittest

from chaser.plane import Vec2
from chaser.scenarios.red_goal import PursuitOutcome, RedGoalScenario, RedGoalSettings


class RedGoalScenarioTests(unittest.TestCase):
    def test_default_blue_is_a_ten_centimeter_steel_sphere(self) -> None:
        settings = RedGoalSettings()

        self.assertTrue(math.isclose(settings.blue_radius_m, 0.05))
        self.assertTrue(math.isclose(settings.blue_mass_kg, 4.110250388, rel_tol=1e-9))
        self.assertTrue(
            math.isclose(
                settings.blue_max_thrust_n,
                settings.blue_mass_kg * settings.blue_max_acceleration_mps2,
            )
        )

    def test_default_blue_intercepts_before_red_reaches_goal(self) -> None:
        record = RedGoalScenario().run()

        self.assertEqual(record.outcome, PursuitOutcome.BLUE_INTERCEPTED)
        self.assertLess(record.duration_s, 10.0)
        self.assertIsNotNone(record.catch_score_m)
        self.assertGreater(record.catch_score_m or 0.0, 0.0)
        self.assertEqual(
            [event.kind for event in record.events[:3]],
            ["visual_observation", "decision", "actuator_values_changed"],
        )

    def test_air_resistance_delays_the_default_interception(self) -> None:
        with_air = RedGoalScenario().run()
        without_air = RedGoalScenario().run(RedGoalSettings(air_density_kg_m3=0.0))

        self.assertEqual(with_air.outcome, PursuitOutcome.BLUE_INTERCEPTED)
        self.assertEqual(without_air.outcome, PursuitOutcome.BLUE_INTERCEPTED)
        self.assertGreater(with_air.duration_s, without_air.duration_s)

    def test_red_goal_surface_clearance_produces_ten_second_goal_time(self) -> None:
        settings = RedGoalSettings(
            blue_start=Vec2(-100_000.0, 100_000.0),
            blue_max_acceleration_mps2=1.0,
        )

        record = RedGoalScenario().run(settings)

        self.assertEqual(record.outcome, PursuitOutcome.RED_SCORED)
        self.assertTrue(math.isclose(record.duration_s, 10.0, abs_tol=1e-7))
        self.assertIsNone(record.catch_score_m)

    def test_blue_start_is_a_deliberate_per_run_setting(self) -> None:
        first = RedGoalScenario().run(RedGoalSettings(blue_start=Vec2(1_000.0, 500.0)))
        second = RedGoalScenario().run(RedGoalSettings(blue_start=Vec2(8_000.0, 500.0)))

        self.assertNotEqual(first.duration_s, second.duration_s)


if __name__ == "__main__":
    unittest.main()
