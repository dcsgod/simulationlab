"""
Explainability, factor attribution waterfall, and trace analysis endpoints.
"""
from fastapi import APIRouter
from typing import List
from pydantic import BaseModel

from mathematical_engine.contracts.scenario import Scenario
from mathematical_engine.explainability import FactorContribution, ContributionAnalyzer
from mathematical_engine.graph.dag_executor import DAGExecutor
from api.routes.scenarios import get_scenario

router = APIRouter(prefix="/api/explainability", tags=["Explainability"])


class WaterfallRequest(BaseModel):
    scenario_id: str
    target_metric: str = "gross_margin_usd"


@router.post("/waterfall", response_model=List[FactorContribution])
def analyze_waterfall(req: WaterfallRequest):
    scenario = get_scenario(req.scenario_id)

    dag = DAGExecutor()
    dag.register_formula("effective_price", "base_price * (1.0 - promo_discount_pct / 100.0)")
    dag.register_formula("revenue", "effective_price * units_sold")
    dag.register_formula("net_sales_usd", "revenue")
    dag.register_formula("gross_margin_usd", "revenue - cogs_usd")

    analyzer = ContributionAnalyzer(dag_executor=dag)
    return analyzer.analyze_waterfall(
        scenario=scenario,
        target_variable=req.target_metric,
        baseline=scenario.baseline,
    )
