"""
Simulation and optimization result contracts, metric deltas, and distributions.
"""
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field
import time
import uuid


class ExecutionStatus(str, Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    INFEASIBLE = "infeasible"


class MetricDelta(BaseModel):
    """
    Quantifies the exact delta between baseline state and scenario state for a variable.
    """
    variable_name: str = Field(..., description="Canonical name of the variable")
    baseline_value: float = Field(..., description="Original baseline value")
    scenario_value: float = Field(..., description="Post-intervention/model value")
    absolute_delta: float = Field(..., description="scenario_value - baseline_value")
    percentage_delta: Optional[float] = Field(
        default=None, 
        description="((scenario_value - baseline_value) / |baseline_value|) * 100 if baseline != 0"
    )
    unit: Optional[str] = Field(default=None, description="Physical or financial unit symbol")

    @classmethod
    def compute(
        cls, 
        name: str, 
        baseline: float, 
        scenario: float, 
        unit: Optional[str] = None
    ) -> "MetricDelta":
        abs_diff = scenario - baseline
        pct_diff = None
        if abs(baseline) > 1e-12:
            pct_diff = (abs_diff / abs(baseline)) * 100.0
        return cls(
            variable_name=name,
            baseline_value=baseline,
            scenario_value=scenario,
            absolute_delta=abs_diff,
            percentage_delta=pct_diff,
            unit=unit
        )


class DistributionSummary(BaseModel):
    """
    Summary statistics from stochastic Monte Carlo simulations.
    """
    variable_name: str = Field(..., description="Canonical name of the variable")
    mean: float = Field(..., description="Empirical mean")
    std: float = Field(..., description="Sample standard deviation")
    median: float = Field(..., description="50th percentile")
    min_val: float = Field(..., description="Minimum sampled value")
    max_val: float = Field(..., description="Maximum sampled value")
    p5: float = Field(..., description="5th percentile")
    p25: float = Field(..., description="25th percentile")
    p75: float = Field(..., description="75th percentile")
    p95: float = Field(..., description="95th percentile")
    var_95: Optional[float] = Field(default=None, description="Value at Risk at 95% confidence")
    cvar_95: Optional[float] = Field(default=None, description="Conditional Value at Risk (Expected Shortfall) at 95%")
    samples_count: int = Field(default=0, description="Total sample iterations")


class SensitivityDriver(BaseModel):
    """
    Sensitivity coefficient for a variable intervention driving an outcome metric.
    """
    variable_name: str = Field(..., description="Input variable name")
    target_metric: str = Field(..., description="Target outcome variable")
    elasticity: float = Field(..., description="% change in target / % change in input")
    absolute_derivative: float = Field(..., description="d(Target) / d(Input)")
    normalized_impact: float = Field(..., description="Rank-scaled or variance-explained impact")
    rank: int = Field(..., description="Relative importance rank (1 = highest impact)")
    direction: str = Field(default="positive", description="'positive' or 'negative'")


class SimulationResult(BaseModel):
    """
    Comprehensive result payload for a simulation run.
    """
    simulation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    scenario_id: str = Field(...)
    status: ExecutionStatus = Field(default=ExecutionStatus.SUCCESS)
    metrics: Dict[str, MetricDelta] = Field(default_factory=dict)
    all_values: Dict[str, float] = Field(default_factory=dict, description="Full scenario state dict")
    distributions: Dict[str, DistributionSummary] = Field(default_factory=dict)
    sensitivity_drivers: List[SensitivityDriver] = Field(default_factory=list)
    traces: List[Dict[str, Any]] = Field(default_factory=list)
    validation_passed: bool = Field(default=True)
    invariants_checked: int = Field(default=0)
    invariants_violated: List[str] = Field(default_factory=list)
    execution_time_ms: float = Field(default=0.0)
    timestamp: float = Field(default_factory=time.time)
    metadata: Dict[str, Any] = Field(default_factory=dict)
