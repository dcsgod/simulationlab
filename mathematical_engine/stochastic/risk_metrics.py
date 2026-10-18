"""
Statistical risk metrics, Value-at-Risk (VaR), and Conditional Value-at-Risk (CVaR).
"""
from typing import Dict, Optional, Sequence
import numpy as np
from mathematical_engine.contracts.results import DistributionSummary


def compute_distribution_summary(
    name: str,
    samples: np.ndarray,
    baseline_value: Optional[float] = None,
) -> DistributionSummary:
    """
    Computes statistical moments and empirical percentiles for a 1D sample array.
    """
    arr = np.asarray(samples, dtype=float)
    if arr.size == 0:
        raise ValueError(f"Cannot compute risk metrics on empty samples array for {name}")

    mean_val = float(np.mean(arr))
    std_val = float(np.std(arr, ddof=1)) if arr.size > 1 else 0.0
    median_val = float(np.median(arr))
    min_val = float(np.min(arr))
    max_val = float(np.max(arr))

    p5 = float(np.percentile(arr, 5))
    p25 = float(np.percentile(arr, 25))
    p75 = float(np.percentile(arr, 75))
    p95 = float(np.percentile(arr, 95))

    # VaR 95% as downside threshold (5th percentile)
    var_95 = p5

    # CVaR 95% (Expected Shortfall below 5th percentile)
    tail = arr[arr <= p5]
    cvar_95 = float(np.mean(tail)) if tail.size > 0 else p5

    return DistributionSummary(
        variable_name=name,
        mean=mean_val,
        std=std_val,
        median=median_val,
        min_val=min_val,
        max_val=max_val,
        p5=p5,
        p25=p25,
        p75=p75,
        p95=p95,
        var_95=var_95,
        cvar_95=cvar_95,
        samples_count=int(arr.size),
    )


def compute_breach_probability(samples: np.ndarray, threshold: float, condition: str = "less_than") -> float:
    """
    Computes fraction of samples that violate a threshold condition.
    condition: 'less_than' (e.g. profit < 0) or 'greater_than' (e.g. cost > 100).
    """
    arr = np.asarray(samples, dtype=float)
    if arr.size == 0:
        return 0.0
    if condition == "less_than":
        return float(np.mean(arr < threshold))
    elif condition == "greater_than":
        return float(np.mean(arr > threshold))
    else:
        raise ValueError(f"Unknown breach condition: {condition}")
