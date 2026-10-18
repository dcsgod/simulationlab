"""
Retail price elasticity, promotional markdown, and margin response model.
"""
from typing import Dict
from mathematical_engine.core.base_model import (
    BaseSimulationModel,
    ModelMetadata,
    ModelCapability,
)
from mathematical_engine.core.context import ExecutionContext


class RetailPriceElasticityModel(BaseSimulationModel):
    """
    Simulates demand volume response, revenue, and gross profit following price and promo interventions.
    """

    def __init__(self):
        super().__init__(
            ModelMetadata(
                id="retail_price_elasticity_model",
                name="Retail Price Elasticity & Margin Model",
                version="1.0.0",
                description="Simulates demand elasticity Q = Q0 * (P_eff / P0)^elasticity, gross revenue, and profit margins.",
                capabilities=[ModelCapability.DETERMINISTIC, ModelCapability.SENSITIVITY],
                required_inputs=[
                    "base_price",
                    "promo_discount_pct",
                    "units_sold",
                    "price_elasticity",
                ],
                produced_outputs=[
                    "effective_price",
                    "units_sold_simulated",
                    "net_sales_usd",
                    "gross_margin_usd",
                    "gross_margin_pct",
                ],
            )
        )

    def run(self, context: ExecutionContext) -> Dict[str, float]:
        self.validate_inputs(context)

        base_price = context.get_value("base_price")
        promo_pct = context.get_value("promo_discount_pct")
        base_units = context.get_value("units_sold")
        elasticity = context.get_value("price_elasticity")
        cogs_usd = context.current_values.get("cogs_usd", base_units * 0.5 * base_price)

        # 1. Effective price after promotional discount
        eff_price = max(0.01, base_price * (1.0 - promo_pct / 100.0))

        # 2. Demand response: Q_new = Q0 * (P_eff / P0)^elasticity
        price_ratio = eff_price / max(0.01, base_price)
        units_simulated = max(0.0, base_units * (price_ratio ** elasticity))

        # 3. Revenue & COGS
        revenue = eff_price * units_simulated
        unit_cost = cogs_usd / max(1.0, base_units)
        total_cogs = unit_cost * units_simulated
        gross_margin = revenue - total_cogs
        margin_pct = (gross_margin / revenue * 100.0) if revenue > 1e-6 else 0.0

        outputs = {
            "effective_price": round(eff_price, 2),
            "units_sold_simulated": round(units_simulated, 1),
            "net_sales_usd": round(revenue, 2),
            "gross_margin_usd": round(gross_margin, 2),
            "gross_margin_pct": round(margin_pct, 2),
        }

        return outputs
