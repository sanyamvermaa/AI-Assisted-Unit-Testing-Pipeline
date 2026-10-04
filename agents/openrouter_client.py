"""OpenRouter client with free-model discovery and basic validation."""

import os
from typing import Any, Dict, List, Optional

import requests


class OpenRouterError(RuntimeError):
    """Raised when an OpenRouter request cannot be completed."""


class OpenRouterClient:
    BASE_URL = "https://openrouter.ai/api/v1"
    DEFAULT_TIMEOUT = (10, 60)

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout=None,
    ):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise OpenRouterError(
                "OPENROUTER_API_KEY is not set. "
                "Set it in the environment before running the pipeline."
            )

        self.model = model or os.getenv("OPENROUTER_MODEL")
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        self._candidates_cache: Optional[List[str]] = None

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://openrouter.ai/",
            "X-Title": "AI-Assisted Unit Testing Pipeline",
        }

    def available_free_models(self) -> List[str]:
        """Return currently listed free chat-capable models."""
        response = requests.get(
            f"{self.BASE_URL}/models",
            headers=self._headers(),
            timeout=self.timeout,
        )
        if response.status_code != 200:
            raise OpenRouterError(
                f"Could not retrieve OpenRouter models "
                f"(HTTP {response.status_code}): {response.text[:500]}"
            )

        data = response.json().get("data", [])
        models = []

        for item in data:
            model_id = item.get("id", "")
            pricing = item.get("pricing") or {}
            prompt_price = pricing.get("prompt")
            completion_price = pricing.get("completion")

            # OpenRouter represents free pricing as zero in many model records.
            if model_id.endswith(":free") or (
                str(prompt_price) in {"0", "0.0"} and
                str(completion_price) in {"0", "0.0"}
            ):
                models.append(model_id)

        return models

    def _candidate_models(self) -> List[str]:
        if self.model:
            return [self.model]
        if self._candidates_cache is not None:
            return self._candidates_cache

        # Prefer common free-model families, then fall back to any free model.
        preferred_tokens = (
            "qwen", "deepseek", "mistral", "gemma", "llama", "nemotron"
        )
        free_models = self.available_free_models()

        preferred = [
            m for m in free_models
            if any(token in m.lower() for token in preferred_tokens)
        ]

        # Keep the list short so an unavailable/slow model does not cause
        # an excessive number of retries.
        ordered = []
        for model in preferred + free_models:
            if model not in ordered:
                ordered.append(model)
        self._candidates_cache = ordered[:8]
        return self._candidates_cache

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 1500,
        exclude_models: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Send a chat-completion request and return text plus model metadata."""
        candidates = [
            m for m in self._candidate_models()
            if not exclude_models or m not in exclude_models
        ]
        if not candidates:
            raise OpenRouterError("No free OpenRouter models were found.")

        errors = []

        for model in candidates:
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }

            try:
                response = requests.post(
                    f"{self.BASE_URL}/chat/completions",
                    headers=self._headers(),
                    json=payload,
                    timeout=self.timeout,
                )

                if response.status_code != 200:
                    errors.append(
                        f"{model}: HTTP {response.status_code}: "
                        f"{response.text[:300]}"
                    )
                    continue

                data = response.json()
                choices = data.get("choices") or []
                if not choices:
                    errors.append(f"{model}: response contained no choices")
                    continue

                content = choices[0].get("message", {}).get("content")
                if not isinstance(content, str) or not content.strip():
                    errors.append(f"{model}: empty model response")
                    continue

                return {
                    "text": content.strip(),
                    "model": data.get("model") or model,
                    "raw": data,
                }

            except requests.RequestException as exc:
                errors.append(f"{model}: {exc}")

        raise OpenRouterError(
            "All OpenRouter model attempts failed:\n" + "\n".join(errors)
        )
