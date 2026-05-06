from __future__ import annotations

import json
import re

from lxml import etree

from chartmind.backends.base import InferenceBackend
from chartmind.models import ChartSpec, QueryResult
from chartmind.render.matplotlib_fallback import render_spec_to_svg

DEFAULT_SVG_MODEL = "DanielRegaladoCardoso/svg-renderer-deepseek-coder-1.3b-lora"

PROMPT_TEMPLATE = """You generate SVG markup from a chart specification and the data to plot.

Spec:
{spec_json}

Data ({n} rows):
{data_json}

Return ONLY a single self-contained <svg>...</svg> element. No markdown, no prose.
SVG:
"""


def _extract_svg(raw: str) -> str | None:
    m = re.search(r"<svg[\s\S]*?</svg>", raw, re.IGNORECASE)
    return m.group(0) if m else None


def _is_valid_svg(svg: str) -> bool:
    try:
        root = etree.fromstring(svg.encode("utf-8"))
        return etree.QName(root).localname.lower() == "svg"
    except etree.XMLSyntaxError:
        return False


class SVGRender:
    """Stage 6: ChartSpec + data → SVG string, with matplotlib fallback."""

    def __init__(
        self,
        backend: InferenceBackend,
        model: str = DEFAULT_SVG_MODEL,
        max_new_tokens: int = 1500,
        temperature: float = 0.0,
        max_data_rows: int = 50,
    ):
        self._backend = backend
        self._model = model
        self._max_new_tokens = max_new_tokens
        self._temperature = temperature
        self._max_data_rows = max_data_rows

    def run(self, spec: ChartSpec, data: QueryResult) -> str:
        prompt = PROMPT_TEMPLATE.format(
            spec_json=spec.model_dump_json(),
            n=min(len(data.rows), self._max_data_rows),
            data_json=json.dumps(data.rows[: self._max_data_rows], default=str),
        )
        try:
            raw = self._backend.complete(
                prompt,
                model=self._model,
                max_new_tokens=self._max_new_tokens,
                temperature=self._temperature,
                stop=["</svg>\n\n"],
            )
            svg = _extract_svg(raw)
            if svg and _is_valid_svg(svg):
                return svg
        except Exception:
            pass
        return render_spec_to_svg(spec, data)
