# Two Cooperative Blue Chasers vs Red Target

## Scenario

This scenario compares how effectively two automated chasers (`blue_1` and `blue_2`) intercept an automated target (`red`) relative to a single chaser.

- `blue_1` (Lead): Intercepts on a direct lead trajectory.
- `blue_2` (Wing): Intercepts with a flanking/cutoff offset to bracket or envelope maneuvers.
- `red` (Target): Crosses the field toward the goal.
- `goal`: Circular goal post.

## Running

```shell
uv run chaser simulate --scenario dual_chaser
uv run chaser visualize --scenario dual_chaser
```
