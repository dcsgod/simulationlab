"""
Execution context tracking variables, intermediate traces, and diagnostics during simulation.
"""
from typing import Dict, List, Optional, Any
import time
import uuid
from mathematical_engine.contracts.metrics import NumericVariable
from mathematical_engine.core.errors import OutOfBoundsError


class ExecutionContext:
    """
    Maintains the dynamic evaluation state and telemetry for a simulation run.
    """

    def __init__(
        self,
        run_id: Optional[str] = None,
        baseline_values: Optional[Dict[str, float]] = None,
        variable_definitions: Optional[Dict[str, NumericVariable]] = None,
    ):
        self.run_id = run_id or str(uuid.uuid4())
        self.baseline_values: Dict[str, float] = dict(baseline_values or {})
        self.current_values: Dict[str, float] = dict(self.baseline_values)
        self.variable_definitions: Dict[str, NumericVariable] = dict(variable_definitions or {})
        self.traces: List[Dict[str, Any]] = []
        self.invariants_checked: int = 0
        self.invariants_violated: List[str] = []
        self.start_time: float = time.time()

    def get_value(self, name: str) -> float:
        """Retrieves current numeric value of a variable."""
        if name not in self.current_values:
            raise KeyError(f"Variable '{name}' not found in current execution context")
        return self.current_values[name]

    def set_value(self, name: str, value: float, validate_bounds: bool = True) -> None:
        """Sets a numeric value and optionally validates against registered bounds."""
        if validate_bounds and name in self.variable_definitions:
            var_def = self.variable_definitions[name]
            if var_def.min_bound is not None and value < var_def.min_bound:
                raise OutOfBoundsError(
                    f"Variable '{name}' value {value} is below min_bound {var_def.min_bound}"
                )
            if var_def.max_bound is not None and value > var_def.max_bound:
                raise OutOfBoundsError(
                    f"Variable '{name}' value {value} exceeds max_bound {var_def.max_bound}"
                )
        self.current_values[name] = float(value)

    def record_step(
        self,
        variable_name: str,
        formula_or_model: str,
        input_values: Dict[str, float],
        output_value: float,
        step_metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Appends an execution trace step for grounded explainability."""
        self.traces.append({
            "step_index": len(self.traces) + 1,
            "variable_name": variable_name,
            "formula_or_model": formula_or_model,
            "input_values": input_values,
            "output_value": output_value,
            "timestamp": time.time(),
            "metadata": step_metadata or {},
        })

    def record_invariant_result(self, name: str, passed: bool, message: Optional[str] = None) -> None:
        """Tracks evaluation of a domain invariant."""
        self.invariants_checked += 1
        if not passed:
            self.invariants_violated.append(message or f"Invariant '{name}' violated")

    def elapsed_ms(self) -> float:
        return (time.time() - self.start_time) * 1000.0
