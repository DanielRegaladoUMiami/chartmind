from chartmind import ChartSpec, ColumnSchema, QueryResult, Result, Schema, SQLDraft, Table


def test_schema_roundtrip():
    s = Schema(
        dialect="sqlite",
        tables=[
            Table(
                name="orders",
                columns=[ColumnSchema(name="id", dtype="INTEGER", nullable=False)],
                primary_key=["id"],
            )
        ],
    )
    assert s.model_dump()["tables"][0]["name"] == "orders"


def test_sql_draft_read_only_flag():
    draft = SQLDraft(
        sql="SELECT 1", dialect="sqlite", is_read_only=True, referenced_tables=[]
    )
    assert draft.is_read_only is True


def test_result_assembly():
    r = Result(
        question="how many?",
        sql=SQLDraft(sql="SELECT COUNT(*) FROM t", dialect="sqlite", is_read_only=True),
        data=QueryResult(
            columns=[ColumnSchema(name="c", dtype="INTEGER")],
            rows=[{"c": 1}],
            row_count=1,
        ),
        spec=ChartSpec(type="table", title="count"),
        svg="<svg/>",
    )
    assert r.svg == "<svg/>"
    assert r.data.row_count == 1
