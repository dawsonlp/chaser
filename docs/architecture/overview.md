# System Architecture Overview

The Chaser simulation engine is designed for discrete-event multi-agent pursuit simulation, trajectory analysis, and visual projection.

## Architectural Layers

```text
┌────────────────────────────────────────────────────────┐
│                   CLI & Experiments                    │
│   chaser (simulate/visualize/compare/sweep), Harness   │
├────────────────────────────────────────────────────────┤
│                       Scenarios                        │
│   red_goal, dual_chaser, ScenarioRegistry              │
├────────────────────────────────────────────────────────┤
│                   Composable Arena                     │
│   ComposableArenaModel, InteractionRule, Record        │
├────────────────────────────────────────────────────────┤
│             Components & High-Level Entities           │
│   Agent, Sensors, DecisionPolicy, Actuators, Style     │
├────────────────────────────────────────────────────────┤
│             Kinematics, Collision & Physics            │
│   Path, KinematicState, CircleContact, Atmosphere, Drag│
├────────────────────────────────────────────────────────┤
│                   Math & Numerics                      │
│   Vec2, Vec3, Roots, Cubic Hermite, RK45 Integrator    │
├────────────────────────────────────────────────────────┤
│                   Core Event Kernel                    │
│   EventDrivenRuntime, ModelEvent, EventRecord          │
└────────────────────────────────────────────────────────┘
```

## Core Principles

1. **Discrete-Event Simulation (Continuous Time)**: The simulation advances only to model events (observations, decisions, actuator updates, collisions) rather than advancing in fixed time steps.
2. **Unified `Path` Trajectory Contract**: Both analytic paths and adaptive numerical integration paths implement `state_at(time: float) -> KinematicState`.
3. **Decoupled Entities and Policies**: Agents are composed of typed, immutable dataclasses. Guidance policies are pure decision algorithms with zero knowledge of global simulation state beyond their sensor observations.
4. **Universal Simulation Records**: Completed runs are stored in standardized `SimulationRecord` objects, allowing universal SDL playback and projection without writing UI code for each scenario.
