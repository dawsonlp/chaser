# Chaser

Chaser is a simulation project for comparing how effectively automated chasers can catch an automated target under evolving strategies and capabilities.

The framework provides a discrete-event continuous-time physics engine on a 2D plane (3D-ready architecture). Participants sense their environment, compute guidance decisions, actuate physical forces against quadratic atmospheric drag, and record trajectories for SDL video visualization.

See [the load-bearing design decisions](docs/design/readme.md).

Component design: [system componentization](docs/design/system-componentization.md).

Development planning: [active plans & roadmaps](docs/development_planning/readme.md).

Architecture overview: [system architecture](docs/architecture/overview.md).

## Scenarios & Guides

- [Scenario index](docs/scenarios/readme.md)
  - [Red target, single blue interceptor, and goal post](docs/scenarios/red-target-blue-interceptor.md)
  - [Red target, two cooperative blue chasers, and goal post](docs/scenarios/dual-chaser-comparative.md)
  - [Evasive red target, single blue interceptor, and goal post](docs/scenarios/evasive-target.md)
- [How-to Guide: Composable Scenarios & Component Catalog](docs/guides/04-composable-scenarios-and-mixins.md)
- [How-to Guide: Creating a new Scenario](docs/guides/01-creating-a-scenario.md)
- [How-to Guide: Implementing Guidance Policies](docs/guides/02-implementing-policies.md)
- [How-to Guide: Running Parameter Sweeps & Comparative Studies](docs/guides/03-running-sweeps.md)

## Implementation

Written in Python 3.12 or newer:

- **Component Catalog (`chaser.catalog`)**: Discoverable catalog of guidance policies (`straight_line`, `quadratic_drag`, `pure_pursuit`, `dual_pincer`, `adaptive_intercept`, `evasive_goal_steering`) and sensors (`direct_visual`, `periodic_threat`).
- **Dynamic Scenario Builder (`chaser.builder`)**: Declarative configuration to mix and match arbitrary numbers of chasers, starting positions, policies, and evasion behaviors.
- **Discrete-Event Kernel (`chaser.core`, `chaser.engine`)**: Event-driven runtime advancing in continuous time only when model events occur, handling multi-agent observations, decisions, and contact detection.
- **Unified Trajectories (`chaser.kinematics`, `chaser.physics`)**: Analytic motion paths and adaptive numerical integration paths (RK45 with memoized cubic Hermite dense output).
- **Universal Visualization (`chaser.visualization`)**: Simulation records sampled dynamically by an SDL renderer.

## Running

Run the test suite:

```shell
uv sync
uv run python -m unittest discover -s tests -v
```

### 1. Dynamic Composition & Catalog (`chaser compose`, `chaser catalog`)

List all available guidance algorithms, policies, and sensors:

```shell
uv run chaser catalog
```

Compose arbitrary scenarios from the command line:

```shell
# 2 Chasers using Dual Pincer vs Active Evasive Target (Visualized)
uv run chaser compose --chasers 2 --chaser-policy dual_pincer --target-policy evasive_goal_steering --visualize

# 1 Chaser vs Passive Target
uv run chaser compose --chasers 1 --chaser-policy quadratic_drag --target-policy straight_line

# Custom starting coordinates and evasion burst acceleration
uv run chaser compose --chasers 2 --chaser-1-x 3500 --chaser-1-y -2000 --target-policy evasive_goal_steering --target-evade-acc 400
```

### 2. Policy Matrix Tournament (`chaser matrix`)

Run an automated benchmark tournament evaluating chaser strategies against target strategies:

```shell
uv run chaser matrix
```

### 3. Preset Scenarios

List registered preset scenarios:

```shell
uv run chaser list
```

Run preset simulations:

```shell
uv run chaser simulate --scenario red_goal
uv run chaser simulate --scenario dual_chaser
uv run chaser simulate --scenario evasive_target
```

Visualize preset scenarios in SDL:

```shell
uv run chaser visualize --scenario red_goal
uv run chaser visualize --scenario dual_chaser
uv run chaser visualize --scenario evasive_target
```

Generate reachability intercept regions SVG:

```shell
uv run chaser plot-regions --output docs/plots/intercept-regions.svg
```

## License

Licensed under the [GNU General Public License v3.0 or later](LICENSE) (GPL-3.0-or-later).

