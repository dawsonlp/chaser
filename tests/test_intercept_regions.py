from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from chaser.plane import Vec2
from chaser.visualization.intercept_regions import InterceptRegionPlot


class InterceptRegionPlotTests(unittest.TestCase):
    def test_boundaries_are_present_for_each_requested_capability(self) -> None:
        plot = InterceptRegionPlot(time_samples=128, horizontal_samples=80)

        boundaries = plot.boundaries()

        self.assertEqual(
            [boundary.acceleration_mps2 for boundary in boundaries],
            [50.0, 100.0, 150.0, 200.0, 250.0],
        )
        maximum_heights = [max(point.y for point in item.points) for item in boundaries]
        self.assertEqual(maximum_heights, sorted(maximum_heights))

    def test_svg_contains_legend_trajectory_and_goal(self) -> None:
        plot = InterceptRegionPlot(time_samples=64, horizontal_samples=40)

        svg = plot.render_svg(width=800, height=500)

        self.assertIn("Minimum capability required", svg)
        self.assertIn("50 m/s²", svg)
        self.assertIn("250 m/s²", svg)
        self.assertIn("red start", svg)
        self.assertIn("goal", svg)

    def test_known_start_requires_150_mps2_in_the_current_model(self) -> None:
        plot = InterceptRegionPlot(time_samples=2_048, horizontal_samples=40)

        capability = plot.minimum_capability_for(Vec2(4_000.0, 1_000.0))

        self.assertEqual(capability, 150.0)

    def test_svg_can_be_written(self) -> None:
        plot = InterceptRegionPlot(time_samples=32, horizontal_samples=20)
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "regions.svg"

            written = plot.write_svg(destination)

            self.assertEqual(written, destination)
            self.assertTrue(destination.read_text().startswith("<svg"))


if __name__ == "__main__":
    unittest.main()
