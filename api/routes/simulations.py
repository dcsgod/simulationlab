"""
Simulation execution endpoints (deterministic and stochastic Monte Carlo).
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Optional, Any
from pydantic import BaseModel, Field

from mathematical_engine.contracts.scenario import Scenario
from mathematical_engine.contracts.results import SimulationResult
from mathematical_engine.stochastic.distributions import ParameterDistribution, DistributionType
from mathematical_engine.graph.dag_executor import DAGExecutor
from mathematical_engine.core.engine import MathematicalEngine
from connectors import MockDataProvider
from orchestration.scenario_planner import ScenarioPlanner
from api.routes.scenarios import get_scenario

router = APIRouter(prefix="/api/simulations", tags=["Simulations"])


def _build_engine() -> MathematicalEngine:
    dag = DAGExecutor()
    dag.register_formula("effective_price", "base_price * (1.0 - promo_discount_pct / 100.0)")
    dag.register_formula("revenue", "effective_price * units_sold")
    dag.register_formula("net_sales_usd", "revenue")
    dag.register_formula("gross_margin_usd", "revenue - cogs_usd")
    return MathematicalEngine(dag_executor=dag)


class RunSimulationRequest(BaseModel):
    scenario: Optional[Scenario] = None
    scenario_id: Optional[str] = None
    mode: str = Field(default="deterministic", description="'deterministic' or 'monte_carlo'")
    num_iterations: int = Field(default=1000, ge=10, le=10000)
    seed: Optional[int] = 42
    uncertain_parameters: Optional[Dict[str, ParameterDistribution]] = None


@router.post("/run", response_model=SimulationResult)
def run_simulation(req: RunSimulationRequest):
    # Resolve scenario
    if req.scenario:
        scenario = req.scenario
    elif req.scenario_id:
        scenario = get_scenario(req.scenario_id)
    else:
        # Default scenario
        provider = MockDataProvider()
        planner = ScenarioPlanner(provider)
        scenario = planner.plan_scenario_from_intent(
            intent=None, scenario_name="Default Retail Margin Simulation"
        )

    engine = _build_engine()

    if req.mode == "monte_carlo":
        # Build default uncertainty on volume if none provided
        uncertain_params = req.uncertain_parameters or {
            "units_sold": ParameterDistribution(
                variable_name="units_sold",
                dist_type=DistributionType.NORMAL,
                parameters={"mean": scenario.baseline.get_value("units_sold"), "std": 15.0},
            )
        }
        res = engine.run_monte_carlo(
            scenario=scenario,
            uncertain_parameters=uncertain_params,
            num_iterations=req.num_iterations,
            seed=req.seed,
            baseline=scenario.baseline,
        )
    else:
        res = engine.run_deterministic(scenario, baseline=scenario.baseline)

    return res
