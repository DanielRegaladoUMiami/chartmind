from pathlib import Path

import pytest

from chartmind.connectors.sqlite import SQLiteConnector
from chartmind.stages.executor import Executor, ExecutorError
from chartmind.stages.schema_probe import SchemaProbe
from chartmind.models import SQLDraft

FIXTURE = Path(__file__).parent / "fixtures" / "chinook.sqlite"


@pytest.fixture
def conn():
    c = SQLiteConnector(FIXTURE)
    yield c
    c.close()


def test_schema_probe_finds_chinook_tables(conn):
    schema = SchemaProbe(conn).run()
    names = {t.name for t in schema.tables}
    assert {"Album", "Artist", "Track", "Invoice", "Customer"} <= names
    assert schema.dialect == "sqlite"


def test_schema_probe_columns_and_keys(conn):
    schema = SchemaProbe(conn).run()
    album = next(t for t in schema.tables if t.name == "Album")
    col_names = {c.name for c in album.columns}
    assert {"AlbumId", "Title", "ArtistId"} <= col_names
    assert "AlbumId" in album.primary_key
    assert any(fk["ref_table"] == "Artist" for fk in album.foreign_keys)


def test_executor_runs_select(conn):
    draft = SQLDraft(
        sql="SELECT Name FROM Artist ORDER BY ArtistId LIMIT 3",
        dialect="sqlite",
        is_read_only=True,
    )
    result = Executor(conn).run(draft)
    assert result.row_count == 3
    assert result.rows[0]["Name"] == "AC/DC"
    assert result.truncated is False


def test_executor_truncates(conn):
    draft = SQLDraft(
        sql="SELECT Name FROM Artist", dialect="sqlite", is_read_only=True
    )
    result = Executor(conn, max_rows=5).run(draft)
    assert result.row_count == 5
    assert result.truncated is True


def test_executor_refuses_non_readonly(conn):
    draft = SQLDraft(
        sql="DELETE FROM Artist", dialect="sqlite", is_read_only=False
    )
    with pytest.raises(ExecutorError):
        Executor(conn).run(draft)
