"""Command-line entry points for simulation, visualization, and experimentation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from chaser.math.vec2 import Vec2
from chaser.scenarios.dual_chaser import DualChaserScenario, DualChaserSettings
from chaser.scenarios.red_goal import RedGoalScenario, RedGoalSettings
from chaser.scenarios.registry import ScenarioRegistry


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="chaser", description="Chaser pursuit simulation engine")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # list
    subparsers.add_parser("list", help="list all registered pursuit scenarios")

    # Shared simulation settings
    def add_scenario_settings(command: argparse.ArgumentParser) -> None:
        command.add_argument(
            "--scenario",
            type=str,
            default="red_goal",
            choices=ScenarioRegistry.list_scenarios(),
            help="scenario name to run",
        )
        command.add_argument("--blue-x", type=float, default=4_000.0)
        command.add_argument("--blue-y", type=float, default=-2_500.0)
        command.add_argument(
            "--blue-max-acceleration",
            type=float,
            default=500.0,
        )
        command.add_argument("--air-density", type=float, default=1.225)
        command.add_argument("--drag-coefficient", type=float, default=0.47)

    # simulate
    simulate = subparsers.add_parser("simulate", help="run a pursuit scenario and print results")
    add_scenario_settings(simulate)

    # visualize
    visualize = subparsers.add_parser(
        "visualize",
        help="run and display a scenario through SDL",
    )
    add_scenario_settings(visualize)
    visualize.add_argument("--playback-rate", type=float, default=1.0)
    visualize.add_argument("--fps", type=float, default=60.0)

    # plot-regions
    regions = subparsers.add_parser(
        "plot-regions",
        help="write an SVG of successful blue starting regions",
    )
    regions.add_argument("--output", type=Path, default=Path("intercept-regions.svg"))
    regions.add_argument("--air-density", type=float, default=1.225)
    regions.add_argument("--drag-coefficient", type=float, default=0.47)

    # compare
    compare = subparsers.add_parser(
        "compare",
        help="run comparative 1-vs-2 chaser study across sample starting positions",
    )
    compare.add_argument("--acceleration", type=float, default=500.0)

    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(arguments)

    if args.command == "list":
        print("Registered Scenarios:")
        for name in ScenarioRegistry.list_scenarios():
            scenario = ScenarioRegistry.get(name)
            desc = getattr(scenario, "description", "")
            print(f"  - {name:15s} : {desc}")
        return 0

    if args.command == "plot-regions":
        from chaser.visualization.intercept_regions import InterceptRegionPlot

        settings = RedGoalSettings(
            air_density_kg_m3=args.air_density,
            sphere_drag_coefficient=args.drag_coefficient,
        )
        output = InterceptRegionPlot(settings).write_svg(args.output)
        print(output)
        return 0

    if args.command == "compare":
        from chaser.experiments.comparison import SingleVsDualChaserStudy

        test_points = [
            Vec2(2_000.0, -2_000.0),
            Vec2(4_000.0, -2_500.0),
            Vec2(6_000.0, -3_000.0),
            Vec2(4_000.0, 2_500.0),
            Vec2(7_000.0, 3_500.0),
        ]
        study = SingleVsDualChaserStudy(
            test_positions=test_points,
            acceleration_mps2=args.acceleration,
        )
        report = study.run()

        print(
            json.dumps(
                {
                    "total_positions_tested": report.total_positions_tested,
                    "single_chaser_intercepts": report.single_chaser_intercepts,
                    "dual_chaser_intercepts": report.dual_chaser_intercepts,
                    "single_chaser_mean_score_m": report.single_chaser_mean_score,
                    "dual_chaser_mean_score_m": report.dual_chaser_mean_score,
                    "trials": [
                        {
                            "blue_1_start": {"x": t.blue_1_start.x, "y": t.blue_1_start.y},
                            "single": {"outcome": t.single_chaser_outcome, "score": t.single_chaser_score, "duration": t.single_chaser_duration},
                            "dual": {"outcome": t.dual_chaser_outcome, "score": t.dual_chaser_score, "duration": t.dual_chaser_duration},
                        }
                        for t in report.trials
                    ],
                },
                indent=2,
            )
        )
        return 0

    if args.command in {"simulate", "visualize"}:
        if args.scenario == "dual_chaser":
            settings = DualChaserSettings(
                blue_1_start=Vec2(args.blue_x, args.blue_y),
                blue_max_acceleration_mps2=args.blue_max_acceleration,
                air_density_kg_m3=args.air_density,
                sphere_drag_coefficient=args.drag_coefficient,
            )
            record = DualChaserScenario().run(settings)
        else:
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

        outcome_str = record.outcome.value if hasattr(record.outcome, "value") else str(record.outcome)
        print(
            json.dumps(
                {
                    "scenario": args.scenario,
                    "outcome": outcome_str,
                    "duration_s": record.duration_s,
                    "catch_score_m": record.catch_score_m,
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
