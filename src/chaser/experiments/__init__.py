"""Experimentation, parameter sweeps, and comparative studies."""

from chaser.experiments.comparison import (
    ComparativeStudyReport,
    ComparisonTrialResult,
    SingleVsDualChaserStudy,
)
from chaser.experiments.matrix import (
    MatrixMatchResult,
    PolicyMatrixTournament,
    TournamentReport,
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
    "MatrixMatchResult",
    "ParameterSweep",
    "PolicyMatrixTournament",
    "SingleVsDualChaserStudy",
    "SweepResult",
    "TournamentReport",
    "summarize_records",
]
