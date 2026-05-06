from chartmind.backends.base import InferenceBackend
from chartmind.models import ChartSpec, ColumnSchema, QueryResult
from chartmind.stages.chart_reason import ChartReason, _extract_json, _fallback_spec


class FakeBackend(InferenceBackend):
    def __init__(self, response: str):
        self.response = response

    def complete(self, prompt, *, model, max_new_tokens=512, temperature=0.0, stop=None):
        return self.response


DATA = QueryResult(
    columns=[
        ColumnSchema(name="region", dtype="TEXT"),
        ColumnSchema(name="sales", dtype="INTEGER"),
    ],
    rows=[{"region": "North", "sales": 100}, {"region": "South", "sales": 80}],
    row_count=2,
)


def test_extract_json_from_fenced_block():
    raw = '```json\n{"type":"bar","title":"x"}\n```'
    assert _extract_json(raw) == '{"type":"bar","title":"x"}'


def test_extract_json_bare():
    assert '{"type":"bar"' in _extract_json('prefix {"type":"bar","title":"x"} suffix')


def test_chart_reason_parses_valid_json():
    backend = FakeBackend('{"type":"bar","title":"Sales by region","x":"region","y":"sales"}')
    spec = ChartReason(backend).run("Sales by region", DATA)
    assert spec.type == "bar"
    assert spec.x == "region"
    assert spec.y == "sales"


def test_chart_reason_falls_back_on_invalid_json():
    backend = FakeBackend("not json at all")
    spec = ChartReason(backend).run("Sales by region", DATA)
    assert isinstance(spec, ChartSpec)
    assert spec.type in ("bar", "table")


def test_chart_reason_falls_back_on_invalid_spec_type():
    backend = FakeBackend('{"type":"holographic","title":"x"}')
    spec = ChartReason(backend).run("q", DATA)
    assert spec.type in ("bar", "table")


def test_fallback_picks_numeric_y():
    spec = _fallback_spec("Sales by region", DATA)
    assert spec.x == "region"
    assert spec.y == "sales"
