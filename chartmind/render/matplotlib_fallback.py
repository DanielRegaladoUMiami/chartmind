from __future__ import annotations

import io

from chartmind.models import ChartSpec, QueryResult


def render_spec_to_svg(spec: ChartSpec, data: QueryResult) -> str:
    """Deterministic fallback: render a ChartSpec + data to SVG using matplotlib.

    Used when the LLM-generated SVG fails validation. Always succeeds for
    bar/line/scatter/area/pie/table given matching columns.
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows = data.rows
    fig, ax = plt.subplots(figsize=(8, 5))

    if spec.type == "table" or not rows:
        ax.axis("off")
        col_names = [c.name for c in data.columns]
        cell_text = [[str(r.get(c, "")) for c in col_names] for r in rows[:20]]
        ax.table(cellText=cell_text or [[""]], colLabels=col_names, loc="center")
        ax.set_title(spec.title)
    elif spec.type in ("bar", "line", "area", "scatter"):
        x_col = spec.x or data.columns[0].name
        y_cols = (
            [spec.y] if isinstance(spec.y, str)
            else (spec.y or [data.columns[1].name if len(data.columns) > 1 else data.columns[0].name])
        )
        xs = [r.get(x_col) for r in rows]
        for y in y_cols:
            ys = [r.get(y) for r in rows]
            if spec.type == "bar":
                ax.bar(range(len(xs)), ys, label=str(y))
                ax.set_xticks(range(len(xs)))
                ax.set_xticklabels([str(x) for x in xs], rotation=45, ha="right")
            elif spec.type == "line":
                ax.plot(xs, ys, marker="o", label=str(y))
            elif spec.type == "area":
                ax.fill_between(range(len(xs)), ys, alpha=0.4, label=str(y))
            elif spec.type == "scatter":
                ax.scatter(xs, ys, label=str(y))
        ax.set_xlabel(x_col)
        ax.set_ylabel(", ".join(str(y) for y in y_cols))
        if len(y_cols) > 1:
            ax.legend()
        ax.set_title(spec.title)
    elif spec.type == "pie":
        label_col = spec.x or data.columns[0].name
        value_col = (
            spec.y if isinstance(spec.y, str) and spec.y
            else (data.columns[1].name if len(data.columns) > 1 else data.columns[0].name)
        )
        labels = [str(r.get(label_col)) for r in rows]
        values = [r.get(value_col) for r in rows]
        ax.pie(values, labels=labels, autopct="%1.1f%%")
        ax.set_title(spec.title)

    fig.tight_layout()
    buf = io.StringIO()
    fig.savefig(buf, format="svg")
    plt.close(fig)
    return buf.getvalue()
