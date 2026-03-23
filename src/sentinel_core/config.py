from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path

import yaml


def _mapping(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return {str(key): nested for key, nested in value.items()}
    return {}


def _string_mapping(value: object) -> dict[str, str]:
    return {str(key): str(nested) for key, nested in _mapping(value).items()}


def _channels(value: object) -> tuple[str, ...]:
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value)
    return ("vorticity",)


def _as_int(value: object, default: int) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        return int(value)
    return default


def _as_float(value: object, default: float) -> float:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return float(value)
    return default


@dataclass(frozen=True)
class GeometryConfig:
    kind: str
    resolution: int = 16
    domain_size: float = 6.283185307179586
    channels: tuple[str, ...] = ("vorticity",)
    boundary: str = "periodic"
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class SymmetryConfig:
    kind: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class OperatorConfig:
    family: str | None = None
    viscosity: float = 0.02
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ClosureConfig:
    kind: str = "neural_operator_surrogate"
    history: int = 2
    latent_width: int = 8
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class IntegratorConfig:
    kind: str = "structure_preserving_euler"
    dt: float = 0.05
    projection: str = "mean_free"
    max_stable_dt: float = 0.1
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class TrainingConfig:
    epochs: int = 2
    learning_rate: float = 1e-3
    teacher_forcing_steps: int = 2


@dataclass(frozen=True)
class TaskConfig:
    name: str
    geometry: GeometryConfig
    schema_version: str = "1"
    symmetry: SymmetryConfig = field(default_factory=SymmetryConfig)
    operator: OperatorConfig = field(default_factory=OperatorConfig)
    closure: ClosureConfig = field(default_factory=ClosureConfig)
    integrator: IntegratorConfig = field(default_factory=IntegratorConfig)
    metadata: dict[str, str] = field(default_factory=dict)


def task_config_to_dict(config: TaskConfig) -> dict[str, object]:
    return asdict(config)


def _geometry_config_from_mapping(data: dict[str, object]) -> GeometryConfig:
    return GeometryConfig(
        kind=str(data.get("kind", "grid")),
        resolution=_as_int(data.get("resolution", 16), 16),
        domain_size=_as_float(data.get("domain_size", 6.283185307179586), 6.283185307179586),
        channels=_channels(data.get("channels", ("vorticity",))),
        boundary=str(data.get("boundary", "periodic")),
        metadata=_string_mapping(data.get("metadata", {})),
    )


def _symmetry_config_from_mapping(data: dict[str, object]) -> SymmetryConfig:
    kind = data.get("kind")
    return SymmetryConfig(
        kind=str(kind) if kind is not None else None,
        metadata=_string_mapping(data.get("metadata", {})),
    )


def _operator_config_from_mapping(data: dict[str, object]) -> OperatorConfig:
    family = data.get("family")
    return OperatorConfig(
        family=str(family) if family is not None else None,
        viscosity=_as_float(data.get("viscosity", 0.02), 0.02),
        metadata=_string_mapping(data.get("metadata", {})),
    )


def _closure_config_from_mapping(data: dict[str, object]) -> ClosureConfig:
    return ClosureConfig(
        kind=str(data.get("kind", "neural_operator_surrogate")),
        history=_as_int(data.get("history", 2), 2),
        latent_width=_as_int(data.get("latent_width", 8), 8),
        metadata=_string_mapping(data.get("metadata", {})),
    )


def _integrator_config_from_mapping(data: dict[str, object]) -> IntegratorConfig:
    return IntegratorConfig(
        kind=str(data.get("kind", "structure_preserving_euler")),
        dt=_as_float(data.get("dt", 0.05), 0.05),
        projection=str(data.get("projection", "mean_free")),
        max_stable_dt=_as_float(data.get("max_stable_dt", 0.1), 0.1),
        metadata=_string_mapping(data.get("metadata", {})),
    )


def task_config_from_mapping(data: dict[str, object]) -> TaskConfig:
    return TaskConfig(
        name=str(data["name"]),
        geometry=_geometry_config_from_mapping(_mapping(data["geometry"])),
        schema_version=str(data.get("schema_version", "1")),
        symmetry=_symmetry_config_from_mapping(_mapping(data.get("symmetry", {}))),
        operator=_operator_config_from_mapping(_mapping(data.get("operator", {}))),
        closure=_closure_config_from_mapping(_mapping(data.get("closure", {}))),
        integrator=_integrator_config_from_mapping(_mapping(data.get("integrator", {}))),
        metadata=_string_mapping(data.get("metadata", {})),
    )


def load_task_config(path: str | Path) -> TaskConfig:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("task config must deserialize to a mapping")
    return task_config_from_mapping({str(key): value for key, value in raw.items()})
