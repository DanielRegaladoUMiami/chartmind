from __future__ import annotations

import json
import re

from pydantic import ValidationError

from chartmind.backends.base import InferenceBackend
from chartmind.models import ChartSpec, QueryResult

DEFAULT_CHART_MODEL = "DanielRegaladoCardoso/chart-reasoner-phi3-mini-lora"

PROMPT_TEMPLATE = """You design data visualizations. Given a user question and the schema of a query result, output a JSON chart specification.

Allowed shape:
{{"type": "bar"|"line"|"pie"|"scatter"|"area"|"table",
  "title": str,
  "x": str | null,
  "y": str | list[str] | null,
  "color": str | null,
  "palette": list[str] | null}}

Question: {question}

Result columns:
{columns_text}

Sample rows (up to 5):
{sample_text}

Return ONLY the JSON object, no prose.
JSON:
"""

_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


class ChartReasonError(ValueError):
    pass


def _serialize_columns(data: QueryResult) -> str:
    return "\n".join(f"- {c.name} ({c.dtype})" for c in data.columns)


def _serialize_sample(data: QueryResult, n: int = 5) -> str:
    return json.dumps(data.rows[:n], default=str, indent=2)


def _extract_json(raw: str) -> str:
    raw = raw.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL | re.IGNORECASE)
    if fence:
        return fence.group(1)
    m = _JSON_RE.search(raw)
    if not m:
        raise ChartReasonError(f"No JSON object found in response: {raw[:200]}")
    return m.group(0)


def _fallback_spec(question: str, data: QueryResult) -> ChartSpec:
    """Heuristic spec when LLM output is unusable."""
    cols = data.columns
    if len(cols) == 1:
        return ChartSpec(type="table", title=question[:80])
    numeric_kinds = {"int", "float", "Decimal", "INTEGER", "REAL", "NUMERIC"}
    y_candidates = [c.name for c in cols[1:] if any(k in c.dtype for k in numeric_kinds)]
    return ChartSpec(
        type="bar",
        title=question[:80],
        x=cols[0].name,
        y=y_candidates[0] if y_candidates else cols[1].name,
    )


class ChartReason:
    """Stage 5: (question + result schema/sample) → ChartSpec via LLM, with fallback."""

    def __init__(
        self,
        backend: InferenceBackend,
        model: str = DEFAULT_CHART_MODEL,
        max_new_tokens: int = 200,
        temperature: float = 0.0,
    ):
        self._backend = backend
        self._model = model
        self._max_new_tokens = max_new_tokens
        self._temperature = temperature

    def run(self, question: str, data: QueryResult) -> ChartSpec:
        prompt = PROMPT_TEMPLATE.format(
            question=question.strip(),
            columns_text=_serialize_columns(data),
            sample_text=_serialize_sample(data),
        )
        raw = self._backend.complete(
            prompt,
            model=self._model,
            max_new_tokens=self._max_new_tokens,
            temperature=self._temperature,
            stop=["```\n", "\nQuestion:"],
        )
        try:
            payload = json.loads(_extract_json(raw))
            return ChartSpec.model_validate(payload)
        except (json.JSONDecodeError, ChartReasonError, ValidationError):
            return _fallback_spec(question, data)
