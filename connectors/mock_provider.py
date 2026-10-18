"""
Synthetic enterprise data provider offering realistic Retail and Energy industry datasets.
Runs fully in-memory with zero external service dependencies.
"""
from typing import Dict, List, Optional, Any
import time
import numpy as np
import pandas as pd

from connectors.base import (
    BaseDataProvider,
    DataSourceType,
    TableSchema,
    ColumnDefinition,
    QueryResult,
)
from connectors.cache import MetadataCache


def _generate_synthetic_retail_data() -> Dict[str, pd.DataFrame]:
    rng = np.random.default_rng(42)
    n_days = 30
    stores = ["STORE_001", "STORE_002", "STORE_003"]
    skus = [
        {"sku": "SKU_BEV_01", "base_price": 4.99, "unit_cost": 2.50, "cat": "Beverages"},
        {"sku": "SKU_SNK_02", "base_price": 3.49, "unit_cost": 1.70, "cat": "Snacks"},
        {"sku": "SKU_ORG_03", "base_price": 8.99, "unit_cost": 5.20, "cat": "Organics"},
        {"sku": "SKU_DAI_04", "base_price": 5.49, "unit_cost": 3.10, "cat": "Dairy"},
    ]

    sales_rows = []
    base_date = pd.Timestamp("2026-09-01")

    for d in range(n_days):
        curr_date = base_date + pd.Timedelta(days=d)
        is_weekend = curr_date.dayofweek >= 5

        for store in stores:
            for item in skus:
                promo_pct = rng.choice([0.0, 0.10, 0.15, 0.20], p=[0.6, 0.2, 0.1, 0.1])
                eff_price = item["base_price"] * (1.0 - promo_pct)

                # Base volume with promo lift and weekend lift
                lift = 1.0 + (promo_pct * 2.5) + (0.3 if is_weekend else 0.0)
                base_qty = rng.normal(loc=120, scale=15)
                units = max(5, int(base_qty * lift))

                net_sales = round(units * eff_price, 2)
                cogs = round(units * item["unit_cost"], 2)
                margin = round(net_sales - cogs, 2)

                sales_rows.append({
                    "date": curr_date.strftime("%Y-%m-%d"),
                    "store_id": store,
                    "product_sku": item["sku"],
                    "category": item["cat"],
                    "units_sold": units,
                    "base_price": item["base_price"],
                    "promo_discount_pct": promo_pct * 100.0,
                    "effective_price": round(eff_price, 2),
                    "net_sales_usd": net_sales,
                    "cogs_usd": cogs,
                    "gross_margin_usd": margin,
                })

    df_sales = pd.DataFrame(sales_rows)

    # Inventory levels
    inv_rows = []
    for store in stores:
        for item in skus:
            inv_rows.append({
                "store_id": store,
                "product_sku": item["sku"],
                "on_hand_qty": int(rng.uniform(300, 1500)),
                "safety_stock_qty": 200,
                "reorder_point": 350,
                "lead_time_days": 3,
                "carrying_cost_pct": 18.5,
            })
    df_inv = pd.DataFrame(inv_rows)

    # Elasticity reference
    df_elast = pd.DataFrame([
        {"category": "Beverages", "price_elasticity": -1.45, "cross_elasticity": 0.25},
        {"category": "Snacks", "price_elasticity": -1.15, "cross_elasticity": 0.18},
        {"category": "Organics", "price_elasticity": -2.10, "cross_elasticity": 0.40},
        {"category": "Dairy", "price_elasticity": -0.85, "cross_elasticity": 0.12},
    ])

    return {
        "daily_store_sales": df_sales,
        "inventory_levels": df_inv,
        "price_elasticity_reference": df_elast,
    }


def _generate_synthetic_energy_data() -> Dict[str, pd.DataFrame]:
    rng = np.random.default_rng(123)
    hours = 48
    base_time = pd.Timestamp("2026-10-01 00:00:00")

    gen_rows = []
    assets = [
        {"id": "SOLAR_FARM_ALPHA", "fuel": "Solar", "cap_mw": 150.0, "cost": 5.0, "co2": 0.0},
        {"id": "WIND_PARK_BETA", "fuel": "Wind", "cap_mw": 200.0, "cost": 8.0, "co2": 0.0},
        {"id": "CCGT_GAS_GEN_1", "fuel": "Natural Gas", "cap_mw": 400.0, "cost": 48.0, "co2": 0.38},
        {"id": "PEAKER_GAS_2", "fuel": "Peaker Gas", "cap_mw": 180.0, "cost": 92.0, "co2": 0.55},
    ]

    for h in range(hours):
        t = base_time + pd.Timedelta(hours=h)
        hour_of_day = t.hour

        # Solar profile
        solar_factor = max(0.0, np.sin((hour_of_day - 6) * np.pi / 12)) if 6 <= hour_of_day <= 18 else 0.0
        # Wind profile
        wind_factor = 0.4 + 0.3 * np.cos(hour_of_day * np.pi / 12) + rng.normal(0, 0.05)
        wind_factor = max(0.1, min(1.0, wind_factor))

        for asset in assets:
            if asset["fuel"] == "Solar":
                gen = asset["cap_mw"] * solar_factor * rng.uniform(0.9, 1.0)
            elif asset["fuel"] == "Wind":
                gen = asset["cap_mw"] * wind_factor
            elif asset["fuel"] == "Natural Gas":
                gen = asset["cap_mw"] * rng.uniform(0.6, 0.95)
            else:
                # Peaker runs mostly in evening peak
                gen = asset["cap_mw"] * (0.8 if 17 <= hour_of_day <= 21 else 0.0)

            gen = round(max(0.0, gen), 2)
            emissions = round(gen * asset["co2"], 2)

            gen_rows.append({
                "timestamp": t.strftime("%Y-%m-%d %H:%M:%S"),
                "asset_id": asset["id"],
                "fuel_type": asset["fuel"],
                "capacity_mw": asset["cap_mw"],
                "generation_mwh": gen,
                "marginal_cost_usd_mwh": asset["cost"],
                "co2_emissions_tons": emissions,
            })

    df_gen = pd.DataFrame(gen_rows)

    # Battery storage assets
    df_batteries = pd.DataFrame([
        {"asset_id": "BESS_CENTRAL_01", "capacity_mwh": 200.0, "max_discharge_mw": 50.0, "roundtrip_efficiency_pct": 88.0, "soc_initial_pct": 50.0},
        {"asset_id": "BESS_WEST_02", "capacity_mwh": 100.0, "max_discharge_mw": 25.0, "roundtrip_efficiency_pct": 85.0, "soc_initial_pct": 65.0},
    ])

    return {
        "hourly_generation": df_gen,
        "battery_storage_assets": df_batteries,
    }


