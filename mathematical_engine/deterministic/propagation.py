"""
Deterministic simulation propagation engine applying baseline states, interventions, and DAG updates.
"""
from typing import Dict, List, Optional, TYPE_CHECKING
import time

if TYPE_CHECKING:
    from mathematical_engine.graph.dag_executor import DAGExecutor

from mathematical_engine.contracts.inputs import BaselineState, Intervention
from mathematical_engine.contracts.scenario import Scenario
from mathematical_engine.contracts.results import (
    SimulationResult,
    MetricDelta,
    ExecutionStatus,
)
from mathematical_engine.core.context import ExecutionContext


class PropagationEngine:
    """
    Coordinates baseline instantiation, intervention application, and DAG topological evaluation.
    """

    def __init__(self, dag_executor: Optional["DAGExecutor"] = None):
        if dag_executor is None:
            from mathematical_engine.graph.dag_executor import DAGExecutor
            self.dag_executor = DAGExecutor()
        else:
            self.dag_executor = dag_executor

    def run(
        self,
        scenario: Scenario,
        baseline: Optional[BaselineState] = None,
    ) -> SimulationResult:
        """
        Executes a deterministic simulation run for the given scenario.
        """
        start_time = time.time()
        active_baseline = baseline or scenario.baseline
        if active_baseline is None:
            raise ValueError("Scenario must have an attached BaselineState or baseline passed explicitly.")

        # 1. Establish full baseline values by running DAG on baseline if needed
        baseline_ctx = ExecutionContext(
            baseline_values=active_baseline.to_value_dict(),
            variable_definitions=active_baseline.variables,
        )
        self.dag_executor.execute(baseline_ctx, target_variables=scenario.target_variables or None)
        full_baseline_values = dict(baseline_ctx.current_values)

        # 2. Initialize scenario execution context from resolved baseline
        context = ExecutionContext(
            baseline_values=full_baseline_values,
            variable_definitions=active_baseline.variables,
        )

        # 3. Apply scenario interventions
        for intervention in scenario.interventions:
            target = intervention.target_variable
            if target not in context.current_values:
                context.current_values[target] = 0.0
            
            baseline_val = context.current_values[target]
            new_val = intervention.apply(baseline_val)
            context.set_value(target, new_val)
            context.record_step(
                variable_name=target,
                formula_or_model=f"intervention: {intervention.intervention_type.value} ({intervention.value})",
                input_values={f"{target}_baseline": baseline_val},
                output_value=new_val,
                step_metadata={"intervention_description": intervention.description},
            )

        # 4. Propagate scenario through DAG
        self.dag_executor.execute(context, target_variables=scenario.target_variables or None)

        # 5. Compute metric deltas
        metrics: Dict[str, MetricDelta] = {}
        all_var_names = set(full_baseline_values.keys()).union(set(context.current_values.keys()))
        eval_vars = scenario.target_variables if scenario.target_variables else all_var_names

        for var_name in eval_vars:
            b_val = full_baseline_values.get(var_name, 0.0)
            s_val = context.current_values.get(var_name, 0.0)
            unit_sym = None
            if var_name in active_baseline.variables and active_baseline.variables[var_name].unit:
                unit_sym = active_baseline.variables[var_name].unit
            
            metrics[var_name] = MetricDelta.compute(
                name=var_name,
                baseline=b_val,
                scenario=s_val,
                unit=unit_sym,
            )

        execution_time_ms = (time.time() - start_time) * 1000.0

        return SimulationResult(
            scenario_id=scenario.id,
            status=ExecutionStatus.SUCCESS if len(context.invariants_violated) == 0 else ExecutionStatus.PARTIAL,
            metrics=metrics,
            all_values=dict(context.current_values),
            traces=context.traces,
            validation_passed=(len(context.invariants_violated) == 0),
            invariants_checked=context.invariants_checked,
            invariants_violated=context.invariants_violated,
            execution_time_ms=execution_time_ms,
        )
