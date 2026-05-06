from __future__ import annotations

import re

from chartmind.backends.base import InferenceBackend
from chartmind.models import Schema

DEFAULT_SQL_MODEL = "DanielRegaladoCardoso/sql-generator-qwen25-coder-7b-lora"

PROMPT_TEMPLATE = """You are an expert {dialect} analyst. Given the schema below, write a single SQL query that answers the user's question. Return ONLY the SQL — no markdown, no comments, no explanation.

Schema:
{schema_text}

Question: {question}

SQL:
"""


def _serialize_schema(schema: Schema) -> str:
    lines = []
    for t in schema.tables:
        cols = ", ".join(f"{c.name} {c.dtype}" for c in t.columns)
        pk = f" PK={'+'.join(t.primary_key)}" if t.primary_key else ""
        fks = (
            " FKS=[" + ", ".join(f"{fk['column']}->{fk['ref_table']}.{fk['ref_column']}" for fk in t.foreign_keys) + "]"
            if t.foreign_keys
            else ""
        )
        lines.append(f"TABLE {t.name} ({cols}){pk}{fks}")
    return "\n".join(lines)


_FENCE_RE = re.compile(r"```(?:sql)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def _clean_sql(raw: str) -> str:
    """Strip markdown fences, leading 'SQL:' labels, trailing prose."""
    raw = raw.strip()
    m = _FENCE_RE.search(raw)
    if m:
        raw = m.group(1).strip()
    raw = re.sub(r"^\s*sql\s*:\s*", "", raw, flags=re.IGNORECASE)
    # take only up to the first blank line if model rambled afterwards
    raw = raw.split("\n\n")[0].strip()
    return raw


class SQLGen:
    """Stage 2: convert (Schema + question) → raw SQL string via LLM."""

    def __init__(
        self,
        backend: InferenceBackend,
        model: str = DEFAULT_SQL_MODEL,
        max_new_tokens: int = 400,
        temperature: float = 0.0,
    ):
        self._backend = backend
        self._model = model
        self._max_new_tokens = max_new_tokens
        self._temperature = temperature

    def run(self, schema: Schema, question: str) -> str:
        prompt = PROMPT_TEMPLATE.format(
            dialect=schema.dialect,
            schema_text=_serialize_schema(schema),
            question=question.strip(),
        )
        raw = self._backend.complete(
            prompt,
            model=self._model,
            max_new_tokens=self._max_new_tokens,
            temperature=self._temperature,
            stop=["\n\nQuestion:", "\n\nSchema:"],
        )
        return _clean_sql(raw)
