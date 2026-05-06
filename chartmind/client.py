from __future__ import annotations

import time
from typing import Literal

from chartmind.backends.base import InferenceBackend
from chartmind.connectors.base import DBConnector
from chartmind.connectors.postgres import PostgresConnector
from chartmind.connectors.sqlite import SQLiteConnector
from chartmind.models import Result
from chartmind.stages.chart_reason import ChartReason
from chartmind.stages.executor import Executor
from chartmind.stages.schema_probe import SchemaProbe
from chartmind.stages.sql_gen import SQLGen
from chartmind.stages.sql_validate import SQLValidate
from chartmind.stages.svg_render import SVGRender

BackendName = Literal["hf-inference"]


def _make_connector(db: str | DBConnector) -> DBConnector:
    if isinstance(db, DBConnector):
        return db
    if db.startswith("sqlite:///"):
        return SQLiteConnector(db.removeprefix("sqlite:///"))
    if db.endswith(".sqlite") or db.endswith(".db"):
        return SQLiteConnector(db)
    if db.startswith(("postgresql://", "postgresql+")):
        return PostgresConnector(db)
    raise ValueError(f"Unrecognized db string: {db!r}")


def _make_backend(name: BackendName | InferenceBackend) -> InferenceBackend:
    if isinstance(name, InferenceBackend):
        return name
    if name == "hf-inference":
        from chartmind.backends.hf_inference import HFInferenceBackend

        return HFInferenceBackend()
    raise ValueError(f"Unknown backend: {name!r}")


class Client:
    """Top-level orchestrator: question + db → Result with SQL, data, spec, SVG."""

    def __init__(
        self,
        db: str | DBConnector,
        backend: BackendName | InferenceBackend = "hf-inference",
        sql_model: str | None = None,
        chart_model: str | None = None,
        svg_model: str | None = None,
        max_rows: int = 200,
    ):
        self._connector = _make_connector(db)
        self._backend = _make_backend(backend)
        sql_kwargs = {"model": sql_model} if sql_model else {}
        chart_kwargs = {"model": chart_model} if chart_model else {}
        svg_kwargs = {"model": svg_model} if svg_model else {}

        self._probe = SchemaProbe(self._connector)
        self._gen = SQLGen(self._backend, **sql_kwargs)
        self._validate = SQLValidate(self._connector.dialect)
        self._exec = Executor(self._connector, max_rows=max_rows)
        self._reason = ChartReason(self._backend, **chart_kwargs)
        self._render = SVGRender(self._backend, **svg_kwargs)

    def ask(self, question: str) -> Result:
        timings: dict[str, int] = {}

        t0 = time.perf_counter()
        schema = self._probe.run()
        timings["schema_probe"] = int((time.perf_counter() - t0) * 1000)

        t0 = time.perf_counter()
        raw_sql = self._gen.run(schema, question)
        timings["sql_gen"] = int((time.perf_counter() - t0) * 1000)

        t0 = time.perf_counter()
        draft = self._validate.run(raw_sql)
        timings["sql_validate"] = int((time.perf_counter() - t0) * 1000)

        t0 = time.perf_counter()
        data = self._exec.run(draft)
        timings["execute"] = int((time.perf_counter() - t0) * 1000)

        t0 = time.perf_counter()
        spec = self._reason.run(question, data)
        timings["chart_reason"] = int((time.perf_counter() - t0) * 1000)

        t0 = time.perf_counter()
        svg = self._render.run(spec, data)
        timings["svg_render"] = int((time.perf_counter() - t0) * 1000)

        return Result(
            question=question,
            sql=draft,
            data=data,
            spec=spec,
            svg=svg,
            timings_ms=timings,
        )

    def close(self) -> None:
        self._connector.close()
