from abc import ABC, abstractmethod

from chartmind.models import Dialect, QueryResult, Schema


class DBConnector(ABC):
    dialect: Dialect

    @abstractmethod
    def introspect(self) -> Schema:
        """Return the schema (tables, columns, keys) of the connected database."""

    @abstractmethod
    def execute(self, sql: str, max_rows: int = 200) -> QueryResult:
        """Execute a read-only SQL query and return results.

        Truncates results at `max_rows` and sets `truncated=True` if exceeded.
        """

    @abstractmethod
    def close(self) -> None:
        """Release any held resources."""
