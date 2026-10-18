"""
Scenario and model assumption recording and audit registries.
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class Assumption(BaseModel):
    name: str = Field(..., description="Assumption key or short identifier")
    statement: str = Field(..., description="Explicit business or mathematical premise")
    source: Optional[str] = Field(default=None, description="Author, paper, or business unit")
    confidence: Optional[str] = Field(default="medium", description="high, medium, low")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AssumptionAudit:
    """
    Registry collecting assumptions across models and active scenarios.
    """

    def __init__(self):
        self.assumptions: List[Assumption] = []

    def record(self, assumption: Assumption) -> None:
        self.assumptions.append(assumption)

    def list_statements(self) -> List[str]:
        return [f"[{a.confidence.upper()}] {a.statement} (Source: {a.source or 'Unknown'})" for a in self.assumptions]
