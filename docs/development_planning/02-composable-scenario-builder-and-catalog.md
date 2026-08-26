# Planning Decision: Composable Scenario Builder & Component Catalog

**Date**: August 25, 2026  
**Status**: Pending Review / Implementation  
**Related Active Plan**: [implementation_plan.md](file:///Users/dawsonlp/.gemini/antigravity/brain/27ccde55-6d0e-456a-9190-a808cb244995/implementation_plan.md)

## Motivation

As the chaser designer and the target designer iterate in an arms-race (e.g. adding periodic threat sensing, lateral evasion, multi-chaser pincer tactics, decoys, zigzag evasions), hardcoding fixed scenario classes becomes limiting. We need a mix-and-match architecture where algorithms and machinery can be freely combined.

## Architecture

1. **Component Catalog (`chaser.catalog`)**: Central registry for policies, sensors, actuator response models, and physical bodies.
2. **Dynamic Scenario Builder (`chaser.builder`)**: Declarative configuration (`ScenarioConfig`, `ChaserSpec`, `TargetSpec`) that instantiates arbitrary team setups into `ComposableArenaModel`.
3. **CLI Composition (`chaser compose`)**:
   ```shell
   chaser compose --chasers 2 --chaser-policy dual_pincer --target-policy evasive_goal_steering --visualize
   ```
4. **Policy Matrix Tournament (`chaser matrix`)**: Automated benchmarking of $N$ chaser strategies against $M$ target strategies.

