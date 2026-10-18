"""
Automated semantic and calculation ontology discovery from tabular schemas.
"""
from typing import List, Dict, Optional, Tuple
import re

from connectors.base import TableSchema, ColumnDefinition
from ontology_service.models import (
    OntologyGraph,
    EntityNode,
    RelationshipEdge,
    EntityType,
    EdgeType,
)


class ConceptPattern:
    def __init__(self, regex: str, default_unit: str, entity_type: EntityType, default_formula: Optional[str] = None):
        self.pattern = re.compile(regex, re.IGNORECASE)
        self.default_unit = default_unit
        self.entity_type = entity_type
        self.default_formula = default_formula


_PATTERNS = [
    ConceptPattern(r"(promo|discount).*(pct|percent|rate)?", "%", EntityType.DECISION_LEVER),
    ConceptPattern(r"(base_)?price", "USD", EntityType.DECISION_LEVER),
    ConceptPattern(r"effective_price", "USD", EntityType.METRIC, default_formula="base_price * (1.0 - promo_discount_pct / 100.0)"),
    ConceptPattern(r"(units_sold|quantity|volume)", "units", EntityType.METRIC),
    ConceptPattern(r"(net_sales|revenue)", "USD", EntityType.METRIC, default_formula="effective_price * units_sold"),
    ConceptPattern(r"(cogs|cost_of_goods|total_cost)", "USD", EntityType.METRIC),
    ConceptPattern(r"(gross_margin|gross_profit|profit)", "USD", EntityType.METRIC, default_formula="net_sales_usd - cogs_usd"),
    ConceptPattern(r"(generation|gen_mwh)", "MWh", EntityType.METRIC),
    ConceptPattern(r"(capacity|cap_mw)", "MW", EntityType.ASSET),
    ConceptPattern(r"(co2|emissions)", "tons", EntityType.METRIC),
    ConceptPattern(r"(soc|state_of_charge)", "%", EntityType.METRIC),
]


class OntologyDiscovery:
    """
    Infers business concepts, metrics, decision levers, and dependencies from schema metadata.
    """

    @classmethod
    def discover_from_tables(cls, tables: List[TableSchema], graph_name: str = "Discovered Enterprise Ontology") -> OntologyGraph:
        graph = OntologyGraph(name=graph_name)

        # 1. Map columns to EntityNodes
        for table in tables:
            for col in table.columns:
                node = cls._classify_column(table, col)
                if node:
                    graph.add_node(node)

        # 2. Infer semantic and calculation edges based on discovered formulas
        for node_name, node in list(graph.nodes.items()):
            if node.formula:
                # Extract identifiers from formula
                tokens = re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", node.formula)
                for token in tokens:
                    if token in graph.nodes and token != node_name:
                        graph.add_edge(
                            source_name=token,
                            target_name=node_name,
                            edge_type=EdgeType.CALCULATION,
                            formula=node.formula,
                        )

            # Sourced data flow edge if source table exists
            if node.source_table:
                # Sourced from data
                pass

        # 3. Add domain causal hypotheses
        if "promo_discount_pct" in graph.nodes and "units_sold" in graph.nodes:
            graph.add_edge(
                source_name="promo_discount_pct",
                target_name="units_sold",
                edge_type=EdgeType.CAUSAL_HYPOTHESIS,
                formula="Promotional price elasticity lift hypothesis",
                confidence=0.85,
            )

        return graph

    @classmethod
    def _classify_column(cls, table: TableSchema, col: ColumnDefinition) -> Optional[EntityNode]:
        name_lower = col.name.lower()

        matched_unit = None
        matched_type = EntityType.METRIC
        formula = None

        for p in _PATTERNS:
            if p.pattern.search(name_lower):
                matched_unit = p.default_unit
                matched_type = p.entity_type
                formula = p.default_formula
                break

        if not col.is_numeric and matched_type != EntityType.DIMENSION:
            matched_type = EntityType.DIMENSION

        return EntityNode(
            name=col.name,
            entity_type=matched_type,
            data_type=col.data_type,
            unit=matched_unit,
            formula=formula,
            min_bound=col.min_value,
            max_bound=col.max_value,
            source_table=f"{table.catalog_name}.{table.schema_name}.{table.table_name}",
            source_column=col.name,
            description=f"Auto-discovered {matched_type.value} from {table.table_name}.{col.name}",
        )
