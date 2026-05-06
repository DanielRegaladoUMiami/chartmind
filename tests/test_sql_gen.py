from chartmind.backends.base import InferenceBackend
from chartmind.models import ColumnSchema, Schema, Table
from chartmind.stages.sql_gen import SQLGen, _clean_sql, _serialize_schema


class FakeBackend(InferenceBackend):
    def __init__(self, response: str):
        self.response = response
        self.last_prompt: str | None = None
        self.last_kwargs: dict | None = None

    def complete(self, prompt, *, model, max_new_tokens=512, temperature=0.0, stop=None):
        self.last_prompt = prompt
        self.last_kwargs = {
            "model": model,
            "max_new_tokens": max_new_tokens,
            "temperature": temperature,
            "stop": stop,
        }
        return self.response


SCHEMA = Schema(
    dialect="sqlite",
    tables=[
        Table(
            name="Artist",
            columns=[
                ColumnSchema(name="ArtistId", dtype="INTEGER", nullable=False),
                ColumnSchema(name="Name", dtype="TEXT"),
            ],
            primary_key=["ArtistId"],
        ),
        Table(
            name="Album",
            columns=[
                ColumnSchema(name="AlbumId", dtype="INTEGER", nullable=False),
                ColumnSchema(name="Title", dtype="TEXT"),
                ColumnSchema(name="ArtistId", dtype="INTEGER", nullable=False),
            ],
            primary_key=["AlbumId"],
            foreign_keys=[{"column": "ArtistId", "ref_table": "Artist", "ref_column": "ArtistId"}],
        ),
    ],
)


def test_serialize_schema_includes_tables_and_keys():
    text = _serialize_schema(SCHEMA)
    assert "TABLE Artist" in text
    assert "TABLE Album" in text
    assert "PK=ArtistId" in text
    assert "ArtistId->Artist.ArtistId" in text


def test_clean_sql_strips_markdown_fence():
    raw = "```sql\nSELECT * FROM Artist\n```"
    assert _clean_sql(raw) == "SELECT * FROM Artist"


def test_clean_sql_strips_sql_label():
    assert _clean_sql("SQL: SELECT 1") == "SELECT 1"


def test_clean_sql_drops_trailing_prose():
    raw = "SELECT 1\n\nThis query returns the number 1."
    assert _clean_sql(raw) == "SELECT 1"


def test_sql_gen_calls_backend_with_prompt_and_returns_clean_sql():
    backend = FakeBackend("```sql\nSELECT Name FROM Artist LIMIT 5\n```")
    gen = SQLGen(backend, model="test/model")
    result = gen.run(SCHEMA, "Show me 5 artists")
    assert result == "SELECT Name FROM Artist LIMIT 5"
    assert "Show me 5 artists" in backend.last_prompt
    assert "TABLE Artist" in backend.last_prompt
    assert backend.last_kwargs["model"] == "test/model"
