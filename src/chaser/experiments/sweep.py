"""Parameter sweep and batch experiment runner."""

from __future__ import annotations

from dataclasses import dataclass, field
import itertools
from typing import Any, Callable, Iterator, Mapping, Sequence

from chaser.engine.record import SimulationRecord
from chaser.scenarios.base import Scenario


@dataclass(frozen=True, slots=True)
class ExperimentTrial:
    parameters: Mapping[str, Any]
    record: SimulationRecord


@dataclass(frozen=True, slots=True)
class SweepResult:
    scenario_name: str
    trials: tuple[ExperimentTrial, ...]

    @property
    def total_runs(self) -> int:
        return len(self.trials)

    @property
    def successful_intercepts(self) -> int:
        return sum(1 for t in self.trials if "intercept" in t.record.outcome)

    @property
    def success_rate(self) -> float:
        if not self.trials:
            return 0.0
        return self.successful_intercepts / len(self.trials)


class ParameterSweep:
    """Generate combinations and execute batch scenario trials."""

    def __init__(
        self,
        scenario: Scenario,
        parameter_grid: Mapping[str, Sequence[Any]],
        settings_factory: Callable[[Mapping[str, Any]], Any],
    ) -> None:
        self.scenario = scenario
        self.parameter_grid = parameter_grid
        self.settings_factory = settings_factory

    def generate_parameter_sets(self) -> Iterator[dict[str, Any]]:
        keys = list(self.parameter_grid.keys())
        values = [self.parameter_grid[k] for k in keys]
        for combination in itertools.product(*values):
            yield dict(zip(keys, combination))

    def run(self) -> SweepResult:
        trials: list[ExperimentTrial] = []
        for params in self.generate_parameter_sets():
            settings = self.settings_factory(params)
            record = self.scenario.run(settings)
            trials.append(ExperimentTrial(parameters=params, record=record))
        return SweepResult(scenario_name=self.scenario.name, trials=tuple(trials))
