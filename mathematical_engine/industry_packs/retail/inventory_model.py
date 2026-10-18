"""
Retail inventory, safety stock, and stockout risk models.
"""
from typing import Dict
from mathematical_engine.core.base_model import (
    BaseSimulationModel,
    ModelMetadata,
    ModelCapability,
)
from mathematical_engine.core.context import ExecutionContext


class RetailInventoryModel(BaseSimulationModel):
    """
    Evaluates inventory turnover, holding costs, and stockout probability given simulated sales volume.
    """

    def __init__(self):
        super().__init__(
            ModelMetadata(
                id="retail_inventory_model",
                name="Retail Inventory & Stockout Risk Model",
                version="1.0.0",
                description="Calculates inventory runway, stockout probability, and inventory carrying costs.",
                capabilities=[ModelCapability.DETERMINISTIC],
                required_inputs=["units_sold", "on_hand_inventory"],
                produced_outputs=["days_of_supply", "stockout_risk_score", "carrying_cost_usd"],
            )
        )

    def run(self, context: ExecutionContext) -> Dict[str, float]:
        self.validate_inputs(context)

        units_demand = max(0.1, context.get_value("units_sold"))
        on_hand = max(0.0, context.get_value("on_hand_inventory"))
        carrying_rate = context.current_values.get("carrying_rate_pct", 20.0) / 100.0
        unit_cost = context.current_values.get("unit_cost", 10.0)

        daily_rate = units_demand / 30.0  # assume monthly volume
        days_of_supply = on_hand / daily_rate if daily_rate > 0 else 999.0

        # Stockout risk is high if days of supply < 5
        if days_of_supply < 3:
            stockout_risk = 0.95
        elif days_of_supply < 7:
            stockout_risk = 0.45
        elif days_of_supply < 14:
            stockout_risk = 0.10
        else:
            stockout_risk = 0.01

        carrying_cost = on_hand * unit_cost * (carrying_rate / 12.0)

        return {
            "days_of_supply": round(days_of_supply, 1),
            "stockout_risk_score": round(stockout_risk, 2),
            "carrying_cost_usd": round(carrying_cost, 2),
        }
