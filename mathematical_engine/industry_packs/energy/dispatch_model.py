"""
Grid dispatch merit-order economic model with carbon accounting.
"""
from typing import Dict
from mathematical_engine.core.base_model import (
    BaseSimulationModel,
    ModelMetadata,
    ModelCapability,
)
from mathematical_engine.core.context import ExecutionContext


class EnergyDispatchModel(BaseSimulationModel):
    """
    Solves hourly merit-order economic dispatch across renewable and thermal generation fleets.
    """

    def __init__(self):
        super().__init__(
            ModelMetadata(
                id="energy_dispatch_model",
                name="Grid Economic Merit-Order Dispatch Model",
                version="1.0.0",
                description="Dispatches generation assets in ascending order of marginal operating cost to satisfy net demand.",
                capabilities=[ModelCapability.DETERMINISTIC, ModelCapability.OPTIMIZATION],
                required_inputs=[
                    "grid_demand_mw",
                    "solar_available_mw",
                    "wind_available_mw",
                    "gas_ccgt_capacity_mw",
                    "peaker_capacity_mw",
                ],
                produced_outputs=[
                    "solar_dispatched_mw",
                    "wind_dispatched_mw",
                    "ccgt_dispatched_mw",
                    "peaker_dispatched_mw",
                    "unserved_energy_mw",
                    "total_operating_cost_usd",
                    "total_co2_emissions_tons",
                    "marginal_clearing_price_usd",
                ],
            )
        )

    def run(self, context: ExecutionContext) -> Dict[str, float]:
        self.validate_inputs(context)

        demand = context.get_value("grid_demand_mw")
        solar_cap = context.get_value("solar_available_mw")
        wind_cap = context.get_value("wind_available_mw")
        ccgt_cap = context.get_value("gas_ccgt_capacity_mw")
        peaker_cap = context.get_value("peaker_capacity_mw")

        # Marginal costs per MWh
        c_solar = 0.0
        c_wind = 0.0
        c_ccgt = context.current_values.get("marginal_cost_ccgt", 45.0)
        c_peaker = context.current_values.get("marginal_cost_peaker", 95.0)

        # Emissions tons per MWh
        e_ccgt = 0.38
        e_peaker = 0.55

        remaining = demand
        total_cost = 0.0
        total_co2 = 0.0
        clearing_price = 0.0

        # 1. Dispatch Solar
        solar_disp = min(remaining, solar_cap)
        remaining -= solar_disp
        total_cost += solar_disp * c_solar
        if solar_disp > 0:
            clearing_price = c_solar

        # 2. Dispatch Wind
        wind_disp = min(remaining, wind_cap)
        remaining -= wind_disp
        total_cost += wind_disp * c_wind
        if wind_disp > 0:
            clearing_price = c_wind

        # 3. Dispatch Gas CCGT
        ccgt_disp = min(remaining, ccgt_cap)
        remaining -= ccgt_disp
        total_cost += ccgt_disp * c_ccgt
        total_co2 += ccgt_disp * e_ccgt
        if ccgt_disp > 0:
            clearing_price = c_ccgt

        # 4. Dispatch Peaker
        peaker_disp = min(remaining, peaker_cap)
        remaining -= peaker_disp
        total_cost += peaker_disp * c_peaker
        total_co2 += peaker_disp * e_peaker
        if peaker_disp > 0:
            clearing_price = c_peaker

        unserved = max(0.0, remaining)
        if unserved > 0:
            clearing_price = 1000.0  # Value of Lost Load (VoLL)

        return {
            "solar_dispatched_mw": round(solar_disp, 2),
            "wind_dispatched_mw": round(wind_disp, 2),
            "ccgt_dispatched_mw": round(ccgt_disp, 2),
            "peaker_dispatched_mw": round(peaker_disp, 2),
            "unserved_energy_mw": round(unserved, 2),
            "total_operating_cost_usd": round(total_cost, 2),
            "total_co2_emissions_tons": round(total_co2, 2),
            "marginal_clearing_price_usd": round(clearing_price, 2),
        }
