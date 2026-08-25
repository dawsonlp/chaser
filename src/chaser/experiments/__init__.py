"""Experimentation, parameter sweeps, and comparative studies."""

from chaser.experiments.comparison import (
    ComparativeStudyReport,
    ComparisonTrialResult,
    SingleVsDualChaserStudy,
)
from chaser.experiments.metrics import summarize_records
from chaser.experiments.sweep import (
    ExperimentTrial,
    ParameterSweep,
    SweepResult,
)

__all__ = [
    "ComparativeStudyReport",
    "ComparisonTrialResult",
    "ExperimentTrial",
    "ParameterSweep",
    "SingleVsDualChaserStudy",
    "SweepResult",
    "summarize_records",
]

