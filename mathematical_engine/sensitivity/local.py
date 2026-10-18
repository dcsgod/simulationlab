"""
Local sensitivity analysis, central finite difference derivatives, and elasticity ranking.
"""
from typing import Dict, List, Optional
import numpy as np

from mathematical_engine.contracts.inputs import BaselineState, Intervention, InterventionType
from mathematical_engine.contracts.scenario import Scenario
from mathematical_engine.contracts.results import SensitivityDriver
from mathematical_engine.graph.dag_executor import DAGExecutor
from mathematical_engine.deterministic.propagation import PropagationEngine


class LocalSensitivityAnalyzer:
    """
    Computes local derivatives and elasticities for input parameters driving target metrics.
    """

    def __init__(self, dag_executor: Optional[DAGExecutor] = None):
        self.dag_executor = dag_executor or DAGExecutor()
        self.propagation_engine = PropagationEngine(dag_executor=self.dag_executor)

    def analyze(
        self,
        baseline: BaselineState,
        target_metric: str,
        parameters: Optional[List[str]] = None,
        relative_step: float = 0.01,  # 1% perturbation
    ) -> List[SensitivityDriver]:
        """
        Calculates central finite-difference elasticities for each parameter.
        """
        # Baseline run
        base_scenario = Scenario(
            name="Base",
            baseline=baseline,
            target_variables=[target_metric],
        )
        base_res = self.propagation_engine.run(base_scenario)
        y0 = base_res.all_values.get(target_metric, 0.0)

        input_names = parameters or [k for k in baseline.variables.keys() if not baseline.variables[k].is_derived]
        drivers: List[SensitivityDriver] = []

        for param in input_names:
            x0 = baseline.get_value(param)
            delta_x = relative_step * max(abs(x0), 1e-4)

            # Plus step
            plus_scen = Scenario(
                name=f"+{param}",
                baseline=baseline,
                interventions=[
                    Intervention(
                        target_variable=param,
                        intervention_type=InterventionType.ABSOLUTE_DELTA,
                        value=delta_x,
                    )
                ],
                target_variables=[target_metric],
            )
            y_plus = self.propagation_engine.run(plus_scen).all_values[target_metric]

            # Minus step
            minus_scen = Scenario(
                name=f"-{param}",
                baseline=baseline,
                interventions=[
                    Intervention(
                        target_variable=param,
                        intervention_type=InterventionType.ABSOLUTE_DELTA,
                        value=-delta_x,
                    )
                ],
                target_variables=[target_metric],
            )
            y_minus = self.propagation_engine.run(minus_scen).all_values[target_metric]

            derivative = (y_plus - y_minus) / (2.0 * delta_x)
            
            # Elasticity: (% delta in y) / (% delta in x) = (dy/dx) * (x0 / y0)
            elasticity = 0.0
            if abs(y0) > 1e-12:
                elasticity = derivative * (x0 / y0)

            drivers.append(
                SensitivityDriver(
                    variable_name=param,
                    target_metric=target_metric,
                    elasticity=float(elasticity),
                    absolute_derivative=float(derivative),
                    normalized_impact=float(abs(elasticity)),
                    rank=0,
                    direction="positive" if derivative >= 0 else "negative",
                )
            )

        # Sort by absolute elasticity descending and assign ranks
        drivers.sort(key=lambda d: abs(d.elasticity), reverse=True)
        for idx, d in enumerate(drivers):
            d.rank = idx + 1

        return drivers
