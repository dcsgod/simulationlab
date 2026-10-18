"""
Seeds Databricks Unity Catalog with realistic enterprise synthetic datasets for Retail and Energy.
"""
import os
from databricks import sql
from dotenv import load_dotenv
import numpy as np
import pandas as pd

load_dotenv()

SERVER_HOSTNAME = os.getenv("DATABRICKS_SERVER_HOSTNAME", "dbc-f8931cc5-1b2d.cloud.databricks.com")
HTTP_PATH = os.getenv("DATABRICKS_HTTP_PATH", "/sql/1.0/warehouses/e4ee9c52dd6d4ef6")
ACCESS_TOKEN = os.getenv("DATABRICKS_TOKEN", "")


def seed():
    print(f"Connecting to Databricks {SERVER_HOSTNAME}...")
    conn = sql.connect(
        server_hostname=SERVER_HOSTNAME,
        http_path=HTTP_PATH,
        access_token=ACCESS_TOKEN,
    )
    cursor = conn.cursor()

    # Try creating simulationlab schema, fallback to default
    target_catalog = "workspace"
    target_schema = "default"

    print(f"Using `{target_catalog}`.`{target_schema}`...")

    # 1. Retail Store Sales Table
    print("Creating retail_store_sales table...")
    cursor.execute(f"DROP TABLE IF EXISTS `{target_catalog}`.`{target_schema}`.`retail_store_sales`")
    cursor.execute(f"""
        CREATE TABLE `{target_catalog}`.`{target_schema}`.`retail_store_sales` (
            sale_date STRING,
            store_id STRING,
            product_sku STRING,
            category STRING,
            base_price DOUBLE,
            promo_discount_pct DOUBLE,
            effective_price DOUBLE,
            units_sold INT,
            net_sales_usd DOUBLE,
            cogs_usd DOUBLE,
            gross_margin_usd DOUBLE
        ) USING DELTA
    """)

    # Generate synthetic retail rows
    rng = np.random.default_rng(42)
    skus = [
        ("SKU_BEV_01", "Beverages", 4.99, 2.50),
        ("SKU_SNK_02", "Snacks", 3.49, 1.70),
        ("SKU_ORG_03", "Organics", 8.99, 5.20),
        ("SKU_DAI_04", "Dairy", 5.49, 3.10),
    ]
    stores = ["STORE_001", "STORE_002", "STORE_003"]
    dates = pd.date_range("2026-09-01", periods=14, freq="D").strftime("%Y-%m-%d").tolist()

    insert_vals = []
    for d in dates:
        for store in stores:
            for sku, cat, bp, uc in skus:
                promo = float(rng.choice([0.0, 10.0, 15.0, 20.0], p=[0.6, 0.2, 0.1, 0.1]))
                eff_p = round(bp * (1.0 - promo / 100.0), 2)
                lift = 1.0 + (promo / 100.0 * 2.5)
                units = max(10, int(rng.normal(120, 15) * lift))
                net_sales = round(units * eff_p, 2)
                cogs = round(units * uc, 2)
                margin = round(net_sales - cogs, 2)

                insert_vals.append(
                    f"('{d}', '{store}', '{sku}', '{cat}', {bp}, {promo}, {eff_p}, {units}, {net_sales}, {cogs}, {margin})"
                )

    # Insert in batches of 50
    batch_size = 50
    for i in range(0, len(insert_vals), batch_size):
        batch = insert_vals[i:i + batch_size]
        query = f"INSERT INTO `{target_catalog}`.`{target_schema}`.`retail_store_sales` VALUES {','.join(batch)}"
        cursor.execute(query)

    print(f"Inserted {len(insert_vals)} retail sales rows.")

    # 2. Energy Generation Dispatch Table
    print("Creating energy_generation_dispatch table...")
    cursor.execute(f"DROP TABLE IF EXISTS `{target_catalog}`.`{target_schema}`.`energy_generation_dispatch`")
    cursor.execute(f"""
        CREATE TABLE `{target_catalog}`.`{target_schema}`.`energy_generation_dispatch` (
            record_time STRING,
            asset_id STRING,
            fuel_type STRING,
            capacity_mw DOUBLE,
            generation_mwh DOUBLE,
            marginal_cost_usd_mwh DOUBLE,
            co2_emissions_tons DOUBLE
        ) USING DELTA
    """)

    assets = [
        ("SOLAR_FARM_ALPHA", "Solar", 150.0, 5.0, 0.0),
        ("WIND_PARK_BETA", "Wind", 200.0, 8.0, 0.0),
        ("CCGT_GAS_GEN_1", "Natural Gas", 400.0, 48.0, 0.38),
        ("PEAKER_GAS_2", "Peaker Gas", 180.0, 92.0, 0.55),
    ]
    hours = pd.date_range("2026-10-01 00:00:00", periods=24, freq="h").strftime("%Y-%m-%d %H:%M:%S").tolist()

    energy_vals = []
    for h in hours:
        hour_int = int(h.split()[1].split(":")[0])
        solar_f = max(0.0, np.sin((hour_int - 6) * np.pi / 12)) if 6 <= hour_int <= 18 else 0.0
        wind_f = max(0.1, min(1.0, 0.4 + 0.3 * np.cos(hour_int * np.pi / 12)))

        for aid, fuel, cap, cost, co2_rate in assets:
            if fuel == "Solar":
                gen = round(cap * solar_f, 2)
            elif fuel == "Wind":
                gen = round(cap * wind_f, 2)
            elif fuel == "Natural Gas":
                gen = round(cap * 0.75, 2)
            else:
                gen = round(cap * (0.8 if 17 <= hour_int <= 21 else 0.0), 2)
            emiss = round(gen * co2_rate, 2)
            energy_vals.append(f"('{h}', '{aid}', '{fuel}', {cap}, {gen}, {cost}, {emiss})")

    for i in range(0, len(energy_vals), batch_size):
        batch = energy_vals[i:i + batch_size]
        query = f"INSERT INTO `{target_catalog}`.`{target_schema}`.`energy_generation_dispatch` VALUES {','.join(batch)}"
        cursor.execute(query)

    print(f"Inserted {len(energy_vals)} energy generation records.")

    # 3. Battery Storage Assets Table
    print("Creating battery_storage_assets table...")
    cursor.execute(f"DROP TABLE IF EXISTS `{target_catalog}`.`{target_schema}`.`battery_storage_assets`")
    cursor.execute(f"""
        CREATE TABLE `{target_catalog}`.`{target_schema}`.`battery_storage_assets` (
            asset_id STRING,
            capacity_mwh DOUBLE,
            max_discharge_mw DOUBLE,
            roundtrip_efficiency_pct DOUBLE,
            soc_initial_pct DOUBLE
        ) USING DELTA
    """)

    bess_vals = [
        "('BESS_CENTRAL_01', 200.0, 50.0, 88.0, 50.0)",
        "('BESS_WEST_02', 100.0, 25.0, 85.0, 65.0)",
        "('BESS_SUBSTATION_09', 80.0, 20.0, 90.0, 40.0)",
    ]
    cursor.execute(f"INSERT INTO `{target_catalog}`.`{target_schema}`.`battery_storage_assets` VALUES {','.join(bess_vals)}")
    print(f"Inserted {len(bess_vals)} battery assets.")

    cursor.close()
    conn.close()
    print("All 3 Databricks synthetic datasets created and populated successfully!")


if __name__ == "__main__":
    seed()
