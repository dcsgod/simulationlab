"""
Waterfall factor attribution decomposing total delta into intervention contributions.
"""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from mathematical_engine.contracts.inputs import BaselineState, Intervention
from mathematical_engine.contracts.scenario import Scenario
from mathematical_engine.deterministic.propagation import PropagationEngine
from mathematical_engine.graph.dag_executor import DAGExecutor


class FactorContribution(BaseModel):
    intervention_variable: str
    target_metric: str
    marginal_delta: float
    percentage_contribution: float = Field(
        ..., description="% of total delta explained by this factor"
    )
    description: Optional[str] = None


class ContributionAnalyzer:
    """
    Decomposes the total observed delta of a target variable across individual interventions.
    """

    def __init__(self, dag_executor: Optional[DAGExecutor] = None):
        self.propagation_engine = PropagationEngine(dag_executor=dag_executor)

    def analyze_waterfall(
        self,
        scenario: Scenario,
        target_variable: str,
        baseline: Optional[BaselineState] = None,
    ) -> List[FactorContribution]:
        """
        Runs one-at-a-time (OAT) marginal simulations for each intervention to attribute
        the overall change in target_variable.
        """
        active_baseline = baseline or scenario.baseline
        if not active_baseline:
            raise ValueError("Baseline is required for contribution analysis")

        # Full run
        full_res = self.propagation_engine.run(scenario, baseline=active_baseline)
        total_delta = full_res.metrics[target_variable].absolute_delta

        marginal_deltas: Dict[str, float] = {}

        # Run each intervention in isolation
        for intervention in scenario.interventions:
            single_scenario = Scenario(
                name=f"Single: {intervention.target_variable}",
                baseline=active_baseline,
                interventions=[intervention],
                target_variables=[target_variable],
            )
            single_res = self.propagation_engine.run(single_scenario, baseline=active_baseline)
            marginal_deltas[intervention.target_variable] = single_res.metrics[target_variable].absolute_delta

        sum_abs_marginal = sum(abs(v) for v in marginal_deltas.values())

        contributions: List[FactorContribution] = []
        for intervention in scenario.interventions:
            var_name = intervention.target_variable
            delta = marginal_deltas.get(var_name, 0.0)
            
            pct = 0.0
            if abs(sum_abs_marginal) > 1e-12:
                pct = (abs(delta) / sum_abs_marginal) * 100.0

            contributions.append(
                FactorContribution(
                    intervention_variable=var_name,
                    target_metric=target_variable,
                    marginal_delta=delta,
                    percentage_contribution=pct,
                    description=intervention.description,
                )
            )

        return contributions
