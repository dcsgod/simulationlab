"""
Scenario definitions, intervention sets, and configuration contracts.
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
import uuid

from mathematical_engine.contracts.inputs import Intervention, BaselineState


class Scenario(BaseModel):
    """
    Represents a specific simulation scenario, consisting of baseline context,
    interventions, target metrics, and assumptions.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique scenario ID")
    name: str = Field(..., description="Human-readable scenario title")
    description: Optional[str] = Field(default=None, description="Detailed description of hypothesis or goal")
    baseline: Optional[BaselineState] = Field(default=None, description="Baseline system state snapshot")
    interventions: List[Intervention] = Field(default_factory=list, description="Ordered parameter interventions")
    target_variables: List[str] = Field(default_factory=list, description="Primary variables of interest")
    assumptions: Dict[str, Any] = Field(default_factory=dict, description="Documented assumptions for scenario")
    tags: List[str] = Field(default_factory=list, description="Categorization or project tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Extensible scenario metadata")

    def get_intervention_for_variable(self, variable_name: str) -> Optional[Intervention]:
        """Finds the first intervention targeting the specified variable, if any."""
        for intervention in self.interventions:
            if intervention.target_variable == variable_name:
                return intervention
        return None

    def add_intervention(self, intervention: Intervention) -> None:
        """Adds an intervention, replacing any existing intervention on the same variable."""
        self.interventions = [i for i in self.interventions if i.target_variable != intervention.target_variable]
        self.interventions.append(intervention)
