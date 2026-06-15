# marketiq

[![CI](https://github.com/vFoex/marketiq/actions/workflows/ci.yml/badge.svg)](https://github.com/vFoex/marketiq/actions/workflows/ci.yml)

Real-time crypto market-data pipeline with a tool-calling GenAI assistant.

marketiq ingests Binance's live trade stream, computes rolling metrics (VWAP,
volatility, volume) and price/volume-spike anomalies in deterministic, tested
code, and exposes an LLM assistant that answers natural-language questions about
the live and recent data.

> **The assistant never does arithmetic.** Every number it reports comes from
> deterministic, unit-tested query functions that it calls as tools — the
> language model selects and orchestrates, tested code computes. Putting that
> boundary in the right place is the whole point of this project.

## Status

Early development — **Phase 0 (project skeleton)**. See the [roadmap](#roadmap).

## Tech stack

- **Language:** Python 3.12 — fully type-hinted, `ruff` + `mypy --strict` clean
- **Backend:** FastAPI (REST + WebSocket)
- **Storage:** TimescaleDB (PostgreSQL + time-series hypertables)
- **GenAI:** Claude Haiku 4.5 behind a model-agnostic interface (AWS Bedrock in
  deployment, Anthropic API in local dev)
- **Frontend:** Angular — minimal dashboard (price chart, anomaly feed,
  assistant panel)
- **Tooling:** uv, pre-commit, GitHub Actions

## Getting started

Requires [uv](https://docs.astral.sh/uv/). uv provisions the correct Python
(3.12) for you automatically.

```bash
# Install dependencies into a local virtualenv from the lockfile
uv sync

# Install the git pre-commit hooks (ruff, mypy, file hygiene)
uv run pre-commit install

# Run the test suite
uv run pytest
```

The full quality gate — lint, format, type-check, tests — runs locally on every
commit (via pre-commit) and in CI on every push.

## Architecture

A detailed architecture diagram and design write-up — covering the LLM
tool-calling boundary and the deterministic processing core — will land in a
later phase. _(Coming in Phase 7.)_

## Roadmap

- **Phase 0** — Project skeleton: uv, ruff/mypy/pytest, pre-commit, CI _(current)_
- **Phase 1** — Ingestion: Binance WebSocket + REST backfill → TimescaleDB
- **Phase 2** — Processing: rolling metrics + anomaly detection (deterministic, tested)
- **Phase 3** — API: FastAPI REST + WebSocket
- **Phase 4** — GenAI + evals: tool-calling assistant and an eval harness for it
- **Phase 5** — Frontend: Angular dashboard
- **Phase 6** — Deploy: Docker → AWS, live URL
- **Phase 7** — Polish: architecture docs, demo, eval report

## License

[MIT](LICENSE) © 2026 vFoex
