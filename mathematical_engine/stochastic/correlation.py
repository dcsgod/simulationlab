"""
Multivariate correlation matrix validation and Gaussian copula sampling.
"""
from typing import List, Dict, Tuple, Optional
import numpy as np
from scipy import stats
from mathematical_engine.stochastic.distributions import ParameterDistribution, DistributionType


def is_positive_semidefinite(matrix: np.ndarray, tol: float = 1e-8) -> bool:
    """Checks whether symmetric matrix has all eigenvalues >= -tol."""
    eigenvalues = np.linalg.eigvalsh(matrix)
    return bool(np.all(eigenvalues >= -tol))


def nearest_correlation_matrix(matrix: np.ndarray, tol: float = 1e-6) -> np.ndarray:
    """
    Projects a symmetric matrix onto the set of positive semi-definite correlation matrices
    by clipping negative eigenvalues and rescaling diagonals to 1.0.
    """
    sym = (matrix + matrix.T) / 2.0
    eigenvalues, eigenvectors = np.linalg.eigh(sym)
    eigenvalues = np.maximum(eigenvalues, tol)
    reconstructed = eigenvectors @ np.diag(eigenvalues) @ eigenvectors.T
    
    # Rescale diagonal to 1.0
    inv_diag = 1.0 / np.sqrt(np.diag(reconstructed))
    corr = reconstructed * np.outer(inv_diag, inv_diag)
    np.fill_diagonal(corr, 1.0)
    return corr


class CorrelatedSampler:
    """
    Generates joint random samples honoring marginal distributions and correlation matrix
    using a Gaussian Copula approach.
    """

    def __init__(
        self,
        variable_order: List[str],
        distributions: Dict[str, ParameterDistribution],
        correlation_matrix: Optional[np.ndarray] = None,
    ):
        self.variable_order = variable_order
        self.distributions = distributions
        dim = len(variable_order)

        if correlation_matrix is None:
            self.corr_matrix = np.eye(dim)
        else:
            if correlation_matrix.shape != (dim, dim):
                raise ValueError(f"Correlation matrix shape {correlation_matrix.shape} != ({dim}, {dim})")
            if not is_positive_semidefinite(correlation_matrix):
                self.corr_matrix = nearest_correlation_matrix(correlation_matrix)
            else:
                self.corr_matrix = np.array(correlation_matrix, dtype=float)

        # Cholesky factor L such that L @ L.T = corr_matrix
        self.cholesky_factor = np.linalg.cholesky(self.corr_matrix)

    def sample(self, num_samples: int, seed: Optional[int] = None) -> Dict[str, np.ndarray]:
        """
        Draws `num_samples` correlated vectors.
        """
        rng = np.random.default_rng(seed)
        dim = len(self.variable_order)

        # 1. Generate independent standard normal vectors (dim, num_samples)
        std_normals = rng.standard_normal(size=(dim, num_samples))

        # 2. Correlate standard normals: Z = L @ X
        corr_normals = self.cholesky_factor @ std_normals

        # 3. Transform to uniform margins via standard normal CDF
        uniforms = stats.norm.cdf(corr_normals)

        # 4. Invert uniforms into individual marginal distributions
        results: Dict[str, np.ndarray] = {}
        for idx, var_name in enumerate(self.variable_order):
            dist = self.distributions[var_name]
            u = uniforms[idx, :]

            if dist.dist_type == DistributionType.CONSTANT:
                val = dist.parameters.get("value", 0.0)
                results[var_name] = np.full(num_samples, val, dtype=float)

            elif dist.dist_type == DistributionType.NORMAL:
                loc = dist.parameters["mean"]
                scale = max(dist.parameters["std"], 1e-9)
                results[var_name] = stats.norm.ppf(u, loc=loc, scale=scale)

            elif dist.dist_type == DistributionType.LOGNORMAL:
                mean = dist.parameters.get("mean", 1.0)
                sigma = dist.parameters.get("sigma", 0.2)
                results[var_name] = stats.lognorm.ppf(u, s=sigma, scale=np.exp(mean))

            elif dist.dist_type == DistributionType.UNIFORM:
                low = dist.parameters["min"]
                high = dist.parameters["max"]
                results[var_name] = stats.uniform.ppf(u, loc=low, scale=(high - low))

            elif dist.dist_type == DistributionType.TRIANGULAR:
                left = dist.parameters["min"]
                mode = dist.parameters["mode"]
                right = dist.parameters["max"]
                c = (mode - left) / (right - left)
                results[var_name] = stats.triang.ppf(u, c=c, loc=left, scale=(right - left))

            else:
                results[var_name] = dist.sample(num_samples, rng=rng)

        return results
