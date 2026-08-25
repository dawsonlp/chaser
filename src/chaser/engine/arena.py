"""Generic composable spatial arena model for discrete-event simulation."""

from __future__ import annotations

from typing import Iterable, Mapping, Sequence

from chaser.collision.circle_contact import earliest_circle_contact
from chaser.components.sensors.base import VisualObservation
from chaser.core import EventRecord, ModelEvent
from chaser.engine.record import SimulationRecord, TrackRecord
from chaser.engine.rules import InteractionRule, ScoringPolicy
from chaser.entities.agent import Agent
from chaser.kinematics.path import Path2D, PiecewisePath2D


class ComposableArenaModel:
    """Generic discrete-event arena coordinating agents, sensors, actuators, and collisions."""

    def __init__(
        self,
        scenario_id: str,
        agents: Mapping[str, Agent],
        interaction_rules: Sequence[InteractionRule],
        *,
        scoring_policy: ScoringPolicy | None = None,
        horizon_time: float = 100.0,
    ) -> None:
        self.scenario_id = scenario_id
        self._agents = dict(agents)
        self._rules = tuple(interaction_rules)
        self._scoring_policy = scoring_policy
        self._horizon_time = horizon_time

        self._paths: dict[str, Path2D] = {
            agent_id: agent.initial_path for agent_id, agent in self._agents.items()
        }
        self._observations: dict[str, VisualObservation] = {}
        self._outcome: str | None = None

    @property
    def is_complete(self) -> bool:
        return self._outcome is not None

    def initial_events(self) -> Iterable[ModelEvent]:
        events: list[ModelEvent] = []
        for agent_id, agent in self._agents.items():
            if agent.sensors:
                events.append(
                    ModelEvent(
                        time=0.0,
                        kind="observation",
                        participants=(agent_id,),
                        priority=10,
                    )
                )
        return tuple(events)

    def handle_event(self, event: ModelEvent) -> Iterable[ModelEvent]:
        if event.kind == "observation":
            agent_id = event.participants[0]
            agent = self._agents[agent_id]
            target_id = agent.target_id or (
                "red"
                if "red" in self._agents and "red" != agent_id
                else next((aid for aid in self._agents if aid != agent_id), "")
            )
            scheduled: list[ModelEvent] = []

            if agent.sensors and target_id:
                sensor = agent.sensors[0]
                obs = sensor.observe(
                    time=event.time,
                    observer_id=agent_id,
                    target_id=target_id,
                    observer_path=self._paths[agent_id],
                    target_path=self._paths[target_id],
                )
                self._observations[agent_id] = obs
                scheduled.append(
                    ModelEvent(
                        event.time,
                        "decision",
                        (agent_id,),
                        priority=20,
                    )
                )

                # If the sensor performs periodic scans, schedule the next scan event
                scan_interval = getattr(sensor, "scan_interval_s", None)
                if scan_interval is not None and scan_interval > 0:
                    next_scan = event.time + scan_interval
                    if next_scan <= self._horizon_time:
                        scheduled.append(
                            ModelEvent(
                                time=next_scan,
                                kind="observation",
                                participants=(agent_id,),
                                priority=10,
                            )
                        )

            return tuple(scheduled)

        if event.kind == "decision":
            agent_id = event.participants[0]
            agent = self._agents[agent_id]
            if agent.policy and agent_id in self._observations:
                obs = self._observations[agent_id]
                changes = agent.policy.choose_actuator_changes(obs)
                if changes:
                    return (
                        ModelEvent(
                            event.time,
                            "actuator_values_changed",
                            (agent_id,),
                            payload=dict(changes),
                            priority=30,
                        ),
                    )
            return ()

        if event.kind == "actuator_values_changed":
            agent_id = event.participants[0]
            agent = self._agents[agent_id]
            if agent.actuators:
                changes = {name: float(val) for name, val in event.payload.items()}
                updated_actuators = agent.actuators.with_changes(changes)
                self._agents[agent_id] = agent.with_actuators(updated_actuators)

                if agent.path_builder:
                    old_state = self._paths[agent_id].state_at(event.time)
                    new_segment = agent.path_builder(
                        self._agents[agent_id],
                        event.time,
                        old_state,
                        updated_actuators,
                    )
                    current_path = self._paths[agent_id]
                    if event.time > 0.0:
                        if isinstance(current_path, PiecewisePath2D):
                            self._paths[agent_id] = PiecewisePath2D(
                                (*current_path.segments, new_segment)
                            )
                        else:
                            self._paths[agent_id] = PiecewisePath2D(
                                (current_path, new_segment)
                            )
                    else:
                        self._paths[agent_id] = new_segment

                return self._schedule_interactions(event.time)
            return ()

        # Check for interaction rules
        for rule in self._rules:
            if event.kind == rule.event_kind:
                # Validate that entities are actually in contact at this event time
                if rule.entity_a in self._paths and rule.entity_b in self._paths:
                    pos_a = self._paths[rule.entity_a].state_at(event.time).position
                    pos_b = self._paths[rule.entity_b].state_at(event.time).position
                    radius_sum = (
                        self._agents[rule.entity_a].radius_m
                        + self._agents[rule.entity_b].radius_m
                    )
                    distance = (pos_a - pos_b).magnitude
                    if distance > radius_sum + 1e-2:
                        # Obsolete interaction event from a superseded trajectory
                        return ()

                if rule.outcome:
                    self._outcome = rule.outcome
                return ()

        raise ValueError(f"unrecognized event kind: {event.kind!r}")

    def _schedule_interactions(self, from_time: float) -> tuple[ModelEvent, ...]:
        events: list[ModelEvent] = []
        for rule in self._rules:
            if rule.entity_a in self._paths and rule.entity_b in self._paths:
                agent_a = self._agents[rule.entity_a]
                agent_b = self._agents[rule.entity_b]
                contact_time = earliest_circle_contact(
                    self._paths[rule.entity_a],
                    agent_a.radius_m,
                    self._paths[rule.entity_b],
                    agent_b.radius_m,
                    from_time=from_time,
                    through_time=self._horizon_time,
                )
                if contact_time is not None:
                    events.append(
                        ModelEvent(
                            time=contact_time,
                            kind=rule.event_kind,
                            participants=(rule.entity_a, rule.entity_b),
                            priority=rule.priority,
                        )
                    )
        return tuple(events)

    def build_result(
        self,
        final_time: float,
        events: tuple[EventRecord, ...],
    ) -> SimulationRecord:
        if self._outcome is None:
            raise RuntimeError("cannot build result before simulation reaches an outcome")

        catch_score_m: float | None = None
        if self._scoring_policy:
            catch_score_m = self._scoring_policy.calculate_score(
                final_time,
                self._outcome,
                events,
                self._paths,
            )

        tracks = {
            agent_id: TrackRecord(
                entity_id=agent_id,
                display_name=agent.display_name,
                radius_m=agent.radius_m,
                path=self._paths[agent_id],
                style=agent.style,
            )
            for agent_id, agent in self._agents.items()
        }

        return SimulationRecord(
            scenario_id=self.scenario_id,
            outcome=self._outcome,
            duration_s=final_time,
            catch_score_m=catch_score_m,
            events=events,
            tracks=tracks,
        )
