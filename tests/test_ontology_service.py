"""
Unit and integration tests for Phase 4: Ontology and Dependency Graph Services.
"""
import pytest
from connectors import MockDataProvider
from ontology_service import (
    EntityType,
    EdgeType,
    EntityNode,
    RelationshipEdge,
    OntologyGraph,
    OntologyDiscovery,
    GraphRepository,
)


class TestOntologyDiscovery:
    def setup_method(self):
        self.provider = MockDataProvider()

    def test_discovery_from_retail_tables(self):
        tables = self.provider.discover_tables("retail_lakehouse", "gold_analytics")
        graph = OntologyDiscovery.discover_from_tables(tables)

        assert "effective_price" in graph.nodes
        assert "units_sold" in graph.nodes
        assert "net_sales_usd" in graph.nodes
        assert "gross_margin_usd" in graph.nodes

        # Check units inferred
        assert graph.nodes["effective_price"].unit == "USD"
        assert graph.nodes["promo_discount_pct"].unit == "%"
        assert graph.nodes["units_sold"].unit == "units"

        # Check types
        assert graph.nodes["base_price"].entity_type == EntityType.DECISION_LEVER
        assert graph.nodes["net_sales_usd"].entity_type == EntityType.METRIC

        # Check edge inference
        calc_edges = [e for e in graph.edges if e.edge_type == EdgeType.CALCULATION]
        assert len(calc_edges) > 0


class TestGraphRepository:
    def setup_method(self):
        self.graph = OntologyGraph(name="Test Graph")
        self.graph.add_node(EntityNode(name="promo", unit="%", entity_type=EntityType.DECISION_LEVER))
        self.graph.add_node(EntityNode(name="price", unit="USD", entity_type=EntityType.DECISION_LEVER))
        self.graph.add_node(EntityNode(name="volume", unit="units", entity_type=EntityType.METRIC))
        self.graph.add_node(EntityNode(name="revenue", unit="USD", entity_type=EntityType.METRIC, formula="price * volume"))
        self.graph.add_node(EntityNode(name="profit", unit="USD", entity_type=EntityType.METRIC, formula="revenue - 100"))

        self.graph.add_edge("promo", "volume", edge_type=EdgeType.CAUSAL_HYPOTHESIS)
        self.graph.add_edge("price", "revenue", edge_type=EdgeType.CALCULATION)
        self.graph.add_edge("volume", "revenue", edge_type=EdgeType.CALCULATION)
        self.graph.add_edge("revenue", "profit", edge_type=EdgeType.CALCULATION)

        self.repo = GraphRepository(self.graph)

    def test_pathfinding(self):
        paths = self.repo.find_all_paths("promo", "profit")
        assert len(paths) == 1
        assert paths[0] == ["promo", "volume", "revenue", "profit"]

    def test_upstream_and_downstream_impact(self):
        downstream = self.repo.get_downstream_impact("promo")
        assert downstream == {"volume", "revenue", "profit"}

        upstream = self.repo.get_upstream_drivers("profit")
        assert upstream == {"promo", "price", "volume", "revenue"}

    def test_calculation_dag_acyclic(self):
        self.repo.assert_acyclic_calculation_graph()

    def test_versioning_and_rollback(self):
        v1 = self.repo.current_version
        self.repo.add_node(EntityNode(name="new_node", unit="count"))
        v2 = self.repo.save_new_version("Added new_node")
        assert v2 == v1 + 1
        assert "new_node" in self.repo.to_ontology_graph().nodes

        # Rollback to v1
        assert self.repo.rollback_to_version(v1) is True
        assert "new_node" not in self.repo.to_ontology_graph().nodes
