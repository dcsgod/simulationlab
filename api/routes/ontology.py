"""
Ontology graph inspection, node/edge editing, and versioning endpoints.
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any
from pydantic import BaseModel

from ontology_service.models import EntityNode, RelationshipEdge, OntologyGraph
from api.routes.discovery import get_shared_repository

router = APIRouter(prefix="/api/ontology", tags=["Ontology"])


@router.get("", response_model=OntologyGraph)
def get_current_ontology():
    repo = get_shared_repository()
    return repo.to_ontology_graph()


@router.post("/nodes")
def add_entity_node(node: EntityNode):
    repo = get_shared_repository()
    repo.add_node(node)
    repo.save_new_version(f"Added node '{node.name}'")
    return {"status": "created", "node": node}


@router.post("/edges")
def add_relationship_edge(edge: RelationshipEdge):
    repo = get_shared_repository()
    repo.add_edge(edge)
    repo.save_new_version(f"Added edge '{edge.source_id}' -> '{edge.target_id}'")
    return {"status": "created", "edge": edge}


@router.get("/versions")
def list_versions():
    repo = get_shared_repository()
    return {"versions": repo.list_versions(), "current_version": repo.current_version}


@router.post("/rollback/{version}")
def rollback_version(version: int):
    repo = get_shared_repository()
    success = repo.rollback_to_version(version)
    if not success:
        raise HTTPException(status_code=404, detail=f"Version {version} not found in history.")
    return {"status": "rolled_back", "current_version": version}