class MockDataProvider(BaseDataProvider):
    """
    Mock enterprise data connector providing instant access to pre-built retail
    and energy lakehouse tables.
    """

    def __init__(self, source_id: str = "mock_lakehouse", name: str = "Mock Enterprise Lakehouse"):
        super().__init__(source_id=source_id, name=name, source_type=DataSourceType.MOCK)
        self.cache = MetadataCache(default_ttl_seconds=600.0)
        
        # Populate catalog hierarchy
        self._catalogs: Dict[str, Dict[str, Dict[str, pd.DataFrame]]] = {
            "retail_lakehouse": {
                "gold_analytics": _generate_synthetic_retail_data()
            },
            "energy_grid": {
                "dispatch_market": _generate_synthetic_energy_data()
            }
        }

    def test_connection(self) -> bool:
        return True

    def discover_catalogs(self) -> List[str]:
        return list(self._catalogs.keys())

    def discover_schemas(self, catalog: str) -> List[str]:
        if catalog not in self._catalogs:
            raise KeyError(f"Catalog '{catalog}' not found in mock provider.")
        return list(self._catalogs[catalog].keys())

    def discover_tables(self, catalog: str, schema: str) -> List[TableSchema]:
        cache_key = f"{catalog}.{schema}.tables"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        if catalog not in self._catalogs or schema not in self._catalogs[catalog]:
            raise KeyError(f"Schema '{catalog}.{schema}' not found.")

        tables_dict = self._catalogs[catalog][schema]
        result: List[TableSchema] = []

        for tbl_name, df in tables_dict.items():
            cols: List[ColumnDefinition] = []
            for col_name in df.columns:
                series = df[col_name]
                is_num = pd.api.types.is_numeric_dtype(series)
                
                min_v = float(series.min()) if is_num and not series.empty else None
                max_v = float(series.max()) if is_num and not series.empty else None
                mean_v = float(series.mean()) if is_num and not series.empty else None

                cols.append(
                    ColumnDefinition(
                        name=col_name,
                        data_type=str(series.dtype),
                        is_nullable=bool(series.isnull().any()),
                        is_numeric=is_num,
                        min_value=min_v,
                        max_value=max_v,
                        mean_value=mean_v,
                        distinct_count=int(series.nunique()),
                        sample_values=[
                            int(x) if isinstance(x, (np.integer, int)) else float(x) if isinstance(x, (np.floating, float)) else str(x)
                            for x in series.dropna().head(3).tolist()
                        ],
                    )
                )

            result.append(
                TableSchema(
                    catalog_name=catalog,
                    schema_name=schema,
                    table_name=tbl_name,
                    columns=cols,
                    row_count_estimate=len(df),
                )
            )

        self.cache.set(cache_key, result)
        return result

    def sample_table(
        self,
        catalog: str,
        schema: str,
        table: str,
        limit: int = 100,
    ) -> QueryResult:
        start_time = time.time()
        if catalog not in self._catalogs or schema not in self._catalogs[catalog]:
            raise KeyError(f"Schema '{catalog}.{schema}' not found.")
        tables = self._catalogs[catalog][schema]
        if table not in tables:
            raise KeyError(f"Table '{table}' not found in '{catalog}.{schema}'.")

        df = tables[table]
        sliced = df.head(limit)
        exec_ms = (time.time() - start_time) * 1000.0

        return QueryResult(
            columns=list(df.columns),
            rows=sliced.to_dict(orient="records"),
            row_count=len(sliced),
            execution_time_ms=exec_ms,
            is_truncated=(len(df) > limit),
        )

    def execute_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        max_rows: int = 1000,
    ) -> QueryResult:
        """
        Executes bounded query simulation against mock tables.
        """
        start_time = time.time()
        # Default fallback to daily_store_sales if retail query
        if "energy" in query.lower() or "generation" in query.lower():
            df = self._catalogs["energy_grid"]["dispatch_market"]["hourly_generation"]
        else:
            df = self._catalogs["retail_lakehouse"]["gold_analytics"]["daily_store_sales"]

        sliced = df.head(max_rows)
        exec_ms = (time.time() - start_time) * 1000.0

        return QueryResult(
            columns=list(df.columns),
            rows=sliced.to_dict(orient="records"),
            row_count=len(sliced),
            execution_time_ms=exec_ms,
            is_truncated=(len(df) > max_rows),
        )

    def get_table_profile(self, catalog: str, schema: str, table: str) -> Dict[str, Any]:
        tables = self.discover_tables(catalog, schema)
        for t in tables:
            if t.table_name == table:
                return t.model_dump()
        raise KeyError(f"Table '{table}' not found for profiling.")
