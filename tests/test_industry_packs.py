"""
Tests for Industry Packs (Retail and Energy domain simulation models).
"""
import pytest
from mathematical_engine.core.context import ExecutionContext
from mathematical_engine.industry_packs.retail import (
    RetailPriceElasticityModel,
    RetailInventoryModel,
)
from mathematical_engine.industry_packs.energy import (
    EnergyDispatchModel,
    BatteryStorageModel,
)


class TestRetailPack:
    def test_price_elasticity_model(self):
        model = RetailPriceElasticityModel()
        ctx = ExecutionContext(
            baseline_values={
                "base_price": 10.0,
                "promo_discount_pct": 10.0,
                "units_sold": 1000.0,
                "price_elasticity": -1.5,
                "cogs_usd": 4000.0,  # $4.00 per unit
            }
        )
        outputs = model.run(ctx)

        # eff_price = 10 * 0.9 = 9.0
        # price_ratio = 0.9 -> (0.9)^(-1.5) = 1.1712
        # units = 1000 * 1.1712 = 1171.2
        # revenue = 9.0 * 1171.2 = 10540.8
        # cogs = 4.0 * 1171.2 = 4684.8
        # margin = 10540.8 - 4684.8 = 5856.0
        assert outputs["effective_price"] == 9.0
        assert pytest.approx(outputs["units_sold_simulated"], rel=1e-2) == 1171.2
        assert outputs["net_sales_usd"] > 10000.0
        assert outputs["gross_margin_usd"] > 5500.0
        assert outputs["gross_margin_pct"] > 50.0

    def test_inventory_model(self):
        model = RetailInventoryModel()
        ctx = ExecutionContext(
            baseline_values={
                "units_sold": 300.0,      # 10 units/day
                "on_hand_inventory": 40.0, # 4 days of supply
            }
        )
        outputs = model.run(ctx)
        assert outputs["days_of_supply"] == 4.0
        assert outputs["stockout_risk_score"] == 0.45


class TestEnergyPack:
    def test_merit_order_dispatch(self):
        model = EnergyDispatchModel()
        ctx = ExecutionContext(
            baseline_values={
                "grid_demand_mw": 500.0,
                "solar_available_mw": 100.0,
                "wind_available_mw": 150.0,
                "gas_ccgt_capacity_mw": 300.0,
                "peaker_capacity_mw": 100.0,
                "marginal_cost_ccgt": 40.0,
                "marginal_cost_peaker": 90.0,
            }
        )
        outputs = model.run(ctx)

        # Solar (100) + Wind (150) = 250 MW renewables
        # Remaining demand = 500 - 250 = 250 MW from CCGT (cap 300)
        # Peaker = 0 MW
        assert outputs["solar_dispatched_mw"] == 100.0
        assert outputs["wind_dispatched_mw"] == 150.0
        assert outputs["ccgt_dispatched_mw"] == 250.0
        assert outputs["peaker_dispatched_mw"] == 0.0
        assert outputs["unserved_energy_mw"] == 0.0
        assert outputs["marginal_clearing_price_usd"] == 40.0
        assert outputs["total_operating_cost_usd"] == 250.0 * 40.0

    def test_battery_storage_arbitrage(self):
        model = BatteryStorageModel()
        # Case 1: Low market price -> Charge
        ctx_charge = ExecutionContext(
            baseline_values={
                "battery_capacity_mwh": 100.0,
                "current_soc_mwh": 20.0,
                "max_charge_rate_mw": 25.0,
                "max_discharge_rate_mw": 25.0,
                "market_price_usd_mwh": 15.0,  # <= 25.0 threshold
            }
        )
        out_charge = model.run(ctx_charge)
        assert out_charge["battery_dispatch_action"] == 1.0
        assert out_charge["battery_flow_mw"] > 0
        assert out_charge["next_soc_mwh"] > 20.0

        # Case 2: High market price -> Discharge
        ctx_discharge = ExecutionContext(
            baseline_values={
                "battery_capacity_mwh": 100.0,
                "current_soc_mwh": 80.0,
                "max_charge_rate_mw": 25.0,
                "max_discharge_rate_mw": 25.0,
                "market_price_usd_mwh": 85.0,  # >= 65.0 threshold
            }
        )
        out_discharge = model.run(ctx_discharge)
        assert out_discharge["battery_dispatch_action"] == -1.0
        assert out_discharge["battery_flow_mw"] > 0
        assert out_discharge["next_soc_mwh"] < 80.0
        assert out_discharge["arbitrage_profit_usd"] > 0
