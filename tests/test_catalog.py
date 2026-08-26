from __future__ import annotations

import unittest

from chaser.catalog.registry import PolicyCatalog, SensorCatalog
from chaser.components.policies.intercept.adaptive import AdaptiveInterceptPolicy
from chaser.components.policies.intercept.quadratic_drag import QuadraticDragInterceptDecision
from chaser.components.policies.target.evasive import EvasiveGoalSteeringPolicy
from chaser.components.sensors.periodic import PeriodicThreatSensor
from chaser.components.sensors.visual import DirectVisualSensor


class CatalogTests(unittest.TestCase):
    def test_list_policies(self) -> None:
        policies = PolicyCatalog.list_policies()
        self.assertIn("straight_line", policies)
        self.assertIn("quadratic_drag", policies)
        self.assertIn("pure_pursuit", policies)
        self.assertIn("dual_pincer", policies)
        self.assertIn("adaptive_intercept", policies)
        self.assertIn("evasive_goal_steering", policies)

    def test_list_sensors(self) -> None:
        sensors = SensorCatalog.list_sensors()
        self.assertIn("direct_visual", sensors)
        self.assertIn("periodic_threat", sensors)

    def test_create_policies(self) -> None:
        p1 = PolicyCatalog.create("quadratic_drag", maximum_acceleration=400.0)
        self.assertIsInstance(p1, QuadraticDragInterceptDecision)

        p2 = PolicyCatalog.create("adaptive_intercept", maximum_acceleration=400.0)
        self.assertIsInstance(p2, AdaptiveInterceptPolicy)

        p3 = PolicyCatalog.create("evasive_goal_steering")
        self.assertIsInstance(p3, EvasiveGoalSteeringPolicy)

    def test_create_sensors(self) -> None:
        s1 = SensorCatalog.create("direct_visual")
        self.assertIsInstance(s1, DirectVisualSensor)

        s2 = SensorCatalog.create("periodic_threat", scan_interval_s=0.1)
        self.assertIsInstance(s2, PeriodicThreatSensor)


if __name__ == "__main__":
    unittest.main()

