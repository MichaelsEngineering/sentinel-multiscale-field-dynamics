from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import typer
import yaml

from ..config import load_task_config, task_config_to_dict
from ..core import build_task, run_rollout
from ..evaluators.core import EvaluationReport, evaluate_grid_rollout
from ..interfaces import RunManifest
from ..reporting import describe_architecture, theory_mapping


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_TASK_CONFIG = REPO_ROOT / "configs" / "tasks" / "turbulence2d_baseline.yaml"
DEFAULT_BENCHMARK_CONFIG = REPO_ROOT / "configs" / "benchmarks" / "turbulence_horizon.yaml"
RUNS_ROOT = REPO_ROOT / "runs"

app = typer.Typer(add_completion=False, no_args_is_help=True)
smoke_app = typer.Typer(add_completion=False, no_args_is_help=True)
run_app = typer.Typer(add_completion=False, no_args_is_help=True)
bench_app = typer.Typer(add_completion=False, no_args_is_help=True)
eval_app = typer.Typer(add_completion=False, no_args_is_help=True)
report_app = typer.Typer(add_completion=False, no_args_is_help=True)
native_app = typer.Typer(add_completion=False, no_args_is_help=True)
trace_app = typer.Typer(add_completion=False, no_args_is_help=True)
data_app = typer.Typer(add_completion=False, no_args_is_help=True)


def _json_hash(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:12]


def _load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise typer.BadParameter(f"{path} did not deserialize to a mapping")
    return payload


def _artifact_dir(problem: str, config_hash: str, seed: int) -> Path:
    date_prefix = datetime.now(timezone.utc).strftime("%Y%m%d")
    artifact_path = RUNS_ROOT / date_prefix / problem / f"workspace_{config_hash}_{seed}"
    artifact_path.mkdir(parents=True, exist_ok=True)
    return artifact_path


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_trace(path: Path, trajectory: list[list[list[float]]]) -> None:
    records = []
    for step, state in enumerate(trajectory):
        flat = [value for row in state for value in row]
        records.append(
            {
                "step": step,
                "mean": sum(flat) / len(flat),
                "max_abs": max(abs(value) for value in flat),
            }
        )
    path.write_text(
        "\n".join(json.dumps(record, sort_keys=True) for record in records), encoding="utf-8"
    )


def _build_manifest(
    command: str, config_path: Path, config_hash: str, seed: int, problem: str, artifact_path: Path
) -> RunManifest:
    return RunManifest(
        schema_version="1",
        command=command,
        config_path=str(config_path),
        config_hash=config_hash,
        seed=seed,
        artifact_path=str(artifact_path),
        problem=problem,
        runtime="python",
        metadata={"entrypoint": "uv run sentinel", "validated_scope": "grid_only"},
    )


def _run_grid(
    command: str,
    config_path: Path,
    steps: int,
    seed: int,
    thresholds: dict[str, float] | None = None,
) -> dict[str, object]:
    task_config = load_task_config(config_path)
    config_hash = _json_hash(task_config_to_dict(task_config))
    task = build_task(task_config)
    result = run_rollout(task, steps=steps)
    evaluation: EvaluationReport = evaluate_grid_rollout(result.trajectory, thresholds=thresholds)
    artifact_path = _artifact_dir(task.name, config_hash, seed)
    manifest = _build_manifest(command, config_path, config_hash, seed, task.name, artifact_path)
    summary = {
        "task": task.name,
        "steps": steps,
        "seed": seed,
        "config_hash": config_hash,
        "artifact_path": str(artifact_path),
        "diagnostics": result.diagnostics,
        "evaluation": evaluation.to_dict(),
    }
    _write_json(artifact_path / "run_manifest.json", asdict(manifest))
    _write_json(artifact_path / "run_summary.json", summary)
    _write_trace(artifact_path / "trace.jsonl", result.trajectory)
    return summary


@smoke_app.command("grid")
def smoke_grid(
    config: Path = typer.Option(DEFAULT_TASK_CONFIG, exists=True, dir_okay=False),
    steps: int = typer.Option(3, min=1),
    seed: int = typer.Option(7, min=0),
) -> None:
    typer.echo(json.dumps(_run_grid("smoke grid", config, steps, seed), indent=2, sort_keys=True))


@run_app.command("rollout")
def run_rollout_command(
    config: Path = typer.Option(DEFAULT_TASK_CONFIG, exists=True, dir_okay=False),
    steps: int = typer.Option(8, min=1),
    seed: int = typer.Option(..., min=0, help="Explicit seed required for tracked runs."),
) -> None:
    typer.echo(json.dumps(_run_grid("run rollout", config, steps, seed), indent=2, sort_keys=True))


