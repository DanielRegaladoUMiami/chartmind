from __future__ import annotations

import sqlglot
from sqlglot import exp

from chartmind.models import Dialect, SQLDraft

DESTRUCTIVE_NODES: tuple[type[exp.Expression], ...] = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Drop,
    exp.Create,
    exp.Alter,
    exp.TruncateTable,
    exp.Merge,
)


class SQLValidationError(ValueError):
    pass


class SQLValidate:
    """Stage 3: parse SQL with sqlglot, classify read-only, extract referenced tables."""

    def __init__(self, dialect: Dialect):
        self._dialect = dialect

    def run(self, sql: str) -> SQLDraft:
        sql_clean = sql.strip().rstrip(";").strip()
        if not sql_clean:
            raise SQLValidationError("Empty SQL.")

        try:
            parsed = sqlglot.parse(sql_clean, dialect=self._sqlglot_dialect())
        except sqlglot.errors.ParseError as e:
            raise SQLValidationError(f"SQL parse error: {e}") from e

        statements = [s for s in parsed if s is not None]
        if len(statements) != 1:
            raise SQLValidationError(
                f"Expected exactly 1 statement, got {len(statements)}."
            )
        stmt = statements[0]

        is_read_only = not any(
            isinstance(node, DESTRUCTIVE_NODES) for node in stmt.walk()
        )

        tables = sorted({t.name for t in stmt.find_all(exp.Table) if t.name})

        return SQLDraft(
            sql=sql_clean,
            dialect=self._dialect,
            is_read_only=is_read_only,
            referenced_tables=tables,
        )

    def _sqlglot_dialect(self) -> str:
        # sqlglot uses "postgres" too, sqlite/mysql/duckdb match directly
        return self._dialect
