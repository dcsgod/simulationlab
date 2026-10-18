"""
Dependency graph and computational DAG exploration endpoints.
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Dict, List, Set

from api.routes.discovery import get_shared_repository
from ontology_service.models import EdgeType

router = APIRouter(prefix="/api/dag", tags=["DAG"])


@router.get("")
def get_calculation_dag():
    repo = get_shared_repository()
    # Filter only calculation and causal edges
    nodes = list(repo._node_models.values())
    calc_edges = [
        e for e in repo._edge_models
        if e.edge_type in (EdgeType.CALCULATION, EdgeType.CAUSAL_HYPOTHESIS, EdgeType.VALIDATED_CAUSAL)
    ]
    return {
        "nodes": nodes,
        "edges": calc_edges,
        "is_acyclic": len(repo.detect_cycles()) == 0,
    }


@router.get("/paths")
def get_paths(source: str = Query(...), target: str = Query(...)):
    repo = get_shared_repository()
    paths = repo.find_all_paths(source, target)
    return {"source": source, "target": target, "paths": paths}


@router.get("/impact/{node_name}")
def get_impact_analysis(node_name: str):
    repo = get_shared_repository()
    if node_name not in repo._graph:
        raise HTTPException(status_code=404, detail=f"Node '{node_name}' not found in DAG.")
    
    upstream = repo.get_upstream_drivers(node_name)
    downstream = repo.get_downstream_impact(node_name)

    return {
        "node": node_name,
        "upstream_drivers": sorted(list(upstream)),
        "downstream_impacted": sorted(list(downstream)),
    }
