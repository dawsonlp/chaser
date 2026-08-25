# Load-bearing design decisions

1. **The initial question is comparative.** The project will compare one automated chaser with two automated chasers pursuing an automated target.

2. **The first case is two-dimensional.** It will use simple circular objects moving on a two-dimensional plane.

3. **The first case does not define the architecture.** Space and object models must be replaceable so later cases can use three-dimensional space, complex surfaces, different shapes, or different physical behavior.

4. **The simulation is event-driven.** A global sequence of equal time steps will not define how the simulation advances.

5. **Motion is determined between events.** While the relevant conditions remain unchanged, an object's path is derived by integrating its current model. When an event changes those conditions, the path is determined again.

6. **Core simulation concerns are separable.** The architecture must allow the space, object behavior, sensors, contact or collision detection, and object decision-making to vary independently of the first case.

7. **Decisions change object-owned actuator values.** Each object can have a set of actuators with current values. Its decision-making algorithm may choose which actuator values to change. The object model determines the effects of those actuators, which may include causing acceleration, redirecting acceleration, or something else. The decision-making algorithm does not directly assign the object's actual trajectory.

8. **Decisions use sensor observations.** Each object has sensors. Its decision-making algorithm uses the observations produced by those sensors to decide how to operate the object's actuators; it does not receive unrestricted simulation state directly.

9. **Results are visualized through projection.** The simulator's results will be projected into a video representation of what occurred. The visualization represents simulation output; it does not define the simulated space or drive simulation state.

10. **Use cases remain separate scenarios.** Each use case defines and presents its own participants, objectives, environment, and visualization choices without turning those choices into rules of the simulation core.

Examples discussed for future exploration are not design commitments. No implementation language, API structure, numerical method, event-scheduling mechanism, exact sensor set, exact actuator set, projection method, rendering technology, video format, or later physical model has been selected.

## Proposed designs

- [System componentization](system-componentization.md) — a draft for review, not an approved load-bearing decision
