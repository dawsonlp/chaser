"""Decision and guidance policy protocols."""

from __future__ import annotations

from typing import Mapping, Protocol

from chaser.components.sensors.base import VisualObservation


class DecisionPolicy(Protocol):
    """Protocol for an autonomous decision-making policy."""

    def choose_actuator_changes(
        self,
        observation: VisualObservation,
    ) -> Mapping[str, float]: ...

