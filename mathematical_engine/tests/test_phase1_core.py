"""
Unit and integration tests for Phase 1: Mathematical Engine Foundation.
"""
import pytest
import math
from mathematical_engine.contracts import (
    NumericVariable,
    Intervention,
    InterventionType,
    BaselineState,
    Scenario,
)
from mathematical_engine.core import (
    ExecutionContext,
    FormulaEvaluationError,
    CyclicDependencyError,
    OutOfBoundsError,
    ModelRegistry,
    BaseSimulationModel,
    ModelMetadata,
)
from mathematical_engine.deterministic import (
    SafeFormulaEvaluator,
    PropagationEngine,
    weighted_average,
    compound_growth,
    elasticity_impact,
)
from mathematical_engine.graph import (
    find_cycle,
    assert_acyclic,
    DependencyResolver,
    DAGExecutor,
)
from mathematical_engine.validation import (
    BoundChecker,
    InvariantValidator,
    ReconciliationRule,
    ReconciliationEngine,
)
from mathematical_engine.explainability import (
    TraceExplainer,
    ContributionAnalyzer,
)


class TestSafeFormulaEvaluator:
    def setup_method(self):
        self.evaluator = SafeFormulaEvaluator()

    def test_arithmetic_operations(self):
        scope = {"a": 10.0, "b": 3.0}
        assert self.evaluator.evaluate("a + b", scope) == 13.0
        assert self.evaluator.evaluate("a - b", scope) == 7.0
        assert self.evaluator.evaluate("a * b", scope) == 30.0
        assert pytest.approx(self.evaluator.evaluate("a / b", scope)) == 10.0 / 3.0
        assert self.evaluator.evaluate("a // b", scope) == 3.0
        assert self.evaluator.evaluate("a % b", scope) == 1.0
        assert self.evaluator.evaluate("a ** 2", scope) == 100.0

    def test_math_functions_and_constants(self):
        scope = {"x": 16.0, "angle": 0.0}
        assert self.evaluator.evaluate("sqrt(x)", scope) == 4.0
        assert self.evaluator.evaluate("cos(angle)", scope) == 1.0
        assert self.evaluator.evaluate("clip(x, 1.0, 10.0)", scope) == 10.0
        assert pytest.approx(self.evaluator.evaluate("pi * 2", scope)) == 2.0 * math.pi

    def test_variable_extraction(self):
        vars_found = self.evaluator.extract_variables("revenue - (cogs + opex) + sqrt(growth)")
        assert vars_found == {"revenue", "cogs", "opex", "growth"}

    def test_division_by_zero_fails(self):
        with pytest.raises(FormulaEvaluationError, match="Division by zero"):
            self.evaluator.evaluate("10 / 0", {})

    def test_security_rejections(self):
        with pytest.raises(FormulaEvaluationError):
            self.evaluator.evaluate("__import__('os').system('ls')", {})
        with pytest.raises(FormulaEvaluationError):
            self.evaluator.evaluate("open('secret.txt')", {})
        with pytest.raises(FormulaEvaluationError):
            self.evaluator.evaluate("[x for x in [1, 2]]", {})


class TestGraphAndDAG:
    def test_cycle_detection(self):
        # A -> B -> C -> A
        adj = {"A": ["B"], "B": ["C"], "C": ["A"]}
        cycle = find_cycle(adj)
        assert cycle is not None
        assert cycle[0] == cycle[-1]

        with pytest.raises(CyclicDependencyError):
            assert_acyclic(adj)

    def test_acyclic_and_topological_sort(self):
        # price, volume -> revenue -> gross_margin
        resolver = DependencyResolver()
        resolver.add_dependency("revenue", "price")
        resolver.add_dependency("revenue", "volume")
        resolver.add_dependency("gross_margin", "revenue")
        resolver.add_dependency("gross_margin", "cogs")

        order = resolver.topological_order()
        assert order.index("price") < order.index("revenue")
        assert order.index("volume") < order.index("revenue")
        assert order.index("revenue") < order.index("gross_margin")
        assert order.index("cogs") < order.index("gross_margin")

        ancestors = resolver.get_ancestors("gross_margin")
        assert "revenue" in ancestors
        assert "price" in ancestors
        assert "volume" in ancestors
        assert "cogs" in ancestors


