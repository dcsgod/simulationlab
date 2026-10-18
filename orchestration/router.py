"""
Capability-based model router executing simulation, sensitivity, or optimization flows.
"""
from typing import Optional, Dict, Any

from mathematical_engine.core.engine import MathematicalEngine
from mathematical_engine.graph.dag_executor import DAGExecutor
from mathematical_engine.optimization.problem import OptimizationProblem
from mathematical_engine.optimization.objectives import set_profit_maximization_objective
from mathematical_engine.optimization.constraints import add_budget_constraint
from orchestration.intent_parser import ParsedIntent, IntentType
from orchestration.scenario_planner import ScenarioPlanner
from orchestration.evidence_envelope import GroundedEvidenceEnvelope
from connectors.base import BaseDataProvider


class ModelRouter:
    """
    Directs parsed intent queries to appropriate mathematical models and constructs grounded evidence envelopes.
    """

    def __init__(self, data_provider: BaseDataProvider):
        self.data_provider = data_provider
        self.planner = ScenarioPlanner(data_provider=data_provider)
        
        # Configure mathematical engine with default retail calculation formulas
        dag = DAGExecutor()
        dag.register_formula("effective_price", "base_price * (1.0 - promo_discount_pct / 100.0)")
        # Volume response with price elasticity: volume_new = units_sold * (effective_price / base_price) ^ elasticity
        dag.register_formula("revenue", "effective_price * units_sold")
        dag.register_formula("cogs_total", "(cogs_usd / units_sold) * units_sold")
        dag.register_formula("gross_margin_usd", "revenue - cogs_usd")

        self.math_engine = MathematicalEngine(dag_executor=dag)

    def route_and_execute(self, intent: ParsedIntent) -> GroundedEvidenceEnvelope:
        """Executes full end-to-end pipeline from intent to evidence envelope."""
        scenario = self.planner.plan_scenario_from_intent(intent)
        baseline = scenario.baseline

        # Execute simulation
        sim_result = self.math_engine.run_deterministic(scenario, baseline=baseline)

        # Run sensitivity drivers for target metric
        target_var = intent.target_metric or "gross_margin_usd"
        sensitivity_drivers = self.math_engine.run_sensitivity(
            baseline=baseline,
            target_metric=target_var,
        )

        envelope = GroundedEvidenceEnvelope(
            envelope_id=f"env_{sim_result.simulation_id[:8]}",
            scenario_id=scenario.id,
            scenario_title=scenario.name,
            execution_status=sim_result.status,
            baseline_snapshot_id=baseline.snapshot_id,
            data_source_id=self.data_provider.source_id,
            baseline_values=baseline.to_value_dict(),
            interventions_applied=[i.model_dump() for i in scenario.interventions],
            calculation_path=[t.get("variable_name") for t in sim_result.traces if "variable_name" in t],
            execution_traces=sim_result.traces,
            metric_deltas=sim_result.metrics,
            distributions=sim_result.distributions,
            sensitivity_drivers=sensitivity_drivers,
            validation_passed=sim_result.validation_passed,
            invariants_checked=sim_result.invariants_checked,
            invariants_violated=sim_result.invariants_violated,
        )

        envelope.generate_narrative(target_metric=target_var)
        return envelope
