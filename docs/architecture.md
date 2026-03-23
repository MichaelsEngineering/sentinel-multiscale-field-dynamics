# architecture summary

The repo is organized around a theory chain that makes the physics and engineering assumptions explicit:

- `geometry`: grid, graph, or equivariant state layout
- `symmetry`: periodic translation, permutation/locality, or Euclidean equivariance
- `operator`: deterministic resolved dynamics backbone
- `closure`: learned or analytical unresolved-scale correction
- `integrator`: structure-preserving rollout logic
- `controller`: bounded intervention surface for constraint enforcement or regret-aware correction
- `evaluator`: invariant, benchmark, and trace-based verdict layer

The only validated executable core today is periodic 2D turbulence on a regular grid. Graph and equivariant paths remain scaffold-level extensions under the same task-building interface.

# file tree

```text
src/sentinel_core/
|-- cli/
|-- closure/
|-- controllers/
|-- evaluators/
|-- geometry/
|-- integrators/
|-- operators/
|-- problems/
|-- symmetry/
|-- cli_support.py
|-- config.py
|-- core.py
|-- interfaces.py
|-- reporting.py
|-- tasks.py
|-- training.py
```

# theory mapping

- Brandstetter-style geometric deep learning informs the geometry-to-symmetry contract.
- neuraloperator-style closures map to the unresolved-scale correction layer.
- SciML principles inform the integrator as the place where rollout stability is enforced.
- control sits after integration as explicit intervention, not hidden model compensation.
- evaluator artifacts unify physics, ML, and control claims through invariant and benchmark reports.
