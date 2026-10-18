"""
Unified facade for the Simulation Lab Mathematical Engine.
Coordinates deterministic propagation, stochastic simulation, sensitivity, and optimization.
"""
from typing import Dict, List, Optional
import numpy as np

from mathematical_engine.contracts.inputs import BaselineState
from mathematical_engine.contracts.scenario import Scenario
from mathematical_engine.contracts.results import SimulationResult, SensitivityDriver
from mathematical_engine.core.registry import ModelRegistry, default_model_registry
from mathematical_engine.graph.dag_executor import DAGExecutor
from mathematical_engine.deterministic.propagation import PropagationEngine
from mathematical_engine.stochastic.monte_carlo import MonteCarloEngine
from mathematical_engine.stochastic.distributions import ParameterDistribution
from mathematical_engine.sensitivity.local import LocalSensitivityAnalyzer
from mathematical_engine.optimization.problem import OptimizationProblem
from mathematical_engine.optimization.solver_registry import HiGHSSolver, OptimizationResult


class MathematicalEngine:
    """
    Primary interface for running simulations, sensitivity analysis, and optimizations.
    """

    def __init__(
        self,
        registry: Optional[ModelRegistry] = None,
        dag_executor: Optional[DAGExecutor] = None,
    ):
        self.registry = registry or default_model_registry
        self.dag_executor = dag_executor or DAGExecutor()
        self.propagation_engine = PropagationEngine(dag_executor=self.dag_executor)
        self.monte_carlo_engine = MonteCarloEngine(dag_executor=self.dag_executor)
        self.sensitivity_analyzer = LocalSensitivityAnalyzer(dag_executor=self.dag_executor)
        self.solver = HiGHSSolver()

    def register_formula(self, variable_name: str, formula: str) -> None:
        """Adds a derived variable calculation formula to the execution DAG."""
        self.dag_executor.register_formula(variable_name, formula)

    def run_deterministic(
        self,
        scenario: Scenario,
        baseline: Optional[BaselineState] = None,
    ) -> SimulationResult:
        """Executes single deterministic scenario propagation."""
        return self.propagation_engine.run(scenario, baseline=baseline)

    def run_monte_carlo(
        self,
        scenario: Scenario,
        uncertain_parameters: Dict[str, ParameterDistribution],
        correlation_matrix: Optional[np.ndarray] = None,
        num_iterations: int = 1000,
        seed: Optional[int] = 42,
        baseline: Optional[BaselineState] = None,
    ) -> SimulationResult:
        """Executes stochastic Monte Carlo simulations with uncertainty profiles."""
        return self.monte_carlo_engine.run(
            scenario=scenario,
            uncertain_parameters=uncertain_parameters,
            correlation_matrix=correlation_matrix,
            num_iterations=num_iterations,
            seed=seed,
            baseline=baseline,
        )

    def run_sensitivity(
        self,
        baseline: BaselineState,
        target_metric: str,
        parameters: Optional[List[str]] = None,
        relative_step: float = 0.01,
    ) -> List[SensitivityDriver]:
        """Calculates elasticities and local derivatives for driving parameters."""
        return self.sensitivity_analyzer.analyze(
            baseline=baseline,
            target_metric=target_metric,
            parameters=parameters,
            relative_step=relative_step,
        )

    def solve_optimization(
        self,
        problem: OptimizationProblem,
        raise_on_infeasible: bool = False,
    ) -> OptimizationResult:
        """Solves LP or MILP optimization problem using HiGHS."""
        return self.solver.solve(problem, raise_on_infeasible=raise_on_infeasible)
