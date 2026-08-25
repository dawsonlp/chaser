"""Small, model-agnostic discrete-event runtime."""

from __future__ import annotations

from dataclasses import dataclass, field
import heapq
import itertools
import math
from typing import Generic, Iterable, Mapping, Protocol, TypeVar


@dataclass(frozen=True, slots=True)
class ModelEvent:
    """An event proposed by a model for a particular simulation time."""

    time: float
    kind: str
    participants: tuple[str, ...] = ()
    payload: Mapping[str, object] = field(default_factory=dict)
    priority: int = 100


@dataclass(frozen=True, slots=True)
class EventRecord:
    """The stable, externally visible record of a processed event."""

    time: float
    kind: str
    participants: tuple[str, ...]
    payload: Mapping[str, object]


ResultT = TypeVar("ResultT")


class EventDrivenModel(Protocol, Generic[ResultT]):
    @property
    def is_complete(self) -> bool: ...

    def initial_events(self) -> Iterable[ModelEvent]: ...

    def handle_event(self, event: ModelEvent) -> Iterable[ModelEvent]: ...

    def build_result(
        self, final_time: float, events: tuple[EventRecord, ...]
    ) -> ResultT: ...


class EventDrivenRuntime:
    """Advance a model only at event times supplied by that model."""

    def __init__(self, *, time_tolerance: float = 1e-9) -> None:
        if time_tolerance <= 0.0:
            raise ValueError("time_tolerance must be positive")
        self._time_tolerance = time_tolerance

    def run(self, model: EventDrivenModel[ResultT]) -> ResultT:
        queue: list[tuple[float, int, int, ModelEvent]] = []
        sequence = itertools.count()

        def schedule(event: ModelEvent, *, current_time: float) -> None:
            if not math.isfinite(event.time):
                raise ValueError(f"event time must be finite: {event.time!r}")
            if event.time < current_time - self._time_tolerance:
                raise ValueError(
                    f"event {event.kind!r} regresses from {current_time} to {event.time}"
                )
            heapq.heappush(
                queue,
                (event.time, event.priority, next(sequence), event),
            )

        now = 0.0
        for event in model.initial_events():
            schedule(event, current_time=now)

        records: list[EventRecord] = []
        while queue and not model.is_complete:
            _, _, _, event = heapq.heappop(queue)
            now = max(now, event.time)
            records.append(
                EventRecord(
                    time=now,
                    kind=event.kind,
                    participants=event.participants,
                    payload=dict(event.payload),
                )
            )
            for proposed in model.handle_event(event):
                schedule(proposed, current_time=now)

        if not model.is_complete:
            raise RuntimeError("simulation exhausted its events without an outcome")

        return model.build_result(now, tuple(records))
