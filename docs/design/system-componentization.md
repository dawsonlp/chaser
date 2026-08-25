# System componentization

**Status:** Implemented for the first scenario; boundaries remain subject to review

## Purpose

Define component boundaries that can model the first pursuit scenario accurately while allowing later scenarios to replace the space, objects, sensors, actuators, behavior, contact rules, and presentation.

## Scope

This design covers responsibility boundaries and collaborations for simulation and visualization. It does not select implementation technology, algorithms, numeric values, or physical rules that have not been specified.

## Inputs consulted

- [Load-bearing design decisions](readme.md)
- [First scenario](../scenarios/red-target-blue-interceptor.md)

## Expected change profile

| Change | Importance | Reason |
| --- | --- | --- |
| Add scenarios | High | Multiple separately presented use cases are expected. |
| Replace space or geometry | High | Two dimensions and circles are only the first case. |
| Replace sensors, decisions, or actuators | High | These are explicit object-level abstractions. |
| Replace motion and contact behavior | High | More realistic physical models are expected later. |
| Replace projection or rendering | Medium | The simulation result must be viewable, but display technology is undecided. |

## Models considered

### Model 1: Independently pluggable capabilities

Each concern is a separately replaceable component: space, object state, sensors, decisions, actuators, motion, contact, scenario, and visualization.

**Boundary:** The simulation runtime coordinates all components through individual interfaces.

**Interfaces and collaboration:** Each capability offers its own domain operation to the runtime; sensors consume access to the modeled situation, decisions consume observations and actuator availability, motion consumes actuator effects, and contact detection consumes compatible paths and geometry.

**Strength:** Maximum independent substitution.

**Risk:** The pieces are not inherently compatible. A sensor, motion model, and collision detector may each expect different representations of space or object state. The runtime can become responsible for translating domain concepts it should not own.

### Model 2: Scenario-owned simulator

Each scenario owns one cohesive simulation model. A shared runner starts it, receives results, and passes them to a visualizer.

**Boundary:** Only run control and result delivery are shared across scenarios.

**Interfaces and collaboration:** A scenario-owned simulator consumes a scenario request and offers a completed simulation record. A separate visualizer consumes that record. All other collaboration remains private to the scenario implementation.

**Strength:** Each scenario can remain internally coherent and accurate without a large universal abstraction.

**Risk:** Sensors, actuators, collision behavior, and motion models become difficult to reuse. Similar scenarios may duplicate most of their implementation.

### Model 3: Compatible model set with a small runtime

A scenario selects a compatible set of domain models. Those models retain explicit responsibility boundaries, but they are assembled and validated together rather than assumed to work in every combination.

The shared runtime knows only how to advance simulation time, apply model-produced events, and record results. It does not interpret coordinates, sensor observations, actuator commands, or collision geometry.

**Strength:** Preserves the abstractions already chosen while keeping compatibility and domain meaning inside a scenario's model set.

**Risk:** The boundary between the generic runtime and a model set must remain narrow. If it expands to include two-dimensional coordinates or acceleration-specific operations, the first scenario will leak into the core.

## Comparison

| Model | Responsibility clarity | Interface simplicity | Change locality | Main tradeoff |
| --- | --- | --- | --- | --- |
| Independently pluggable capabilities | High | Low | Medium | Flexible pieces create a compatibility problem. |
| Scenario-owned simulator | Medium | High | Low across scenarios | Coherence is gained by sacrificing reuse. |
| Compatible model set with a small runtime | High | Medium | High | Requires explicit model-set compatibility. |

## Recommended component model

Use **Model 3: Compatible model set with a small runtime**.

### Components

| Component | Responsibility | State ownership |
| --- | --- | --- |
| Scenario Definition | Selects a compatible model set and supplies participants, initial settings, objectives, and presentation configuration. | Owns scenario configuration. |
| Simulation Runtime | Advances from event to event and coordinates state transitions without interpreting model-owned values. | Owns simulation time and the active run. |
| Space Model | Defines locations, movement context, and spatial relationships required by the selected models. | Defines space-specific values. |
| Object Model | Defines each object's state and behavior and interprets its actuator state as object-specific effects, which may include acceleration effects or other behavior. | Defines object-specific state and behavior. |
| Sensor Model | Produces observations available to an object from the simulated situation. | Defines sensor state and observations. |
| Decision Model | Uses sensor observations to choose how to operate the object's actuators. | Owns decision-specific memory, if any. |
| Actuator Model | Defines the actuators belonging to an object, their current values, and how requested value changes are applied. | Owns actuator state for the object. |
| Motion Model | Determines an object's path between relevant events from its current modeled conditions. | Defines motion-specific state and paths. |
| Interaction Model | Determines contact and scenario outcomes such as interception or reaching the goal. | Defines interaction rules; does not own object state. |
| Simulation Record | Preserves the time-based results needed to reproduce, inspect, and present a run. | Owns the completed run record. |
| Projection Model | Maps model-owned simulation results into a visual scene without changing them. | Owns view configuration. |
| Renderer | Presents projected scenes on screen and produces video frames. | Owns presentation state only. |

These are responsibility-bearing components. The design does not require one class, process, or deployable unit per row.

### High-level interfaces

