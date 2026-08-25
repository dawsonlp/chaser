from __future__ import annotations

import math
import unittest

from chaser.math import Vec2
from chaser.scenarios.dual_chaser import DualChaserScenario, DualChaserSettings
from chaser.scenarios.registry import ScenarioRegistry


class DualChaserScenarioTests(unittest.TestCase):
    def test_registry_lists_registered_scenarios(self) -> None:
        scenarios = ScenarioRegistry.list_scenarios()
        self.assertIn("red_goal", scenarios)
        self.assertIn("dual_chaser", scenarios)

        instance = ScenarioRegistry.get("dual_chaser")
        self.assertIsInstance(instance, DualChaserScenario)

    def test_dual_chaser_intercepts_target(self) -> None:
        record = DualChaserScenario().run()

        self.assertIn(record.outcome, {"blue_1_intercepted", "blue_2_intercepted"})
        self.assertLess(record.duration_s, 10.0)
        self.assertIsNotNone(record.catch_score_m)
        self.assertGreater(record.catch_score_m or 0.0, 0.0)
        self.assertEqual(len(record.tracks), 4)
        self.assertIn("blue_1", record.tracks)
        self.assertIn("blue_2", record.tracks)

    def test_far_away_chasers_allow_red_score(self) -> None:
        settings = DualChaserSettings(
            blue_1_start=Vec2(-100_000.0, 100_000.0),
            blue_2_start=Vec2(-100_000.0, -100_000.0),
            blue_max_acceleration_mps2=1.0,
        )
        record = DualChaserScenario().run(settings)

        self.assertEqual(record.outcome, "red_scored")
        self.assertAlmostEqual(record.duration_s, 10.0, places=5)
        self.assertIsNone(record.catch_score_m)


if __name__ == "__main__":
    unittest.main()
