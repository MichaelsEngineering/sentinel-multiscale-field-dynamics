from __future__ import annotations

from dataclasses import asdict, dataclass

from ..geometry.grid import Grid


def _grid_energy(field: Grid) -> float:
    flat = [value for row in field for value in row]
    return sum(value * value for value in flat) / len(flat)


def _grid_enstrophy(field: Grid) -> float:
    flat = [abs(value) for row in field for value in row]
    return sum(flat) / len(flat)


def _grid_mean(field: Grid) -> float:
    flat = [value for row in field for value in row]
    return sum(flat) / len(flat)


@dataclass(frozen=True)
class InvariantReport:
    energy: float
    enstrophy: float
    mean_value: float
    energy_drift: float
    enstrophy_drift: float
    controller_cost: float = 0.0
    regret: float = 0.0

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


@dataclass(frozen=True)
class EvaluationReport:
    invariants: dict[str, float]
    thresholds: dict[str, float]
    passed: bool
    notes: list[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "invariants": self.invariants,
            "thresholds": self.thresholds,
            "passed": self.passed,
            "notes": self.notes,
        }


def evaluate_grid_rollout(
    trajectory: list[Grid], thresholds: dict[str, float] | None = None
) -> EvaluationReport:
    if not trajectory:
        raise ValueError("trajectory must be non-empty")

    baseline = trajectory[0]
    final = trajectory[-1]
    invariants = InvariantReport(
        energy=_grid_energy(final),
        enstrophy=_grid_enstrophy(final),
        mean_value=_grid_mean(final),
        energy_drift=abs(_grid_energy(final) - _grid_energy(baseline)),
        enstrophy_drift=abs(_grid_enstrophy(final) - _grid_enstrophy(baseline)),
    ).to_dict()
    threshold_values = thresholds or {"energy_drift": 5.0, "mean_value_abs": 1e-8}
    passed = (
        invariants["energy_drift"] <= threshold_values["energy_drift"]
        and abs(invariants["mean_value"]) <= threshold_values["mean_value_abs"]
    )
    notes = ["validated_grid_vertical_slice", "graph_and_equivariant_are_scaffolds_only"]
    return EvaluationReport(
        invariants=invariants,
        thresholds=threshold_values,
        passed=passed,
        notes=notes,
    )
