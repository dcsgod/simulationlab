"""
Common objective function builders (profit maximization, cost minimization).
"""
from typing import Dict
from mathematical_engine.optimization.problem import (
    OptimizationProblem,
    ObjectiveDirection,
)


def set_profit_maximization_objective(
    problem: OptimizationProblem,
    margins_or_prices: Dict[str, float],
    fixed_cost: float = 0.0,
) -> None:
    """Sets objective: Maximize sum(margin_i * x_i) - fixed_cost."""
    problem.set_objective(
        coefficients=margins_or_prices,
        direction=ObjectiveDirection.MAXIMIZE,
        constant=-fixed_cost,
        description="Maximize total contribution profit less fixed cost",
    )


def set_cost_minimization_objective(
    problem: OptimizationProblem,
    unit_costs: Dict[str, float],
    fixed_cost: float = 0.0,
) -> None:
    """Sets objective: Minimize sum(unit_cost_i * x_i) + fixed_cost."""
    problem.set_objective(
        coefficients=unit_costs,
        direction=ObjectiveDirection.MINIMIZE,
        constant=fixed_cost,
        description="Minimize total operating and variable costs",
    )
