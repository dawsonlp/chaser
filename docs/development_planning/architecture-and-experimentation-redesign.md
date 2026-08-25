# Architecture & Experimentation Redesign Plan

## 1. Executive Summary

Chaser was conceived to answer a foundational comparative question: **how effectively two automated chasers can catch an automated target relative to one chaser**, while allowing future expansion into 3D, complex geometry, diverse sensor/actuator models, and high-fidelity physics.

The current codebase is clean and mathematically sound. However, the first scenario implementation (`RedGoalModel` in [red_goal.py](../../src/chaser/scenarios/red_goal.py)) combines agent definitions, sensor polling, decision routing, actuator responses, pairwise collision detection, and event lifecycle management into a single monolithic class. Furthermore, the visualization ([projection.py](../../src/chaser/visualization/projection.py), [sdl.py](../../src/chaser/visualization/sdl.py)) and CLI ([cli.py](../../src/chaser/cli.py)) are hard-coded to `RED_ID`, `BLUE_ID`, and `GOAL_ID`.

To enable **constant, frictionless writing of new simulation implementations** with **strict DRY (Don't Repeat Yourself) principles** and **first-class documentation**, this plan decomposes the project into modular layers, introduces a reusable **Composable Spatial Arena**, standardizes **Simulation Records** for universal visualization, establishes a **Continuous & Adaptive Numerical Path Integrator** alongside analytic paths, and establishes an **Experimentation & Parameter Sweep Harness**.

---

## 2. Current State vs. Target State Analysis

| Dimension | Current Implementation | Target Architecture (DRY & Extensible) |
| :--- | :--- | :--- |
| **Scenario Definition** | Monolithic `RedGoalModel` hand-wires event queues, participant IDs, sensor calls, decision steps, and collision pair checks (~390 lines per scenario). | Declarative `Scenario` specification (~30–50 lines). Entity composition via lightweight typed dataclasses (Body, Sensors, Policy, Actuators). |
| **Arena & Event Loop** | Hardcoded event transitions (`visual_observation` $\rightarrow$ `decision` $\rightarrow$ `actuator_values_changed` $\rightarrow$ manual pair contact checks). | Generic `SpatialArenaEngine` that automatically handles sensor dispatch, policy queries, path updates, and N-body/pairwise collision scheduling. |
| **Path & Trajectory Contract** | Analytic paths only ([plane.py](../../src/chaser/plane.py), [atmosphere.py](../../src/chaser/atmosphere.py)). No unified memoized dense-output contract for numerical integration. | Unified `Path` protocol (`state_at(time) -> KinematicState`). Analytic and Adaptive Numerical (RK45 with dense output) paths share identical interface. |
| **Visualization** | `RedGoalProjection` expects `PursuitRecord` with hardcoded `RED_ID`, `BLUE_ID`, `GOAL_ID` and specific colors. | Universal `ProjectionEngine` that renders any 2D/3D `SimulationRecord` using entity track visual metadata (color theme, mesh/circle radius, trail styling). |
| **Mathematical Domain** | [plane.py](../../src/chaser/plane.py) is a kitchen-sink module (Vec2, Kinematics, Actuators, Sensors, Polynomial roots, Circle collision). | Decomposed into dedicated modules: `chaser.math`, `chaser.numerics`, `chaser.kinematics`, `chaser.collision`, `chaser.sensors`, `chaser.actuators`. 3D stubs and class structures prepared. |
| **Experimentation & Sweeps** | Bespoke scripts and hardcoded CLI flags (`--blue-x`, `--blue-y`, `--blue-max-acceleration`). | Unified `ExperimentHarness` supporting parameter grids, Monte Carlo sweeps, comparative 1-vs-2 chaser benchmarks, and metric export (JSON/CSV/plots). |
| **CLI & Discovery** | Hardcoded subcommands for `RedGoal`. | Pluggable CLI discovering scenarios and policies dynamically from a registry (`chaser run <scenario>`, `chaser sweep <scenario>`). |
| **Documentation** | Excellent top-level design docs, but lacks actionable developer guides, API references, and scenario playbooks. | Tiered documentation: Architecture specs, "How-To" contributor guides, Mathematical theory notes, Scenario catalog, and automated docstrings. |

---

## 3. Component Architecture: Typed Dataclasses vs. Dynamic ECS

### What is an "ECS Framework"?
In game engines and some large simulations, **Entity-Component-System (ECS)** refers to a paradigm where:
- An **Entity** is just an integer ID.
- **Components** are raw, untyped data structs attached to IDs via central tables/bitmasks.
- **Systems** are global functions that iterate over every entity matching a component filter (e.g. `All entities with [Position, Velocity]`).

While powerful for millions of homogeneous game sprites, heavy ECS frameworks introduce runtime indirection, defeat static type checkers (mypy/pyright), obscure call graphs, and complicate scientific reproducibility.

### The Chosen Approach: Lightweight Typed Dataclasses & Protocols
For Chaser, we use **explicit, type-safe Python dataclasses and protocols**:
1. **Explicit Composition**: An `Agent` is a typed dataclass containing explicit slots:
   ```python
   @dataclass(frozen=True, slots=True)
   class Agent:
       id: str
       body: SphereBody | RigidBody
       sensors: tuple[Sensor, ...]
       policy: DecisionPolicy
       actuators: ActuatorSet
       actuator_response: ActuatorResponse
       style: VisualStyle
   ```
2. **Strict Protocol Contracts**: Sensors, policies, paths, and contact finders adhere to structural `Protocol`s. Any component can be swapped or mocked in unit tests without base class inheritance or registry overhead.
3. **Full IDE Support & Immutability**: All states and events are immutable (`frozen=True, slots=True`), eliminating hidden side-effects and enabling safe parallel execution across multi-core experiment sweeps.

---

## 4. Trajectory Architecture: Seamless Analytic & Adaptive Numerical Integration

Continuous steering, turning rate limits ($\dot{\theta}_{\max}$), aerodynamic lift, and maneuvering targets will become the norm. The architecture must ensure that **analytic paths and numerical paths are 100% interchangeable without changing any surrounding simulation code**.

### The Unified `Path` Protocol Contract
```python
class Path(Protocol):
    """Time-addressable trajectory in simulation space."""
    
    start_time: float
    end_time: float | None  # None indicates path extends indefinitely
    
    def state_at(self, time: float) -> KinematicState:
        """Return position, velocity, and acceleration at time t."""
        ...
```

### Dense-Output & Memoization for Numerical Integration
A key challenge with numerical ODE integration (e.g. Dormand-Prince RK45) in an event-driven simulator is that root-finding algorithms (such as `_earliest_circle_contact_by_bracketing` or Brent's method) query `state_at(time)` at arbitrary intermediate points during bisection:
- **Requirement**: Numerical paths must implement **memoized forward integration with continuous dense-output interpolation** (Hermite spline / RK polynomial).
- **Behavior**:
  - When `state_at(t)` is queried at $t > t_{\text{cached}}$, the integrator steps forward to $t$ (or slightly beyond) using adaptive step sizes and caches the integration steps.
  - When `state_at(t)` is queried at an intermediate time $t \le t_{\text{cached}}$ during a collision search, it performs an $O(1)$ polynomial interpolation between the cached step boundaries.
  - No re-integration from $t_0$ is ever performed on repeated bisection queries.

```text
[Continuous Dynamics ODE: dx/dt = f(t, x, u(t))]
                 │
                 ▼
[Adaptive Step Integrator (RK45)] ──> [Step History Cache]
                 │                                │
                 ▼                                ▼
[Continuous Dense Polynomial] <──────── [Interpolation Window]
                 │
                 ▼
[state_at(t) -> KinematicState (O(1) continuous evaluation)]
```

With this contract, collision finders, visualizers, sensors, and the event runtime treat `ConstantAccelerationPath`, `ConstantThrustQuadraticDragPath`, and `AdaptiveNumericalPath` identically.

---

## 5. 3D Readiness Strategy

3D spatial models and non-planar geometry are planned. To prepare for 3D without over-engineering Phase 1:
1. **Coordinate Conventions**: Right-handed Cartesian:
   - $+X$: Down-range / forward motion
   - $+Y$: Cross-range / lateral
   - $+Z$: Altitude / vertical (upwards)
2. **Interface Stubs & Class Structures in Phase 1**:
   - `chaser.math.vec3.Vec3`: Vector algebra ($x, y, z$, dot, cross, norm, polar/spherical conversions).
   - `chaser.kinematics.path.Path3D`: 3D kinematic trajectory protocol.
   - `chaser.collision.sphere_contact.SphereContactDetector`: Protocol and stub for 3D sphere-sphere continuous contact.
   - `chaser.physics.bodies.RigidBody`: General mass/inertia specification.
3. **2D as a Subspace**: 2D planes are treated as a special case ($Z=0$), ensuring algorithms migrate directly to 3D when needed.

---

## 6. Target Module & Package Structure

```text
src/chaser/
├── core/                       # Pure discrete-event simulation kernel
│   ├── __init__.py
│   ├── event.py                # ModelEvent, EventRecord
│   ├── runtime.py              # EventDrivenRuntime, EventDrivenModel protocol
│   └── types.py                # Identifiers, Time, generic typevars
│
├── math/                       # Linear algebra & geometry
│   ├── __init__.py
│   ├── vec2.py                 # Vec2 (2D planar vectors)
│   ├── vec3.py                 # Vec3 (3D vector stub & math)
│   └── transforms.py           # Coordinate frame rotations / projections
│
├── numerics/                   # Numerical methods & root finding
│   ├── __init__.py
│   ├── roots.py                # Polynomial root isolation, interval bisection, Brent's method
│   ├── interpolation.py        # Cubic Hermite & dense polynomial interpolators
│   └── ode.py                  # Adaptive RK45 numerical integrator
│
├── kinematics/                 # Trajectory & motion path abstractions
│   ├── __init__.py
│   ├── state.py                # KinematicState (pos, vel, acc)
│   ├── path.py                 # Path2D, Path3D protocols, PiecewisePath
│   ├── constant_acceleration.py # ConstantAccelerationPath
│   └── numerical_path.py       # DenseNumericalPath (adaptive continuous-steering path)
│
├── physics/                    # Physical models & dynamics
│   ├── __init__.py
│   ├── bodies.py               # SphereBody, RigidBody, mass properties
│   ├── atmosphere.py           # UniformAtmosphere, USStandardAtmosphere76
│   ├── aerodynamics.py         # SphereQuadraticDrag, DragModel protocol
│   └── drag_paths.py           # ConstantThrustQuadraticDragPath
│
├── collision/                  # Geometric intersection & contact detection
│   ├── __init__.py
│   ├── detector.py             # ContactDetector protocol
│   ├── circle_contact.py       # Analytic & bracketed circle-circle contact
│   └── sphere_contact.py       # Sphere-sphere contact (3D stub & bracketed search)
│
├── components/                 # Reusable agent building blocks
│   ├── __init__.py
│   ├── sensors/                # Sensor protocols & models
│   │   ├── __init__.py
│   │   ├── base.py             # Sensor protocol, Observation types
│   │   ├── visual.py           # DirectVisualSensor, NoisyVisualSensor, FOVSensor
│   │   └── periodic.py         # PeriodicScanningSensor
│   ├── actuators/              # Actuator models
│   │   ├── __init__.py
│   │   ├── base.py             # ActuatorDefinition, ActuatorSet
│   │   └── responses.py        # PlanarThrustResponse, GimballedThrustResponse
│   └── policies/               # Decision & guidance policies
│       ├── __init__.py
│       ├── base.py             # DecisionPolicy protocol
│       ├── intercept/          # Single-chaser intercept algorithms
│       │   ├── quadratic_drag.py  # QuadraticDragInterceptDecision
│       │   ├── prop_nav.py        # Proportional Navigation (PN)
│       │   └── pure_pursuit.py    # Pure pursuit / Lead pursuit
│       ├── cooperative/        # Multi-chaser algorithms (1-vs-2 comparison)
│       │   ├── dual_pincer.py     # Flanking / Pincer interception
│       │   └── assignment.py      # Lead-Trail role assignment
│       └── target/             # Target behavior policies
│           ├── constant_velocity.py
│           └── evasive.py         # Zig-zag, reactive evasion
│
├── entities/                   # High-level Agent/Object abstractions
│   ├── __init__.py
│   ├── agent.py                # Agent dataclass (body, sensors, policy, actuators, path)
│   └── visual_style.py         # Color, icon, trail configuration for visualization
│
├── engine/                     # Composable Arena simulation engine
│   ├── __init__.py
│   ├── arena.py                # ComposableArenaModel (DRY discrete-event coordinator)
│   ├── rules.py                # InteractionRule, TerminationCondition, ScoringPolicy
│   └── record.py               # Universal SimulationRecord, TrackRecord, Telemetry
│
├── scenarios/                  # Declarative scenario definitions
│   ├── __init__.py
│   ├── registry.py             # ScenarioRegistry (for CLI & experiment discovery)
│   ├── base.py                 # Scenario protocol & ScenarioConfig base
│   ├── red_goal/               # First baseline scenario
│   │   ├── __init__.py
│   │   ├── scenario.py         # RedGoalScenario definition
│   │   └── settings.py         # RedGoalSettings
│   ├── dual_chaser/            # Two chasers vs one red target
│   │   ├── __init__.py
│   │   ├── scenario.py         # DualChaserScenario
│   │   └── settings.py
│   └── evasive_target/         # Chaser vs maneuvering target
│       ├── __init__.py
│       └── scenario.py
│
├── experiments/                # Parameter sweeps & comparative studies
│   ├── __init__.py
│   ├── sweep.py                # ParameterGrid, MonteCarloSampler, BatchRunner
│   ├── comparison.py           # ComparativeStudy (e.g. Single vs Dual Chaser benchmark)
│   ├── metrics.py              # Metric aggregators (success rate, catch time, fuel)
│   └── plots.py                # SVG & Matplotlib figure generators
│
├── visualization/              # Scenario-agnostic visualization pipeline
│   ├── __init__.py
│   ├── projection.py           # Universal 2D/3D screen projection engine
│   ├── sdl.py                  # Universal SDL renderer & playback
│   ├── static_plots.py         # Generic reachability / contour / trajectory plotter
│   └── themes.py               # Color palettes & visual themes
│
└── cli.py                      # Unified CLI with subcommand & scenario discovery
```

---

## 7. Key Architectural Patterns for DRY & Rapid Experimentation

### Pattern 1: The Generic `ComposableArenaModel`
Scenarios instantiate `ComposableArenaModel` rather than implementing raw event loops:
```python
class ComposableArenaModel(EventDrivenModel[SimulationRecord]):
    """Generic discrete-event arena that coordinates arbitrary agents,
    sensors, policies, actuators, and interaction rules."""
    
    def __init__(
        self,
        agents: Mapping[str, Agent],
        interaction_rules: Sequence[InteractionRule],
        termination_conditions: Sequence[TerminationCondition],
        scoring_policy: ScoringPolicy | None = None,
    ): ...
```

### Pattern 2: Universal `SimulationRecord` & Scenario-Agnostic Visualizer
```python
@dataclass(frozen=True, slots=True)
class TrackRecord:
    entity_id: str
    display_name: str
    shape: Shape2D  # Circle(radius), Polygon, etc.
    style: VisualStyle  # color, trail_color, show_vector_thrust
    path: Path

@dataclass(frozen=True, slots=True)
class SimulationRecord:
    scenario_id: str
    outcome: str
    duration_s: float
    events: tuple[EventRecord, ...]
    tracks: Mapping[str, TrackRecord]
    metrics: Mapping[str, float | str | None]
```
The `ProjectionEngine` and `SDLPlayback` consume `SimulationRecord` directly without scenario-specific code.

### Pattern 3: Comparative Experimentation & Parameter Sweeps
```python
sweep = ParameterSweep(
    scenario=DualChaserScenario(),
    parameters={
        "blue_start": [Vec2(x, y) for x in range(1000, 9000, 1000) for y in range(-4000, 4000, 1000)],
        "blue_max_acceleration": [100.0, 250.0, 500.0],
        "chaser_policy": ["dual_pincer", "independent_intercept"],
    },
    metrics=["outcome", "catch_score_m", "duration_s", "energy_consumed"],
)
results = sweep.run_parallel(max_workers=8)
results.plot_comparative_heatmap("chaser_policy", "catch_score_m")
```

---

## 8. Comprehensive Documentation Strategy (Diátaxis)

```text
docs/
├── architecture/                   # Explanation & System Architecture
│   ├── overview.md                 # System overview & layer boundaries
│   ├── event-driven-runtime.md     # Discrete-event mechanics vs fixed-step
│   ├── agent-component-model.md    # Typed Agent, Sensor, Policy, Actuator abstractions
│   ├── trajectory-and-numerics.md  # Unified Path contract, analytic & RK45 dense paths
│   ├── arena-and-interactions.md   # Arena event loop & collision detection
│   └── visualizer-pipeline.md      # Projection & rendering architecture
│
├── guides/                         # How-To Guides (Action-oriented, practical)
│   ├── 01-creating-a-scenario.md   # Step-by-step: Write a new scenario in 15 minutes
│   ├── 02-implementing-policies.md # Writing new guidance & intercept algorithms
│   ├── 03-custom-physics-paths.md  # Adding new drag models, thrust profiles, paths
│   ├── 04-multi-agent-setups.md    # Configuring multi-chaser / team coordination
│   └── 05-running-sweeps.md        # Running parameter sweeps and batch benchmarks
│
├── reference/                      # Technical Reference (Information-oriented)
│   ├── core-api.md                 # EventDrivenRuntime, ModelEvent, EventRecord
│   ├── kinematics-and-math.md      # Vec2, Vec3, Path, KinematicState contracts
│   ├── component-catalog.md        # Catalog of existing sensors, actuators, policies
│   ├── scenario-registry.md        # Registered scenarios and their settings schemas
│   └── cli-reference.md            # Command-line interface usage & examples
│
├── scenarios/                      # Scenario Specifications & Research Questions
│   ├── readme.md                   # Scenario catalog & research questions index
│   ├── 01-red-target-blue-goal.md  # Single chaser baseline (current)
│   ├── 02-dual-chaser-pincer.md    # Dual chaser comparative benchmark
│   └── 03-evasive-maneuvers.md     # Evasive target study
│
└── theory/                         # Theoretical & Mathematical Foundations
    ├── analytic-paths.md           # Derivation of constant-thrust quadratic drag equations
    ├── numerical-dense-paths.md    # Hermite spline & RK45 dense output evaluation
    ├── circle-intersections.md     # Polynomial root isolation for 4th degree relative paths
    └── aerodynamic-drag.md         # Atmospheric assumptions, Mach/Reynolds limitations
```

---

## 9. Refactoring Roadmap (Phased & Non-Breaking)

### Phase 1: Mathematical, Numerical & Component Decomposition (Zero Functional Change)
- Extract `Vec2` to `chaser.math.vec2`, define `Vec3` stub in `chaser.math.vec3`.
- Extract root-finding to `chaser.numerics.roots`.
- Define `Path` protocol and `KinematicState` in `chaser.kinematics`.
- Build `DenseNumericalPath` and dense interpolation utilities in `chaser.numerics` and `chaser.kinematics`.
- Extract collision detection to `chaser.collision.circle_contact`, stub `sphere_contact`.
- Extract `SphereBody`, `UniformAtmosphere`, `SphereQuadraticDrag`, `ConstantThrustQuadraticDragPath` into `chaser.physics`.
- Extract `ActuatorSet`, `Sensors`, and `Decision` into `chaser.components`.
- *Verification*: Existing tests pass with 100% backward compatibility via module re-exports.

### Phase 2: Composable Arena & Universal Simulation Record
- Implement `chaser.entities.Agent` and `TrackRecord`.
- Implement `chaser.engine.ComposableArenaModel`.
- Generalize `chaser.visualization.projection` to render arbitrary tracks without hardcoded IDs.
- Port `RedGoalScenario` to use `ComposableArenaModel` and verify numerical equivalence with existing baseline tests.

### Phase 3: Scenario Registry & Dual-Chaser Scenario
- Create `ScenarioRegistry` and standardized `Scenario` protocol.
- Implement `DualChaserScenario` (two blue chasers vs red target) to fulfill the primary comparative research goal.
- Implement cooperative guidance policies (`DualPincerPolicy`, `LeadTrailPolicy`).

### Phase 4: Experimentation & Parameter Sweeps Harness
- Build `chaser.experiments` batch execution, grid sweep, and metric aggregator.
- Build comparative visualizer (SVG/Matplotlib plots comparing 1-chaser vs 2-chaser capture envelopes).
- Update CLI with `chaser list`, `chaser run`, `chaser visualize`, `chaser sweep`, and `chaser compare`.

### Phase 5: Documentation Suite Completion
- Author the complete guide set (`01-creating-a-scenario.md`, `02-implementing-policies.md`, etc.).
- Update design documents to reflect the componentized architecture.
