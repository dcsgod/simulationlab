"""
Standard constraint patterns: budgets, capacities, balance, and exclusivity.
"""
from typing import Dict, List, Optional
from mathematical_engine.optimization.problem import (
    LinearConstraint,
    ConstraintSense,
    OptimizationProblem,
)


def add_budget_constraint(
    problem: OptimizationProblem,
    name: str,
    costs: Dict[str, float],
    max_budget: float,
) -> LinearConstraint:
    """Adds sum(cost_i * x_i) <= max_budget."""
    return problem.add_constraint(
        name=name,
        coefficients=costs,
        sense=ConstraintSense.LE,
        rhs=max_budget,
        description=f"Total cost budget limit of {max_budget:g}",
    )


def add_demand_balance_constraint(
    problem: OptimizationProblem,
    name: str,
    supply_vars: List[str],
    demand_target: float,
) -> LinearConstraint:
    """Adds sum(supply_vars) == demand_target."""
    coefs = {v: 1.0 for v in supply_vars}
    return problem.add_constraint(
        name=name,
        coefficients=coefs,
        sense=ConstraintSense.EQ,
        rhs=demand_target,
        description=f"Supply must meet target demand of {demand_target:g}",
    )