@bench_app.command("turbulence2d")
def bench_turbulence2d(
    suite: Path = typer.Option(DEFAULT_BENCHMARK_CONFIG, exists=True, dir_okay=False),
    seed: int = typer.Option(..., min=0, help="Explicit seed required for benchmark runs."),
) -> None:
    suite_payload = _load_yaml(suite)
    config_path = REPO_ROOT / str(suite_payload["task_config"])
    thresholds = {
        "energy_drift": float(suite_payload.get("thresholds", {}).get("energy_drift", 5.0)),
        "mean_value_abs": float(suite_payload.get("thresholds", {}).get("mean_value_abs", 1e-8)),
    }
    steps = int(suite_payload.get("steps", 8))
    summary = _run_grid("bench turbulence2d", config_path, steps, seed, thresholds=thresholds)
    summary["suite"] = suite_payload["name"]
    typer.echo(json.dumps(summary, indent=2, sort_keys=True))


@eval_app.command("invariants")
def eval_invariants(
    run: Path = typer.Option(..., exists=True, file_okay=False, dir_okay=True),
) -> None:
    summary = json.loads((run / "run_summary.json").read_text(encoding="utf-8"))
    typer.echo(json.dumps(summary["evaluation"], indent=2, sort_keys=True))


@eval_app.command("compare")
def eval_compare(
    baseline: Path = typer.Option(..., exists=True, file_okay=False, dir_okay=True),
    candidate: Path = typer.Option(..., exists=True, file_okay=False, dir_okay=True),
) -> None:
    baseline_summary = json.loads((baseline / "run_summary.json").read_text(encoding="utf-8"))
    candidate_summary = json.loads((candidate / "run_summary.json").read_text(encoding="utf-8"))
    comparison = {
        "baseline": str(baseline),
        "candidate": str(candidate),
        "energy_drift_delta": candidate_summary["evaluation"]["invariants"]["energy_drift"]
        - baseline_summary["evaluation"]["invariants"]["energy_drift"],
        "passed_delta": int(candidate_summary["evaluation"]["passed"])
        - int(baseline_summary["evaluation"]["passed"]),
    }
    typer.echo(json.dumps(comparison, indent=2, sort_keys=True))


@report_app.command("architecture")
def report_architecture() -> None:
    typer.echo(describe_architecture())


@report_app.command("theory-map")
def report_theory_map() -> None:
    typer.echo(theory_mapping())


@report_app.command("run-summary")
def report_run_summary(
    run: Path = typer.Option(..., exists=True, file_okay=False, dir_okay=True),
) -> None:
    typer.echo((run / "run_summary.json").read_text(encoding="utf-8"))


@native_app.command("demo")
def native_demo(name: str = typer.Argument(...)) -> None:
    payload = {
        "demo": name,
        "native_root": str(REPO_ROOT / "native" / "c"),
        "cmake_preset": "native-debug",
        "status": "scaffolded",
    }
    typer.echo(json.dumps(payload, indent=2, sort_keys=True))


@native_app.command("bench")
def native_bench(name: str = typer.Argument(...)) -> None:
    payload = {
        "bench": name,
        "preset": "native-release",
        "status": "scaffolded",
        "docs": str(REPO_ROOT / "native" / "docs" / "README.md"),
    }
    typer.echo(json.dumps(payload, indent=2, sort_keys=True))


@trace_app.command("inspect")
def trace_inspect(
    run: Path = typer.Option(..., exists=True, file_okay=False, dir_okay=True),
) -> None:
    trace_path = run / "trace.jsonl"
    lines = [line for line in trace_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    typer.echo(
        json.dumps(
            {"run": str(run), "trace_path": str(trace_path), "records": len(lines)},
            indent=2,
            sort_keys=True,
        )
    )


@trace_app.command("tail")
def trace_tail(source: str = typer.Option(...)) -> None:
    typer.echo(json.dumps({"source": source, "status": "tail_not_implemented_in_phase0"}, indent=2))


@data_app.command("manifest")
def data_manifest_validate(
    action: str = typer.Argument(..., help="Use 'validate' for Phase 0 manifest checks."),
    path: Path = typer.Option(..., exists=True, dir_okay=False),
) -> None:
    if action != "validate":
        raise typer.BadParameter("Phase 0 supports only 'validate'")
    payload = _load_yaml(path)
    result = {
        "path": str(path),
        "schema_version": payload.get("schema_version"),
        "valid": "schema_version" in payload and "name" in payload,
    }
    typer.echo(json.dumps(result, indent=2, sort_keys=True))


app.add_typer(smoke_app, name="smoke")
app.add_typer(run_app, name="run")
app.add_typer(bench_app, name="bench")
app.add_typer(eval_app, name="eval")
app.add_typer(report_app, name="report")
app.add_typer(native_app, name="native")
app.add_typer(trace_app, name="trace")
app.add_typer(data_app, name="data")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
