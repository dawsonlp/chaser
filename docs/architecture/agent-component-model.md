# Agent & Component Model

Chaser models simulation participants as **Agents** assembled from typed, lightweight components rather than monolithic classes or heavyweight dynamic ECS systems.

## The `Agent` Dataclass

```python
from chaser.entities.agent import Agent
from chaser.entities.visual_style import CircleShape, VisualStyle, BLUE_COLOR

agent = Agent(
    id="blue_lead",
    display_name="Blue Lead Interceptor",
    shape=CircleShape(radius_m=0.05),
    initial_path=initial_path,
    body=sphere_body,
    sensors=(DirectVisualSensor(),),
    policy=QuadraticDragInterceptDecision(...),
    actuators=actuator_set,
    actuator_response=PlanarThrustResponse(),
    path_builder=build_drag_path,
    target_id="red",
    style=VisualStyle(color=BLUE_COLOR),
)
```

## Component Roles

- **Body (`SphereBody`, `RigidBody`)**: Owns mass, geometric radius, reference area, and material density.
- **Sensors (`Sensor`, `DirectVisualSensor`)**: Converts true simulation state into agent observations (`VisualObservation`).
- **Policy (`DecisionPolicy`)**: Autonomous decision algorithm mapping observations to requested actuator changes.
- **Actuators (`ActuatorSet`, `PlanarThrustResponse`)**: Validates bounds and translates actuator commands into net force or acceleration.
- **Path Builder**: Callback function recreating the agent's `Path2D` when actuator values change.
- **Visual Style (`VisualStyle`)**: Configures display color, trail color, trail visibility, and minimum screen radius for projection and SDL rendering.

