"""
Linear and Mixed-Integer Linear Programming mathematical problem specifications.
"""
from typing import Dict, List, Optional
from enum import Enum
from pydantic import BaseModel, Field


class VariableType(str, Enum):
    CONTINUOUS = "continuous"
    INTEGER = "integer"
    BINARY = "binary"


class ConstraintSense(str, Enum):
    LE = "<="
    GE = ">="
    EQ = "=="


class ObjectiveDirection(str, Enum):
    MINIMIZE = "minimize"
    MAXIMIZE = "maximize"


class DecisionVariable(BaseModel):
    name: str = Field(..., description="Unique variable name")
    var_type: VariableType = Field(default=VariableType.CONTINUOUS)
    lower_bound: Optional[float] = Field(default=0.0, description="Lower bound (None for -inf)")
    upper_bound: Optional[float] = Field(default=None, description="Upper bound (None for +inf)")
    unit: Optional[str] = None
    description: Optional[str] = None


class LinearConstraint(BaseModel):
    name: str = Field(..., description="Unique constraint identifier")
    coefficients: Dict[str, float] = Field(..., description="Mapping of variable name to linear coefficient")
    sense: ConstraintSense = Field(default=ConstraintSense.LE)
    rhs: float = Field(..., description="Right-hand side numeric bound")
    description: Optional[str] = None


class LinearObjective(BaseModel):
    direction: ObjectiveDirection = Field(default=ObjectiveDirection.MAXIMIZE)
    coefficients: Dict[str, float] = Field(..., description="Mapping of variable name to objective coefficient")
    constant: float = Field(default=0.0, description="Constant offset term in objective")
    description: Optional[str] = None


class OptimizationProblem(BaseModel):
    """
    Standard linear / mixed-integer linear programming specification.
    """
    name: str = Field(..., description="Optimization problem title")
    variables: Dict[str, DecisionVariable] = Field(default_factory=dict)
    objective: Optional[LinearObjective] = None
    constraints: List[LinearConstraint] = Field(default_factory=list)
    description: Optional[str] = None

    def add_variable(
        self,
        name: str,
        var_type: VariableType = VariableType.CONTINUOUS,
        lower_bound: Optional[float] = 0.0,
        upper_bound: Optional[float] = None,
        unit: Optional[str] = None,
        description: Optional[str] = None,
    ) -> DecisionVariable:
        if var_type == VariableType.BINARY:
            lower_bound = 0.0
            upper_bound = 1.0

        var = DecisionVariable(
            name=name,
            var_type=var_type,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            unit=unit,
            description=description,
        )
        self.variables[name] = var
        return var

    def set_objective(
        self,
        coefficients: Dict[str, float],
        direction: ObjectiveDirection = ObjectiveDirection.MAXIMIZE,
        constant: float = 0.0,
        description: Optional[str] = None,
    ) -> None:
        self.objective = LinearObjective(
            direction=direction,
            coefficients=coefficients,
            constant=constant,
            description=description,
        )

    def add_constraint(
        self,
        name: str,
        coefficients: Dict[str, float],
        sense: ConstraintSense = ConstraintSense.LE,
        rhs: float = 0.0,
        description: Optional[str] = None,
    ) -> LinearConstraint:
        c = LinearConstraint(
            name=name,
            coefficients=coefficients,
            sense=sense,
            rhs=rhs,
            description=description,
        )
        self.constraints.append(c)
        return c
