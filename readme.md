# Chaser

Chaser is a simulation project for comparing how effectively two automated chasers can catch an automated target relative to one chaser.

The first case uses circular objects moving on a two-dimensional plane. Each object senses its surroundings, uses those observations to make decisions, and acts through its available actuators. Simulation results are recorded and projected into video visualization. The architecture is modular and decoupled to support other spaces (3D ready), object models, sensors, actuators, and behaviors.

See [the load-bearing design decisions](docs/design/readme.md).

Component design: [system componentization](docs/design/system-componentization.md).

Development planning: [active plans & roadmaps](docs/development_planning/readme.md).

Architecture overview: [system architecture](docs/architecture/overview.md).

## Scenarios & Guides

- [Scenario index](docs/scenarios/readme.md)
  - [Red target, single blue interceptor, and goal post](docs/scenarios/red-target-blue-interceptor.md)
  - [Red target, two cooperative blue chasers, and goal post](docs/scenarios/dual-chaser-comparative.md)
- [How-to Guide: Creating a new Scenario](docs/guides/01-creating-a-scenario.md)
- [How-to Guide: Implementing Guidance Policies](docs/guides/02-implementing-policies.md)
- [How-to Guide: Running Parameter Sweeps & Comparative Studies](docs/guides/03-running-sweeps.md)

## Implementation

Written in Python 3.12 or newer:

- **Discrete-Event Kernel**: A small priority-queue discrete-event runtime advances only to model-produced events in continuous time.
- **Composable Spatial Arena**: Reusable event-driven arena coordinator managing agents, sensors, policies, actuator updates, and automatic pairwise collision scheduling.
- **Unified Trajectories**: Both analytic paths and adaptive numerical integration paths (RK45 with memoized Hermite dense output) adhere to the standard `Path2D` protocol.
- **Universal Visualization**: Completed simulation records are projected into screen-space primitives and sampled by an SDL renderer for any scenario.

## Running

Run the test suite:

```shell
uv sync
uv run python -m unittest discover -s tests -v
```

List available scenarios:

```shell
uv run chaser list
```

Run simulation:

```shell
uv run chaser simulate --scenario red_goal
uv run chaser simulate --scenario dual_chaser
```

Run comparative 1-vs-2 chaser study:

```shell
uv run chaser compare --acceleration 500
```

The visualization uses SDL 3.4.14 and PySDL3 0.9.11b1. On macOS with Homebrew:

```shell
brew install sdl3
uv sync --extra visualization
uv run chaser visualize --scenario red_goal
uv run chaser visualize --scenario dual_chaser
```

Generate intercept regions SVG:

```shell
uv run chaser plot-regions --output docs/plots/intercept-regions.svg
```
