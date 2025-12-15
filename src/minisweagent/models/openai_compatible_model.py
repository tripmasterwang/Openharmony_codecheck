import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import requests
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_not_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from minisweagent.utils.log import logger


@dataclass
class OpenAICompatibleModelConfig:
    model_name: str
    api_base: str
    api_key: str | None = None
    model_kwargs: dict[str, Any] = field(default_factory=dict)


class OpenAICompatibleModel:
    def __init__(self, *, config_class: type = OpenAICompatibleModelConfig, **kwargs):
        self.config = config_class(**kwargs)
        self.n_calls = 0

    @retry(
        stop=stop_after_attempt(10),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        before_sleep=before_sleep_log(logger, logger.level),
        retry=retry_if_not_exception_type((requests.HTTPError, requests.Timeout, requests.ConnectionError, KeyboardInterrupt)),
    )
    def _query(self, messages: list[dict[str, str]], **kwargs) -> dict:
        api_key = self.config.api_key or os.getenv("HUAWEI_API_KEY")
        if not api_key:
            raise ValueError("API key not found. Set HUAWEI_API_KEY in ~/.config/mini-swe-agent/.env")

        base = self.config.api_base.rstrip("/")
        url = f"{base}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.config.model_name,
            "messages": messages,
            **(self.config.model_kwargs | kwargs),
        }
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=120)
        response.raise_for_status()
        return response.json()

    def query(self, messages: list[dict[str, str]], **kwargs) -> dict:
        data = self._query(messages, **kwargs)
        self.n_calls += 1
        content = ""
        try:
            content = data["choices"][0]["message"]["content"] or ""
        except Exception:
            logger.warning(f"Unexpected response structure: {data}")
        return {
            "content": content,
            "extra": {"response": data},
        }

    def get_template_vars(self) -> dict[str, Any]:
        return asdict(self.config) | {"n_model_calls": self.n_calls}

