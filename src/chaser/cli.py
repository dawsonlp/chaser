"""Command-line entry points for simulation, visualization, experimentation, and dynamic composition."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from chaser.builder.config import ScenarioConfig
from chaser.builder.factory import run_composed_scenario
from chaser.catalog.registry import PolicyCatalog, SensorCatalog
from chaser.experiments.matrix import PolicyMatrixTournament
from chaser.math.vec2 import Vec2
from chaser.scenarios.dual_chaser import DualChaserScenario, DualChaserSettings
from chaser.scenarios.evasive_target import EvasiveTargetScenario, EvasiveTargetSettings
from chaser.scenarios.red_goal import RedGoalScenario, RedGoalSettings
from chaser.scenarios.registry import ScenarioRegistry


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="chaser", description="Chaser pursuit simulation engine")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # list
    subparsers.add_parser("list", help="list all registered preset scenarios")

    # catalog
    subparsers.add_parser("catalog", help="list all available component algorithms, policies, and sensors")

    # Shared simulation settings
    def add_scenario_settings(command: argparse.ArgumentParser) -> None:
        command.add_argument(
            "--scenario",
            type=str,
            default="red_goal",
            choices=ScenarioRegistry.list_scenarios(),
            help="preset scenario name to run",
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
    simulate = subparsers.add_parser("simulate", help="run a preset scenario and print results")
    add_scenario_settings(simulate)

    # visualize
    visualize = subparsers.add_parser(
        "visualize",
        help="run and display a preset scenario through SDL",
    )
    add_scenario_settings(visualize)
    visualize.add_argument("--playback-rate", type=float, default=1.0)
    visualize.add_argument("--fps", type=float, default=60.0)

    # compose
    compose = subparsers.add_parser(
        "compose",
        help="dynamically compose and run/visualize custom combinations of chasers, policies, and targets",
    )
    compose.add_argument("--chasers", type=int, default=1, help="number of chaser interceptors (1..N)")
    compose.add_argument(
        "--chaser-policy",
        type=str,
        default="quadratic_drag",
        choices=list(PolicyCatalog.list_policies().keys()),
        help="guidance policy for chasers",
    )
    compose.add_argument("--chaser-acc", type=float, default=500.0, help="chaser max thrust acceleration")
    compose.add_argument("--chaser-1-x", type=float, default=4000.0)
    compose.add_argument("--chaser-1-y", type=float, default=-2500.0)
    compose.add_argument("--chaser-2-x", type=float, default=3000.0)
    compose.add_argument("--chaser-2-y", type=float, default=2000.0)
    compose.add_argument(
        "--target-policy",
        type=str,
        default="straight_line",
        choices=list(PolicyCatalog.list_policies().keys()),
        help="policy for the target",
    )
    compose.add_argument("--target-evade-acc", type=float, default=350.0, help="target evasion acceleration")
    compose.add_argument("--visualize", action="store_true", help="display simulation run in SDL window")
    compose.add_argument("--playback-rate", type=float, default=1.0)
    compose.add_argument("--fps", type=float, default=60.0)

    # matrix
    matrix = subparsers.add_parser(
        "matrix",
        help="run full policy tournament matrix benchmarking chaser vs target co-evolution",
    )
    matrix.add_argument("--chaser-acc", type=float, default=500.0)
    matrix.add_argument("--target-evade-acc", type=float, default=350.0)

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

    if args.command == "catalog":
        print("Component Catalog:\n")
        print("--- Available Policies ---")
        for name, desc in PolicyCatalog.list_policies().items():
            print(f"  - {name:25s} : {desc}")
        print("\n--- Available Sensors ---")
        for name, desc in SensorCatalog.list_sensors().items():
            print(f"  - {name:25s} : {desc}")
        return 0

    if args.command == "matrix":
        print("Running Policy Tournament Matrix...\n")
        tournament = PolicyMatrixTournament(
            chaser_acc=args.chaser_acc,
            target_evade_acc=args.target_evade_acc,
        )
        report = tournament.run_default_tournament()
        print(report.summary_table())
        return 0

    if args.command == "compose":
        starts = [
            Vec2(args.chaser_1_x, args.chaser_1_y),
            Vec2(args.chaser_2_x, args.chaser_2_y),
        ]
        config = ScenarioConfig.create(
            scenario_id=f"{args.chasers}_chasers_{args.chaser_policy}_vs_{args.target_policy}",
            chaser_count=args.chasers,
            chaser_policy=args.chaser_policy,
            chaser_acc=args.chaser_acc,
            chaser_starts=starts,
            target_policy=args.target_policy,
            target_evade_acc=args.target_evade_acc,
        )
        record = run_composed_scenario(config)

        if args.visualize:
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
                    "scenario": config.scenario_id,
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
        elif args.scenario == "evasive_target":
            settings = EvasiveTargetSettings(
                blue_start=Vec2(args.blue_x, args.blue_y),
                blue_max_acceleration_mps2=args.blue_max_acceleration,
                air_density_kg_m3=args.air_density,
                sphere_drag_coefficient=args.drag_coefficient,
            )
            record = EvasiveTargetScenario().run(settings)
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
