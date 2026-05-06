from pathlib import Path

import pytest

from chartmind import Client, Result
from chartmind.backends.base import InferenceBackend

FIXTURE = Path(__file__).parent / "fixtures" / "chinook.sqlite"


class ScriptedBackend(InferenceBackend):
    """Returns canned responses keyed by which model is called."""

    def __init__(self, by_model: dict[str, str]):
        self.by_model = by_model
        self.calls: list[str] = []

    def complete(self, prompt, *, model, max_new_tokens=512, temperature=0.0, stop=None):
        self.calls.append(model)
        for key, value in self.by_model.items():
            if key in model:
                return value
        raise KeyError(f"No scripted response for model {model}")


@pytest.fixture
def backend():
    return ScriptedBackend(
        by_model={
            "sql-generator": "SELECT Name FROM Artist ORDER BY ArtistId LIMIT 3",
            "chart-reasoner": '{"type":"bar","title":"Top 3 artists","x":"Name","y":"Name"}',
            "svg-renderer": '<svg xmlns="http://www.w3.org/2000/svg"><rect/></svg>',
        }
    )


def test_client_end_to_end(backend):
    cm = Client(db=str(FIXTURE), backend=backend)
    result = cm.ask("Show me 3 artists")
    cm.close()

    assert isinstance(result, Result)
    assert result.question == "Show me 3 artists"
    assert result.sql.is_read_only is True
    assert "Artist" in result.sql.referenced_tables
    assert result.data.row_count == 3
    assert result.data.rows[0]["Name"] == "AC/DC"
    assert result.spec.type == "bar"
    assert "<svg" in result.svg
    assert set(result.timings_ms.keys()) == {
        "schema_probe", "sql_gen", "sql_validate", "execute", "chart_reason", "svg_render"
    }
    assert backend.calls == [
        "DanielRegaladoCardoso/sql-generator-qwen25-coder-7b-lora",
        "DanielRegaladoCardoso/chart-reasoner-phi3-mini-lora",
        "DanielRegaladoCardoso/svg-renderer-deepseek-coder-1.3b-lora",
    ]
