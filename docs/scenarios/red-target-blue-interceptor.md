# Red target, blue interceptor, and goal post

## Scenario

The first scenario takes place in two dimensions and contains:

- A red circular object attempting to score
- A blue circular object attempting to chase or intercept the red object
- A goal post represented by a third circle

The red object scores by hitting the goal post. The blue object attempts to prevent that outcome by catching or intercepting the red object.

## Model rules used by this scenario

- Items can have speed and acceleration.
- Each item can have its own set of actuators, each with a current value.
- An item's decision-making algorithm uses its sensor observations to choose which actuator values to change.
- The item's model determines the effects of its actuator values. Those effects may include causing acceleration, redirecting acceleration, or something else.

## Initial settings

1. The goal post is on the right side of the field.
2. The red circle enters from the far left, `10 km` from the goal post, moving toward it at `1,000 m/s`.
3. At that speed, the red circle will reach the goal in `10 seconds` if it is not intercepted.
4. The blue circle begins at rest at a deliberately selected position on the field. Its position is an experiment input rather than a random placement.

The first runnable configuration supplies these adjustable defaults:

| Setting | Default |
| --- | --- |
| Red start | `(0 m, 0 m)` |
| Goal center | `(10,200 m, 0 m)` |
| Blue start | `(4,000 m, -2,500 m)` |
| Red velocity | `(1,000 m/s, 0 m/s)` and constant |
| Blue velocity | `(0 m/s, 0 m/s)` |
| Red and goal radii | `100 m` each |
| Blue diameter | `0.1 m` |
| Blue material density | `7,850 kg/m³` (configured steel baseline) |
| Blue derived mass | approximately `4.110 kg` |
| Blue low-speed acceleration | `500 m/s²` |
| Blue derived constant thrust | approximately `2,055 N` |
| Air density | `1.225 kg/m³` (uniform sea-level baseline) |
| Sphere drag coefficient | `0.47` (configurable first-order baseline) |

The goal center includes the red and goal radii, leaving `10 km` between their surfaces at the start. This preserves the specified `10-second` time to contact.

## Run behavior

1. The blue circle senses the red circle visually.
2. Using that sensor observation, the blue circle's decision-making algorithm determines an intended interception trajectory and chooses which actuator values to change.
3. The blue circle accelerates in an attempt to hit the red circle before the red circle hits the goal post.

The intended trajectory informs the decision. The decision's outward action is a set of requested actuator-value changes. The blue circle's actual trajectory results from the actuator state and object model.

The first visual sensor reports red's exact position and velocity relative to blue when red enters. It has no range, delay, error, or later observation in this initial model.

Blue's first actuator set contains a thrust-acceleration magnitude and thrust direction. The magnitude states how quickly that thrust would accelerate this object's mass when drag is negligible. The object model converts it to force from the blue object's derived mass. The initial decision algorithm uses the observation and the drag-limited path to request actuator values for an intercept. These are replaceable first-model choices, not universal actuator semantics.

## Blue atmospheric motion

The blue object is a sphere with radius `0.05 m`. Its volume, frontal area, and mass are derived from that geometry and the configured material density. Aerodynamic drag follows

`drag force = 0.5 × air density × drag coefficient × frontal area × speed²`

and acts opposite the velocity. With constant thrust, constant air density, and a constant drag coefficient, the implementation evaluates the resulting path analytically between events. The simulator therefore still advances to observation, decision, actuator-change, and contact events rather than advancing through equal simulation time steps. Numeric intervals used to locate a contact are an event-root search, not state-update steps.

This is a first-order physical model, not a complete high-supersonic atmosphere model. The current run assumes still air of uniform sea-level density, no gravity, no altitude change, and a constant sphere drag coefficient. A real sphere's drag coefficient changes with Reynolds number and Mach number, particularly through transonic and supersonic flow. The coefficient and air density are explicit settings so a later model can replace those assumptions without changing the actuator, decision, or event-runtime boundaries.

The formula and its dependence on density, speed, area, and coefficient follow NASA Glenn's [drag equation](https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/drag-equation/). NASA's [sphere-drag discussion](https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/drag-of-a-sphere/) is the basis for treating the constant coefficient as a stated limitation rather than as complete sphere behavior. The sea-level density baseline comes from the [U.S. Standard Atmosphere, 1976](https://ntrs.nasa.gov/api/citations/20060053240/downloads/20060053240.pdf).

## Outcome and score

- Blue wins the round if it hits the red circle before the red circle hits the goal post.
- Red wins the round if it hits the goal post first.
- A successful blue interception receives a catch score equal to the remaining surface-to-surface clearance between red and the goal, in meters. Greater clearance produces a higher score.

## Presentation

The scenario is visualized on a square grid. The grid should be light enough to provide a spatial reference without obscuring the motion of the red and blue objects or the goal post.

The scenario also provides a placement-region plot. For each requested acceleration capability, it takes the union of blue's drag-limited reachable contact circles over the interval before red reaches the goal. The nested colors therefore mean "minimum low-speed acceleration capability that permits an intercept from this starting position." The calculation samples continuous path equations to construct the plotted boundary; it does not advance a simulation through equal time steps.

Current plot: [successful starting regions](../plots/intercept-regions.svg).

## Current implementation and open choices

The simulation currently has no field boundary. The projection fits the recorded paths on screen and draws grid lines every `1 km`. A blue-red or red-goal outcome occurs at the first surface contact between the relevant circles.

The set of blue placements to compare, any placement constraints, and whether later experiments replace the ideal sensor, constant red velocity, actuator set, decision algorithm, or acceleration limit remain open.
