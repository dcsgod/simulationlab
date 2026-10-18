"""
Canonical ontology models, entity nodes, relationships, and graph definitions.
"""
from typing import Dict, List, Optional, Any
from enum import Enum
import uuid
from pydantic import BaseModel, Field


class EntityType(str, Enum):
    BUSINESS_CONCEPT = "business_concept"
    METRIC = "metric"
    DECISION_LEVER = "decision_lever"
    ASSET = "asset"
    PROCESS = "process"
    DIMENSION = "dimension"


class EdgeType(str, Enum):
    SEMANTIC = "semantic"                       # is_a, part_of
    CALCULATION = "calculation"                 # formula/arithmetic derivation
    DATA_FLOW = "data_flow"                     # sourced from table/column
    CAUSAL_HYPOTHESIS = "causal_hypothesis"     # hypothesized causal link
    VALIDATED_CAUSAL = "validated_causal"       # econometric or validated causal driver
    CONSTRAINT = "constraint"                   # upper/lower bound or capacity limit


class EntityNode(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="Canonical concept name (e.g. 'gross_margin')")
    entity_type: EntityType = Field(default=EntityType.METRIC)
    description: Optional[str] = None
    data_type: str = "float"
    unit: Optional[str] = None
    formula: Optional[str] = None
    min_bound: Optional[float] = None
    max_bound: Optional[float] = None
    source_table: Optional[str] = None
    source_column: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RelationshipEdge(BaseModel):
    source_id: str = Field(..., description="Origin node (driver, input, or parent)")
    target_id: str = Field(..., description="Destination node (outcome, dependent, or child)")
    edge_type: EdgeType = Field(default=EdgeType.CALCULATION)
    weight: Optional[float] = 1.0
    formula_expression: Optional[str] = None
    confidence: float = 1.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class OntologyGraph(BaseModel):
    graph_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Enterprise Business Ontology"
    version: int = 1
    nodes: Dict[str, EntityNode] = Field(default_factory=dict)
    edges: List[RelationshipEdge] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def add_node(self, node: EntityNode) -> EntityNode:
        self.nodes[node.name] = node
        return node

    def add_edge(
        self,
        source_name: str,
        target_name: str,
        edge_type: EdgeType = EdgeType.CALCULATION,
        formula: Optional[str] = None,
        confidence: float = 1.0,
    ) -> RelationshipEdge:
        edge = RelationshipEdge(
            source_id=source_name,
            target_id=target_name,
            edge_type=edge_type,
            formula_expression=formula,
            confidence=confidence,
        )
        self.edges.append(edge)
        return edge

    def get_node(self, name: str) -> Optional[EntityNode]:
        return self.nodes.get(name)
