"""
Vector, temporal, and hierarchical aggregation utilities for deterministic models.
"""
from typing import List, Dict, Optional, Sequence
import math
from mathematical_engine.core.errors import NonFiniteValueError


def weighted_average(values: Sequence[float], weights: Sequence[float]) -> float:
    """Computes weighted average sum(w_i * x_i) / sum(w_i)."""
    if len(values) != len(weights):
        raise ValueError(f"Values length ({len(values)}) does not match weights length ({len(weights)})")
    if not values:
        return 0.0

    total_weight = sum(weights)
    if abs(total_weight) < 1e-12:
        raise ValueError("Sum of weights cannot be zero")

    weighted_sum = sum(v * w for v, w in zip(values, weights))
    res = weighted_sum / total_weight
    if math.isnan(res) or math.isinf(res):
        raise NonFiniteValueError("Weighted average produced non-finite result")
    return float(res)


def compound_growth(initial_value: float, rate: float, periods: int) -> float:
    """Computes initial_value * (1 + rate)^periods."""
    if periods < 0:
        raise ValueError("Periods must be non-negative")
    res = initial_value * ((1.0 + rate) ** periods)
    if math.isnan(res) or math.isinf(res):
        raise NonFiniteValueError("Compound growth produced non-finite result")
    return float(res)


def elasticity_impact(base_volume: float, price_ratio: float, elasticity_coeff: float) -> float:
    """
    Constant elasticity demand curve:
    volume_new = base_volume * (price_new / price_base) ^ elasticity_coeff
    where price_ratio = price_new / price_base
    """
    if price_ratio <= 0:
        raise ValueError("Price ratio must be strictly positive")
    res = base_volume * (price_ratio ** elasticity_coeff)
    if math.isnan(res) or math.isinf(res):
        raise NonFiniteValueError("Elasticity impact produced non-finite result")
    return float(res)
