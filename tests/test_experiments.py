from __future__ import annotations

import unittest

from chaser.experiments import (
    ParameterSweep,
    SingleVsDualChaserStudy,
    summarize_records,
)
from chaser.math import Vec2
from chaser.scenarios.red_goal import RedGoalScenario, RedGoalSettings


class ExperimentTests(unittest.TestCase):
    def test_parameter_sweep(self) -> None:
        sweep = ParameterSweep(
            scenario=RedGoalScenario(),
            parameter_grid={
                "blue_start": [Vec2(4_000.0, -2_500.0), Vec2(8_000.0, 1_000.0)],
                "acceleration": [250.0, 500.0],
            },
            settings_factory=lambda p: RedGoalSettings(
                blue_start=p["blue_start"],
                blue_max_acceleration_mps2=p["acceleration"],
            ),
        )
        result = sweep.run()

        self.assertEqual(result.total_runs, 4)
        self.assertGreaterEqual(result.success_rate, 0.5)

    def test_single_vs_dual_study(self) -> None:
        study = SingleVsDualChaserStudy(
            test_positions=[Vec2(4_000.0, -2_500.0), Vec2(7_000.0, 3_000.0)],
            acceleration_mps2=500.0,
        )
        report = study.run()

        self.assertEqual(report.total_positions_tested, 2)
        self.assertGreaterEqual(report.dual_chaser_intercepts, report.single_chaser_intercepts)


if __name__ == "__main__":
    unittest.main()
