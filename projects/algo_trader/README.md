# algo_trader

A safety-first algorithmic trading framework: **backtest → paper → (gated) live**,
for crypto and US equities, with a pluggable strategy engine and risk controls
that are enforced in the loop rather than left to good intentions.

Built on the production discipline studied in
[`notes/jam-with-ai/`](../../notes/jam-with-ai/): explicit decisions, bounded
loops, typed boundaries, fail-safe defaults, observability, and tests.

> ⚠️ **Read this first — honest expectations.** No trading system reliably grows
> money "at lightning speed." Markets are largely efficient, retail latency can't
> compete with professional HFT, and **most retail algorithmic strategies lose
> money after costs.** This framework is built to be *disciplined and hard to blow
> up* — good risk control, no look-ahead bias, realistic costs — not to promise
> returns. Treat every number it prints as a simulation, and never trade money you
> can't afford to lose. Nothing here is financial advice.

## Safety model (how live trading is gated)

| Mode | Reachable? | What it does |
|---|---|---|
| **backtest** | always | Replays historical/synthetic bars; simulated fills |
| **paper** | always | Same engine, live/paper data, simulated or broker-paper fills |
| **live** | **hard-gated** | Real orders — refuses to run unless you deliberately unlock it |

Live trading fails **closed**. `LiveBroker` refuses to even construct unless *all*
of these hold (see [`algo_trader/config.py`](algo_trader/config.py),
[`execution/live.py`](algo_trader/execution/live.py)):

1. environment flag `ALGO_TRADER_ALLOW_LIVE=1`, **and**
2. an explicit `LiveGate(acknowledged_paper_first=True)`, **and**
3. a clean config, **and**
4. a venue client *you* construct with *your* keys, **and**
5. the order-placement adapter, which is intentionally left unimplemented so
   nothing routes real orders until you write that step consciously.

The CLI never exposes live trading. This is by design.

## What it will not do

No market-manipulation or deceptive mechanics — spoofing, layering, wash trading,
quote-stuffing, momentum ignition, pump-and-dump. Those are illegal (securities/
commodities fraud), not "unfair-but-legal" edges, and they are out of scope
permanently. This system trades your own capital through legitimate venue APIs,
honoring their terms and rate limits.

## Architecture

```
   DataFeed ──► Strategy ──► RiskManager ──► Broker ──► Portfolio
 (bars in    (target      (sizing + hard   (fills)   (cash, positions,
  time order) weights)     limits + kill              equity, trades)
                           switch)
                              │
                        Backtester drives the loop with NEXT-BAR execution
                        (a signal on bar t fills at bar t+1's open — no look-ahead)
```

- **Data** (`data/`): `SyntheticFeed` (deterministic GBM, zero-dep, offline),
  `CsvFeed`, and optional live adapters — `CcxtHistoricalFeed` (crypto) and
  `AlpacaHistoricalFeed` (US equities).
- **Strategy** (`strategy/`): a `Strategy` emits `Signal`s with a *target weight*;
  it never sizes orders. Included: `ma_cross`, `rsi_meanrev`. Registry-based so
  new strategies are discoverable by name.
- **Risk** (`risk.py`): position-weight cap, gross-exposure/no-leverage cap,
  long-only by default, daily-loss and drawdown **kill switch** that flattens and
  halts.
- **Execution** (`execution/`): `SimulatedBroker` (fees + slippage), `LiveBroker`
  (hard-gated).
- **Backtest** (`backtest/`): event loop + metrics (return, CAGR, Sharpe, max
  drawdown, volatility, win rate, profit factor).
- **Optimize** (`optimize.py`): **walk-forward** parameter search — the honest form
  of "adaptive strategies" (fit in-sample, judge out-of-sample, so it adapts
  without overfitting noise).

## Quickstart (no dependencies, no network)

```bash
cd projects/algo_trader
python -m algo_trader list-strategies
python -m algo_trader backtest --strategy ma_cross --bars 500
python -m algo_trader optimize --strategy ma_cross      # shows the overfitting gap
python tests/test_algo_trader.py                        # 13 tests, all offline
```

## Using real data (optional)

```bash
pip install -r requirements-extra.txt   # ccxt, alpaca-py, etc.
```

- **Crypto (ccxt):** `CcxtHistoricalFeed("binance", "BTC/USDT", timeframe="1d")`.
- **US equities (Alpaca):** set `ALPACA_API_KEY` / `ALPACA_SECRET_KEY`, then
  `AlpacaHistoricalFeed("AAPL", timeframe="1Day")`. Alpaca's paper account is free.

Feed those into `Backtester` exactly like `SyntheticFeed`. (In this repo's locked
web sessions the venue hosts may be blocked; run data pulls where they're
reachable, or on Full network access — see
[`notes/tooling/admin-allowlist.md`](../../notes/tooling/admin-allowlist.md).)

## "Learning from diverse data, continuously" — how it plugs in

This is the roadmap piece that connects to the Jam With AI RAG work. The
`Strategy` interface is deliberately signal-source-agnostic, so a news/LLM signal
is just another strategy that emits target weights:

- Ingest news / filings / transcripts with the RAG pipeline in
  [`tools/transcribe/`](../../tools/transcribe/) and the patterns in
  `notes/jam-with-ai/` → score sentiment/event features per symbol per timestamp.
- Feed those features into a `NewsSentimentStrategy` (a documented next step) or
  blend them with technical/ML signals.
- ML-scored signals (a model predicting short-horizon direction) fit the same
  interface, trained walk-forward to avoid look-ahead.

These are **scaffolded, not yet built** — the interfaces exist and are honest
about that. See the roadmap.

## Roadmap

- [x] Core engine: data → strategy → risk → execution, next-bar backtest
- [x] Risk limits + daily-loss/drawdown kill switch
- [x] Simulated broker with costs; hard-gated live broker
- [x] `ma_cross`, `rsi_meanrev`; walk-forward optimizer; CLI; 13 tests
- [x] Optional ccxt / Alpaca historical data adapters
- [ ] Paper-trading runner against live data (loop + scheduler)
- [ ] News/LLM sentiment signal source (reuse the RAG pipeline)
- [ ] ML-scored strategy with walk-forward training + purged CV
- [ ] Portfolio-level allocation across strategies; regime detection
- [ ] Langfuse-style trade/decision observability (per the RAG playbook)
- [ ] A live venue adapter you wire with your own keys, after paper proves out

## Layout

```
algo_trader/
  types.py config.py portfolio.py risk.py optimize.py cli.py
  data/       base.py synthetic.py csv_feed.py live_adapters.py
  strategy/   base.py registry.py ma_cross.py rsi_mean_reversion.py
  execution/  base.py simulated.py live.py
  backtest/   engine.py metrics.py
tests/        test_algo_trader.py
```
