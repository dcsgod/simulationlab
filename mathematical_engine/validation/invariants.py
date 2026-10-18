"""
Business, physical, and conservation invariant specifications and verification.
"""
from typing import Dict, List, Callable, Optional, Any
from pydantic import BaseModel, Field
from mathematical_engine.core.errors import InvariantViolationError


class Invariant(BaseModel):
    name: str = Field(..., description="Unique invariant name (e.g., 'non_negative_cash')")
    description: Optional[str] = Field(default=None)
    predicate: Optional[str] = Field(
        default=None, 
        description="Optional expression string or comparison condition (e.g., 'gross_margin <= revenue')"
    )
    severity: str = Field(default="error", description="'error' or 'warning'")

    def evaluate_dict(
        self,
        values: Dict[str, float],
        eval_fn: Optional[Callable[[str, Dict[str, float]], bool]] = None,
    ) -> bool:
        """Evaluates whether the invariant holds."""
        if eval_fn and self.predicate:
            return eval_fn(self.predicate, values)
        return True


class InvariantValidator:
    """
    Executes a collection of invariants against simulated state values.
    """

    def __init__(self, invariants: Optional[List[Invariant]] = None):
        self.invariants: List[Invariant] = list(invariants or [])
        self._custom_checks: Dict[str, Callable[[Dict[str, float]], bool]] = {}

    def add_invariant(self, invariant: Invariant) -> None:
        self.invariants.append(invariant)

    def add_custom_rule(self, name: str, check_fn: Callable[[Dict[str, float]], bool], description: str = "") -> None:
        """Registers a Python function checking state dict."""
        self._custom_checks[name] = check_fn
        self.invariants.append(Invariant(name=name, description=description))

    def validate(
        self,
        values: Dict[str, float],
        raise_on_error: bool = False,
    ) -> List[str]:
        """
        Validates all invariants against state. Returns list of failure messages.
        """
        violations: List[str] = []
        for inv in self.invariants:
            if inv.name in self._custom_checks:
                passed = self._custom_checks[inv.name](values)
                if not passed:
                    msg = f"Invariant '{inv.name}' failed: {inv.description or 'condition not satisfied'}"
                    violations.append(msg)
                    if raise_on_error:
                        raise InvariantViolationError(msg)
        return violations
