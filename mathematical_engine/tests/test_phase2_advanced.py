"""
Unit and analytical correctness tests for Phase 2:
Stochastic Monte Carlo, Sensitivity Analysis, and SciPy HiGHS Optimization.
"""
import pytest
import numpy as np

from mathematical_engine.contracts import (
    NumericVariable,
    BaselineState,
    Scenario,
    Intervention,
    InterventionType,
)
from mathematical_engine.graph import DAGExecutor
from mathematical_engine.stochastic import (
    DistributionType,
    ParameterDistribution,
    CorrelatedSampler,
    compute_distribution_summary,
    compute_breach_probability,
    MonteCarloEngine,
)
from mathematical_engine.sensitivity import (
    LocalSensitivityAnalyzer,
    GlobalSensitivityAnalyzer,
    ParameterRange,
)
from mathematical_engine.optimization import (
    OptimizationProblem,
    VariableType,
    ConstraintSense,
    ObjectiveDirection,
    HiGHSSolver,
    add_budget_constraint,
    set_profit_maximization_objective,
)
from mathematical_engine.core import InfeasibleOptimizationError


class TestStochasticAndMonteCarlo:
    def test_parameter_distributions(self):
        norm_dist = ParameterDistribution(
            variable_name="demand",
            dist_type=DistributionType.NORMAL,
            parameters={"mean": 100.0, "std": 10.0},
        )
        samples = norm_dist.sample(size=1000, rng=np.random.default_rng(42))
        assert len(samples) == 1000
        assert pytest.approx(np.mean(samples), rel=0.05) == 100.0
        assert pytest.approx(np.std(samples), rel=0.1) == 10.0

    def test_correlated_sampler(self):
        # Two positively correlated variables (correlation = 0.8)
        dist_x = ParameterDistribution(
            variable_name="x",
            dist_type=DistributionType.NORMAL,
            parameters={"mean": 50.0, "std": 5.0},
        )
        dist_y = ParameterDistribution(
            variable_name="y",
            dist_type=DistributionType.NORMAL,
            parameters={"mean": 200.0, "std": 20.0},
        )
        corr_mat = np.array([[1.0, 0.8], [0.8, 1.0]])

        sampler = CorrelatedSampler(
            variable_order=["x", "y"],
            distributions={"x": dist_x, "y": dist_y},
            correlation_matrix=corr_mat,
        )
        draws = sampler.sample(num_samples=5000, seed=123)
        sample_corr = np.corrcoef(draws["x"], draws["y"])[0, 1]
        assert pytest.approx(sample_corr, abs=0.05) == 0.8

    def test_monte_carlo_engine(self):
        baseline = BaselineState(
            snapshot_id="mc_snap",
            variables={
                "price": NumericVariable(name="price", value=50.0),
                "volume": NumericVariable(name="volume", value=1000.0),
                "unit_cost": NumericVariable(name="unit_cost", value=30.0),
            }
        )
        dag = DAGExecutor()
        dag.register_formula("revenue", "price * volume")
        dag.register_formula("total_cost", "unit_cost * volume")
        dag.register_formula("profit", "revenue - total_cost")

        scenario = Scenario(
            name="Uncertain Demand Scenario",
            baseline=baseline,
            target_variables=["profit", "revenue"],
        )

        uncertain_params = {
            "volume": ParameterDistribution(
                variable_name="volume",
                dist_type=DistributionType.NORMAL,
                parameters={"mean": 1000.0, "std": 100.0},
            )
        }

        mc = MonteCarloEngine(dag_executor=dag)
        result = mc.run(
            scenario=scenario,
            uncertain_parameters=uncertain_params,
            num_iterations=2000,
            seed=42,
        )

        assert "profit" in result.distributions
        p_dist = result.distributions["profit"]
        # Expected profit = (50 - 30) * 1000 = 20,000. Std = 20 * 100 = 2000.
        assert pytest.approx(p_dist.mean, rel=0.05) == 20000.0
        assert pytest.approx(p_dist.std, rel=0.1) == 2000.0
        assert p_dist.var_95 < 20000.0
        assert p_dist.cvar_95 <= p_dist.var_95


class TestSensitivityAnalysis:
    def test_local_sensitivity_elasticity(self):
        baseline = BaselineState(
            snapshot_id="sens_snap",
            variables={
                "price": NumericVariable(name="price", value=100.0),
                "volume": NumericVariable(name="volume", value=500.0),
            }
        )
        dag = DAGExecutor()
        dag.register_formula("revenue", "price * volume")

        analyzer = LocalSensitivityAnalyzer(dag_executor=dag)
        drivers = analyzer.analyze(baseline, target_metric="revenue")

        # For revenue = price * volume, elasticity of price is 1.0 and volume is 1.0
        assert len(drivers) == 2
        for d in drivers:
            assert pytest.approx(d.elasticity, abs=1e-3) == 1.0
            assert d.direction == "positive"

    def test_global_morris_screening(self):
        baseline = BaselineState(
            snapshot_id="global_snap",
            variables={
                "x1": NumericVariable(name="x1", value=10.0),
                "x2": NumericVariable(name="x2", value=10.0),
                "dummy": NumericVariable(name="dummy", value=10.0),
            }
        )
        dag = DAGExecutor()
        # x1 has large effect (factor 10), x2 has modest effect (factor 2), dummy has zero effect
        dag.register_formula("target", "10 * x1 + 2 * x2 + 0 * dummy")

        analyzer = GlobalSensitivityAnalyzer(dag_executor=dag)
        ranges = {
            "x1": ParameterRange(min_val=5.0, max_val=20.0),
            "x2": ParameterRange(min_val=5.0, max_val=20.0),
            "dummy": ParameterRange(min_val=1.0, max_val=50.0),
        }
        drivers = analyzer.analyze_morris(baseline, "target", ranges, num_trajectories=30)
        assert drivers[0].variable_name == "x1"
        assert drivers[1].variable_name == "x2"
        assert drivers[2].variable_name == "dummy"
        assert drivers[2].normalized_impact == 0.0


