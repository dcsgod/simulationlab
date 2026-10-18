"""
Core exceptions for the Simulation Lab Mathematical Engine.
"""


class SimulationLabError(Exception):
    """Base exception for all simulation lab errors."""
    pass


class ModelNotFoundError(SimulationLabError):
    """Raised when a requested model is not found in the registry."""
    pass


class CapabilityMismatchError(SimulationLabError):
    """Raised when a model does not support the requested capabilities."""
    pass


class FormulaEvaluationError(SimulationLabError):
    """Raised when safe formula evaluation fails (syntax, division by zero, invalid ops)."""
    pass


class CyclicDependencyError(SimulationLabError):
    """Raised when a cycle is detected in a dependency DAG."""
    pass


class DependencyResolutionError(SimulationLabError):
    """Raised when variable dependencies cannot be resolved or are missing."""
    pass


class InvariantViolationError(SimulationLabError):
    """Raised when a business invariant or mathematical constraint is violated."""
    pass


class OutOfBoundsError(SimulationLabError):
    """Raised when a variable value falls outside its defined operating range."""
    pass


class InfeasibleOptimizationError(SimulationLabError):
    """Raised when an optimization problem is proven infeasible or unbounded."""
    pass


class NonFiniteValueError(SimulationLabError):
    """Raised when calculations yield NaN or infinite values."""
    pass


class IncompatibleUnitError(SimulationLabError):
    """Raised when operations are attempted between incompatible physical or financial units."""
    pass
