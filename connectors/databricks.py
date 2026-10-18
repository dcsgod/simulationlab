"""
Databricks Unity Catalog and SQL Warehouse connector with token masking and safety bounds.
"""
from typing import Dict, List, Optional, Any
import time
import re
from pydantic import BaseModel, Field

from connectors.base import (
    BaseDataProvider,
    DataSourceType,
    TableSchema,
    ColumnDefinition,
    QueryResult,
)
from connectors.cache import MetadataCache


class DatabricksConfig(BaseModel):
    server_hostname: str = Field(..., description="Workspace URL (e.g. 'adb-123.azuredatabricks.net')")
    http_path: str = Field(..., description="SQL Warehouse HTTP path (e.g. '/sql/1.0/warehouses/abc')")
    access_token: str = Field(..., description="Databricks Personal Access Token or OAuth M2M token")
    catalog: Optional[str] = Field(default=None, description="Default Unity Catalog name")
    schema_name: Optional[str] = Field(default=None, description="Default schema name")

    @property
    def masked_token(self) -> str:
        if not self.access_token:
            return ""
        if len(self.access_token) <= 8:
            return "***"
        return f"{self.access_token[:4]}...{self.access_token[-4:]}"


class DatabricksConnector(BaseDataProvider):
    """
    Connects to Databricks SQL Warehouse and Unity Catalog using databricks-sql-connector.
    """

    def __init__(
        self,
        config: DatabricksConfig,
        source_id: str = "databricks_primary",
        name: str = "Databricks Unity Catalog",
    ):
        super().__init__(source_id=source_id, name=name, source_type=DataSourceType.DATABRICKS_UC)
        self.config = config
        self.cache = MetadataCache(default_ttl_seconds=300.0)

    def _get_connection(self):
        try:
            from databricks import sql
            return sql.connect(
                server_hostname=self.config.server_hostname,
                http_path=self.config.http_path,
                access_token=self.config.access_token,
            )
        except ImportError:
            raise ImportError(
                "databricks-sql-connector is not installed. Install with 'pip install databricks-sql-connector'"
            )

    def test_connection(self) -> bool:
        """Attempts a lightweight query to test connectivity."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    return True
        except Exception:
            return False

    def discover_catalogs(self) -> List[str]:
        cache_key = "catalogs"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SHOW CATALOGS")
                rows = cursor.fetchall()
                catalogs = [r[0] for r in rows]
                self.cache.set(cache_key, catalogs)
                return catalogs

    def discover_schemas(self, catalog: str) -> List[str]:
        cache_key = f"{catalog}.schemas"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"SHOW SCHEMAS IN `{catalog}`")
                rows = cursor.fetchall()
                schemas = [r[0] for r in rows]
                self.cache.set(cache_key, schemas)
                return schemas

    def discover_tables(self, catalog: str, schema: str) -> List[TableSchema]:
        cache_key = f"{catalog}.{schema}.tables"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        tables_result: List[TableSchema] = []
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"SHOW TABLES IN `{catalog}`.`{schema}`")
                tbl_rows = cursor.fetchall()
                table_names = [r[1] for r in tbl_rows]

                for tname in table_names:
                    cursor.execute(f"DESCRIBE TABLE EXTENDED `{catalog}`.`{schema}`.`{tname}`")
                    desc_rows = cursor.fetchall()
                    cols = []
                    for d in desc_rows:
                        col_name = d[0]
                        if not col_name or col_name.startswith("#"):
                            break
                        data_type = d[1] if len(d) > 1 else "string"
                        is_num = any(t in data_type.lower() for t in ["int", "double", "float", "decimal"])
                        cols.append(ColumnDefinition(
                            name=col_name,
                            data_type=data_type,
                            is_numeric=is_num,
                        ))

                    tables_result.append(
                        TableSchema(
                            catalog_name=catalog,
                            schema_name=schema,
                            table_name=tname,
                            columns=cols,
                        )
                    )

        self.cache.set(cache_key, tables_result)
        return tables_result

    def sample_table(
        self,
        catalog: str,
        schema: str,
        table: str,
        limit: int = 100,
    ) -> QueryResult:
        query = f"SELECT * FROM `{catalog}`.`{schema}`.`{table}` LIMIT {int(limit)}"
        return self.execute_query(query)

    def execute_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        max_rows: int = 1000,
    ) -> QueryResult:
        start_time = time.time()
        
        # Enforce safety limit if missing in query
        safe_query = query.strip()
        if not re.search(r"\blimit\s+\d+", safe_query, re.IGNORECASE):
            safe_query = f"{safe_query} LIMIT {max_rows}"

        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(safe_query, parameters=params)
                desc = cursor.description
                columns = [d[0] for d in desc] if desc else []
                raw_rows = cursor.fetchall()
                rows = [dict(zip(columns, r)) for r in raw_rows]
                exec_ms = (time.time() - start_time) * 1000.0

                return QueryResult(
                    columns=columns,
                    rows=rows,
                    row_count=len(rows),
                    execution_time_ms=exec_ms,
                    is_truncated=(len(rows) >= max_rows),
                )

    def get_table_profile(self, catalog: str, schema: str, table: str) -> Dict[str, Any]:
        tables = self.discover_tables(catalog, schema)
        for t in tables:
            if t.table_name == table:
                return t.model_dump()
        raise KeyError(f"Table '{table}' not found in `{catalog}`.`{schema}`.")
