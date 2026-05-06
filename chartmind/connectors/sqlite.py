from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine

from chartmind.connectors.base import DBConnector
from chartmind.models import ColumnSchema, QueryResult, Schema, Table


class SQLiteConnector(DBConnector):
    dialect = "sqlite"

    def __init__(self, path: str | Path):
        url = f"sqlite:///{Path(path).expanduser().resolve()}"
        self._engine: Engine = create_engine(url, future=True)

    def introspect(self) -> Schema:
        insp = inspect(self._engine)
        tables: list[Table] = []
        for tname in insp.get_table_names():
            cols = [
                ColumnSchema(
                    name=c["name"],
                    dtype=str(c["type"]),
                    nullable=bool(c.get("nullable", True)),
                )
                for c in insp.get_columns(tname)
            ]
            pk = insp.get_pk_constraint(tname).get("constrained_columns", []) or []
            fks = [
                {
                    "column": fk["constrained_columns"][0] if fk["constrained_columns"] else "",
                    "ref_table": fk["referred_table"],
                    "ref_column": fk["referred_columns"][0] if fk["referred_columns"] else "",
                }
                for fk in insp.get_foreign_keys(tname)
            ]
            tables.append(Table(name=tname, columns=cols, primary_key=pk, foreign_keys=fks))
        return Schema(dialect=self.dialect, tables=tables)

    def execute(self, sql: str, max_rows: int = 200) -> QueryResult:
        with self._engine.connect() as conn:
            cursor = conn.execute(text(sql))
            keys = list(cursor.keys())
            fetched = cursor.fetchmany(max_rows + 1)
            truncated = len(fetched) > max_rows
            rows_data = fetched[:max_rows]
            rows = [dict(zip(keys, r, strict=False)) for r in rows_data]

        cols = [
            ColumnSchema(name=k, dtype=type(rows[0][k]).__name__ if rows else "unknown")
            for k in keys
        ]
        return QueryResult(
            columns=cols,
            rows=rows,
            row_count=len(rows),
            truncated=truncated,
        )

    def close(self) -> None:
        self._engine.dispose()
