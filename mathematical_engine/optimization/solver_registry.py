"""
SciPy HiGHS optimization solver wrapper for LP and MILP problems with diagnostics.
"""
from typing import Dict, List, Optional, Any
import time
import numpy as np
from pydantic import BaseModel, Field
from scipy.optimize import milp, LinearConstraint as ScipyLinearConstraint, Bounds

from mathematical_engine.optimization.problem import (
    OptimizationProblem,
    ObjectiveDirection,
    ConstraintSense,
    VariableType,
)
from mathematical_engine.core.errors import InfeasibleOptimizationError


class OptimizationResult(BaseModel):
    problem_name: str
    status: str = Field(..., description="'OPTIMAL', 'INFEASIBLE', 'UNBOUNDED', or 'FAILED'")
    is_optimal: bool
    objective_value: Optional[float] = None
    variable_values: Dict[str, float] = Field(default_factory=dict)
    constraint_slacks: Dict[str, float] = Field(default_factory=dict)
    diagnostics: List[str] = Field(default_factory=list)
    solve_time_ms: float = 0.0


class HiGHSSolver:
    """
    Executes Linear and Mixed-Integer Linear Programs via SciPy's HiGHS C++ solver engine.
    """

    def solve(self, problem: OptimizationProblem, raise_on_infeasible: bool = False) -> OptimizationResult:
        start_time = time.time()
        if not problem.variables:
            raise ValueError(f"Optimization problem '{problem.name}' has no decision variables.")
        if problem.objective is None:
            raise ValueError(f"Optimization problem '{problem.name}' has no objective defined.")

        var_names = list(problem.variables.keys())
        n_vars = len(var_names)
        var_to_idx = {name: i for i, name in enumerate(var_names)}

        # 1. Objective vector 'c' (SciPy minimizes c^T * x)
        direction_sign = 1.0 if problem.objective.direction == ObjectiveDirection.MINIMIZE else -1.0
        c = np.zeros(n_vars, dtype=float)
        for name, coef in problem.objective.coefficients.items():
            if name in var_to_idx:
                c[var_to_idx[name]] = coef * direction_sign

        # 2. Variable bounds and integrality
        lb = np.zeros(n_vars, dtype=float)
        ub = np.zeros(n_vars, dtype=float)
        integrality = np.zeros(n_vars, dtype=int)

        for i, name in enumerate(var_names):
            var = problem.variables[name]
            lb[i] = var.lower_bound if var.lower_bound is not None else -np.inf
            ub[i] = var.upper_bound if var.upper_bound is not None else np.inf

            if var.var_type in (VariableType.INTEGER, VariableType.BINARY):
                integrality[i] = 1

        bounds = Bounds(lb=lb, ub=ub)

        # 3. Constraints
        constraints_list = []
        if problem.constraints:
            n_cons = len(problem.constraints)
            A = np.zeros((n_cons, n_vars), dtype=float)
            c_lb = np.zeros(n_cons, dtype=float)
            c_ub = np.zeros(n_cons, dtype=float)

            for i, constraint in enumerate(problem.constraints):
                for vname, coef in constraint.coefficients.items():
                    if vname in var_to_idx:
                        A[i, var_to_idx[vname]] = coef

                if constraint.sense == ConstraintSense.LE:
                    c_lb[i] = -np.inf
                    c_ub[i] = constraint.rhs
                elif constraint.sense == ConstraintSense.GE:
                    c_lb[i] = constraint.rhs
                    c_ub[i] = np.inf
                elif constraint.sense == ConstraintSense.EQ:
                    c_lb[i] = constraint.rhs
                    c_ub[i] = constraint.rhs

            constraints_list.append(ScipyLinearConstraint(A, c_lb, c_ub))

        # 4. Invoke SciPy MILP HiGHS solver
        res = milp(
            c=c,
            integrality=integrality,
            bounds=bounds,
            constraints=constraints_list if constraints_list else None,
        )

        solve_time_ms = (time.time() - start_time) * 1000.0

        # Translate status
        if res.success:
            status = "OPTIMAL"
            is_optimal = True
            obj_val = float(res.fun * direction_sign + problem.objective.constant)
            var_vals = {name: float(res.x[i]) for i, name in enumerate(var_names)}

            # Compute constraint slacks
            slacks: Dict[str, float] = {}
            for i, constraint in enumerate(problem.constraints):
                lhs = sum(constraint.coefficients.get(v, 0.0) * var_vals[v] for v in var_names)
                if constraint.sense == ConstraintSense.LE:
                    slacks[constraint.name] = constraint.rhs - lhs
                elif constraint.sense == ConstraintSense.GE:
                    slacks[constraint.name] = lhs - constraint.rhs
                else:
                    slacks[constraint.name] = abs(lhs - constraint.rhs)

            return OptimizationResult(
                problem_name=problem.name,
                status=status,
                is_optimal=is_optimal,
                objective_value=obj_val,
                variable_values=var_vals,
                constraint_slacks=slacks,
                diagnostics=["Optimization solved to proven optimality."],
                solve_time_ms=solve_time_ms,
            )

        else:
            diagnostics = [f"HiGHS solver reported status: {res.status} ({res.message})"]
            if res.status in (2, 3):  # Infeasible or unbounded
                status = "INFEASIBLE"
                diagnostics.append("Problem constraints or variable bounds are contradictory.")
                if raise_on_infeasible:
                    raise InfeasibleOptimizationError(
                        f"Optimization problem '{problem.name}' is infeasible: {res.message}"
                    )
            else:
                status = "FAILED"

            return OptimizationResult(
                problem_name=problem.name,
                status=status,
                is_optimal=False,
                objective_value=None,
                variable_values={},
                constraint_slacks={},
                diagnostics=diagnostics,
                solve_time_ms=solve_time_ms,
            )
