from __future__ import annotations

import pytest

from src.sentinel_core import build_task, run_rollout
from src.sentinel_core.evaluators.core import evaluate_grid_rollout
from src.sentinel_core.problems import default_grid_task_config


@pytest.mark.physics
def test_grid_evaluator_tracks_invariants_and_passes_baseline_thresholds() -> None:
    task = build_task(default_grid_task_config(resolution=8))
    result = run_rollout(task, steps=3)
    evaluation = evaluate_grid_rollout(result.trajectory)

    assert evaluation.passed is True
    assert evaluation.invariants["energy"] > 0.0
    assert abs(evaluation.invariants["mean_value"]) < evaluation.thresholds["mean_value_abs"]
