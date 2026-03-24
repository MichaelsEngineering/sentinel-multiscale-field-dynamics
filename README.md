# Sentinel Multiscale Field Dynamics

Sentinel Multiscale Field Dynamics is a deterministic research workspace for multiscale physics, learned dynamics, and intervention-aware control. The current validated executable path is the 2D periodic grid turbulence baseline.

## Overview

This repository uses the Johns Hopkins Turbulence Database (JHTDB) as a canonical physics dataset for multiscale field analysis. JHTDB provides direct numerical simulation (DNS) data for turbulent flows governed by the Navier-Stokes equations, making it a useful reference source for studying geometry, invariants, and scale-coupled dynamics in chaotic field systems.

In this project, turbulence is treated as a representative multiscale field dynamics problem. The goal is not only to model flow evolution, but to extract reusable geometric structure, conservation behavior, and invariant summaries that can support a broader unification of physics-grounded learning and intelligence systems.

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
uv run sentinel data ingest jhtdb --url https://example.jhtdb/query
uv run sentinel data inspect --path data/jhtdb/isotropic1024coarse/<slice-id>/velocity.jsonl
uv run sentinel smoke grid --config configs/tasks/turbulence2d_baseline.yaml
uv run sentinel run rollout --config configs/tasks/turbulence2d_baseline.yaml --seed 7
uv run sentinel bench turbulence2d --suite configs/benchmarks/turbulence_horizon.yaml --seed 7
```

Do not rely on shell activation in examples or automation.

## Command Surface

Use these entrypoints first:

- `uv sync --dev`
- `uv run sentinel ...`
- `uv run sentinel data ingest jhtdb ...`
- `uv run sentinel data validate ...`
- `uv run sentinel data inspect ...`
- `cmake --preset ...`
- `ctest --preset ...`

`Makefile` is a Linux convenience layer and CI helper. It is not the only supported interface.

## Data Source

JHTDB is a multi-terabyte turbulence archive built from DNS simulations of fluid flows. Rather than distributing static downloadable files for the full corpus, it exposes query APIs that return requested subsets of the simulation state. Typical queries target 3D spatial subcubes at selected times and fields, including velocity components `(u, v, w)` and pressure.

For this repository, the important property is that JHTDB gives access to time-resolved volumetric flow states from a canonical multiscale chaotic system. A representative source is isotropic turbulence, which contains thousands of time steps and vector-valued velocity fields sampled over a 3D grid.

## Raw Data Format

JHTDB data is accessed through service queries, historically via SOAP and more practically via REST-style request patterns. The response payloads are binary buffers, typically interpreted as `float32` arrays after download.

The raw payload represents structured field data such as:

- velocity field with shape `(nx, ny, nz, 3)`
- pressure field with shape `(nx, ny, nz)`
- time-indexed subcubes extracted from a larger simulation volume

This raw format is not human-readable and is not directly ready for machine learning or geometry-search workflows.

This dataset does NOT provide JSON, CSV, or JSONL formats. Conversion is required.

## Repository Data Standard

This repository normalizes external field data into a line-oriented JSONL representation so each record can be processed independently by ingestion, feature-extraction, and geometry-search stages.

Canonical schema:

```json
{
  "source": "JHTDB",
  "dataset": "isotropic1024coarse",
  "time": 0.1,
  "state": {
    "type": "velocity_field",
    "shape": [32, 32, 32, 3],
    "data": [...]
  },
  "operator": "NavierStokes",
  "invariants": {},
  "boundary": {}
}
```

Each JSONL line represents one spatial chunk or one time-indexed field sample. The schema is designed to preserve operator identity, field geometry, and derived invariant metadata in a form suitable for deterministic downstream processing.

Dataset assets are stored separately from tracked rollout artifacts under `data/jhtdb/<dataset>/<slice-id>/`. A first-pass ingest writes:

- `velocity.jsonl`
- `manifest.json`
- `summary.json`

## Data Conversion Pipeline

The JHTDB ingestion path is:

1. Query the JHTDB API, preferring REST-style access over SOAP when both are available.
2. Receive the binary response payload for the requested field and subcube.
3. Decode the payload into a NumPy array with the correct scalar type.
4. Reshape the decoded buffer into the expected volumetric field layout.
5. Chunk large volumes into smaller blocks such as `32 x 32 x 32`.
6. Compute derived features such as vorticity, spatial gradients, and energy density.
7. Normalize the result into the repository JSONL schema.
8. Write one record per chunk or timestep to JSONL.

## Cleanup And Preprocessing

The repository does not store full raw volumes blindly. Full DNS volumes are too large to treat as the default working representation, and they contain more spatial extent than most local geometry and invariant analyses need at once.

Cleanup and preprocessing therefore emphasize:

- chunking for memory efficiency and spatial locality
- normalization of units, scales, and tensor layout
- removal of unused or redundant raw fields
- optional compression or conversion to columnar formats such as Parquet for downstream storage

These choices reduce noise, control storage cost, and make the dataset practical for geometry extraction, invariant discovery, and ML-facing preprocessing without losing the physical structure of the underlying flow.

## Example Dataset Entry

```json
{
  "source": "JHTDB",
  "dataset": "isotropic1024coarse",
  "time": 0.1,
  "state": {
    "type": "velocity_field",
    "shape": [32, 32, 32, 3],
    "data": [[[[-0.12, 0.44, 0.08]]]]
  },
  "operator": "NavierStokes",
  "invariants": {
    "energy_density_mean": 0.093,
    "vorticity_l2": 1.84
  },
  "boundary": {
    "type": "periodic"
  }
}
```

## Example Code Snippet

```python
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import requests


def fetch_velocity_chunk(url: str, shape: tuple[int, int, int, int]) -> np.ndarray:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    field = np.frombuffer(response.content, dtype=np.float32)
    return field.reshape(shape)


chunk = fetch_velocity_chunk(
    url="https://example.jhtdb/query",
    shape=(32, 32, 32, 3),
)

record = {
    "source": "JHTDB",
    "dataset": "isotropic1024coarse",
    "time": 0.1,
    "state": {
        "type": "velocity_field",
        "shape": list(chunk.shape),
        "data": chunk.tolist(),
    },
    "operator": "NavierStokes",
    "invariants": {},
    "boundary": {"type": "periodic"},
}

Path("data/jhtdb_velocity.jsonl").write_text(json.dumps(record) + "\n", encoding="utf-8")
```

## Why This Matters

Turbulence is a canonical multiscale system: it contains conservation laws, nested scale interactions, intermittent structure, and chaotic temporal evolution within a single physical setting. That makes it a strong grounding dataset for this repository's core research direction.

Within Sentinel, JHTDB-backed field data supports:

- geometry discovery over structured state spaces
- invariant extraction from Navier-Stokes dynamics
- analysis of boundary behavior and scale-to-scale coupling

## Operator Adapter Layer

The repository now includes an additive operator adapter layer for describing learned and analytic operator families without changing the validated runtime rollout path. The canonical contract is:

```text
OperatorModel:
  type: FNO | DiffFNO | Transformer | PDE
  input_schema: State
  output_schema: State
  invariants_preserved: []
  boundary_behavior: metrics
```

This layer is intended for model registration, operator interchange, and future dataset-to-model integration. It does not replace the current grid operator implementation used by the validated baseline.

## Reference Papers

Influential papers are tracked in [research/reference-papers.md](/home/qol/sentinel-multiscale-field-dynamics/research/reference-papers.md).

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
