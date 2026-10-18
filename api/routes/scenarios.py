"""
Scenario templates, builder endpoints, and scenario persistence.
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional
import uuid

from mathematical_engine.contracts.inputs import BaselineState, Intervention, InterventionType
from mathematical_engine.contracts.metrics import NumericVariable
from mathematical_engine.contracts.scenario import Scenario
from connectors import MockDataProvider
from orchestration.scenario_planner import ScenarioPlanner

router = APIRouter(prefix="/api/scenarios", tags=["Scenarios"])

_scenarios_store: Dict[str, Scenario] = {}


def _get_templates() -> List[Scenario]:
    provider = MockDataProvider()
    planner = ScenarioPlanner(provider)
    base = planner.build_retail_baseline()

    scen1 = Scenario(
        id="template_retail_promo_lift",
        name="Promotional 15% Discount with Elasticity Lift",
        description="Evaluates margin impact of a 15% discount on fast-moving beverages with price elasticity of -1.45.",
        baseline=base,
        interventions=[
            Intervention(
                target_variable="promo_discount_pct",
                intervention_type=InterventionType.SET_VALUE,
                value=15.0,
                description="Set promotional discount to 15%",
            )
        ],
        target_variables=["promo_discount_pct", "effective_price", "units_sold", "net_sales_usd", "gross_margin_usd"],
        tags=["Retail", "Promotions", "Pricing"],
    )

    scen2 = Scenario(
        id="template_retail_cost_inflation",
        name="Supply Chain 8% COGS Inflation",
        description="Assesses gross profit resilience against an 8% increase in unit cost of goods.",
        baseline=base,
        interventions=[
            Intervention(
                target_variable="cogs_usd",
                intervention_type=InterventionType.PERCENTAGE_DELTA,
                value=8.0,
                description="8% increase in COGS due to supplier price adjustments",
            )
        ],
        target_variables=["cogs_usd", "net_sales_usd", "gross_margin_usd"],
        tags=["Retail", "Inflation", "Cost Optimization"],
    )

    return [scen1, scen2]


@router.get("/templates", response_model=List[Scenario])
def get_scenario_templates():
    return _get_templates()


@router.get("", response_model=List[Scenario])
def list_scenarios():
    templates = _get_templates()
    custom = list(_scenarios_store.values())
    return templates + custom


@router.post("", response_model=Scenario)
def save_scenario(scenario: Scenario):
    if not scenario.id:
        scenario.id = str(uuid.uuid4())
    _scenarios_store[scenario.id] = scenario
    return scenario


@router.get("/{scenario_id}", response_model=Scenario)
def get_scenario(scenario_id: str):
    if scenario_id in _scenarios_store:
        return _scenarios_store[scenario_id]
    for t in _get_templates():
        if t.id == scenario_id:
            return t
    raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found.")
