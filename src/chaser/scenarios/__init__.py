"""Simulation scenarios and registry."""

from chaser.scenarios.base import Scenario
from chaser.scenarios.dual_chaser import DualChaserScenario, DualChaserSettings
from chaser.scenarios.red_goal import (
    PursuitOutcome,
    PursuitRecord,
    RedGoalScenario,
    RedGoalSettings,
)
from chaser.scenarios.registry import ScenarioRegistry

# Register available scenarios
ScenarioRegistry.register("red_goal", lambda: RedGoalScenario())
ScenarioRegistry.register("dual_chaser", lambda: DualChaserScenario())

__all__ = [
    "DualChaserScenario",
    "DualChaserSettings",
    "PursuitOutcome",
    "PursuitRecord",
    "RedGoalScenario",
    "RedGoalSettings",
    "Scenario",
    "ScenarioRegistry",
]