| Provider | Offers | Main consumers |
| --- | --- | --- |
| Scenario Definition | Configured run and compatible model set | Simulation Runtime |
| Simulation Runtime | Run coordination and completed run | Scenario caller, Simulation Record |
| Space and Object Models | Model-defined state and spatial operations | Sensors, Motion, Interactions |
| Sensor Model | Observations | Decision Model |
| Decision Model | Requested changes to selected actuator values | Actuator Model |
| Actuator Model | Updated object-owned actuator state | Object Model |
| Object Model | Effects resulting from actuator state | Motion Model and other compatible models |
| Motion Model | Paths between relevant events | Runtime, Sensors, Interactions |
| Interaction Model | Model-defined interaction events and outcomes | Simulation Runtime |
| Simulation Record | Time-based run results | Projection Model, inspection tools |
| Projection Model | Visual scenes | Renderer |
| Renderer | On-screen presentation and video frames | Human viewer |

### Collaboration

```text
Scenario Definition
        |
        v
Simulation Runtime <---- compatible model set
        |                    |
        |              Space + Objects
        |                    |
        |              Sensors -> Decisions
        |                    |
        |       Actuator values -> Object effects -> Motion
        |                    |
        |                 Interactions
        v
Simulation Record -> Projection Model -> Renderer -> screen/video
```

During a run, sensors expose observations to a decision model. The decision model chooses new values for some of the actuators belonging to its object. Actuators not selected by that decision retain their current values. The object model determines the consequences of the resulting actuator state. A compatible motion model uses any motion effects to determine the object's path. The interaction model identifies relevant outcomes. The runtime coordinates these changes at event times and records the result.

Visualization is downstream. It samples and projects the recorded result for human viewing; its frame rate does not advance simulation time.

## Application to the first scenario

The first scenario's model set will provide:

- A two-dimensional plane as its space
- Red, blue, and goal-post circles as its objects
- An initial ideal visual sensor that reports red's exact relative position and velocity at entry
- A blue decision model that plans an interception from sensor observations
- An object-owned acceleration-magnitude and acceleration-direction actuator set for blue
- A constant-velocity red motion model and a thrust-plus-atmospheric-drag blue motion model
- Interaction rules for blue-red contact and red-goal contact
- A projection showing the three circles on a light square grid
- A renderer capable of presenting the projected run on screen as video

For the initial settings, the goal is on the right side of the field. The red object enters from the far left, `10 km` from the goal, at `1,000 m/s`, giving it an uninterrupted time-to-goal of `10 seconds`. The blue object begins at rest at a deliberately configured experiment position. These values configure a run; they are not rules of the simulation model.

The model set must determine whether blue-red contact occurs before red-goal contact without granting the blue decision model access to state that its visual sensor did not report.

A successful interception is scored by its distance from the goal, with greater distance producing a higher score. The scoring formula remains a scenario policy rather than a simulation-runtime responsibility.

The first runnable settings retain `100 m` red and goal radii. Blue is a `0.1 m` diameter sphere whose mass is derived from a configured steel density. Its thrust is sized to produce `500 m/s²` when aerodynamic drag is negligible. Air density and sphere drag coefficient are explicit scenario settings. Catch score is the remaining red-to-goal surface clearance in meters. These are scenario settings and replaceable first-model choices.

## Accuracy boundary

The design can ensure that the simulator faithfully executes the selected models and does not give decision models information or capabilities outside those models. It cannot establish physical accuracy until the scenario's geometry, sensor behavior, controls, dynamics, and contact rules are specified and validated. The first implementation should therefore report which model assumptions produced a result rather than present the visualization alone as proof of real-world behavior.

## Constraints for later architecture

- Scenario-specific models must not become dependencies of the simulation runtime.
- Decision models receive sensor observations rather than unrestricted simulation state.
- Decision models request changes to object-owned actuator values rather than directly assigning effects or actual motion.
- Visualization consumes simulation results and cannot determine simulation outcomes.
- A scenario must select a mutually compatible set of models.
- Model-owned values remain opaque to components that do not need to interpret them.

## First implementation choices, not architectural constraints

- Python 3.12 or newer
- A small priority-queue event runtime
- Analytic constant-acceleration and constant-thrust/quadratic-drag paths, with event-root isolation for circular contact
- SDL 3.4.14 with PySDL3 0.9.11b1 for on-screen presentation

## Decisions explicitly deferred beyond the first implementation

- A general mechanism for declaring or validating model-set compatibility
- Sensor models beyond the initial ideal entry observation
- Actuator models beyond the initial acceleration magnitude and direction values
- Mach- and Reynolds-dependent sphere drag, changing atmospheric conditions, gravity, and physical validation of the thrust limit
- Blue-placement conditions for comparable experiments
- Encoded video-file output

## Remaining experiment questions

1. Which blue starting positions should form the first comparison set, and what placement constraints make their scores comparable?
2. Is `500 m/s²` the intended acceleration limit or only a provisional runnable default?
3. Which idealized sensor assumptions should be relaxed first?
4. Does the simulated field eventually need boundaries or terrain behavior?
5. What information should be added to the on-screen visualization beyond the circles, paths, light grid, time, and outcome?
