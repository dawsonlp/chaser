# Guide: Creating a New Simulation Scenario

With the `ComposableArenaModel`, creating a new pursuit scenario requires only defining the participating agents, interaction rules, and registering the scenario.

## Step-by-Step Walkthrough

### 1. Define Settings
Create a dataclass with the scenario's initial parameters:
```python
@dataclass(frozen=True, slots=True)
class CustomSettings:
    target_speed: float = 800.0
    chaser_acc: float = 400.0
```

### 2. Assemble Agents
Instantiate `Agent` records for each participant:
```python
from chaser.entities.agent import Agent
from chaser.entities.visual_style import CircleShape, VisualStyle, BLUE_COLOR, RED_COLOR

agents = {
    "chaser": Agent(
        id="chaser",
        display_name="Interceptor",
        shape=CircleShape(0.05),
        initial_path=initial_chaser_path,
        sensors=(DirectVisualSensor(),),
        policy=PurePursuitPolicy(maximum_acceleration=400.0),
        target_id="target",
        style=VisualStyle(color=BLUE_COLOR),
    ),
    "target": Agent(
        id="target",
        display_name="Target",
        shape=CircleShape(100.0),
        initial_path=target_path,
        style=VisualStyle(color=RED_COLOR),
    ),
}
```

### 3. Define Interaction Rules
```python
rules = [
    InteractionRule("chaser", "target", "intercept_event", outcome="target_intercepted", priority=20),
    InteractionRule("target", "goal", "goal_event", outcome="target_escaped", priority=10),
]
```

### 4. Run through `ComposableArenaModel`
```python
model = ComposableArenaModel(
    scenario_id="custom_scenario",
    agents=agents,
    interaction_rules=rules,
)
record = EventDrivenRuntime().run(model)
```

### 5. Register Scenario
```python
ScenarioRegistry.register("custom_scenario", lambda: CustomScenario())
```
Once registered, the scenario is immediately available via `chaser simulate --scenario custom_scenario` and `chaser visualize --scenario custom_scenario`!

