"""
Tests for Data Connectors (Mock Data Provider, Cache, Databricks Config & Masking).
"""
import pytest
import time
from connectors import (
    MockDataProvider,
    MetadataCache,
    DatabricksConfig,
    DatabricksConnector,
)


class TestMockDataProvider:
    def setup_method(self):
        self.provider = MockDataProvider()

    def test_connection(self):
        assert self.provider.test_connection() is True

    def test_discover_catalogs_and_schemas(self):
        catalogs = self.provider.discover_catalogs()
        assert "retail_lakehouse" in catalogs
        assert "energy_grid" in catalogs

        schemas = self.provider.discover_schemas("retail_lakehouse")
        assert "gold_analytics" in schemas

        energy_schemas = self.provider.discover_schemas("energy_grid")
        assert "dispatch_market" in energy_schemas

    def test_discover_tables_and_columns(self):
        tables = self.provider.discover_tables("retail_lakehouse", "gold_analytics")
        table_names = [t.table_name for t in tables]
        assert "daily_store_sales" in table_names
        assert "inventory_levels" in table_names
        assert "price_elasticity_reference" in table_names

        sales_table = next(t for t in tables if t.table_name == "daily_store_sales")
        col_names = [c.name for c in sales_table.columns]
        assert "units_sold" in col_names
        assert "effective_price" in col_names
        assert "gross_margin_usd" in col_names

        margin_col = next(c for c in sales_table.columns if c.name == "gross_margin_usd")
        assert margin_col.is_numeric is True
        assert margin_col.min_value is not None
        assert margin_col.max_value is not None

    def test_sample_table(self):
        sample = self.provider.sample_table("retail_lakehouse", "gold_analytics", "daily_store_sales", limit=10)
        assert sample.row_count == 10
        assert len(sample.rows) == 10
        assert "units_sold" in sample.rows[0]
        assert sample.execution_time_ms >= 0.0

    def test_execute_query(self):
        res = self.provider.execute_query("SELECT * FROM daily_store_sales LIMIT 25", max_rows=25)
        assert res.row_count == 25
        assert len(res.rows) == 25


class TestMetadataCache:
    def test_cache_set_get_and_expiration(self):
        cache = MetadataCache(default_ttl_seconds=0.1)
        cache.set("test_key", {"foo": "bar"})
        assert cache.get("test_key") == {"foo": "bar"}
        
        time.sleep(0.15)
        assert cache.get("test_key") is None

    def test_cache_freshness(self):
        cache = MetadataCache(default_ttl_seconds=60.0)
        cache.set("fresh_key", 123)
        freshness = cache.get_freshness("fresh_key")
        assert freshness is not None
        assert freshness >= 0.0


class TestDatabricksSecurityAndConfig:
    def test_token_masking(self):
        cfg = DatabricksConfig(
            server_hostname="test-host.azuredatabricks.net",
            http_path="/sql/1.0/warehouses/123",
            access_token="dapi1234567890abcdef1234567890",
        )
        masked = cfg.masked_token
        assert "1234567890abcdef" not in masked
        assert masked.startswith("dapi")
        assert masked.endswith("7890")

    def test_connector_offline_test_connection(self):
        cfg = DatabricksConfig(
            server_hostname="invalid-host-offline.net",
            http_path="/sql/1.0/warehouses/dummy",
            access_token="dapi-dummy-token",
        )
        conn = DatabricksConnector(cfg)
        # Should gracefully return False without raising uncaught exceptions
        assert conn.test_connection() is False
