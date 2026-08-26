from __future__ import annotations

import unittest

from chaser.math import Vec2
from chaser.scenarios.evasive_target import (
    EvasiveTargetScenario,
    EvasiveTargetSettings,
)
from chaser.scenarios.registry import ScenarioRegistry


class EvasiveTargetScenarioTests(unittest.TestCase):
    def test_evasive_target_registered(self) -> None:
        scenarios = ScenarioRegistry.list_scenarios()
        self.assertIn("evasive_target", scenarios)
        instance = ScenarioRegistry.get("evasive_target")
        self.assertIsInstance(instance, EvasiveTargetScenario)

    def test_target_evades_single_chaser_and_scores(self) -> None:
        settings = EvasiveTargetSettings(
            blue_start=Vec2(4_000.0, -2_500.0),
            blue_max_acceleration_mps2=500.0,
            red_scan_interval_s=0.25,
            red_evasion_acceleration_mps2=350.0,
        )
        record = EvasiveTargetScenario().run(settings)

        self.assertEqual(record.outcome, "red_scored")
        self.assertGreater(record.duration_s, 10.0)

        # Check final position of red is in contact with goal
        red_final = record.state_at("red", record.duration_s).position
        goal_pos = record.state_at("goal", record.duration_s).position
        self.assertAlmostEqual((red_final - goal_pos).magnitude, 200.0, delta=1.0)


if __name__ == "__main__":
    unittest.main()

