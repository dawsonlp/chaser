from __future__ import annotations

import unittest

from chaser.scenarios.red_goal import BLUE_ID, GOAL_ID, RED_ID, RedGoalScenario
from chaser.visualization.projection import BLUE, GOAL, RED, RedGoalProjection


class ProjectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.record = RedGoalScenario().run()
        self.projection = RedGoalProjection(self.record)

    def test_scene_has_grid_and_scenario_objects(self) -> None:
        scene = self.projection.scene_at(0.0)

        self.assertGreater(len(scene.grid), 2)
        circles = {circle.object_id: circle for circle in scene.circles}
        self.assertEqual(set(circles), {RED_ID, BLUE_ID, GOAL_ID})
        self.assertEqual(circles[RED_ID].color, RED)
        self.assertEqual(circles[BLUE_ID].color, BLUE)
        self.assertEqual(circles[GOAL_ID].color, GOAL)

    def test_projection_samples_record_without_changing_outcome(self) -> None:
        original_events = self.record.events
        midway = self.projection.scene_at(self.record.duration_s * 0.5)
        final = self.projection.scene_at(self.record.duration_s)

        self.assertGreater(len(midway.trails), 0)
        self.assertGreater(len(final.trails), len(midway.trails))
        self.assertIs(self.record.events, original_events)


if __name__ == "__main__":
    unittest.main()
