"""
Optimization workspace endpoints solving LP and MILP problems with HiGHS.
"""
from fastapi import APIRouter
from typing import Optional
from pydantic import BaseModel, Field

from mathematical_engine.optimization.problem import (
    OptimizationProblem,
    VariableType,
    ConstraintSense,
    ObjectiveDirection,
)
from mathematical_engine.optimization.solver_registry import HiGHSSolver, OptimizationResult

router = APIRouter(prefix="/api/optimization", tags=["Optimization"])


class SolveOptimizationRequest(BaseModel):
    problem: Optional[OptimizationProblem] = None
    template_name: Optional[str] = Field(
        default=None,
        description="'retail_promo_allocation' or 'energy_dispatch_least_cost'"
    )


def _build_retail_allocation_template() -> OptimizationProblem:
    # Allocate $50,000 promotional budget across 3 product categories to maximize total margin lift
    prob = OptimizationProblem(name="Promotional Budget Allocation")
    prob.add_variable("promo_beverages", lower_bound=0.0, upper_bound=25000.0)
    prob.add_variable("promo_snacks", lower_bound=0.0, upper_bound=20000.0)
    prob.add_variable("promo_organics", lower_bound=0.0, upper_bound=20000.0)

    # Return per marketing dollar: Beverages: $3.20, Snacks: $2.80, Organics: $4.10
    prob.set_objective(
        coefficients={"promo_beverages": 3.20, "promo_snacks": 2.80, "promo_organics": 4.10},
        direction=ObjectiveDirection.MAXIMIZE,
        description="Maximize Gross Margin Contribution Lift",
    )

    # Total budget constraint <= 50,000
    prob.add_constraint(
        name="total_promo_budget",
        coefficients={"promo_beverages": 1.0, "promo_snacks": 1.0, "promo_organics": 1.0},
        sense=ConstraintSense.LE,
        rhs=50000.0,
        description="Marketing and Markdown Budget Limit",
    )

    # Minimum threshold on beverages (contractual) >= 10,000
    prob.add_constraint(
        name="min_beverage_support",
        coefficients={"promo_beverages": 1.0},
        sense=ConstraintSense.GE,
        rhs=10000.0,
    )

    return prob


def _build_energy_dispatch_template() -> OptimizationProblem:
    # Least-cost hourly generation dispatch meeting 600 MW demand
    prob = OptimizationProblem(name="Grid Dispatch Least-Cost Optimization")
    prob.add_variable("solar_mw", lower_bound=0.0, upper_bound=120.0)
    prob.add_variable("wind_mw", lower_bound=0.0, upper_bound=180.0)
    prob.add_variable("ccgt_gas_mw", lower_bound=0.0, upper_bound=400.0)
    prob.add_variable("peaker_mw", lower_bound=0.0, upper_bound=150.0)

    # Marginal cost per MWh: Solar: $5, Wind: $8, CCGT: $48, Peaker: $95
    prob.set_objective(
        coefficients={"solar_mw": 5.0, "wind_mw": 8.0, "ccgt_gas_mw": 48.0, "peaker_mw": 95.0},
        direction=ObjectiveDirection.MINIMIZE,
        description="Minimize Generation Operating Cost",
    )

    # Supply must meet 600 MW load
    prob.add_constraint(
        name="grid_load_balance",
        coefficients={"solar_mw": 1.0, "wind_mw": 1.0, "ccgt_gas_mw": 1.0, "peaker_mw": 1.0},
        sense=ConstraintSense.EQ,
        rhs=600.0,
        description="Generation must match target load exactly",
    )

    return prob


@router.post("/solve", response_model=OptimizationResult)
def solve_optimization(req: SolveOptimizationRequest):
    if req.problem:
        prob = req.problem
    elif req.template_name == "energy_dispatch_least_cost":
        prob = _build_energy_dispatch_template()
    else:
        prob = _build_retail_allocation_template()

    solver = HiGHSSolver()
    return solver.solve(prob)
