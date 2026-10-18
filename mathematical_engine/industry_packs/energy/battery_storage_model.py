"""
Battery Energy Storage System (BESS) dispatch, charging, and state-of-charge tracking model.
"""
from typing import Dict
from mathematical_engine.core.base_model import (
    BaseSimulationModel,
    ModelMetadata,
    ModelCapability,
)
from mathematical_engine.core.context import ExecutionContext


class BatteryStorageModel(BaseSimulationModel):
    """
    Simulates charging from low-cost renewable surplus and discharging into high-clearing evening peak.
    """

    def __init__(self):
        super().__init__(
            ModelMetadata(
                id="battery_storage_model",
                name="Battery Storage (BESS) Arbitrage Model",
                version="1.0.0",
                description="Models battery state of charge (SoC), charging from low-cost supply, and peak shaving discharge.",
                capabilities=[ModelCapability.DETERMINISTIC, ModelCapability.OPTIMIZATION],
                required_inputs=[
                    "battery_capacity_mwh",
                    "current_soc_mwh",
                    "max_charge_rate_mw",
                    "max_discharge_rate_mw",
                    "market_price_usd_mwh",
                ],
                produced_outputs=[
                    "battery_dispatch_action",
                    "battery_flow_mw",
                    "next_soc_mwh",
                    "arbitrage_profit_usd",
                ],
            )
        )

    def run(self, context: ExecutionContext) -> Dict[str, float]:
        self.validate_inputs(context)

        capacity = context.get_value("battery_capacity_mwh")
        curr_soc = context.get_value("current_soc_mwh")
        max_chg = context.get_value("max_charge_rate_mw")
        max_dis = context.get_value("max_discharge_rate_mw")
        price = context.get_value("market_price_usd_mwh")

        roundtrip_eff = context.current_values.get("roundtrip_efficiency_pct", 88.0) / 100.0
        one_way_eff = roundtrip_eff ** 0.5

        charge_threshold_price = context.current_values.get("charge_threshold_price", 25.0)
        discharge_threshold_price = context.current_values.get("discharge_threshold_price", 65.0)

        action = 0.0  # 0 = idle, 1 = charge, -1 = discharge
        flow_mw = 0.0
        profit = 0.0

        if price <= charge_threshold_price and curr_soc < capacity:
            # Charge
            action = 1.0
            space = (capacity - curr_soc) / one_way_eff
            flow_mw = min(max_chg, space)
            next_soc = curr_soc + flow_mw * one_way_eff
            profit = -flow_mw * price  # cost to charge

        elif price >= discharge_threshold_price and curr_soc > 0.05 * capacity:
            # Discharge
            action = -1.0
            available = curr_soc * one_way_eff
            flow_mw = min(max_dis, available)
            next_soc = curr_soc - (flow_mw / one_way_eff)
            profit = flow_mw * price  # revenue from discharge

        else:
            # Idle
            action = 0.0
            flow_mw = 0.0
            next_soc = curr_soc

        return {
            "battery_dispatch_action": action,
            "battery_flow_mw": round(flow_mw, 2),
            "next_soc_mwh": round(next_soc, 2),
            "arbitrage_profit_usd": round(profit, 2),
        }
