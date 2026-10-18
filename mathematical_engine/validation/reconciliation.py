"""
Financial and conservation reconciliation checkers (e.g. Total = Component A + Component B).
"""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
import math
from mathematical_engine.core.errors import InvariantViolationError


class ReconciliationRule(BaseModel):
    name: str = Field(..., description="Reconciliation rule identifier")
    total_variable: str = Field(..., description="Target summary/total variable name")
    component_variables: List[str] = Field(..., description="Variables whose sum must equal total")
    tolerance: float = Field(default=1e-5, description="Absolute allowable difference")
    description: Optional[str] = Field(default=None)


class ReconciliationEngine:
    """
    Verifies that additive/reconciled balance identities hold exactly within numeric tolerance.
    """

    def __init__(self, rules: Optional[List[ReconciliationRule]] = None):
        self.rules: List[ReconciliationRule] = list(rules or [])

    def add_rule(self, rule: ReconciliationRule) -> None:
        self.rules.append(rule)

    def reconcile(
        self,
        values: Dict[str, float],
        raise_on_error: bool = False,
    ) -> List[str]:
        """
        Validates all reconciliation rules against the values dict.
        Returns list of discrepancy messages.
        """
        discrepancies: List[str] = []

        for rule in self.rules:
            if rule.total_variable not in values:
                continue
            total = values[rule.total_variable]
            comp_sum = sum(values.get(c, 0.0) for c in rule.component_variables)
            diff = abs(total - comp_sum)

            if diff > rule.tolerance:
                msg = (
                    f"Reconciliation error '{rule.name}': {rule.total_variable} ({total}) != "
                    f"sum of components {rule.component_variables} ({comp_sum}), diff={diff:g}"
                )
                discrepancies.append(msg)
                if raise_on_error:
                    raise InvariantViolationError(msg)

        return discrepancies
