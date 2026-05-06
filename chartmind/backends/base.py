from abc import ABC, abstractmethod


class InferenceBackend(ABC):
    """Adapter for any text-in / text-out LLM provider.

    Concrete implementations: HFInferenceBackend, ModalBackend,
    LocalTransformersBackend, OpenAIBackend, etc.
    """

    @abstractmethod
    def complete(
        self,
        prompt: str,
        *,
        model: str,
        max_new_tokens: int = 512,
        temperature: float = 0.0,
        stop: list[str] | None = None,
    ) -> str:
        """Run completion and return raw text output."""
