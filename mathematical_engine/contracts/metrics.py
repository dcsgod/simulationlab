"""
Metric and numeric variable contracts with unit specifications.
"""
from typing import Optional, Any
from enum import Enum
from pydantic import BaseModel, Field, field_validator
import math


class UnitDimension(str, Enum):
    CURRENCY = "currency"
    PERCENTAGE = "percentage"
    RATIO = "ratio"
    COUNT = "count"
    ENERGY_MWH = "energy_mwh"
    POWER_MW = "power_mw"
    TIME_HOURS = "time_hours"
    TIME_DAYS = "time_days"
    WEIGHT_KG = "weight_kg"
    VOLUME_LITERS = "volume_liters"
    DIMENSIONLESS = "dimensionless"


class Unit(BaseModel):
    symbol: str = Field(..., description="Unit symbol (e.g., 'USD', '%', 'units', 'MWh')")
    dimension: UnitDimension = Field(default=UnitDimension.DIMENSIONLESS)
    scale_factor: float = Field(default=1.0, description="Multiplication factor relative to SI base")


class NumericVariable(BaseModel):
    name: str = Field(..., description="Unique canonical name of the variable")
    value: float = Field(..., description="Numerical value of the variable")
    unit: Optional[str] = Field(default=None, description="Symbolic unit representation")
    description: Optional[str] = Field(default=None)
    min_bound: Optional[float] = Field(default=None, description="Lower physical or business limit")
    max_bound: Optional[float] = Field(default=None, description="Upper physical or business limit")
    is_derived: bool = Field(default=False, description="True if computed from a formula or model")
    formula: Optional[str] = Field(default=None, description="Safe AST formula if derived")

    @field_validator("value")
    @classmethod
    def validate_finite(cls, v: float) -> float:
        if math.isnan(v) or math.isinf(v):
            raise ValueError(f"NumericVariable value must be finite, received {v}")
        return v

    def validate_bounds(self) -> None:
        if self.min_bound is not None and self.value < self.min_bound:
            raise ValueError(f"Variable '{self.name}' value {self.value} is below min_bound {self.min_bound}")
        if self.max_bound is not None and self.value > self.max_bound:
            raise ValueError(f"Variable '{self.name}' value {self.value} exceeds max_bound {self.max_bound}")
