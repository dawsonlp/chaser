"""Standard scenario protocol."""

from __future__ import annotations

from typing import Any, Protocol

from chaser.engine.record import SimulationRecord


class Scenario(Protocol):
    """Protocol for an executable pursuit scenario."""

    @property
    def name(self) -> str: ...

    @property
    def description(self) -> str: ...

    def run(self, settings: Any = None) -> SimulationRecord: ...
