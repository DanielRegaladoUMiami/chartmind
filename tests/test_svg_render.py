from chartmind.backends.base import InferenceBackend
from chartmind.models import ChartSpec, ColumnSchema, QueryResult
from chartmind.stages.svg_render import SVGRender, _is_valid_svg


class FakeBackend(InferenceBackend):
    def __init__(self, response: str, raise_exc: Exception | None = None):
        self.response = response
        self.raise_exc = raise_exc

    def complete(self, prompt, *, model, max_new_tokens=512, temperature=0.0, stop=None):
        if self.raise_exc:
            raise self.raise_exc
        return self.response


SPEC = ChartSpec(type="bar", title="t", x="region", y="sales")
DATA = QueryResult(
    columns=[
        ColumnSchema(name="region", dtype="TEXT"),
        ColumnSchema(name="sales", dtype="INTEGER"),
    ],
    rows=[{"region": "N", "sales": 1}, {"region": "S", "sales": 2}],
    row_count=2,
)


def test_is_valid_svg_true():
    assert _is_valid_svg('<svg xmlns="http://www.w3.org/2000/svg"><rect/></svg>')


def test_is_valid_svg_false():
    assert _is_valid_svg("<svg><unclosed>") is False
    assert _is_valid_svg("not xml") is False


def test_svg_render_uses_llm_output_when_valid():
    backend = FakeBackend('<svg xmlns="http://www.w3.org/2000/svg"><rect width="10"/></svg>')
    out = SVGRender(backend).run(SPEC, DATA)
    assert "<rect" in out


def test_svg_render_falls_back_when_llm_returns_garbage():
    backend = FakeBackend("LOL no SVG here")
    out = SVGRender(backend).run(SPEC, DATA)
    assert out.startswith("<?xml") or out.lstrip().startswith("<svg")


def test_svg_render_falls_back_when_backend_raises():
    backend = FakeBackend("", raise_exc=RuntimeError("network down"))
    out = SVGRender(backend).run(SPEC, DATA)
    assert "<svg" in out
