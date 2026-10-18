"""
Base contracts and abstract class for Data Providers and Connectors.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from enum import Enum
import time
from pydantic import BaseModel, Field


class DataSourceType(str, Enum):
    MOCK = "mock"
    DATABRICKS_UC = "databricks_uc"
    DATABRICKS_SQL = "databricks_sql"
    POSTGRES = "postgres"
    SNOWFLAKE = "snowflake"
    CSV = "csv"


class ColumnDefinition(BaseModel):
    name: str = Field(..., description="Column identifier")
    data_type: str = Field(..., description="Data type (e.g. 'float', 'string', 'integer', 'timestamp')")
    is_nullable: bool = True
    is_numeric: bool = False
    is_primary_key: bool = False
    description: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    mean_value: Optional[float] = None
    distinct_count: Optional[int] = None
    null_count: Optional[int] = 0
    sample_values: List[Any] = Field(default_factory=list)


class TableSchema(BaseModel):
    catalog_name: str
    schema_name: str
    table_name: str
    columns: List[ColumnDefinition] = Field(default_factory=list)
    row_count_estimate: Optional[int] = None
    table_type: str = "MANAGED"
    comment: Optional[str] = None

    @property
    def full_name(self) -> str:
        return f"{self.catalog_name}.{self.schema_name}.{self.table_name}"


class QueryResult(BaseModel):
    columns: List[str]
    rows: List[Dict[str, Any]]
    row_count: int
    execution_time_ms: float
    is_truncated: bool = False
    query_id: Optional[str] = None


class DataSourceMetadata(BaseModel):
    source_id: str
    name: str
    source_type: DataSourceType
    is_connected: bool
    catalogs: List[str] = Field(default_factory=list)
    last_synced_at: Optional[float] = None
    error_message: Optional[str] = None


class BaseDataProvider(ABC):
    """
    Abstract interface for connecting to enterprise data sources, discovering metadata,
    and retrieving tabular data slices.
    """

    def __init__(self, source_id: str, name: str, source_type: DataSourceType):
        self.source_id = source_id
        self.name = name
        self.source_type = source_type

    @abstractmethod
    def test_connection(self) -> bool:
        """Verifies network and credential connectivity."""
        pass

    @abstractmethod
    def discover_catalogs(self) -> List[str]:
        """Lists available catalogs/databases."""
        pass

    @abstractmethod
    def discover_schemas(self, catalog: str) -> List[str]:
        """Lists available schemas in the specified catalog."""
        pass

    @abstractmethod
    def discover_tables(self, catalog: str, schema: str) -> List[TableSchema]:
        """Discovers tables and columns within a schema."""
        pass

    @abstractmethod
    def sample_table(
        self,
        catalog: str,
        schema: str,
        table: str,
        limit: int = 100,
    ) -> QueryResult:
        """Retrieves a bounded sample of records from a table."""
        pass

    @abstractmethod
    def execute_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        max_rows: int = 1000,
    ) -> QueryResult:
        """Executes a bounded, parameterized query."""
        pass

    @abstractmethod
    def get_table_profile(self, catalog: str, schema: str, table: str) -> Dict[str, Any]:
        """Calculates profile statistics (min, max, mean, nulls, cardinality)."""
        pass
