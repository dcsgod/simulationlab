"""
DAG execution coordinator evaluating formulas and models in topological order.
"""
from typing import Dict, List, Set, Optional, Any
import time

from mathematical_engine.core.context import ExecutionContext
from mathematical_engine.core.base_model import BaseSimulationModel
from mathematical_engine.deterministic.formula_engine import formula_evaluator
from mathematical_engine.graph.dependency_resolver import DependencyResolver


class DAGExecutor:
    """
    Executes a computational DAG comprising AST formulas and simulation models.
    """

    def __init__(self):
        self.formulas: Dict[str, str] = {}
        self.models: Dict[str, BaseSimulationModel] = {}
        self.resolver = DependencyResolver()

    def register_formula(self, variable_name: str, formula: str) -> None:
        """Registers a formula for a derived variable and connects dependencies."""
        self.formulas[variable_name] = formula
        deps = formula_evaluator.extract_variables(formula)
        for dep in deps:
            self.resolver.add_dependency(dependent=variable_name, dependency=dep)

    def register_model(self, model: BaseSimulationModel) -> None:
        """Registers a simulation model and connects its input/output dependencies."""
        self.models[model.id] = model
        for out_var in model.metadata.produced_outputs:
            for in_var in model.metadata.required_inputs:
                self.resolver.add_dependency(dependent=out_var, dependency=in_var)

    def execute(self, context: ExecutionContext, target_variables: Optional[List[str]] = None) -> None:
        """
        Executes required calculations in topological order, updating the execution context.
        """
        # Determine nodes to evaluate
        if target_variables:
            needed_nodes: Set[str] = set()
            for target in target_variables:
                needed_nodes.add(target)
                needed_nodes.update(self.resolver.get_ancestors(target))
        else:
            needed_nodes = set(self.resolver._all_nodes)

        # Topological sort
        exec_order = self.resolver.topological_order(needed_nodes)

        executed_models: Set[str] = set()

        for node in exec_order:
            # Case 1: Node computed via formula
            if node in self.formulas:
                formula = self.formulas[node]
                var_names = formula_evaluator.extract_variables(formula)
                scope = {v: context.get_value(v) for v in var_names}
                result = formula_evaluator.evaluate(formula, scope)
                context.set_value(node, result)
                context.record_step(
                    variable_name=node,
                    formula_or_model=f"formula: {formula}",
                    input_values=scope,
                    output_value=result,
                )

            # Case 2: Node produced by a registered model
            else:
                for model_id, model in self.models.items():
                    if node in model.metadata.produced_outputs and model_id not in executed_models:
                        model.validate_inputs(context)
                        inputs_snapshot = {
                            var: context.get_value(var)
                            for var in model.metadata.required_inputs
                        }
                        outputs = model.run(context)
                        executed_models.add(model_id)
                        for out_var, val in outputs.items():
                            context.set_value(out_var, val)
                            context.record_step(
                                variable_name=out_var,
                                formula_or_model=f"model: {model.name} ({model_id})",
                                input_values=inputs_snapshot,
                                output_value=val,
                            )
