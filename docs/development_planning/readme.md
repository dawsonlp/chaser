# Development Planning

This directory contains architectural roadmaps, refactoring plans, and decision records for the Chaser simulation engine.

## Active Plans

- [Architecture & Experimentation Redesign Plan](architecture-and-experimentation-redesign.md) — Comprehensive plan for decomposing the codebase into modular layers, introducing a composable spatial arena, universal simulation records, adaptive numerical path integration, parameter sweeps, and a Diátaxis-based documentation structure.

## Decision Log

| Date | Topic | Status | Summary |
| :--- | :--- | :--- | :--- |
| 2026-08-25 | Component Architecture Model | **Approved** | Adopt lightweight, immutable typed dataclasses and Python protocols (`Agent`, `Sensor`, `DecisionPolicy`, `ActuatorSet`) rather than heavyweight dynamic ECS frameworks. |
| 2026-08-25 | 3D Spatial Readiness | **Approved** | Include 3D class structures, interface stubs (`Vec3`, `Path3D`, `SphereContactDetector`), and documentation in Phase 1 without requiring full 3D physics implementation upfront. |
| 2026-08-25 | Continuous Steering & Numerical Integration | **Approved** | Unify analytic paths and adaptive numerical paths (RK45 with memoized dense-output interpolation) under the identical `Path` protocol (`state_at(t)`), ensuring zero code changes across the arena, sensors, policies, or collision finders. |
| 2026-08-25 | Architecture Redesign for Rapid Experimentation | **Approved** | 5-phase modular refactoring roadmap approved for implementation planning. |
