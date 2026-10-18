"""
NetworkX-backed ontology graph repository with versioning, pathfinding, and impact analysis.
"""
from typing import Dict, List, Optional, Set, Any
import networkx as nx
import copy

from ontology_service.models import (
    OntologyGraph,
    EntityNode,
    RelationshipEdge,
    EdgeType,
)
from mathematical_engine.core.errors import CyclicDependencyError


class GraphRepository:
    """
    Manages in-memory NetworkX directed graph representation of the enterprise ontology
    with version history and graph analytics.
    """

    def __init__(self, initial_graph: Optional[OntologyGraph] = None):
        self._graph = nx.DiGraph()
        self._node_models: Dict[str, EntityNode] = {}
        self._edge_models: List[RelationshipEdge] = []
        self._versions: Dict[int, OntologyGraph] = {}
        self.current_version: int = 1

        if initial_graph:
            self.load_ontology_graph(initial_graph)

    def load_ontology_graph(self, ontology: OntologyGraph) -> None:
        """Loads an OntologyGraph Pydantic model into the NetworkX repository."""
        self._graph.clear()
        self._node_models = dict(ontology.nodes)
        self._edge_models = list(ontology.edges)
        self.current_version = ontology.version

        for node_name, node in ontology.nodes.items():
            self._graph.add_node(node_name, **node.model_dump())

        for edge in ontology.edges:
            self._graph.add_edge(
                edge.source_id,
                edge.target_id,
                edge_type=edge.edge_type.value,
                weight=edge.weight or 1.0,
                formula=edge.formula_expression,
                confidence=edge.confidence,
            )

        self._save_snapshot(self.current_version)

    def to_ontology_graph(self, name: str = "Enterprise Ontology") -> OntologyGraph:
        """Exports current state back to Pydantic OntologyGraph model."""
        return OntologyGraph(
            name=name,
            version=self.current_version,
            nodes=dict(self._node_models),
            edges=list(self._edge_models),
        )

    def add_node(self, node: EntityNode) -> None:
        self._node_models[node.name] = node
        self._graph.add_node(node.name, **node.model_dump())

    def add_edge(self, edge: RelationshipEdge) -> None:
        self._edge_models.append(edge)
        self._graph.add_edge(
            edge.source_id,
            edge.target_id,
            edge_type=edge.edge_type.value,
            weight=edge.weight or 1.0,
            formula=edge.formula_expression,
            confidence=edge.confidence,
        )

    def find_all_paths(self, source: str, target: str) -> List[List[str]]:
        """Returns all directed paths from source node to target node."""
        if source not in self._graph or target not in self._graph:
            return []
        try:
            return list(nx.all_simple_paths(self._graph, source, target))
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []

    def get_upstream_drivers(self, target: str) -> Set[str]:
        """Returns all ancestors that directly or indirectly influence target."""
        if target not in self._graph:
            return set()
        return nx.ancestors(self._graph, target)

    def get_downstream_impact(self, source: str) -> Set[str]:
        """Returns all descendants affected by changes to source."""
        if source not in self._graph:
            return set()
        return nx.descendants(self._graph, source)

    def detect_cycles(self) -> List[List[str]]:
        """Returns any cycles detected in the graph."""
        return list(nx.simple_cycles(self._graph))

    def assert_acyclic_calculation_graph(self) -> None:
        """Validates that calculation sub-edges form a DAG."""
        calc_edges = [
            (u, v) for u, v, data in self._graph.edges(data=True)
            if data.get("edge_type") == EdgeType.CALCULATION.value
        ]
        calc_subgraph = self._graph.edge_subgraph(calc_edges)
        cycles = list(nx.simple_cycles(calc_subgraph))
        if cycles:
            raise CyclicDependencyError(f"Calculation cycles detected: {cycles}")

    def save_new_version(self, description: str = "") -> int:
        """Increments version counter and stores snapshot."""
        self.current_version += 1
        graph_copy = self.to_ontology_graph()
        graph_copy.version = self.current_version
        graph_copy.metadata["description"] = description
        self._save_snapshot(self.current_version)
        return self.current_version

    def rollback_to_version(self, version: int) -> bool:
        """Restores graph state from specified version."""
        if version not in self._versions:
            return False
        snapshot = copy.deepcopy(self._versions[version])
        self.load_ontology_graph(snapshot)
        return True

    def list_versions(self) -> List[Dict[str, Any]]:
        return [
            {
                "version": v,
                "node_count": len(snap.nodes),
                "edge_count": len(snap.edges),
                "metadata": snap.metadata,
            }
            for v, snap in sorted(self._versions.items())
        ]

    def _save_snapshot(self, version: int) -> None:
        self._versions[version] = copy.deepcopy(self.to_ontology_graph())
