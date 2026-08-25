"""Metrics aggregation and formatting for experiments."""

from __future__ import annotations

from typing import Mapping, Sequence

from chaser.engine.record import SimulationRecord


def summarize_records(records: Sequence[SimulationRecord]) -> dict[str, object]:
    """Calculate aggregate statistics across multiple simulation records."""
    if not records:
        return {"total_runs": 0}

    total = len(records)
    intercepts = sum(1 for r in records if "intercept" in r.outcome)
    scores = [r.catch_score_m for r in records if r.catch_score_m is not None]
    durations = [r.duration_s for r in records]

    return {
        "total_runs": total,
        "intercept_count": intercepts,
        "success_rate": intercepts / total,
        "mean_duration_s": sum(durations) / total,
        "mean_catch_score_m": sum(scores) / len(scores) if scores else None,
        "max_catch_score_m": max(scores) if scores else None,
    }
