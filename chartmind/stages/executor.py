from chartmind.connectors.base import DBConnector
from chartmind.models import QueryResult, SQLDraft


class ExecutorError(RuntimeError):
    pass


class Executor:
    """Stage 4: execute a validated SQL draft against the connected database."""

    def __init__(self, connector: DBConnector, max_rows: int = 200):
        self._connector = connector
        self._max_rows = max_rows

    def run(self, draft: SQLDraft) -> QueryResult:
        if not draft.is_read_only:
            raise ExecutorError(
                "Refusing to execute SQL not flagged as read-only. "
                "Run SQLValidate first to set is_read_only."
            )
        return self._connector.execute(draft.sql, max_rows=self._max_rows)
