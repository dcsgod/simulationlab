"""
Cycle detection algorithms for computational graphs and dependency DAGs.
"""
from typing import Dict, List, Set, Optional
from mathematical_engine.core.errors import CyclicDependencyError


def find_cycle(adjacency_list: Dict[str, List[str]]) -> Optional[List[str]]:
    """
    Detects any directed cycle in the graph.
    Returns the cycle as an ordered list of node keys (e.g., ['A', 'B', 'C', 'A']),
    or None if acyclic.
    
    adjacency_list: mapping from node to list of successor/dependent nodes.
    """
    visited: Set[str] = set()
    rec_stack: List[str] = []
    rec_set: Set[str] = set()

    def dfs(node: str) -> Optional[List[str]]:
        visited.add(node)
        rec_stack.append(node)
        rec_set.add(node)

        for neighbor in adjacency_list.get(node, []):
            if neighbor not in visited:
                cycle = dfs(neighbor)
                if cycle:
                    return cycle
            elif neighbor in rec_set:
                # Cycle found: slice rec_stack from first occurrence of neighbor
                idx = rec_stack.index(neighbor)
                return rec_stack[idx:] + [neighbor]

        rec_stack.pop()
        rec_set.remove(node)
        return None

    # Iterate over all nodes in sorted order for deterministic cycle detection
    for node in sorted(adjacency_list.keys()):
        if node not in visited:
            cycle = dfs(node)
            if cycle:
                return cycle
    return None


def assert_acyclic(adjacency_list: Dict[str, List[str]]) -> None:
    """
    Raises CyclicDependencyError if any directed cycle is present.
    """
    cycle = find_cycle(adjacency_list)
    if cycle:
        path_str = " -> ".join(cycle)
        raise CyclicDependencyError(f"Cyclic dependency detected: {path_str}")
