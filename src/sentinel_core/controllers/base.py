from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ControlAction:
    mode: str
    scale: float = 0.0
    projection: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)


class AbstainingController:
    name = "abstain"

    def act(self, state: object, metrics: dict[str, float], ctx: object) -> ControlAction:
        return ControlAction(mode="abstain", metadata={"reason": "phase0_default"})
