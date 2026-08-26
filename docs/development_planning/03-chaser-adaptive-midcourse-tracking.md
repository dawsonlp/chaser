# Planning Decision: Chaser Mid-Course Vector Tracking & Adaptive Intercept

**Date**: August 25, 2026  
**Status**: Pending Execution  
**Related Active Plan**: [implementation_plan.md](file:///Users/dawsonlp/.gemini/antigravity/brain/27ccde55-6d0e-456a-9190-a808cb244995/implementation_plan.md)

## Motivation

When the target executes active lateral evasion maneuvers and course corrections, initial static lead predictions miss. The chaser needs periodic vector-tracking sensors and adaptive guidance (such as Augmented Proportional Navigation and Dynamic Mid-Course Lead Guidance) that calculate continuous thrust redirection from current non-zero chaser velocities.

## Key Algorithms

1. **`DynamicLeadInterceptPolicy`**: Solves optimal lead time $t_{\text{int}}$ accounting for $(\vec{p}_c, \vec{v}_c)$ and $(\vec{p}_t, \vec{v}_t)$.
2. **`AugmentedProportionalNavigationPolicy` (APN)**: Nullifies line-of-sight rate with navigation constant $N \in [3, 5]$ and target acceleration compensation.

