"""Policy tournament matrix for evaluating chaser vs target co-evolution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from chaser.builder.config import ScenarioConfig
from chaser.builder.factory import run_composed_scenario
from chaser.math.vec2 import Vec2


@dataclass(frozen=True, slots=True)
class MatrixMatchResult:
    chaser_setup: str
    target_setup: str
    outcome: str
    duration_s: float
    catch_score_m: float | None


@dataclass(frozen=True, slots=True)
class TournamentReport:
    matches: tuple[MatrixMatchResult, ...]

    def summary_table(self) -> str:
        lines = [
            f"{'Chaser Team':<25} | {'Target Strategy':<25} | {'Outcome':<20} | {'Time (s)':<8} | {'Score (m)':<10}",
            "-" * 95,
        ]
        for m in self.matches:
            score_str = f"{m.catch_score_m:.1f}" if m.catch_score_m is not None else "N/A"
            lines.append(
                f"{m.chaser_setup:<25} | {m.target_setup:<25} | {m.outcome:<20} | {m.duration_s:<8.2f} | {score_str:<10}"
            )
        return "\n".join(lines)


class PolicyMatrixTournament:
    """Evaluate multiple chaser algorithms against multiple target evasion strategies."""

    def __init__(
        self,
        chaser_acc: float = 500.0,
        target_evade_acc: float = 350.0,
    ) -> None:
        self.chaser_acc = chaser_acc
        self.target_evade_acc = target_evade_acc

    def run_default_tournament(self) -> TournamentReport:
        chaser_setups = [
            ("1 Chaser (Direct Intercept)", 1, "quadratic_drag"),
            ("1 Chaser (Pure Pursuit)", 1, "pure_pursuit"),
            ("2 Chasers (Pincer Flank)", 2, "dual_pincer"),
            ("2 Chasers (Adaptive Pincer)", 2, "dynamic_lead"),
        ]

        target_setups = [
            ("Passive Target", "straight_line"),
            ("Evasive Target", "evasive_goal_steering"),
        ]

        matches: list[MatrixMatchResult] = []
        for c_label, c_count, c_policy in chaser_setups:
            for t_label, t_policy in target_setups:
                cfg = ScenarioConfig.create(
                    scenario_id=f"{c_policy}_vs_{t_policy}",
                    chaser_count=c_count,
                    chaser_policy=c_policy,
                    chaser_acc=self.chaser_acc,
                    target_policy=t_policy,
                    target_evade_acc=self.target_evade_acc,
                )
                record = run_composed_scenario(cfg)
                matches.append(
                    MatrixMatchResult(
                        chaser_setup=c_label,
                        target_setup=t_label,
                        outcome=str(record.outcome),
                        duration_s=record.duration_s,
                        catch_score_m=record.catch_score_m,
                    )
                )

        return TournamentReport(matches=tuple(matches))

