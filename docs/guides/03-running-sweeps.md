# Guide: Running Parameter Sweeps & Comparative Studies

Chaser includes an experiment harness for executing batch trials and comparative studies.

## 1. Running a Parameter Grid Sweep

```python
from chaser.experiments.sweep import ParameterSweep
from chaser.math import Vec2
from chaser.scenarios.red_goal import RedGoalScenario, RedGoalSettings

sweep = ParameterSweep(
    scenario=RedGoalScenario(),
    parameter_grid={
        "blue_start": [Vec2(2000, -2000), Vec2(4000, -2500), Vec2(6000, -3000)],
        "acceleration": [100.0, 250.0, 500.0],
    },
    settings_factory=lambda p: RedGoalSettings(
        blue_start=p["blue_start"],
        blue_max_acceleration_mps2=p["acceleration"],
    ),
)
result = sweep.run()
print(f"Success rate: {result.success_rate * 100:.1f}% ({result.successful_intercepts}/{result.total_runs})")
```

## 2. Comparative 1-vs-2 Chaser Benchmark

Run the comparative study from Python:
```python
from chaser.experiments.comparison import SingleVsDualChaserStudy
from chaser.math import Vec2

study = SingleVsDualChaserStudy(
    test_positions=[Vec2(x, y) for x in range(2000, 8000, 1000) for y in [-2500, 2500]],
    acceleration_mps2=500.0,
)
report = study.run()
print(f"Single chaser intercepts: {report.single_chaser_intercepts}")
print(f"Dual chaser intercepts:   {report.dual_chaser_intercepts}")
```

Or execute via the CLI:
```shell
uv run chaser compare --acceleration 500
```
