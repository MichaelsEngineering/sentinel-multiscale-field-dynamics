# AGENTS.md

This repository is a deterministic research-and-systems workspace for multiscale field dynamics.

## Supported environment

Primary target:
- Linux
- Windows only through WSL 2 with Ubuntu

Assume Linux semantics for paths, scripts, tooling, and examples. If the user is on Windows, prefer WSL Ubuntu commands and file operations over native Windows shells.

## Public command surface

Use cross-platform entrypoints first:
- `uv sync --dev`
- `uv run sentinel ...`
- `cmake --preset ...`
- `ctest --preset ...`

Do not rely on shell activation in examples or automation.

## Workflow rules

- Treat `Makefile` as a Linux convenience layer and CI helper, not the only supported interface.
- Preserve the current validated scope: the grid turbulence path is executable; graph and equivariant modes are scaffold-level.
- Every tracked run should write artifacts under `runs/` with an explicit seed and config hash.
- Keep docs, configs, and tests aligned when changing the command surface.
- Prefer editing from Linux or WSL Ubuntu only. Do not treat native Windows Codex execution as a safe default workflow for this repo.
- If the worktree shows broad text-file churn and `git` warns about `CRLF`/`LF`, treat it as a likely Windows-only file issue before assuming the content changed intentionally.
- When Windows-specific file issues appear, update docs and guidance toward WSL 2 usage rather than expanding native Windows support.

## Editing focus

- Core Python package: `src/sentinel_core/`
- Research/public docs: `research/` and `docs/`
- Native scaffolding: `native/c/`
- Cross-platform wrappers: `scripts/dev.ps1`, `scripts/dev.sh`

## Windows-only file issue guidance

- Files tracked with LF in git should stay LF-normalized in the repository.
- Native Windows Codex sessions can rewrite working-tree files as CRLF and create noisy diffs in docs, YAML, workflow files, and Python sources.
- If this occurs, do not normalize the repo around native Windows behavior. Preserve Linux/WSL-first expectations in documentation and automation.

## Validation

Before finishing code changes, prefer:
- `uv run ruff format src tests`
- `uv run ruff check src tests`
- `uv run mypy src tests`
- `uv run pytest -q`

On Linux, `make format` and `make check` mirror the same workflow.
