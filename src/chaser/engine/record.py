"""Standard simulation records and track representations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from chaser.core import EventRecord
from chaser.entities.visual_style import VisualStyle
from chaser.kinematics.path import Path2D
from chaser.kinematics.state import KinematicState


@dataclass(frozen=True, slots=True)
class TrackRecord:
    """The spatial history and visual styling of one entity."""

    entity_id: str
    display_name: str
    radius_m: float
    path: Path2D
    style: VisualStyle


@dataclass(frozen=True, slots=True)
class SimulationRecord:
    """Standardized, scenario-agnostic simulation run record."""

    scenario_id: str
    outcome: str
    duration_s: float
    catch_score_m: float | None
    events: tuple[EventRecord, ...]
    tracks: Mapping[str, TrackRecord]
    metrics: Mapping[str, object] = field(default_factory=dict)

    def state_at(self, entity_id: str, time: float) -> KinematicState:
        """Query an entity's kinematic state at simulation time t."""
        bounded_time = min(self.duration_s, max(0.0, time))
        return self.tracks[entity_id].path.state_at(bounded_time)

