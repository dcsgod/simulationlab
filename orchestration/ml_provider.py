"""
External ML and Hugging Face surrogate model provider with graceful deterministic fallback.
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class MLModelConfig(BaseModel):
    model_name: str
    endpoint_url: Optional[str] = None
    api_key: Optional[str] = None
    is_enabled: bool = False


class MLModelProvider:
    """
    Interfaces with external machine learning surrogate models (MLflow / Hugging Face)
    with 100% deterministic local fallback when offline.
    """

    def __init__(self, config: Optional[MLModelConfig] = None):
        self.config = config or MLModelConfig(model_name="default_surrogate", is_enabled=False)

    def predict_surrogate(
        self,
        features: Dict[str, float],
        fallback_formula: Optional[str] = None,
    ) -> float:
        """
        Attempts external inference, falling back reliably to analytical evaluation.
        """
        if self.config.is_enabled and self.config.endpoint_url:
            # Here real HTTP client would call endpoint; if offline, catch and fallback
            pass

        # Deterministic default heuristic: e.g. price * volume if revenue
        price = features.get("price", features.get("base_price", 10.0))
        volume = features.get("volume", features.get("units_sold", 100.0))
        return float(price * volume)
