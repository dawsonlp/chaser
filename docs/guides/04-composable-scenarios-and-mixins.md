# Guide: Composable Scenarios & Component Catalog

Chaser provides a catalog and builder architecture so you can freely mix and match algorithms, guidance policies, sensors, and agent configurations without writing boilerplate simulation classes.

## 1. Inspecting the Catalog

To view all available algorithms and machinery:

```shell
uv run chaser catalog
```

Output:
```text
Component Catalog:

--- Available Policies ---
  - straight_line             : Passive target maintaining constant velocity without maneuvers.
  - quadratic_drag            : Drag-compensated optimal lead intercept guidance.
  - pure_pursuit              : Direct pure pursuit steering directly at the target's current position.
  - dual_pincer               : Cooperative pincer guidance calculating independent lead intercepts from each flank.
  - adaptive_intercept        : Recalculates optimal drag-compensated intercept whenever target maneuvers.
  - evasive_goal_steering     : Active threat detection, lateral dodge burst, and corrective goal re-targeting.

--- Available Sensors ---
  - direct_visual             : Continuous direct observation of target position and relative velocity.
  - periodic_threat           : Periodic scanning sensor measuring threat closing speed and distance.
```

---

## 2. Composing Scenarios via CLI (`chaser compose`)

Mix and match chaser counts, guidance algorithms, and target evasion behaviors directly from the command line:

```shell
# 2 Chasers using Dual Pincer vs Active Evasive Target (Visualized in SDL)
uv run chaser compose --chasers 2 --chaser-policy dual_pincer --target-policy evasive_goal_steering --visualize

# 1 Chaser with Pure Pursuit vs Passive Target
uv run chaser compose --chasers 1 --chaser-policy pure_pursuit --target-policy straight_line

# Custom starting coordinates and evasion burst acceleration
uv run chaser compose --chasers 2 --chaser-1-x 3500 --chaser-1-y -2000 --target-policy evasive_goal_steering --target-evade-acc 400
```

---

## 3. Running Policy Tournament Matrix (`chaser matrix`)

Evaluate all chaser strategies against all target counter-strategies in an automated benchmark matrix:

```shell
uv run chaser matrix
```

Output:
```text
Chaser Team               | Target Strategy           | Outcome              | Time (s) | Score (m) 
-----------------------------------------------------------------------------------------------
1 Chaser (Direct Intercept) | Passive Target            | blue_intercepted     | 3.84     | 6158.1    
1 Chaser (Direct Intercept) | Evasive Target            | target_scored        | 15.32    | N/A       
1 Chaser (Pure Pursuit)   | Passive Target            | target_scored        | 10.00    | N/A       
1 Chaser (Pure Pursuit)   | Evasive Target            | target_scored        | 10.73    | N/A       
2 Chasers (Pincer Flank)  | Passive Target            | blue_2_intercepted   | 3.33     | 6672.5    
2 Chasers (Pincer Flank)  | Evasive Target            | target_scored        | 15.32    | N/A       
```

---

## 4. Programmatic Python Composition

```python
from chaser.builder import ScenarioConfig, run_composed_scenario
from chaser.math import Vec2

config = ScenarioConfig.create(
    chaser_count=2,
    chaser_policy="dual_pincer",
    chaser_acc=600.0,
    target_policy="evasive_goal_steering",
    target_evade_acc=350.0,
)

record = run_composed_scenario(config)
print(f"Outcome: {record.outcome}, Time: {record.duration_s:.2f}s")
```

