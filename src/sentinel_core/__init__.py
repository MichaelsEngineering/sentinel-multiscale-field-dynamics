"""Simulation core organized around geometry -> symmetry -> operator -> closure -> integrator."""

from .config import (
    ClosureConfig,
    GeometryConfig,
    IntegratorConfig,
    OperatorConfig,
    SymmetryConfig,
    TaskConfig,
    TrainingConfig,
    load_task_config,
    task_config_from_mapping,
    task_config_to_dict,
)
from .controllers.base import AbstainingController, ControlAction
from .core import (
    RolloutResult,
    SimulationTask,
    TrainingResult,
    build_task,
    run_rollout,
    train_closure,
)
from .data import DatasetManifest, DatasetRecord, DatasetState
from .evaluators.core import EvaluationReport, InvariantReport, evaluate_grid_rollout
from .interfaces import FieldState, RunManifest, StepContext
from .operator_adapter import OperatorModel, State
from .reporting import describe_architecture, package_file_tree, theory_mapping

__all__ = [
    "AbstainingController",
    "ClosureConfig",
    "ControlAction",
    "DatasetManifest",
    "DatasetRecord",
    "DatasetState",
    "EvaluationReport",
    "FieldState",
    "GeometryConfig",
    "IntegratorConfig",
    "InvariantReport",
    "OperatorModel",
    "OperatorConfig",
    "RolloutResult",
    "RunManifest",
    "SimulationTask",
    "State",
    "StepContext",
    "SymmetryConfig",
    "TaskConfig",
    "TrainingConfig",
    "TrainingResult",
    "build_task",
    "describe_architecture",
    "evaluate_grid_rollout",
    "load_task_config",
    "package_file_tree",
    "run_rollout",
    "task_config_from_mapping",
    "task_config_to_dict",
    "theory_mapping",
    "train_closure",
]
