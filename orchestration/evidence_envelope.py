"""
Grounded Evidence Envelope linking baselines, interventions, DAG paths, and validation.
"""
from typing import Dict, List, Optional, Any
import time
from pydantic import BaseModel, Field

from mathematical_engine.contracts.results import (
    MetricDelta,
    DistributionSummary,
    SensitivityDriver,
    ExecutionStatus,
)


class GroundedEvidenceEnvelope(BaseModel):
    envelope_id: str
    scenario_id: str
    scenario_title: str
    timestamp: float = Field(default_factory=time.time)
    execution_status: ExecutionStatus = ExecutionStatus.SUCCESS

    # Data grounding
    baseline_snapshot_id: str
    data_source_id: str
    baseline_values: Dict[str, float]

    # Interventions
    interventions_applied: List[Dict[str, Any]] = Field(default_factory=list)

    # Calculation graph trace
    calculation_path: List[str] = Field(default_factory=list)
    execution_traces: List[Dict[str, Any]] = Field(default_factory=list)

    # Outcomes
    metric_deltas: Dict[str, MetricDelta] = Field(default_factory=dict)
    distributions: Dict[str, DistributionSummary] = Field(default_factory=dict)
    sensitivity_drivers: List[SensitivityDriver] = Field(default_factory=list)

    # Invariants & Reconciliation
    validation_passed: bool = True
    invariants_checked: int = 0
    invariants_violated: List[str] = Field(default_factory=list)

    # Human-readable grounded narrative
    grounded_summary: str = ""

    def generate_narrative(self, target_metric: str) -> str:
        """Constructs an auditable explanation grounded strictly in computed facts."""
        if target_metric not in self.metric_deltas:
            return f"Scenario executed successfully with {len(self.metric_deltas)} variables tracked."

        delta = self.metric_deltas[target_metric]
        pct_str = f" ({delta.percentage_delta:+.2f}%)" if delta.percentage_delta is not None else ""
        abs_str = f"{delta.absolute_delta:+.2f}"

        interv_str = ", ".join(
            f"{i.get('target_variable')} {i.get('intervention_type')} {i.get('value')}"
            for i in self.interventions_applied
        ) or "None"

        narrative = (
            f"Under scenario '{self.scenario_title}', intervening on [{interv_str}] resulted in "
            f"'{target_metric}' moving from {delta.baseline_value:g} to {delta.scenario_value:g} "
            f"[Delta: {abs_str}{pct_str}]. "
        )

        if self.sensitivity_drivers:
            top_driver = self.sensitivity_drivers[0]
            narrative += (
                f"The primary sensitivity driver is '{top_driver.variable_name}' with an elasticity of "
                f"{top_driver.elasticity:.3f}. "
            )

        if self.validation_passed:
            narrative += f"All {self.invariants_checked} domain bounds and reconciliation invariants passed."
        else:
            narrative += f"Warning: Invariants violated: {'; '.join(self.invariants_violated)}."

        self.grounded_summary = narrative
        return narrative
