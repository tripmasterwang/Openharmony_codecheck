"""This file provides convenience functions for selecting models.
You can ignore this file completely if you explicitly set your model in your run script.
"""

import copy
import importlib
import os
from minisweagent import Model
from minisweagent.models.model_config_loader import load_model_config


class GlobalModelStats:
    """Minimal tracker for call counts (cost tracking removed)."""

    def __init__(self):
        self._n_calls = 0

    def add(self, count: float = 0.0) -> None:
        self._n_calls += 1

    @property
    def n_calls(self) -> int:
        return self._n_calls

    @property
    def cost(self) -> float:
        return 0.0


GLOBAL_MODEL_STATS = GlobalModelStats()


def get_model(input_model_name: str | None = None, config: dict | None = None) -> Model:
    """Get an initialized model object from any kind of user input or settings."""
    resolved_model_name = get_model_name(input_model_name, config)
    if config is None:
        config = {}
    config = copy.deepcopy(config)
    config["model_name"] = resolved_model_name

    # Default to openai_compatible if not specified
    model_class_name = config.pop("model_class", "") or "openai_compatible"

    # Load model config from models.yaml when using openai_compatible
    if model_class_name == "openai_compatible":
        loaded = load_model_config(resolved_model_name)
        merged_kwargs = loaded.get("model_kwargs", {}) | config.get("model_kwargs", {})
        config.update(
            {
                "model_name": loaded["model_name"],
                "api_base": loaded["api_base"],
                "api_key": loaded.get("api_key"),
                "model_kwargs": merged_kwargs,
            }
        )

    model_class = get_model_class(resolved_model_name, model_class_name)

    if (
        any(s in resolved_model_name.lower() for s in ["anthropic", "sonnet", "opus", "claude"])
        and "set_cache_control" not in config
    ):
        # Select cache control for Anthropic models by default
        config["set_cache_control"] = "default_end"

    return model_class(**config)


def get_model_name(input_model_name: str | None = None, config: dict | None = None) -> str:
    """Get a model name from any kind of user input or settings."""
    if config is None:
        config = {}
    if input_model_name:
        return input_model_name
    if from_config := config.get("model_name"):
        return from_config
    if from_env := os.getenv("MSWEA_MODEL_NAME"):
        return from_env
    raise ValueError("No default model set. Please run `mini-extra config setup` to set one.")


_MODEL_CLASS_MAPPING = {
    "openai_compatible": "minisweagent.models.openai_compatible_model.OpenAICompatibleModel",
    "deterministic": "minisweagent.models.test_models.DeterministicModel",
}


def get_model_class(model_name: str, model_class: str = "") -> type:
    """Select the best model class.

    If a model_class is provided (as shortcut name, or as full import path,
    e.g., "anthropic" or "minisweagent.models.anthropic.AnthropicModel"),
    it takes precedence over the `model_name`.
    Otherwise, the model_name is used to select the best model class.
    """
    if model_class:
        full_path = _MODEL_CLASS_MAPPING.get(model_class, model_class)
        try:
            module_name, class_name = full_path.rsplit(".", 1)
            module = importlib.import_module(module_name)
            return getattr(module, class_name)
        except (ValueError, ImportError, AttributeError):
            msg = f"Unknown model class: {model_class} (resolved to {full_path}, available: {_MODEL_CLASS_MAPPING})"
            raise ValueError(msg)

    # Default to OpenAICompatibleModel
    from minisweagent.models.openai_compatible_model import OpenAICompatibleModel

    return OpenAICompatibleModel