class TestDeterministicPropagation:
    def test_retail_margin_scenario(self):
        # Set up baseline
        baseline = BaselineState(
            snapshot_id="test_snap_1",
            variables={
                "price": NumericVariable(name="price", value=100.0, unit="USD", min_bound=10.0),
                "volume": NumericVariable(name="volume", value=1000.0, unit="units", min_bound=0.0),
                "unit_cost": NumericVariable(name="unit_cost", value=60.0, unit="USD"),
            }
        )

        # Set up DAG executor
        dag = DAGExecutor()
        dag.register_formula("revenue", "price * volume")
        dag.register_formula("cogs", "unit_cost * volume")
        dag.register_formula("gross_profit", "revenue - cogs")
        dag.register_formula("gross_margin_pct", "(gross_profit / revenue) * 100")

        # Set up scenario: price discount of 10% (i.e. -10%), volume increases by 15%
        scenario = Scenario(
            name="Promo 10% Discount with 15% Lift",
            baseline=baseline,
            interventions=[
                Intervention(
                    target_variable="price",
                    intervention_type=InterventionType.PERCENTAGE_DELTA,
                    value=-10.0,
                    description="10% promotional price cut"
                ),
                Intervention(
                    target_variable="volume",
                    intervention_type=InterventionType.PERCENTAGE_DELTA,
                    value=15.0,
                    description="15% promotional volume lift"
                ),
            ],
            target_variables=["price", "volume", "revenue", "gross_profit", "gross_margin_pct"]
        )

        engine = PropagationEngine(dag_executor=dag)
        result = engine.run(scenario)

        # Baseline: price=100, volume=1000 -> rev=100,000, cogs=60,000, profit=40,000 (40%)
        # Scenario: price=90, volume=1150 -> rev=103,500, cogs=69,000, profit=34,500 (33.333%)
        assert result.all_values["price"] == 90.0
        assert result.all_values["volume"] == 1150.0
        assert result.all_values["revenue"] == 103500.0
        assert result.all_values["cogs"] == 69000.0
        assert result.all_values["gross_profit"] == 34500.0
        assert pytest.approx(result.all_values["gross_margin_pct"], rel=1e-3) == 33.3333

        # Delta checks
        profit_delta = result.metrics["gross_profit"]
        assert profit_delta.baseline_value == 40000.0
        assert profit_delta.scenario_value == 34500.0
        assert profit_delta.absolute_delta == -5500.0
        assert pytest.approx(profit_delta.percentage_delta, rel=1e-3) == -13.75

        # Check trace explainer
        explanation = TraceExplainer.summarize_path(result.traces, "gross_profit")
        assert "revenue - cogs" in explanation

        # Check waterfall contribution analysis
        analyzer = ContributionAnalyzer(dag_executor=dag)
        contributions = analyzer.analyze_waterfall(scenario, "gross_profit")
        assert len(contributions) == 2


class TestValidationAndInvariants:
    def test_bound_checker(self):
        definitions = {
            "capacity": NumericVariable(name="capacity", value=100.0, min_bound=0.0, max_bound=150.0)
        }
        violations = BoundChecker.check_context({"capacity": 200.0}, definitions)
        assert len(violations) == 1
        assert "exceeds max_bound" in violations[0]

    def test_reconciliation_engine(self):
        rec = ReconciliationEngine([
            ReconciliationRule(
                name="total_cost_balance",
                total_variable="total_cost",
                component_variables=["fixed_cost", "variable_cost"],
            )
        ])
        assert len(rec.reconcile({"total_cost": 100.0, "fixed_cost": 40.0, "variable_cost": 60.0})) == 0
        discrepancies = rec.reconcile({"total_cost": 100.0, "fixed_cost": 40.0, "variable_cost": 50.0})
        assert len(discrepancies) == 1
