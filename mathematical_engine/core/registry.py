"""
Model registry providing discovery, retrieval, and capability filtering.
"""
from typing import Dict, List, Optional
from mathematical_engine.core.base_model import BaseSimulationModel, ModelCapability
from mathematical_engine.core.errors import ModelNotFoundError, CapabilityMismatchError


class ModelRegistry:
    """
    Central repository for simulation models and analytical algorithms.
    """

    def __init__(self):
        self._models: Dict[str, BaseSimulationModel] = {}

    def register(self, model: BaseSimulationModel) -> None:
        """Registers a simulation model instance."""
        if not isinstance(model, BaseSimulationModel):
            raise TypeError(f"Expected BaseSimulationModel, got {type(model)}")
        self._models[model.id] = model

    def get(self, model_id: str) -> BaseSimulationModel:
        """Retrieves a model by its identifier or raises ModelNotFoundError."""
        if model_id not in self._models:
            raise ModelNotFoundError(f"Model with id '{model_id}' is not registered.")
        return self._models[model_id]

    def has(self, model_id: str) -> bool:
        return model_id in self._models

    def list_all(self) -> List[BaseSimulationModel]:
        return list(self._models.values())

    def find_by_capability(self, capability: ModelCapability) -> List[BaseSimulationModel]:
        """Returns all models possessing the specified capability."""
        return [
            m for m in self._models.values()
            if capability in m.metadata.capabilities
        ]

    def find_producers_for(self, variable_name: str) -> List[BaseSimulationModel]:
        """Finds all models that compute/produce a specific variable output."""
        return [
            m for m in self._models.values()
            if variable_name in m.metadata.produced_outputs
        ]

    def find_consumers_for(self, variable_name: str) -> List[BaseSimulationModel]:
        """Finds all models that require a specific variable input."""
        return [
            m for m in self._models.values()
            if variable_name in m.metadata.required_inputs
        ]

    def clear(self) -> None:
        self._models.clear()


# Default global registry instance
default_model_registry = ModelRegistry()
