"""
Probability distribution definitions and sampling for stochastic simulation.
"""
from typing import Optional, Dict, Any, Union
from enum import Enum
import numpy as np
from pydantic import BaseModel, Field


class DistributionType(str, Enum):
    NORMAL = "normal"
    LOGNORMAL = "lognormal"
    UNIFORM = "uniform"
    TRIANGULAR = "triangular"
    CONSTANT = "constant"


class ParameterDistribution(BaseModel):
    variable_name: str
    dist_type: DistributionType
    parameters: Dict[str, float] = Field(
        ..., 
        description="Distribution parameters: e.g. {'mean': 10, 'std': 2} or {'min': 5, 'mode': 8, 'max': 12}"
    )

    def sample(self, size: int = 1, rng: Optional[np.random.Generator] = None) -> np.ndarray:
        """Draws independent samples from this univariate distribution."""
        if rng is None:
            rng = np.random.default_rng()

        if self.dist_type == DistributionType.CONSTANT:
            val = self.parameters.get("value", 0.0)
            return np.full(size, val, dtype=float)

        elif self.dist_type == DistributionType.NORMAL:
            loc = self.parameters["mean"]
            scale = max(self.parameters["std"], 1e-9)
            return rng.normal(loc=loc, scale=scale, size=size)

        elif self.dist_type == DistributionType.LOGNORMAL:
            mean = self.parameters.get("mean", 1.0)
            sigma = self.parameters.get("sigma", 0.2)
            return rng.lognormal(mean=mean, sigma=sigma, size=size)

        elif self.dist_type == DistributionType.UNIFORM:
            low = self.parameters["min"]
            high = self.parameters["max"]
            if high <= low:
                raise ValueError(f"Uniform max ({high}) must be > min ({low})")
            return rng.uniform(low=low, high=high, size=size)

        elif self.dist_type == DistributionType.TRIANGULAR:
            left = self.parameters["min"]
            mode = self.parameters["mode"]
            right = self.parameters["max"]
            if not (left <= mode <= right) or left >= right:
                raise ValueError(f"Triangular requires min ({left}) <= mode ({mode}) <= max ({right})")
            return rng.triangular(left=left, mode=mode, right=right, size=size)

        else:
            raise ValueError(f"Unsupported distribution type: {self.dist_type}")
