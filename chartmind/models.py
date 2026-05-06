from typing import Any, Literal

from pydantic import BaseModel, Field

Dialect = Literal["postgres", "sqlite", "mysql", "duckdb"]
ChartType = Literal["bar", "line", "pie", "scatter", "area", "table"]


class ColumnSchema(BaseModel):
    name: str
    dtype: str
    nullable: bool = True
    sample_values: list[Any] = Field(default_factory=list)


class Table(BaseModel):
    name: str
    columns: list[ColumnSchema]
    primary_key: list[str] = Field(default_factory=list)
    foreign_keys: list[dict[str, str]] = Field(default_factory=list)


class Schema(BaseModel):
    tables: list[Table]
    dialect: Dialect


class SQLDraft(BaseModel):
    sql: str
    dialect: Dialect
    is_read_only: bool
    referenced_tables: list[str] = Field(default_factory=list)


class QueryResult(BaseModel):
    columns: list[ColumnSchema]
    rows: list[dict[str, Any]]
    row_count: int
    truncated: bool = False


class ChartSpec(BaseModel):
    type: ChartType
    title: str
    x: str | None = None
    y: str | list[str] | None = None
    color: str | None = None
    palette: list[str] | None = None


class Result(BaseModel):
    question: str
    sql: SQLDraft
    data: QueryResult
    spec: ChartSpec
    svg: str
    timings_ms: dict[str, int] = Field(default_factory=dict)
    cache_hits: dict[str, bool] = Field(default_factory=dict)

    def show(self) -> None:
        try:
            from IPython.display import SVG, display

            display(SVG(self.svg))
        except ImportError:
            import tempfile
            import webbrowser
            from pathlib import Path

            path = Path(tempfile.mkstemp(suffix=".svg")[1])
            path.write_text(self.svg)
            webbrowser.open(f"file://{path}")
