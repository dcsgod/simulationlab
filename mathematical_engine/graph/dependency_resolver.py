"""
Topological sorting, dependency resolution, ancestor/descendant impact discovery.
"""
from typing import Dict, List, Set, Optional
from collections import defaultdict, deque
from mathematical_engine.graph.cycle_detection import assert_acyclic
from mathematical_engine.core.errors import DependencyResolutionError


class DependencyResolver:
    """
    Manages variable and computation dependencies, ordering calculation steps.
    """

    def __init__(self):
        # dependent -> set of variables it directly depends on (incoming edges)
        self._depends_on: Dict[str, Set[str]] = defaultdict(set)
        # variable -> set of variables that directly depend on it (outgoing edges)
        self._dependents: Dict[str, Set[str]] = defaultdict(set)
        self._all_nodes: Set[str] = set()

    def add_node(self, node: str) -> None:
        self._all_nodes.add(node)

    def add_dependency(self, dependent: str, dependency: str) -> None:
        """
        Registers that `dependent` requires `dependency` to be calculated first.
        (Edge: dependency -> dependent)
        """
        self._all_nodes.add(dependent)
        self._all_nodes.add(dependency)
        self._depends_on[dependent].add(dependency)
        self._dependents[dependency].add(dependent)

    def get_dependencies_for(self, node: str) -> Set[str]:
        """Returns direct inputs required by node."""
        return set(self._depends_on.get(node, set()))

    def get_dependents_for(self, node: str) -> Set[str]:
        """Returns direct outputs that rely on node."""
        return set(self._dependents.get(node, set()))

    def get_ancestors(self, node: str) -> Set[str]:
        """Returns all transitive upstream dependencies that feed into node."""
        ancestors: Set[str] = set()
        queue = deque([node])
        while queue:
            curr = queue.popleft()
            for parent in self._depends_on.get(curr, set()):
                if parent not in ancestors:
                    ancestors.add(parent)
                    queue.append(parent)
        return ancestors

    def get_descendants(self, node: str) -> Set[str]:
        """Returns all transitive downstream variables affected by node."""
        descendants: Set[str] = set()
        queue = deque([node])
        while queue:
            curr = queue.popleft()
            for child in self._dependents.get(curr, set()):
                if child not in descendants:
                    descendants.add(child)
                    queue.append(child)
        return descendants

    def topological_order(self, nodes_subset: Optional[Set[str]] = None) -> List[str]:
        """
        Returns a valid topological calculation order of nodes using Kahn's algorithm.
        Raises CyclicDependencyError if graph contains cycles.
        """
        target_nodes = set(nodes_subset) if nodes_subset is not None else set(self._all_nodes)
        
        # Build adjacency for cycle check: dependency -> list of dependents
        adjacency = {
            u: [v for v in self._dependents.get(u, set()) if v in target_nodes]
            for u in target_nodes
        }
        assert_acyclic(adjacency)

        # In-degree computation within the target set
        in_degree: Dict[str, int] = {u: 0 for u in target_nodes}
        for u in target_nodes:
            for dep in self._depends_on.get(u, set()):
                if dep in target_nodes:
                    in_degree[u] += 1

        # Nodes with in-degree 0 can be processed first (sorted for determinism)
        queue = deque(sorted([node for node, deg in in_degree.items() if deg == 0]))
        order: List[str] = []

        while queue:
            curr = queue.popleft()
            order.append(curr)

            for dependent in sorted(self._dependents.get(curr, set())):
                if dependent in in_degree:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        queue.append(dependent)

        if len(order) < len(target_nodes):
            remaining = target_nodes - set(order)
            raise DependencyResolutionError(
                f"Could not resolve topological order for nodes: {remaining}"
            )
        return order
