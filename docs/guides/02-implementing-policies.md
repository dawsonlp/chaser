# Guide: Implementing Guidance & Decision Policies

Policies define the autonomous behavior of chasers or targets.

## The `DecisionPolicy` Protocol

```python
class DecisionPolicy(Protocol):
    def choose_actuator_changes(
        self,
        observation: VisualObservation,
    ) -> Mapping[str, float]: ...
```

## Example 1: Proportional Navigation (PN)

```python
@dataclass(frozen=True, slots=True)
class ProportionalNavigationPolicy:
    navigation_gain: float = 3.0
    max_acc: float = 500.0

    def choose_actuator_changes(self, obs: VisualObservation) -> Mapping[str, float]:
        r = obs.relative_position
        v = obs.relative_velocity
        los_rate = r.cross_2d(v) / r.magnitude_squared
        desired_acc = self.navigation_gain * obs.relative_velocity.magnitude * los_rate
        return {
            "thrust_acceleration": min(self.max_acc, abs(desired_acc)),
            "thrust_direction": r.direction(),
        }
```

## Example 2: Cooperative Flanking Policy

Cooperative policies use assigned agent roles (e.g. `lead` vs `wing`) or distributed negotiation to envelope the target:

```python
from chaser.components.policies.cooperative.dual_pincer import DualPincerPolicy

lead_policy = DualPincerPolicy(role="lead", maximum_acceleration=500.0, deadline=10.0, drag=drag)
wing_policy = DualPincerPolicy(role="flank", maximum_acceleration=500.0, deadline=10.0, drag=drag, flank_offset_rad=0.2)
```
