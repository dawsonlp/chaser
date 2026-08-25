from __future__ import annotations

import unittest

from chaser.core import EventDrivenRuntime, ModelEvent


class MinimalModel:
    def __init__(self) -> None:
        self.times: list[float] = []

    @property
    def is_complete(self) -> bool:
        return len(self.times) == 2

    def initial_events(self):
        return (ModelEvent(2.0, "first"),)

    def handle_event(self, event):
        self.times.append(event.time)
        if event.kind == "first":
            return (ModelEvent(7.5, "last"),)
        return ()

    def build_result(self, final_time, events):
        return final_time, events


class EventDrivenRuntimeTests(unittest.TestCase):
    def test_runtime_advances_only_to_model_events(self) -> None:
        final_time, events = EventDrivenRuntime().run(MinimalModel())

        self.assertEqual(final_time, 7.5)
        self.assertEqual([event.time for event in events], [2.0, 7.5])


if __name__ == "__main__":
    unittest.main()
