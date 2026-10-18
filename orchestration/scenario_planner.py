"""
Scenario planning bridging parsed intent and connector baseline data.
"""
from typing import Dict, List, Optional
import uuid

from mathematical_engine.contracts.inputs import BaselineState, Intervention, InterventionType
from mathematical_engine.contracts.metrics import NumericVariable
from mathematical_engine.contracts.scenario import Scenario
from connectors.base import BaseDataProvider
from orchestration.intent_parser import ParsedIntent


class ScenarioPlanner:
    """
    Constructs parameterized simulation scenarios from natural language intent and lakehouse data.
    """

    def __init__(self, data_provider: BaseDataProvider):
        self.data_provider = data_provider

    def build_retail_baseline(self) -> BaselineState:
        """
        Samples daily store sales from the data provider and computes mean baseline values.
        Supports both live Databricks Unity Catalog and Mock lakehouse.
        """
        if "databricks" in self.data_provider.source_id.lower():
            catalog = "workspace"
            schema = "default"
            table = "retail_store_sales"
        else:
            catalog = "retail_lakehouse"
            schema = "gold_analytics"
            table = "daily_store_sales"

        sample = self.data_provider.sample_table(
            catalog=catalog,
            schema=schema,
            table=table,
            limit=200,
        )

        rows = sample.rows
        if not rows:
            raise ValueError(f"No records found in {catalog}.{schema}.{table}.")

        avg_price = sum(r.get("base_price", 4.99) for r in rows) / len(rows)
        avg_promo = sum(r.get("promo_discount_pct", 0.0) for r in rows) / len(rows)
        avg_units = sum(r.get("units_sold", 120.0) for r in rows) / len(rows)
        avg_cogs = sum(r.get("cogs_usd", 250.0) for r in rows) / len(rows)
        avg_sales = sum(r.get("net_sales_usd", 500.0) for r in rows) / len(rows)
        avg_margin = sum(r.get("gross_margin_usd", 250.0) for r in rows) / len(rows)

        vars_dict = {
            "base_price": NumericVariable(name="base_price", value=round(avg_price, 2), unit="USD", min_bound=0.5),
            "promo_discount_pct": NumericVariable(name="promo_discount_pct", value=round(avg_promo, 2), unit="%", min_bound=0.0, max_bound=80.0),
            "units_sold": NumericVariable(name="units_sold", value=round(avg_units, 1), unit="units", min_bound=0.0),
            "cogs_usd": NumericVariable(name="cogs_usd", value=round(avg_cogs, 2), unit="USD"),
            "net_sales_usd": NumericVariable(name="net_sales_usd", value=round(avg_sales, 2), unit="USD"),
            "gross_margin_usd": NumericVariable(name="gross_margin_usd", value=round(avg_margin, 2), unit="USD"),
            "price_elasticity": NumericVariable(name="price_elasticity", value=-1.45, unit="ratio"),
        }

        return BaselineState(
            snapshot_id=f"snap_retail_{uuid.uuid4().hex[:8]}",
            variables=vars_dict,
            metadata={"source_table": "retail_lakehouse.gold_analytics.daily_store_sales"},
        )

    def plan_scenario_from_intent(self, intent: ParsedIntent, scenario_name: Optional[str] = None) -> Scenario:
        """
        Translates a parsed intent into an executable Scenario.
        """
        baseline = self.build_retail_baseline()

        interventions: List[Intervention] = []
        for p_int in intent.interventions:
            interventions.append(
                Intervention(
                    target_variable=p_int.variable_name,
                    intervention_type=p_int.intervention_type,
                    value=p_int.value,
                    description=p_int.raw_text or f"{p_int.variable_name} delta {p_int.value}",
                )
            )

        # Target variables
        target_vars = [intent.target_metric] if intent.target_metric else ["gross_margin_usd", "net_sales_usd"]
        for p_int in intent.interventions:
            if p_int.variable_name not in target_vars:
                target_vars.append(p_int.variable_name)

        return Scenario(
            name=scenario_name or f"Plan: {intent.raw_prompt[:50]}",
            baseline=baseline,
            interventions=interventions,
            target_variables=target_vars,
            assumptions={"price_elasticity": -1.45, "cross_elasticity": 0.25},
            metadata={"raw_prompt": intent.raw_prompt},
        )
