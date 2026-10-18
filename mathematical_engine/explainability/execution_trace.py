"""
Execution trace recording, formatting, and human-readable audit narrative.
"""
from typing import Dict, List, Any
from pydantic import BaseModel, Field


class ExecutionTraceStep(BaseModel):
    step_index: int
    variable_name: str
    formula_or_model: str
    input_values: Dict[str, float]
    output_value: float
    timestamp: float
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_readable_sentence(self) -> str:
        inputs_str = ", ".join(f"{k}={v:g}" for k, v in self.input_values.items())
        return f"Step {self.step_index}: Computed '{self.variable_name}' = {self.output_value:g} via [{self.formula_or_model}] using ({inputs_str})"


class TraceExplainer:
    """
    Renders execution traces into clear, audit-ready explanation narratives.
    """

    @staticmethod
    def explain_traces(traces: List[Dict[str, Any]]) -> List[str]:
        steps = [ExecutionTraceStep(**t) for t in traces]
        return [s.to_readable_sentence() for s in steps]

    @staticmethod
    def summarize_path(traces: List[Dict[str, Any]], target_variable: str) -> str:
        """Finds the final step computing target_variable and describes its inputs."""
        matching = [t for t in traces if t.get("variable_name") == target_variable]
        if not matching:
            return f"Variable '{target_variable}' was not modified during DAG evaluation."
        last_step = matching[-1]
        inputs_str = ", ".join(f"{k}={v:g}" for k, v in last_step.get("input_values", {}).items())
        return (
            f"Final value of '{target_variable}' ({last_step.get('output_value'):g}) was produced by "
            f"{last_step.get('formula_or_model')} from inputs: {inputs_str}."
        )
