# chartmind

> Natural language → SQL → chart spec → SVG. A composable pipeline for conversational data visualization.

[![PyPI](https://img.shields.io/pypi/v/chartmind.svg)](https://pypi.org/project/chartmind/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-pre--alpha-orange.svg)]()

`chartmind` turns a question and a database connection into a rendered chart, using three small fine-tuned models chained together:

1. **Question + schema → SQL** (Qwen 2.5 Coder 7B LoRA)
2. **Query result → chart spec JSON** (Phi-3 Mini LoRA)
3. **Chart spec → SVG** (DeepSeek Coder 1.3B LoRA)

Unlike text-to-SQL libraries that stop at a table, `chartmind` ends at a renderable visualization. Unlike plotting libraries, it starts from natural language.

## Status

Pre-alpha. APIs will change. Currently working toward v0.1 (target: 5 weeks).

## Quickstart (target API — not yet implemented)

```python
import chartmind

cm = chartmind.Client(
    db="sqlite:///northwind.db",
    backend="hf-inference",  # uses Hugging Face Inference API
)

result = cm.ask("What were the top 5 product categories by revenue in 1997?")

print(result.sql.sql)         # SELECT ... FROM ... GROUP BY ... LIMIT 5
print(result.data.row_count)  # 5
print(result.spec.type)       # "bar"
result.show()                 # opens the SVG in your browser / Jupyter
```

## Why three models, not one big one?

Each subtask is small enough that a 1-7B parameter LoRA does it well. The chain runs on cheap inference and stays auditable: you can inspect the SQL before it executes, the spec before it renders, and swap any stage for a different model.

## Roadmap

| Version | Scope |
|---|---|
| v0.1 | sqlite + postgres, HF Inference backend, end-to-end demo |
| v0.2 | sqlglot validation, caching, error UX, matplotlib fallback |
| v0.3 | DuckDB + MySQL, vLLM backend, LangChain / Claude tool adapters, CLI |
| v0.4 | Eval harness, benchmarks vs. existing text-to-SQL libraries |
| v1.0 | Async client, Snowflake + BigQuery, hosted docs |

## Models and datasets

- Models: [sql-generator-qwen25-coder-7b-lora](https://hf.co/DanielRegaladoCardoso/sql-generator-qwen25-coder-7b-lora), [chart-reasoner-phi3-mini-lora](https://hf.co/DanielRegaladoCardoso/chart-reasoner-phi3-mini-lora), [svg-renderer-deepseek-coder-1.3b-lora](https://hf.co/DanielRegaladoCardoso/svg-renderer-deepseek-coder-1.3b-lora)
- Datasets: [text-to-sql-mix-v2](https://hf.co/datasets/DanielRegaladoCardoso/text-to-sql-mix-v2), [chart-reasoning-mix-v1](https://hf.co/datasets/DanielRegaladoCardoso/chart-reasoning-mix-v1), [svg-chart-render-v1](https://hf.co/datasets/DanielRegaladoCardoso/svg-chart-render-v1)

## License

Apache 2.0 — see [LICENSE](LICENSE).
