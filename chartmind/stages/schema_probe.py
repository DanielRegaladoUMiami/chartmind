from chartmind.connectors.base import DBConnector
from chartmind.models import Schema


class SchemaProbe:
    """Stage 1: introspect a database connection and return a typed Schema."""

    def __init__(self, connector: DBConnector):
        self._connector = connector

    def run(self) -> Schema:
        return self._connector.introspect()