class TestHiGHSOptimization:
    def test_linear_programming_product_mix(self):
        # Maximize Profit = 40 * ProductA + 30 * ProductB
        # Subject to:
        # Machine Hours: 2 * ProductA + 1 * ProductB <= 100
        # Labor Hours:   1 * ProductA + 1 * ProductB <= 80
        # ProductA, ProductB >= 0
        # Analytical optimum: Intersection of 2A + B = 100 and A + B = 80 => A = 20, B = 60
        # Optimal Profit: 40(20) + 30(60) = 800 + 1800 = 2600.
        problem = OptimizationProblem(name="Product Mix Optimization")
        problem.add_variable("ProductA", lower_bound=0.0)
        problem.add_variable("ProductB", lower_bound=0.0)

        set_profit_maximization_objective(
            problem,
            margins_or_prices={"ProductA": 40.0, "ProductB": 30.0}
        )

        problem.add_constraint(
            name="Machine_Capacity",
            coefficients={"ProductA": 2.0, "ProductB": 1.0},
            sense=ConstraintSense.LE,
            rhs=100.0,
        )
        problem.add_constraint(
            name="Labor_Capacity",
            coefficients={"ProductA": 1.0, "ProductB": 1.0},
            sense=ConstraintSense.LE,
            rhs=80.0,
        )

        solver = HiGHSSolver()
        res = solver.solve(problem)

        assert res.is_optimal is True
        assert res.status == "OPTIMAL"
        assert pytest.approx(res.objective_value, rel=1e-4) == 2600.0
        assert pytest.approx(res.variable_values["ProductA"], abs=1e-4) == 20.0
        assert pytest.approx(res.variable_values["ProductB"], abs=1e-4) == 60.0
        assert pytest.approx(res.constraint_slacks["Machine_Capacity"], abs=1e-4) == 0.0
        assert pytest.approx(res.constraint_slacks["Labor_Capacity"], abs=1e-4) == 0.0

    def test_mixed_integer_linear_programming_knapsack(self):
        # 0-1 Knapsack problem
        # Items: 1 (val 10, wt 5), 2 (val 40, wt 4), 3 (val 30, wt 3), 4 (val 50, wt 5)
        # Max capacity = 10
        # Optimal: take item 2 (wt 4), item 3 (wt 3) = wt 7, or item 2 (wt 4) + item 4 (wt 5) = wt 9 (val 90)
        # Or item 3 (3) + item 4 (5) = 8 (val 80).
        # Best combination: Item 2 + Item 4 => wt = 9 <= 10, value = 40 + 50 = 90.
        problem = OptimizationProblem(name="Knapsack 0-1")
        for i in range(1, 5):
            problem.add_variable(f"item_{i}", var_type=VariableType.BINARY)

        problem.set_objective(
            coefficients={"item_1": 10.0, "item_2": 40.0, "item_3": 30.0, "item_4": 50.0},
            direction=ObjectiveDirection.MAXIMIZE,
        )
        problem.add_constraint(
            name="weight_limit",
            coefficients={"item_1": 5.0, "item_2": 4.0, "item_3": 3.0, "item_4": 5.0},
            sense=ConstraintSense.LE,
            rhs=10.0,
        )

        solver = HiGHSSolver()
        res = solver.solve(problem)

        assert res.is_optimal is True
        assert pytest.approx(res.objective_value) == 90.0
        assert round(res.variable_values["item_2"]) == 1
        assert round(res.variable_values["item_4"]) == 1
        assert round(res.variable_values["item_1"]) == 0
        assert round(res.variable_values["item_3"]) == 0

    def test_infeasible_problem_diagnostics(self):
        # Contradictory constraints: x >= 10 and x <= 5
        problem = OptimizationProblem(name="Infeasible Problem")
        problem.add_variable("x", lower_bound=0.0)
        problem.set_objective(coefficients={"x": 1.0}, direction=ObjectiveDirection.MINIMIZE)

        problem.add_constraint("min_req", {"x": 1.0}, sense=ConstraintSense.GE, rhs=10.0)
        problem.add_constraint("max_cap", {"x": 1.0}, sense=ConstraintSense.LE, rhs=5.0)

        solver = HiGHSSolver()
        res = solver.solve(problem)

        assert res.is_optimal is False
        assert res.status == "INFEASIBLE"
        assert len(res.diagnostics) > 0

        with pytest.raises(InfeasibleOptimizationError):
            solver.solve(problem, raise_on_infeasible=True)
