"""Command-line entry points for simulation and visualization."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from chaser.plane import Vec2
from chaser.scenarios.red_goal import RedGoalScenario, RedGoalSettings


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="chaser")
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_scenario_settings(command: argparse.ArgumentParser) -> None:
        command.add_argument("--blue-x", type=float, default=4_000.0)
        command.add_argument("--blue-y", type=float, default=-2_500.0)
        command.add_argument(
            "--blue-max-acceleration",
            type=float,
            default=500.0,
        )
        command.add_argument("--air-density", type=float, default=1.225)
        command.add_argument("--drag-coefficient", type=float, default=0.47)

    simulate = subparsers.add_parser("simulate", help="run the first scenario")
    add_scenario_settings(simulate)

    visualize = subparsers.add_parser(
        "visualize",
        help="run and display the first scenario through SDL",
    )
    add_scenario_settings(visualize)
    visualize.add_argument("--playback-rate", type=float, default=1.0)
    visualize.add_argument("--fps", type=float, default=60.0)

    regions = subparsers.add_parser(
        "plot-regions",
        help="write an SVG of successful blue starting regions",
    )
    regions.add_argument("--output", type=Path, default=Path("intercept-regions.svg"))
    regions.add_argument("--air-density", type=float, default=1.225)
    regions.add_argument("--drag-coefficient", type=float, default=0.47)
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(arguments)
    if args.command == "plot-regions":
        from chaser.visualization.intercept_regions import InterceptRegionPlot

        settings = RedGoalSettings(
            air_density_kg_m3=args.air_density,
            sphere_drag_coefficient=args.drag_coefficient,
        )
        output = InterceptRegionPlot(settings).write_svg(args.output)
        print(output)
        return 0
    if args.command in {"simulate", "visualize"}:
        settings = RedGoalSettings(
            blue_start=Vec2(args.blue_x, args.blue_y),
            blue_max_acceleration_mps2=args.blue_max_acceleration,
            air_density_kg_m3=args.air_density,
            sphere_drag_coefficient=args.drag_coefficient,
        )
        record = RedGoalScenario().run(settings)
        if args.command == "visualize":
            from chaser.visualization.sdl import SDLPlayback

            SDLPlayback().play(
                record,
                playback_rate=args.playback_rate,
                frames_per_second=args.fps,
            )
            return 0
        print(
            json.dumps(
                {
                    "outcome": record.outcome,
                    "duration_s": record.duration_s,
                    "catch_score_m": record.catch_score_m,
                    "blue_mass_kg": settings.blue_mass_kg,
                    "blue_max_thrust_n": settings.blue_max_thrust_n,
                    "events": [
                        {
                            "time": event.time,
                            "kind": event.kind,
                            "participants": event.participants,
                            "payload": event.payload,
                        }
                        for event in record.events
                    ],
                },
                indent=2,
            )
        )
        return 0
    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
