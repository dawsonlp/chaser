"""Time-addressable trajectory protocols and piecewise paths."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence

from chaser.kinematics.state import KinematicState, KinematicState3D


class Path2D(Protocol):
    """A time-addressable 2D trajectory."""

    start_time: float

    def state_at(self, time: float) -> KinematicState: ...


class Path3D(Protocol):
    """A time-addressable 3D trajectory (3D readiness)."""

    start_time: float

    def state_at(self, time: float) -> KinematicState3D: ...


Path = Path2D


@dataclass(frozen=True, slots=True)
class PiecewisePath2D:
    """A composite path formed by consecutive path segments."""

    segments: tuple[Path2D, ...]

    def __post_init__(self) -> None:
        if not self.segments:
            raise ValueError("piecewise path requires at least one segment")
        for i in range(len(self.segments) - 1):
            if self.segments[i + 1].start_time < self.segments[i].start_time:
                raise ValueError("segments must be sorted chronologically by start_time")

    @property
    def start_time(self) -> float:
        return self.segments[0].start_time

    def state_at(self, time: float) -> KinematicState:
        if time < self.start_time:
            raise ValueError(f"cannot evaluate path at {time} before start_time {self.start_time}")

        # Find the active segment for the requested time
        active_segment = self.segments[0]
        for segment in self.segments:
            if time >= segment.start_time:
                active_segment = segment
            else:
                break
        return active_segment.state_at(time)
