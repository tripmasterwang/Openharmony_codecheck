import os
from pathlib import Path
from typing import Any

import yaml

from minisweagent.utils.log import logger


def load_model_config(model_name: str) -> dict[str, Any]:
    """Load model configuration from config/models.yaml and environment variables."""
    root = Path(__file__).resolve().parents[3]
    config_path = root / "config" / "models.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Model config file not found: {config_path}")

    config_data = yaml.safe_load(config_path.read_text()) or {}
    models = config_data.get("models", {})
    if model_name not in models:
        raise ValueError(f"Model '{model_name}' not found in {config_path}")

    model_cfg = models[model_name]
    api_key_env = model_cfg.get("api_key_env", "HUAWEI_API_KEY")
    api_key = os.getenv(api_key_env)
    if not api_key:
        raise ValueError(f"API key not found in environment variable '{api_key_env}'. Set it in ~/.config/mini-swe-agent/.env")

    result = {
        "model_name": model_cfg.get("model_name", model_name),
        "api_base": model_cfg["api_base"],
        "api_key": api_key,
        "model_kwargs": model_cfg.get("model_kwargs", {}),
    }
    logger.info(f"Loaded model config for {model_name} from {config_path}")
    return result

