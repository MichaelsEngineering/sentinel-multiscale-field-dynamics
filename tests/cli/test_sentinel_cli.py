from __future__ import annotations

import json

from typer.testing import CliRunner

from src.sentinel_core.cli.app import app


runner = CliRunner()


def test_sentinel_smoke_grid_emits_artifact_metadata() -> None:
    result = runner.invoke(
        app, ["smoke", "grid", "--config", "configs/tasks/turbulence2d_baseline.yaml"]
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["task"] == "grid_turbulence"
    assert "config_hash" in payload
    assert "artifact_path" in payload


def test_sentinel_run_rollout_requires_explicit_seed() -> None:
    result = runner.invoke(
        app,
        ["run", "rollout", "--config", "configs/tasks/turbulence2d_baseline.yaml", "--seed", "11"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["seed"] == 11
    assert payload["evaluation"]["passed"] is True


def test_sentinel_data_manifest_validate_reads_schema_version() -> None:
    result = runner.invoke(
        app,
        ["data", "manifest", "validate", "--path", "configs/tasks/turbulence2d_baseline.yaml"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["schema_version"] == "1"
    assert payload["valid"] is True
