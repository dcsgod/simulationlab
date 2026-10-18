"""
Ontology service: canonical models, automated discovery, and versioned graph repository.
"""
from ontology_service.models import (
    EntityType,
    EdgeType,
    EntityNode,
    RelationshipEdge,
    OntologyGraph,
)
from ontology_service.discovery import OntologyDiscovery
from ontology_service.graph_repository import GraphRepository

__all__ = [
    "EntityType",
    "EdgeType",
    "EntityNode",
    "RelationshipEdge",
    "OntologyGraph",
    "OntologyDiscovery",
    "GraphRepository",
]
