from __future__ import annotations

import unittest

from chaser.builder import ScenarioConfig, run_composed_scenario
from chaser.math import Vec2


class BuilderTests(unittest.TestCase):
    def test_compose_single_chaser_vs_straight(self) -> None:
        cfg = ScenarioConfig.create(
            chaser_count=1,
            chaser_policy="quadratic_drag",
            target_policy="straight_line",
        )
        record = run_composed_scenario(cfg)
        self.assertEqual(record.outcome, "blue_intercepted")
        self.assertLess(record.duration_s, 10.0)

    def test_compose_dual_chaser_vs_straight(self) -> None:
        cfg = ScenarioConfig.create(
            chaser_count=2,
            chaser_policy="dual_pincer",
            target_policy="straight_line",
        )
        record = run_composed_scenario(cfg)
        self.assertIn(record.outcome, {"blue_1_intercepted", "blue_2_intercepted"})

    def test_compose_single_chaser_vs_evasive(self) -> None:
        cfg = ScenarioConfig.create(
            chaser_count=1,
            chaser_policy="quadratic_drag",
            target_policy="evasive_goal_steering",
            target_evade_acc=350.0,
        )
        record = run_composed_scenario(cfg)
        self.assertEqual(record.outcome, "target_scored")


if __name__ == "__main__":
    unittest.main()

