"""
Data connector management, schema discovery, and sampling endpoints.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Optional, Any

from connectors import (
    BaseDataProvider,
    MockDataProvider,
    DatabricksConfig,
    DatabricksConnector,
    DataSourceMetadata,
    DataSourceType,
)

import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/api/connectors", tags=["Connectors"])

# Global connector registry
_db_token = os.getenv("DATABRICKS_TOKEN", "")
_db_host = os.getenv("DATABRICKS_SERVER_HOSTNAME", "dbc-f8931cc5-1b2d.cloud.databricks.com")
_db_path = os.getenv("DATABRICKS_HTTP_PATH", "/sql/1.0/warehouses/e4ee9c52dd6d4ef6")
_db_catalog = os.getenv("DATABRICKS_CATALOG", "workspace")
_db_schema = os.getenv("DATABRICKS_SCHEMA", "default")

_providers: Dict[str, BaseDataProvider] = {
    "mock_lakehouse": MockDataProvider(source_id="mock_lakehouse", name="Enterprise Mock Lakehouse"),
    "databricks_primary": DatabricksConnector(
        config=DatabricksConfig(
            server_hostname=_db_host,
            http_path=_db_path,
            access_token=_db_token,
            catalog=_db_catalog,
            schema_name=_db_schema,
        ),
        source_id="databricks_primary",
        name="Databricks Unity Catalog (Live)",
    ),
}


def get_provider(source_id: str) -> BaseDataProvider:
    if source_id not in _providers:
        raise HTTPException(status_code=404, detail=f"Connector '{source_id}' not found.")
    return _providers[source_id]


@router.get("", response_model=List[DataSourceMetadata])
def list_connectors():
    result = []
    for pid, p in _providers.items():
        is_conn = p.test_connection()
        catalogs = p.discover_catalogs() if is_conn else []
        result.append(
            DataSourceMetadata(
                source_id=pid,
                name=p.name,
                source_type=p.source_type,
                is_connected=is_conn,
                catalogs=catalogs,
            )
        )
    return result


@router.post("/databricks/configure")
def configure_databricks(config: DatabricksConfig):
    connector = DatabricksConnector(config=config, source_id="databricks_primary")
    _providers["databricks_primary"] = connector
    return {
        "status": "configured",
        "source_id": "databricks_primary",
        "masked_token": config.masked_token,
        "is_connected": connector.test_connection(),
    }


@router.get("/{source_id}/test")
def test_connector(source_id: str):
    p = get_provider(source_id)
    return {"source_id": source_id, "is_connected": p.test_connection()}


@router.get("/{source_id}/catalogs")
def get_catalogs(source_id: str):
    p = get_provider(source_id)
    return {"catalogs": p.discover_catalogs()}


@router.get("/{source_id}/schemas")
def get_schemas(source_id: str, catalog: str = Query(...)):
    p = get_provider(source_id)
    return {"catalog": catalog, "schemas": p.discover_schemas(catalog)}


@router.get("/{source_id}/tables")
def get_tables(source_id: str, catalog: str = Query(...), schema: str = Query(...)):
    p = get_provider(source_id)
    tables = p.discover_tables(catalog, schema)
    return {"catalog": catalog, "schema": schema, "tables": tables}


@router.get("/{source_id}/sample")
def sample_table(
    source_id: str,
    catalog: str = Query(...),
    schema: str = Query(...),
    table: str = Query(...),
    limit: int = Query(50, ge=1, le=1000),
):
    p = get_provider(source_id)
    return p.sample_table(catalog, schema, table, limit=limit)
