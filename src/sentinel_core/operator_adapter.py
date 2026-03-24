from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Mapping

from .interfaces import FieldState


OperatorModelType = Literal["FNO", "DiffFNO", "Transformer", "PDE"]


@dataclass(frozen=True)
class State:
    kind: str
    channels: tuple[str, ...]
    geometry_id: str
    shape: tuple[int, ...] = ()
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class OperatorModel:
    type: OperatorModelType
    input_schema: State
    output_schema: State
    invariants_preserved: tuple[str, ...] = ()
    boundary_behavior: dict[str, float] = field(default_factory=dict)


def state_from_field_state(state: FieldState) -> State:
    channels = tuple(sorted(state["channels"].keys()))
    return State(
        kind=state["kind"],
        channels=channels,
        geometry_id=state["geometry_id"],
        metadata=dict(state["metadata"]),
    )


def state_from_dataset_record(record: Mapping[str, object]) -> State:
    state = record.get("state", {})
    metadata = record.get("metadata", {})
    boundary = record.get("boundary", {})
    shape = state.get("shape", []) if isinstance(state, dict) else []
    adapter_metadata = {
        "source": str(record.get("source", "")),
        "state_type": str(state.get("type", "")) if isinstance(state, dict) else "",
        "boundary_type": str(boundary.get("type", "")) if isinstance(boundary, dict) else "",
    }
    if isinstance(metadata, dict):
        adapter_metadata.update({str(key): str(value) for key, value in metadata.items()})
    return State(
        kind="grid",
        channels=("velocity",),
        geometry_id=str(record.get("dataset", "unknown_dataset")),
        shape=tuple(int(value) for value in shape) if isinstance(shape, list) else (),
        metadata=adapter_metadata,
    )
