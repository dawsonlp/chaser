"""Direct ideal visual sensor implementation."""

from __future__ import annotations

from dataclasses import dataclass

from chaser.components.sensors.base import VisualObservation
from chaser.kinematics.path import Path2D


@dataclass(frozen=True, slots=True)
class DirectVisualSensor:
    """Initial ideal sensor: reports exact visible target motion at an event time."""

    def observe(
        self,
        *,
        time: float,
        observer_id: str,
        target_id: str,
        observer_path: Path2D,
        target_path: Path2D,
    ) -> VisualObservation:
        observer_state = observer_path.state_at(time)
        target_state = target_path.state_at(time)
        return VisualObservation(
            observed_at=time,
            observer_id=observer_id,
            target_id=target_id,
            relative_position=target_state.position - observer_state.position,
            relative_velocity=target_state.velocity - observer_state.velocity,
        )

