# Sentinel Multiscale Field Dynamics

Sentinel Multiscale Field Dynamics is a deterministic research workspace for multiscale physics, learned dynamics, and intervention-aware control. The validated executable path is the 2D periodic grid turbulence baseline.

## Status

Work in progress. The repository is under active development and the current validated path is still narrow.

Current focus:

- keep the 2D grid turbulence baseline deterministic and reproducible
- stabilize the `sentinel` command surface and supporting docs
- expand evaluation, reporting, and tracked-run artifacts under `runs/`
- mature the native Linux runtime scaffolding under `native/c/`
- keep graph and equivariant paths clearly marked as scaffold-level until they are validated

## Supported Environment

Primary development and execution target:

- Linux
- Windows through WSL 2 with Ubuntu

This repository should be treated as Linux-first. If you are on Windows, run commands from the Ubuntu side of WSL 2, not from native Windows shells.

Current validation has been done on Linux through WSL 2 Ubuntu. Native Linux users, including Red Hat or RHEL-derived distributions, should expect the same command surface but may need different system-package or tool-install steps for their distro.

Native Windows execution is not a supported primary workflow for Codex or day-to-day repo edits. Running Codex outside WSL 2 can introduce Windows-only file damage such as:

- CRLF line-ending churn in tracked files that are stored as LF in git
- noisy diffs across docs, config, and workflow files
- shell-path and script mismatches against the Linux-oriented command surface

## Quick Start

From Linux or WSL Ubuntu:

```bash
uv sync --dev
uv run sentinel report architecture
uv run sentinel smoke grid --config configs/tasks/turbulence2d_baseline.yaml
uv run sentinel run rollout --config configs/tasks/turbulence2d_baseline.yaml --seed 7
uv run sentinel bench turbulence2d --suite configs/benchmarks/turbulence_horizon.yaml --seed 7
```

Do not rely on shell activation in examples or automation.

## Command Surface

Use these entrypoints first:

- `uv sync --dev`
- `uv run sentinel ...`
- `cmake --preset ...`
- `ctest --preset ...`

`Makefile` is a Linux convenience layer and CI helper. It is not the only supported interface.

## Validated Scope

- Validated: periodic 2D grid turbulence rollout with deterministic config-driven execution and invariant summaries
- Scaffolded only: graph and equivariant modes
- Planned but not yet validated: learned closures, controller layers, native kernel execution, telemetry streaming

## Reproducibility Rules

- Every tracked run must use an explicit seed.
- Every tracked run must write artifacts under `runs/`.
- Tracked outputs should include a config hash plus run metadata such as `run_manifest.json`, `run_summary.json`, and `trace.jsonl`.

## Repository Areas

- Core package: `src/sentinel_core/`
- Research and docs: `research/` and `docs/`
- Native scaffolding: `native/c/`
- Wrapper scripts: `scripts/dev.sh` and `scripts/dev.ps1`
