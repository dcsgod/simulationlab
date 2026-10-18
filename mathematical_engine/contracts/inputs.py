"""
Scenario inputs, interventions, and baseline states.
"""
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field
from mathematical_engine.contracts.metrics import NumericVariable


class InterventionType(str, Enum):
    ABSOLUTE_DELTA = "absolute_delta"       # new_val = baseline + value
    PERCENTAGE_DELTA = "percentage_delta"   # new_val = baseline * (1 + value / 100)
    MULTIPLIER = "multiplier"               # new_val = baseline * value
    SET_VALUE = "set_value"                 # new_val = value
    FORMULA_OVERRIDE = "formula_override"   # custom safe formula expression


class Intervention(BaseModel):
    target_variable: str = Field(..., description="Name of the variable being intervened upon")
    intervention_type: InterventionType = Field(default=InterventionType.PERCENTAGE_DELTA)
    value: float = Field(..., description="Numerical parameter of the intervention")
    description: Optional[str] = Field(default=None)
    operating_min: Optional[float] = Field(default=None)
    operating_max: Optional[float] = Field(default=None)

    def apply(self, baseline_val: float) -> float:
        """Applies intervention cleanly to a baseline scalar value."""
        if self.intervention_type == InterventionType.ABSOLUTE_DELTA:
            result = baseline_val + self.value
        elif self.intervention_type == InterventionType.PERCENTAGE_DELTA:
            result = baseline_val * (1.0 + self.value / 100.0)
        elif self.intervention_type == InterventionType.MULTIPLIER:
            result = baseline_val * self.value
        elif self.intervention_type == InterventionType.SET_VALUE:
            result = self.value
        else:
            raise ValueError(f"Direct scalar application not supported for {self.intervention_type}")

        if self.operating_min is not None and result < self.operating_min:
            raise ValueError(f"Intervention result {result} below operating min {self.operating_min}")
        if self.operating_max is not None and result > self.operating_max:
            raise ValueError(f"Intervention result {result} above operating max {self.operating_max}")
        return result


class BaselineState(BaseModel):
    snapshot_id: str = Field(..., description="Unique snapshot identifier or timestamp")
    variables: Dict[str, NumericVariable] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def get_value(self, name: str) -> float:
        if name not in self.variables:
            raise KeyError(f"Variable '{name}' not found in baseline state '{self.snapshot_id}'")
        return self.variables[name].value

    def to_value_dict(self) -> Dict[str, float]:
        return {k: v.value for k, v in self.variables.items()}
