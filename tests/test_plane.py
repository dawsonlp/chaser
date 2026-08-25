from __future__ import annotations

import math
import unittest

from chaser.plane import (
    ActuatorDefinition,
    ActuatorSet,
    ConstantAccelerationPath,
    KinematicState,
    Vec2,
    earliest_circle_contact,
)


class PlaneModelTests(unittest.TestCase):
    def test_constant_acceleration_path_is_evaluated_analytically(self) -> None:
        path = ConstantAccelerationPath(
            2.0,
            KinematicState(Vec2(10.0, 20.0), Vec2(3.0, 4.0), Vec2(2.0, -1.0)),
        )

        state = path.state_at(5.0)

        self.assertEqual(state.position, Vec2(28.0, 27.5))
        self.assertEqual(state.velocity, Vec2(9.0, 1.0))

    def test_actuator_changes_leave_unselected_values_unchanged(self) -> None:
        actuators = ActuatorSet(
            definitions={
                "a": ActuatorDefinition("a", 0.0, 10.0),
                "b": ActuatorDefinition("b", -5.0, 5.0),
            },
            values={"a": 1.0, "b": 2.0},
        )

        changed = actuators.with_changes({"a": 4.0})

        self.assertEqual(changed.values, {"a": 4.0, "b": 2.0})

    def test_circle_contact_is_found_between_runtime_events(self) -> None:
        first = ConstantAccelerationPath(
            0.0,
            KinematicState(Vec2(0.0, 0.0), Vec2(10.0, 0.0), Vec2(0.0, 0.0)),
        )
        second = ConstantAccelerationPath(
            0.0,
            KinematicState(Vec2(100.0, 0.0), Vec2(0.0, 0.0), Vec2(0.0, 0.0)),
        )

        contact = earliest_circle_contact(
            first,
            5.0,
            second,
            5.0,
            from_time=0.0,
            through_time=20.0,
        )

        self.assertIsNotNone(contact)
        self.assertTrue(math.isclose(contact or 0.0, 9.0, abs_tol=1e-7))

    def test_existing_overlap_is_contact_at_current_event_time(self) -> None:
        first = ConstantAccelerationPath(
            0.0,
            KinematicState(Vec2(0.0, 0.0), Vec2(0.0, 0.0)),
        )
        second = ConstantAccelerationPath(
            0.0,
            KinematicState(Vec2(5.0, 0.0), Vec2(0.0, 0.0)),
        )

        contact = earliest_circle_contact(
            first,
            5.0,
            second,
            5.0,
            from_time=3.0,
            through_time=10.0,
        )

        self.assertEqual(contact, 3.0)


if __name__ == "__main__":
    unittest.main()
