"""
Diagnostic aggregation combining bounds, invariants, and reconciliation reports.
"""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class DiagnosticReport(BaseModel):
    is_valid: bool = Field(default=True)
    checked_count: int = Field(default=0)
    violations: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

    def add_violation(self, message: str) -> None:
        self.violations.append(message)
        self.is_valid = False

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)
