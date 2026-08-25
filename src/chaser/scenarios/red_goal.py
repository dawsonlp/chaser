"""First scenario: a blue interceptor, a red target, and a goal."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import math
from typing import Callable, Iterable, Mapping

from chaser.atmosphere import (
    ConstantThrustQuadraticDragPath,
    SphereBody,
    SphereQuadraticDrag,
    UniformAtmosphere,
)
from chaser.core import EventDrivenRuntime, EventRecord, ModelEvent
from chaser.plane import (
    ActuatorDefinition,
    ActuatorSet,
    ConstantAccelerationPath,
    DirectVisualSensor,
    KinematicState,
    Path2D,
    PlanarThrustResponse,
    Vec2,
    VisualObservation,
    ZERO_VEC2,
    earliest_circle_contact,
)


RED_ID = "red"
BLUE_ID = "blue"
GOAL_ID = "goal"


class PursuitOutcome(StrEnum):
    BLUE_INTERCEPTED = "blue_intercepted"
    RED_SCORED = "red_scored"


@dataclass(frozen=True, slots=True)
class RedGoalSettings:
    """Per-run settings, kept separate from reusable model rules."""

    red_goal_clearance_m: float = 10_000.0
    red_speed_mps: float = 1_000.0
    red_radius_m: float = 100.0
    blue_diameter_m: float = 0.1
    blue_material_density_kg_m3: float = 7_850.0
    goal_radius_m: float = 100.0
    blue_start: Vec2 = Vec2(4_000.0, -2_500.0)
    blue_max_acceleration_mps2: float = 500.0
    air_density_kg_m3: float = 1.225
    sphere_drag_coefficient: float = 0.47

    def __post_init__(self) -> None:
        positive = {
            "red_goal_clearance_m": self.red_goal_clearance_m,
            "red_speed_mps": self.red_speed_mps,
            "red_radius_m": self.red_radius_m,
            "blue_diameter_m": self.blue_diameter_m,
            "blue_material_density_kg_m3": self.blue_material_density_kg_m3,
            "goal_radius_m": self.goal_radius_m,
            "blue_max_acceleration_mps2": self.blue_max_acceleration_mps2,
        }
        invalid = [name for name, value in positive.items() if value <= 0.0]
        if invalid:
            raise ValueError(f"settings must be positive: {invalid!r}")
        if self.air_density_kg_m3 < 0.0 or self.sphere_drag_coefficient < 0.0:
            raise ValueError("air density and drag coefficient must be non-negative")

    @property
    def blue_body(self) -> SphereBody:
        return SphereBody(
            self.blue_diameter_m,
            self.blue_material_density_kg_m3,
        )

    @property
    def blue_radius_m(self) -> float:
        return self.blue_body.radius_m

    @property
    def blue_mass_kg(self) -> float:
        return self.blue_body.mass_kg

    @property
    def blue_max_thrust_n(self) -> float:
        return self.blue_mass_kg * self.blue_max_acceleration_mps2

    @property
    def red_start(self) -> Vec2:
        return Vec2(0.0, 0.0)

    @property
    def goal_position(self) -> Vec2:
        center_distance = (
            self.red_goal_clearance_m + self.red_radius_m + self.goal_radius_m
        )
        return Vec2(center_distance, 0.0)

    @property
    def uninterrupted_goal_time(self) -> float:
        return self.red_goal_clearance_m / self.red_speed_mps


@dataclass(frozen=True, slots=True)
class ObjectTrack:
    object_id: str
    radius_m: float
    path: Path2D


@dataclass(frozen=True, slots=True)
class PursuitRecord:
    settings: RedGoalSettings
    outcome: PursuitOutcome
    duration_s: float
    catch_score_m: float | None
    events: tuple[EventRecord, ...]
    tracks: Mapping[str, ObjectTrack]

    def state_at(self, object_id: str, time: float) -> KinematicState:
        bounded_time = min(self.duration_s, max(0.0, time))
        return self.tracks[object_id].path.state_at(bounded_time)


@dataclass(frozen=True, slots=True)
class QuadraticDragInterceptDecision:
    maximum_acceleration: float
    deadline: float
    drag: SphereQuadraticDrag

    def choose_actuator_changes(
        self,
        observation: VisualObservation,
    ) -> Mapping[str, float]:
        relative = observation.relative_position
        relative_velocity = observation.relative_velocity
        full_thrust_path = ConstantThrustQuadraticDragPath(
            start_time=0.0,
            initial_position=ZERO_VEC2,
            thrust_acceleration=Vec2(self.maximum_acceleration, 0.0),
            drag=self.drag,
        )

        def reach_margin(time: float) -> float:
            target_distance = (relative + relative_velocity * time).magnitude
            return full_thrust_path.distance_after(time) - target_distance

        intercept_time = self._first_reachable_time(reach_margin)
        if intercept_time is None:
            intercept_time = self.deadline

        displacement = relative + relative_velocity * intercept_time
        return {
            "thrust_acceleration": self.maximum_acceleration,
            "thrust_direction": displacement.direction(),
        }

    def _first_reachable_time(
        self,
        evaluate: Callable[[float], float],
    ) -> float | None:
        left = 1e-8
        left_value = evaluate(left)
        for index in range(1, 1_025):
            right = self.deadline * index / 1_024
            right_value = evaluate(right)
            if right_value >= 0.0 and left_value < 0.0:
                for _ in range(80):
                    middle = (left + right) * 0.5
                    if right - left <= 1e-9:
                        break
                    if evaluate(middle) >= 0.0:
                        right = middle
                    else:
                        left = middle
                return (left + right) * 0.5
            left = right
            left_value = right_value
        return None


class RedGoalModel:
    """Event-driven model for one configured red/blue/goal run."""

    def __init__(self, settings: RedGoalSettings) -> None:
        self.settings = settings
        self._sensor = DirectVisualSensor()
        self._response = PlanarThrustResponse()
        self._drag = SphereQuadraticDrag(
            body=settings.blue_body,
            atmosphere=UniformAtmosphere(settings.air_density_kg_m3),
            drag_coefficient=settings.sphere_drag_coefficient,
        )
        self._decision = QuadraticDragInterceptDecision(
            maximum_acceleration=settings.blue_max_acceleration_mps2,
            deadline=settings.uninterrupted_goal_time,
            drag=self._drag,
        )
        self._actuators = ActuatorSet(
            definitions={
                "thrust_acceleration": ActuatorDefinition(
                    "thrust_acceleration",
                    0.0,
                    settings.blue_max_acceleration_mps2,
                ),
                "thrust_direction": ActuatorDefinition(
                    "thrust_direction",
                    -math.pi,
                    math.pi,
                ),
            },
            values={"thrust_acceleration": 0.0, "thrust_direction": 0.0},
        )
        self._paths: dict[str, Path2D] = {
            RED_ID: ConstantAccelerationPath(
                0.0,
                KinematicState(
                    settings.red_start,
                    Vec2(settings.red_speed_mps, 0.0),
                    ZERO_VEC2,
                ),
            ),
            BLUE_ID: ConstantAccelerationPath(
                0.0,
                KinematicState(settings.blue_start, ZERO_VEC2, ZERO_VEC2),
            ),
            GOAL_ID: ConstantAccelerationPath(
                0.0,
                KinematicState(settings.goal_position, ZERO_VEC2, ZERO_VEC2),
            ),
        }
        self._observation: VisualObservation | None = None
        self._outcome: PursuitOutcome | None = None
        self._catch_score_m: float | None = None

    @property
    def is_complete(self) -> bool:
        return self._outcome is not None

    def initial_events(self) -> Iterable[ModelEvent]:
        return (
            ModelEvent(
                time=0.0,
                kind="visual_observation",
                participants=(BLUE_ID, RED_ID),
                priority=10,
            ),
        )

    def handle_event(self, event: ModelEvent) -> Iterable[ModelEvent]:
        if event.kind == "visual_observation":
            self._observation = self._sensor.observe(
                time=event.time,
                observer_id=BLUE_ID,
                target_id=RED_ID,
                observer_path=self._paths[BLUE_ID],
                target_path=self._paths[RED_ID],
            )
            return (
                ModelEvent(
                    event.time,
                    "decision",
                    (BLUE_ID,),
                    priority=20,
                ),
            )

        if event.kind == "decision":
            if self._observation is None:
                raise RuntimeError("decision has no sensor observation")
            changes = self._decision.choose_actuator_changes(
                self._observation,
            )
            return (
                ModelEvent(
                    event.time,
                    "actuator_values_changed",
                    (BLUE_ID,),
                    payload=dict(changes),
                    priority=30,
                ),
            )

        if event.kind == "actuator_values_changed":
            changes = {name: float(value) for name, value in event.payload.items()}
            self._actuators = self._actuators.with_changes(changes)
            old_state = self._paths[BLUE_ID].state_at(event.time)
            if old_state.velocity.magnitude > 1e-9:
                raise RuntimeError(
                    "this first drag path currently accepts its thrust setting from rest"
                )
            self._paths[BLUE_ID] = ConstantThrustQuadraticDragPath(
                start_time=event.time,
                initial_position=old_state.position,
                thrust_acceleration=self._response.acceleration(self._actuators),
                drag=self._drag,
            )
            return self._interaction_events(event.time)

        if event.kind == "blue_red_contact":
            self._outcome = PursuitOutcome.BLUE_INTERCEPTED
            red_position = self._paths[RED_ID].state_at(event.time).position
            center_distance = (self.settings.goal_position - red_position).magnitude
            self._catch_score_m = max(
                0.0,
                center_distance
                - self.settings.red_radius_m
                - self.settings.goal_radius_m,
            )
            return ()

        if event.kind == "red_goal_contact":
            self._outcome = PursuitOutcome.RED_SCORED
            return ()

        raise ValueError(f"unrecognized event kind: {event.kind!r}")

    def _interaction_events(self, from_time: float) -> tuple[ModelEvent, ...]:
        horizon = self.settings.uninterrupted_goal_time + 1.0
        blue_contact = earliest_circle_contact(
            self._paths[BLUE_ID],
            self.settings.blue_radius_m,
            self._paths[RED_ID],
            self.settings.red_radius_m,
            from_time=from_time,
            through_time=horizon,
        )
        red_goal_contact = earliest_circle_contact(
            self._paths[RED_ID],
            self.settings.red_radius_m,
            self._paths[GOAL_ID],
            self.settings.goal_radius_m,
            from_time=from_time,
            through_time=horizon,
        )
        events: list[ModelEvent] = []
        if blue_contact is not None:
            events.append(
                ModelEvent(
                    blue_contact,
                    "blue_red_contact",
                    (BLUE_ID, RED_ID),
                    priority=20,
                )
            )
        if red_goal_contact is not None:
            events.append(
                ModelEvent(
                    red_goal_contact,
                    "red_goal_contact",
                    (RED_ID, GOAL_ID),
                    priority=10,
                )
            )
        return tuple(events)

    def build_result(
        self,
        final_time: float,
        events: tuple[EventRecord, ...],
    ) -> PursuitRecord:
        if self._outcome is None:
            raise RuntimeError("cannot build a result before an outcome")
        radii = {
            RED_ID: self.settings.red_radius_m,
            BLUE_ID: self.settings.blue_radius_m,
            GOAL_ID: self.settings.goal_radius_m,
        }
        return PursuitRecord(
            settings=self.settings,
            outcome=self._outcome,
            duration_s=final_time,
            catch_score_m=self._catch_score_m,
            events=events,
            tracks={
                object_id: ObjectTrack(object_id, radii[object_id], path)
                for object_id, path in self._paths.items()
            },
        )


class RedGoalScenario:
    def run(self, settings: RedGoalSettings | None = None) -> PursuitRecord:
        configured = settings or RedGoalSettings()
        return EventDrivenRuntime().run(RedGoalModel(configured))
