from __future__ import annotations

import json
import struct
from pathlib import Path

from typer.testing import CliRunner

from src.sentinel_core.cli.app import app
from src.sentinel_core import data as data_module


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


def test_sentinel_data_ingest_jhtdb_writes_dataset_artifacts(monkeypatch, tmp_path: Path) -> None:
    values = [float(index) for index in range(24)]
    payload = struct.pack("<24f", *values)
    monkeypatch.setattr(data_module, "fetch_binary_payload", lambda url: payload)

    result = runner.invoke(
        app,
        [
            "data",
            "ingest",
            "jhtdb",
            "--url",
            "https://example.invalid/jhtdb",
            "--dataset",
            "isotropic1024coarse",
            "--time",
            "0.1",
            "--nx",
            "2",
            "--ny",
            "2",
            "--nz",
            "2",
            "--channels",
            "3",
            "--chunk-size",
            "1",
            "--output-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0
    summary = json.loads(result.stdout)
    data_path = Path(summary["data_path"])
    manifest_path = Path(summary["manifest_path"])
    assert data_path.exists()
    assert manifest_path.exists()
    assert summary["records"] == 8


def test_sentinel_data_validate_and_inspect_report_dataset_metadata(
    monkeypatch, tmp_path: Path
) -> None:
    payload = struct.pack("<24f", *[float(index) for index in range(24)])
    monkeypatch.setattr(data_module, "fetch_binary_payload", lambda url: payload)
    ingest = runner.invoke(
        app,
        [
            "data",
            "ingest",
            "jhtdb",
            "--url",
            "https://example.invalid/jhtdb",
            "--dataset",
            "isotropic1024coarse",
            "--nx",
            "2",
            "--ny",
            "2",
            "--nz",
            "2",
            "--channels",
            "3",
            "--chunk-size",
            "2",
            "--output-root",
            str(tmp_path),
        ],
    )
    summary = json.loads(ingest.stdout)

    validate = runner.invoke(
        app,
        [
            "data",
            "validate",
            "--manifest",
            summary["manifest_path"],
            "--data",
            summary["data_path"],
        ],
    )
    inspect = runner.invoke(app, ["data", "inspect", "--path", summary["data_path"]])

    assert validate.exit_code == 0
    assert json.loads(validate.stdout)["valid"] is True
    assert inspect.exit_code == 0
    inspect_payload = json.loads(inspect.stdout)
    assert inspect_payload["dataset"] == "isotropic1024coarse"
    assert inspect_payload["records"] == 1
    assert inspect_payload["shapes"] == [[2, 2, 2, 3]]


def test_sentinel_data_validate_rejects_shape_mismatch(tmp_path: Path) -> None:
    data_path = tmp_path / "velocity.jsonl"
    manifest_path = tmp_path / "manifest.json"
    bad_record = {
        "source": "JHTDB",
        "dataset": "isotropic1024coarse",
        "time": 0.1,
        "state": {"type": "velocity_field", "shape": [2, 2, 2, 3], "data": [[[[1.0, 2.0, 3.0]]]]},
        "operator": "NavierStokes",
        "invariants": {},
        "boundary": {"type": "periodic"},
        "metadata": {},
    }
    data_path.write_text(json.dumps(bad_record) + "\n", encoding="utf-8")
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "1",
                "source": "JHTDB",
                "dataset": "isotropic1024coarse",
                "record_path": str(data_path),
                "records": 1,
                "state_type": "velocity_field",
                "chunk_shape": [2, 2, 2, 3],
                "operator": "NavierStokes",
                "metadata": {},
            }
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        app, ["data", "validate", "--manifest", str(manifest_path), "--data", str(data_path)]
    )

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["valid"] is False
    assert "shape expects 24" in payload["errors"][0]
