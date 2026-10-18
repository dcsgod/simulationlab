"""
Core models, errors, context, registry, and unified mathematical engine.
"""
from mathematical_engine.core.errors import (
    SimulationLabError,
    ModelNotFoundError,
    CapabilityMismatchError,
    FormulaEvaluationError,
    CyclicDependencyError,
    DependencyResolutionError,
    InvariantViolationError,
    OutOfBoundsError,
    InfeasibleOptimizationError,
    NonFiniteValueError,
    IncompatibleUnitError,
)
from mathematical_engine.core.context import ExecutionContext
from mathematical_engine.core.base_model import (
    BaseSimulationModel,
    ModelCapability,
    ModelMetadata,
)
from mathematical_engine.core.registry import (
    ModelRegistry,
    default_model_registry,
)
from mathematical_engine.core.engine import MathematicalEngine

__all__ = [
    "SimulationLabError",
    "ModelNotFoundError",
    "CapabilityMismatchError",
    "FormulaEvaluationError",
    "CyclicDependencyError",
    "DependencyResolutionError",
    "InvariantViolationError",
    "OutOfBoundsError",
    "InfeasibleOptimizationError",
    "NonFiniteValueError",
    "IncompatibleUnitError",
    "ExecutionContext",
    "BaseSimulationModel",
    "ModelCapability",
    "ModelMetadata",
    "ModelRegistry",
    "default_model_registry",
    "MathematicalEngine",
]
