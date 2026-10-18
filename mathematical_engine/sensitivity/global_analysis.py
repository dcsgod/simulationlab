"""
Global parameter sensitivity analysis and Morris screening across operating domains.
"""
from typing import Dict, List, Tuple, Optional
import numpy as np
from pydantic import BaseModel, Field

from mathematical_engine.contracts.inputs import BaselineState, Intervention, InterventionType
from mathematical_engine.contracts.scenario import Scenario
from mathematical_engine.contracts.results import SensitivityDriver
from mathematical_engine.graph.dag_executor import DAGExecutor
from mathematical_engine.deterministic.propagation import PropagationEngine


class ParameterRange(BaseModel):
    min_val: float
    max_val: float


class GlobalSensitivityAnalyzer:
    """
    Evaluates global parameter influence across wide operating envelopes using Morris screening.
    """

    def __init__(self, dag_executor: Optional[DAGExecutor] = None):
        self.dag_executor = dag_executor or DAGExecutor()
        self.propagation_engine = PropagationEngine(dag_executor=self.dag_executor)

    def analyze_morris(
        self,
        baseline: BaselineState,
        target_metric: str,
        parameter_ranges: Dict[str, ParameterRange],
        num_trajectories: int = 20,
        grid_levels: int = 4,
        seed: Optional[int] = 42,
    ) -> List[SensitivityDriver]:
        """
        Computes Morris elementary effects (mu* and sigma) across randomized trajectory lines.
        """
        rng = np.random.default_rng(seed)
        param_names = sorted(list(parameter_ranges.keys()))
        k = len(param_names)
        delta = grid_levels / (2 * (grid_levels - 1))

        elementary_effects: Dict[str, List[float]] = {p: [] for p in param_names}

        for _ in range(num_trajectories):
            # Base point in normalized [0, 1] grid
            x_base = rng.choice(np.linspace(0, 1 - delta, grid_levels // 2), size=k)
            
            # Form trajectory by perturbing one parameter at a time
            perm = rng.permutation(k)
            x_curr = np.array(x_base)

            # Evaluate base point
            y_curr = self._eval_point(baseline, param_names, parameter_ranges, x_curr, target_metric)

            for step in perm:
                param = param_names[step]
                x_next = np.array(x_curr)
                x_next[step] += delta

                y_next = self._eval_point(baseline, param_names, parameter_ranges, x_next, target_metric)
                
                # Elementary effect = change in output / change in normalized input
                ee = (y_next - y_curr) / delta
                elementary_effects[param].append(ee)

                x_curr = x_next
                y_curr = y_next

        drivers: List[SensitivityDriver] = []
        for param in param_names:
            effects = np.array(elementary_effects[param])
            mu_star = float(np.mean(np.abs(effects)))
            mean_effect = float(np.mean(effects))

            drivers.append(
                SensitivityDriver(
                    variable_name=param,
                    target_metric=target_metric,
                    elasticity=float(mu_star),
                    absolute_derivative=float(mean_effect),
                    normalized_impact=float(mu_star),
                    rank=0,
                    direction="positive" if mean_effect >= 0 else "negative",
                )
            )

        drivers.sort(key=lambda d: d.normalized_impact, reverse=True)
        for idx, d in enumerate(drivers):
            d.rank = idx + 1

        return drivers

    def _eval_point(
        self,
        baseline: BaselineState,
        param_names: List[str],
        parameter_ranges: Dict[str, ParameterRange],
        norm_x: np.ndarray,
        target_metric: str,
    ) -> float:
        interventions: List[Intervention] = []
        for idx, p in enumerate(param_names):
            rng = parameter_ranges[p]
            real_val = rng.min_val + norm_x[idx] * (rng.max_val - rng.min_val)
            interventions.append(
                Intervention(
                    target_variable=p,
                    intervention_type=InterventionType.SET_VALUE,
                    value=float(real_val),
                )
            )

        scen = Scenario(
            name="MorrisPoint",
            baseline=baseline,
            interventions=interventions,
            target_variables=[target_metric],
        )
        res = self.propagation_engine.run(scen)
        return float(res.all_values[target_metric])
