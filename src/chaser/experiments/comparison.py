"""Comparative study framework for evaluating single vs multi-chaser systems."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from chaser.math.vec2 import Vec2
from chaser.scenarios.dual_chaser import DualChaserScenario, DualChaserSettings
from chaser.scenarios.red_goal import RedGoalScenario, RedGoalSettings


@dataclass(frozen=True, slots=True)
class ComparisonTrialResult:
    blue_1_start: Vec2
    single_chaser_outcome: str
    single_chaser_score: float | None
    single_chaser_duration: float
    dual_chaser_outcome: str
    dual_chaser_score: float | None
    dual_chaser_duration: float


@dataclass(frozen=True, slots=True)
class ComparativeStudyReport:
    total_positions_tested: int
    single_chaser_intercepts: int
    dual_chaser_intercepts: int
    single_chaser_mean_score: float
    dual_chaser_mean_score: float
    trials: tuple[ComparisonTrialResult, ...]


class SingleVsDualChaserStudy:
    """Run head-to-head comparative experiments between 1 chaser and 2 chasers."""

    def __init__(
        self,
        test_positions: Sequence[Vec2],
        blue_2_fixed_start: Vec2 = Vec2(3_000.0, 2_000.0),
        acceleration_mps2: float = 500.0,
    ) -> None:
        self.test_positions = tuple(test_positions)
        self.blue_2_fixed_start = blue_2_fixed_start
        self.acceleration = acceleration_mps2

    def run(self) -> ComparativeStudyReport:
        single_scenario = RedGoalScenario()
        dual_scenario = DualChaserScenario()

        results: list[ComparisonTrialResult] = []
        for pos in self.test_positions:
            # Run single chaser
            single_record = single_scenario.run(
                RedGoalSettings(
                    blue_start=pos,
                    blue_max_acceleration_mps2=self.acceleration,
                )
            )

            # Run dual chaser with blue_1 at pos and blue_2 at fixed wing position
            dual_record = dual_scenario.run(
                DualChaserSettings(
                    blue_1_start=pos,
                    blue_2_start=self.blue_2_fixed_start,
                    blue_max_acceleration_mps2=self.acceleration,
                )
            )

            results.append(
                ComparisonTrialResult(
                    blue_1_start=pos,
                    single_chaser_outcome=single_record.outcome.value if hasattr(single_record.outcome, "value") else str(single_record.outcome),
                    single_chaser_score=single_record.catch_score_m,
                    single_chaser_duration=single_record.duration_s,
                    dual_chaser_outcome=dual_record.outcome,
                    dual_chaser_score=dual_record.catch_score_m,
                    dual_chaser_duration=dual_record.duration_s,
                )
            )

        single_wins = sum(1 for r in results if "intercept" in r.single_chaser_outcome)
        dual_wins = sum(1 for r in results if "intercept" in r.dual_chaser_outcome)

        single_scores = [r.single_chaser_score for r in results if r.single_chaser_score is not None]
        dual_scores = [r.dual_chaser_score for r in results if r.dual_chaser_score is not None]

        mean_s_score = sum(single_scores) / len(single_scores) if single_scores else 0.0
        mean_d_score = sum(dual_scores) / len(dual_scores) if dual_scores else 0.0

        return ComparativeStudyReport(
            total_positions_tested=len(results),
            single_chaser_intercepts=single_wins,
            dual_chaser_intercepts=dual_wins,
            single_chaser_mean_score=mean_s_score,
            dual_chaser_mean_score=mean_d_score,
            trials=tuple(results),
        )
