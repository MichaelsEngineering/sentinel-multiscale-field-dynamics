from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Protocol, TypeAlias, TypedDict


Array: TypeAlias = list[float] | list[list[float]]


class FieldState(TypedDict):
    kind: Literal["grid", "graph", "equivariant"]
    channels: dict[str, Array]
    geometry_id: str
    time_index: int
    metadata: dict[str, str]


@dataclass(frozen=True)
class StepContext:
    seed: int
    dt: float
    step_index: int
    config_hash: str
    runtime: str
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class RunManifest:
    schema_version: str
    command: str
    config_path: str
    config_hash: str
    seed: int
    artifact_path: str
    problem: str
    runtime: str
    metadata: dict[str, str] = field(default_factory=dict)


class Operator(Protocol):
    name: str

    def tendencies(self, state: FieldState, ctx: StepContext) -> FieldState: ...


class Closure(Protocol):
    name: str

    def correction(self, history: list[FieldState], ctx: StepContext) -> FieldState: ...


class Integrator(Protocol):
    name: str

    def step(
        self,
        state: FieldState,
        tendencies: FieldState,
        correction: FieldState | None,
        ctx: StepContext,
    ) -> FieldState: ...


class Controller(Protocol):
    name: str

    def act(
        self, state: FieldState, metrics: dict[str, float], ctx: StepContext
    ) -> dict[str, float]: ...


class Evaluator(Protocol):
    name: str

    def measure(self, rollout: list[FieldState], ctx: RunManifest) -> dict[str, float]: ...


class NativeKernelBridge(Protocol):
    def available(self) -> bool: ...

    def step_many(
        self, init: FieldState, cfg: dict[str, object], steps: int
    ) -> dict[str, object]: ...


class TraceSink(Protocol):
    def open(self, manifest: RunManifest) -> None: ...

    def emit_step(self, state: FieldState, metrics: dict[str, float], step: int) -> None: ...

    def close(self) -> str: ...
