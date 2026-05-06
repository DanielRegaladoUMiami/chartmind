from __future__ import annotations

import os

from huggingface_hub import InferenceClient

from chartmind.backends.base import InferenceBackend


class HFInferenceBackend(InferenceBackend):
    """Calls the Hugging Face Inference API.

    Reads token from `HF_TOKEN` env var (or `HUGGING_FACE_HUB_TOKEN` fallback)
    unless one is passed explicitly.
    """

    def __init__(self, token: str | None = None, timeout: float = 120.0):
        resolved = (
            token
            or os.getenv("HF_TOKEN")
            or os.getenv("HUGGING_FACE_HUB_TOKEN")
        )
        if not resolved:
            raise RuntimeError(
                "No Hugging Face token found. Set HF_TOKEN in your environment "
                "or pass token=... explicitly. Get one at https://hf.co/settings/tokens"
            )
        self._token = resolved
        self._timeout = timeout

    def complete(
        self,
        prompt: str,
        *,
        model: str,
        max_new_tokens: int = 512,
        temperature: float = 0.0,
        stop: list[str] | None = None,
    ) -> str:
        client = InferenceClient(model=model, token=self._token, timeout=self._timeout)
        return client.text_generation(
            prompt=prompt,
            max_new_tokens=max_new_tokens,
            temperature=max(temperature, 1e-4),  # HF API rejects exact 0
            do_sample=temperature > 0,
            stop_sequences=stop or [],
            return_full_text=False,
        )
