"""
Range, physical, and business operating boundary checks.
"""
from typing import Dict, Optional, Tuple, List
from mathematical_engine.contracts.metrics import NumericVariable
from mathematical_engine.core.errors import OutOfBoundsError


class BoundChecker:
    """
    Validates variable values against domain bounds.
    """

    @staticmethod
    def check_variable(
        name: str,
        value: float,
        min_bound: Optional[float] = None,
        max_bound: Optional[float] = None,
        raise_on_error: bool = True,
    ) -> Tuple[bool, Optional[str]]:
        """Checks if a single value satisfies lower and upper bounds."""
        if min_bound is not None and value < min_bound:
            msg = f"Variable '{name}' value {value} is below min_bound {min_bound}"
            if raise_on_error:
                raise OutOfBoundsError(msg)
            return False, msg

        if max_bound is not None and value > max_bound:
            msg = f"Variable '{name}' value {value} exceeds max_bound {max_bound}"
            if raise_on_error:
                raise OutOfBoundsError(msg)
            return False, msg

        return True, None

    @classmethod
    def check_context(
        cls,
        values: Dict[str, float],
        definitions: Dict[str, NumericVariable],
        raise_on_error: bool = False,
    ) -> List[str]:
        """Validates all variables against their registered definitions."""
        violations: List[str] = []
        for name, val in values.items():
            if name in definitions:
                defn = definitions[name]
                passed, msg = cls.check_variable(
                    name=name,
                    value=val,
                    min_bound=defn.min_bound,
                    max_bound=defn.max_bound,
                    raise_on_error=raise_on_error,
                )
                if not passed and msg:
                    violations.append(msg)
        return violations
