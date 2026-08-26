# Evasive Red Target vs Single Blue Interceptor

## Scenario

This scenario tests an active target equipped with:
- **Periodic Visual Threat Sensor**: Scans every $\Delta t$ seconds (e.g. $0.25\,\text{s}$) to detect closing pursuers.
- **Sideways Evasion & Goal Re-Steering Policy**:
  - When an incoming threat is detected, executes a lateral thrust burst away from the pursuer's approach vector.
  - Once clear of the pursuer, computes the corrective vector to the goal and re-steers toward $(10200, 0)$.

## Running

```shell
uv run chaser simulate --scenario evasive_target
uv run chaser visualize --scenario evasive_target
```

