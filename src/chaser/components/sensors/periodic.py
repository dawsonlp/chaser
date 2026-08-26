"""Periodic scanning sensor detecting nearby chasing threats."""

from __future__ import annotations

from dataclasses import dataclass

from chaser.components.sensors.base import VisualObservation
from chaser.kinematics.path import Path2D


@dataclass(frozen=True, slots=True)
class ThreatObservation(VisualObservation):
    """Observation enriched with threat metrics (distance, closing speed)."""

    distance_m: float = 0.0
    closing_speed_mps: float = 0.0
    is_threat: bool = False


@dataclass(frozen=True, slots=True)
class PeriodicThreatSensor:
    """A visual sensor that scans periodically to detect closing pursuers."""

    scan_interval_s: float = 0.5
    detection_range_m: float = 8_000.0
    threat_closing_speed_threshold_mps: float = 100.0

    def observe(
        self,
        *,
        time: float,
        observer_id: str,
        target_id: str,
        observer_path: Path2D,
        target_path: Path2D,
    ) -> ThreatObservation:
        observer_state = observer_path.state_at(time)
        target_state = target_path.state_at(time)

        rel_pos = target_state.position - observer_state.position
        rel_vel = target_state.velocity - observer_state.velocity
        distance = rel_pos.magnitude

        # Closing speed = - d(distance)/dt = - (r . v) / |r|
        closing_speed = 0.0
        if distance > 1e-6:
            closing_speed = -rel_pos.dot(rel_vel) / distance

        is_threat = (
            distance <= self.detection_range_m
            and closing_speed >= self.threat_closing_speed_threshold_mps
        )

        return ThreatObservation(
            observed_at=time,
            observer_id=observer_id,
            target_id=target_id,
            relative_position=rel_pos,
            relative_velocity=rel_vel,
            observer_position=observer_state.position,
            observer_velocity=observer_state.velocity,
            distance_m=distance,
            closing_speed_mps=closing_speed,
            is_threat=is_threat,
        )

