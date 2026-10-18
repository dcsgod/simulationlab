"""
Monte Carlo stochastic simulation engine combining correlated draws and DAG evaluation.
"""
from typing import Dict, List, Optional
import time
import numpy as np

from mathematical_engine.contracts.inputs import BaselineState
from mathematical_engine.contracts.scenario import Scenario
from mathematical_engine.contracts.results import (
    SimulationResult,
    DistributionSummary,
    ExecutionStatus,
    MetricDelta,
)
from mathematical_engine.core.context import ExecutionContext
from mathematical_engine.graph.dag_executor import DAGExecutor
from mathematical_engine.deterministic.propagation import PropagationEngine
from mathematical_engine.stochastic.distributions import ParameterDistribution
from mathematical_engine.stochastic.correlation import CorrelatedSampler
from mathematical_engine.stochastic.risk_metrics import compute_distribution_summary


class MonteCarloEngine:
    """
    Executes repeated stochastic simulations across probability distributions and correlations.
    """

    def __init__(self, dag_executor: Optional[DAGExecutor] = None):
        self.dag_executor = dag_executor or DAGExecutor()
        self.propagation_engine = PropagationEngine(dag_executor=self.dag_executor)

    def run(
        self,
        scenario: Scenario,
        uncertain_parameters: Dict[str, ParameterDistribution],
        correlation_matrix: Optional[np.ndarray] = None,
        num_iterations: int = 1000,
        seed: Optional[int] = 42,
        baseline: Optional[BaselineState] = None,
    ) -> SimulationResult:
        """
        Executes N iterations of Monte Carlo draws, propagating each sample through the DAG.
        """
        start_time = time.time()
        active_baseline = baseline or scenario.baseline
        if active_baseline is None:
            raise ValueError("Scenario must have an attached BaselineState or baseline passed explicitly.")

        # First run base deterministic propagation
        det_result = self.propagation_engine.run(scenario, baseline=active_baseline)

        # Draw correlated inputs
        param_names = sorted(list(uncertain_parameters.keys()))
        sampler = CorrelatedSampler(
            variable_order=param_names,
            distributions=uncertain_parameters,
            correlation_matrix=correlation_matrix,
        )
        sample_draws = sampler.sample(num_samples=num_iterations, seed=seed)

        target_vars = scenario.target_variables or list(det_result.all_values.keys())
        collected_outputs: Dict[str, List[float]] = {var: [] for var in target_vars}

        base_values = dict(det_result.all_values)

        for i in range(num_iterations):
            # Form scenario sample
            ctx = ExecutionContext(baseline_values=base_values)
            for param in param_names:
                draw_val = float(sample_draws[param][i])
                ctx.set_value(param, draw_val, validate_bounds=False)

            # Evaluate DAG
            self.dag_executor.execute(ctx, target_variables=target_vars)

            for var in target_vars:
                collected_outputs[var].append(ctx.get_value(var))

        # Compute summary risk metrics
        distributions: Dict[str, DistributionSummary] = {}
        for var in target_vars:
            samples_arr = np.array(collected_outputs[var])
            b_val = det_result.metrics.get(var, None)
            base_val = b_val.baseline_value if b_val else None
            distributions[var] = compute_distribution_summary(
                name=var,
                samples=samples_arr,
                baseline_value=base_val,
            )

        execution_time_ms = (time.time() - start_time) * 1000.0

        return SimulationResult(
            scenario_id=scenario.id,
            status=ExecutionStatus.SUCCESS,
            metrics=det_result.metrics,
            all_values=det_result.all_values,
            distributions=distributions,
            traces=det_result.traces,
            validation_passed=det_result.validation_passed,
            invariants_checked=det_result.invariants_checked,
            invariants_violated=det_result.invariants_violated,
            execution_time_ms=execution_time_ms,
            metadata={"num_iterations": num_iterations, "seed": seed},
        )
