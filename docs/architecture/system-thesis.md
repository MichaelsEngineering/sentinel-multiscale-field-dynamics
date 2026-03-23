# System Thesis

Sentinel should make the scientific search space legible in code. The core architectural chain is:

`geometry -> symmetry -> operator -> closure -> integrator -> controller -> evaluator`

## Intent

- `geometry` defines the state representation and conservation-relevant layout.
- `symmetry` constrains admissible transformations and operator families.
- `operator` carries resolved deterministic dynamics.
- `closure` adds learned or analytical unresolved-scale correction.
- `integrator` owns rollout evolution and stability hooks.
- `controller` expresses bounded intervention rather than hidden correction.
- `evaluator` provides the common verdict layer across physics, ML, and control.

## Engineering consequences

- Each link should be a stable typed interface, not an informal convention.
- Each tracked run should emit artifacts that preserve the config, thresholds, and metrics used to judge it.
- Only validated paths should be described as validated.
