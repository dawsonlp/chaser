# Chaser

Chaser is a simulation project for comparing how effectively two automated chasers can catch an automated target relative to one chaser.

The first case will use simple circular objects moving on a two-dimensional plane. Each object senses its surroundings, uses those observations to make decisions, and acts through its available actuators. Simulation results will be projected into a video visualization. The simulation is intended to support other spaces, object models, sensors, actuators, and behaviors later.

See [the load-bearing design decisions](docs/design/readme.md).

Component design: [system componentization](docs/design/system-componentization.md).

Development planning: [active plans & roadmaps](docs/development_planning/readme.md).

## Scenarios

- [Scenario index](docs/scenarios/readme.md)
- [Red target, blue interceptor, and goal post](docs/scenarios/red-target-blue-interceptor.md)

## Implementation

The first implementation is written in Python 3.12 or newer. The simulation runs before and independently from visualization:

- A small discrete-event runtime advances only to model-produced events.
- The first model set provides a two-dimensional plane, analytic motion paths, circular contact detection, sensors, object-owned actuators, and an interception decision.
- Blue is a 10 cm steel-density sphere. Constant thrust is derived from its configured low-speed acceleration, and a first-order atmospheric model applies speed-squared drag.
- A completed simulation record is projected into screen-space primitives.
- An SDL renderer samples that projection for display; display frames do not advance simulation time.

Run the simulation and tests:

```shell
uv sync
uv run python -m unittest discover -s tests -v
uv run chaser simulate
```

The visualization uses SDL 3.4.14 and PySDL3 0.9.11b1. PySDL3 is currently published as a prerelease. On macOS with Homebrew:

```shell
brew install sdl3
uv sync --extra visualization
uv run chaser visualize
```

The renderer detects Homebrew's SDL library on Apple Silicon and Intel Macs. On another installation, set `SDL_BINARY_PATH` to the directory containing the SDL 3 library.

Blue's placement, low-speed acceleration, air density, and sphere drag coefficient are configurable:

```shell
uv run chaser visualize --blue-x 4000 --blue-y -2500 --blue-max-acceleration 500
uv run chaser simulate --air-density 1.225 --drag-coefficient 0.47
uv run chaser plot-regions --output docs/plots/intercept-regions.svg
```

The region plot colors blue starting positions by the minimum configured low-speed acceleration capability—`50`, `100`, `150`, `200`, or `250 m/s²`—that permits contact before red reaches the goal.
