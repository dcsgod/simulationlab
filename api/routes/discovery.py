"""
Automated ontology and business semantic discovery endpoints.
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from connectors import MockDataProvider
from ontology_service import OntologyDiscovery, GraphRepository, OntologyGraph
from api.routes.connectors import get_provider

router = APIRouter(prefix="/api/discovery", tags=["Discovery"])

# Shared global graph repository
_shared_repo = GraphRepository()


def get_shared_repository() -> GraphRepository:
    # Auto-initialize from mock if empty
    if not _shared_repo._node_models:
        provider = MockDataProvider()
        tables = provider.discover_tables("retail_lakehouse", "gold_analytics")
        discovered = OntologyDiscovery.discover_from_tables(tables)
        _shared_repo.load_ontology_graph(discovered)
    return _shared_repo


class DiscoveryRequest(BaseModel):
    source_id: str = "mock_lakehouse"
    catalog: str = "retail_lakehouse"
    schema_name: str = "gold_analytics"


@router.post("/run")
def run_discovery(req: DiscoveryRequest):
    provider = get_provider(req.source_id)
    tables = provider.discover_tables(req.catalog, req.schema_name)
    discovered_graph = OntologyDiscovery.discover_from_tables(
        tables=tables,
        graph_name=f"Ontology from {req.catalog}.{req.schema_name}",
    )
    repo = get_shared_repository()
    repo.load_ontology_graph(discovered_graph)

    return {
        "status": "success",
        "nodes_discovered": len(discovered_graph.nodes),
        "edges_inferred": len(discovered_graph.edges),
        "graph": discovered_graph.model_dump(),
    }
