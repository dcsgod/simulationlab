"""
Abstract base class and contract definitions for mathematical simulation models.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field

from mathematical_engine.core.context import ExecutionContext
from mathematical_engine.core.errors import DependencyResolutionError


class ModelCapability(str, Enum):
    DETERMINISTIC = "deterministic"
    STOCHASTIC = "stochastic"
    OPTIMIZATION = "optimization"
    SENSITIVITY = "sensitivity"
    TIME_SERIES = "time_series"


class ModelMetadata(BaseModel):
    id: str = Field(..., description="Unique model identifier")
    name: str = Field(..., description="Human-friendly model title")
    version: str = Field(default="1.0.0", description="Semantic version")
    description: Optional[str] = Field(default=None)
    capabilities: List[ModelCapability] = Field(default_factory=lambda: [ModelCapability.DETERMINISTIC])
    required_inputs: List[str] = Field(default_factory=list, description="Variables needed before execution")
    produced_outputs: List[str] = Field(default_factory=list, description="Variables computed and populated")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Default parameters")
    tags: List[str] = Field(default_factory=list)


class BaseSimulationModel(ABC):
    """
    Standard interface for all analytical, physical, and domain simulation models.
    """

    def __init__(self, metadata: ModelMetadata):
        self.metadata = metadata

    @property
    def id(self) -> str:
        return self.metadata.id

    @property
    def name(self) -> str:
        return self.metadata.name

    def validate_inputs(self, context: ExecutionContext) -> None:
        """Validates that all required input variables exist in the execution context."""
        missing = [inp for inp in self.metadata.required_inputs if inp not in context.current_values]
        if missing:
            raise DependencyResolutionError(
                f"Model '{self.name}' ({self.id}) missing required inputs: {missing}"
            )

    @abstractmethod
    def run(self, context: ExecutionContext) -> Dict[str, float]:
        """
        Executes model computations against the context and returns dict of produced variable values.
        Must also record execution trace and update context.
        """
        pass

    def explain(self) -> str:
        """Returns mathematical explanation or assumptions of the model."""
        return self.metadata.description or f"Simulation model {self.name} v{self.metadata.version}"
