# Trajectory & Numerical Integration Architecture

Chaser operates on continuous time curves represented by the `Path2D` protocol.

## The `Path2D` Protocol

```python
class Path2D(Protocol):
    start_time: float
    def state_at(self, time: float) -> KinematicState: ...
```

Every path exposes `state_at(time)` which returns a `KinematicState(position, velocity, acceleration)` at any requested time $t \ge t_0$.

## Trajectory Types

1. **Analytic Constant Acceleration (`ConstantAccelerationPath`)**:
   $$p(t) = p_0 + v_0 \Delta t + \frac{1}{2} a_0 \Delta t^2$$
   $$v(t) = v_0 + a_0 \Delta t$$
   Evaluated in $O(1)$ closed form. Pairwise collision uses exact 4th-degree polynomial root solving.

2. **Analytic Drag Path (`ConstantThrustQuadraticDragPath`)**:
   Under constant thrust magnitude $T$ and quadratic drag factor $k$:
   $$v(t) = v_\infty \tanh(\sqrt{T k} \Delta t)$$
   $$x(t) = \frac{1}{k} \ln \cosh(\sqrt{T k} \Delta t)$$
   Evaluated in $O(1)$ closed form.

3. **Adaptive Numerical Path (`DenseNumericalPath2D`)**:
   For complex continuous steering, turning rate limits, or non-linear aerodynamic forces, `DenseNumericalPath2D` integrates ODEs forward using adaptive Runge-Kutta 4(5) step doubling and caches step history.
   
   **Dense Output Interpolation**: Root-finding algorithms query `state_at(t)` at arbitrary bisection points. To prevent expensive re-integration from $t_0$, `DenseNumericalPath2D` performs $C^1$ cubic Hermite spline interpolation between cached integration steps in $O(1)$.

