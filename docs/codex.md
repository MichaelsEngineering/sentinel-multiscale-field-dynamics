# Codex Guidance

## Command surface

Use these forms in Codex and documentation:

```bash
uv sync --dev
uv run sentinel report architecture
uv run sentinel smoke grid --config configs/tasks/turbulence2d_baseline.yaml
uv run sentinel run rollout --config configs/tasks/turbulence2d_baseline.yaml --seed 7
```

## Invariants

- Grid turbulence is the only validated executable path.
- Graph and equivariant paths are scaffold-level only.
- Tracked runs require an explicit seed.
- Tracked runs write manifests, summaries, and traces under `runs/`.

## Windows and WSL assumptions

- Prefer `uv run ...` over shell activation.
- `scripts/dev.ps1` is the Windows wrapper.
- `scripts/dev.sh` is the POSIX/Linux wrapper.
- Native runtime work targets Linux first; Windows users should treat CMake presets as the supported native entrypoint.
