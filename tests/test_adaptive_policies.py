from __future__ import annotations

import unittest

from chaser.builder import ScenarioConfig, run_composed_scenario
from chaser.components.policies.intercept.dynamic_lead import DynamicLeadInterceptPolicy
from chaser.components.policies.intercept.proportional_navigation import (
    ProportionalNavigationGuidancePolicy,
)
from chaser.components.sensors.base import VisualObservation
from chaser.math import Vec2
from chaser.physics.aerodynamics import SphereQuadraticDrag
from chaser.physics.atmosphere import UniformAtmosphere
from chaser.physics.bodies import SphereBody


class AdaptivePolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.body = SphereBody(0.1, 7850.0)
        self.atmo = UniformAtmosphere(1.225)
        self.drag = SphereQuadraticDrag(self.body, self.atmo, 0.47)

    def test_dynamic_lead_policy_initial_observation(self) -> None:
        obs = VisualObservation(
            observed_at=0.0,
            observer_id="blue",
            target_id="red",
            relative_position=Vec2(-4000.0, 2500.0),
            relative_velocity=Vec2(1000.0, 0.0),
            observer_position=Vec2(4000.0, -2500.0),
            observer_velocity=Vec2(0.0, 0.0),
        )
        policy = DynamicLeadInterceptPolicy(500.0, 10.0, self.drag)
        actuators = policy.choose_actuator_changes(obs)
        self.assertEqual(actuators["thrust_acceleration"], 500.0)
        self.assertAlmostEqual(actuators["thrust_direction"], 1.605, delta=0.05)

    def test_proportional_navigation_guidance(self) -> None:
        obs = VisualObservation(
            observed_at=1.0,
            observer_id="blue",
            target_id="red",
            relative_position=Vec2(-3000.0, 1500.0),
            relative_velocity=Vec2(800.0, -200.0),
            observer_position=Vec2(4000.0, -2000.0),
            observer_velocity=Vec2(200.0, 200.0),
        )
        policy = ProportionalNavigationGuidancePolicy(navigation_gain=3.5, maximum_acceleration=500.0)
        actuators = policy.choose_actuator_changes(obs)
        self.assertGreater(actuators["thrust_acceleration"], 0.0)

    def test_two_chaser_adaptive_pincer_intercepts_evasive_target(self) -> None:
        config = ScenarioConfig.create(
            chaser_count=2,
            chaser_policy="dynamic_lead",
            chaser_acc=500.0,
            target_policy="evasive_goal_steering",
            target_evade_acc=350.0,
        )
        record = run_composed_scenario(config)
        self.assertIn(record.outcome, {"blue_1_intercepted", "blue_2_intercepted"})
        self.assertLess(record.duration_s, 5.0)


if __name__ == "__main__":
    unittest.main()

