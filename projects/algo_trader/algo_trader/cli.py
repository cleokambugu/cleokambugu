"""Command-line entry point.

    python -m algo_trader backtest --strategy ma_cross --bars 500
    python -m algo_trader optimize --strategy ma_cross
    python -m algo_trader list-strategies

Backtest/paper only from the CLI. Live trading is not exposed here on purpose —
it requires the operator to construct a gated LiveBroker in code (see README).
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from .config import Config, RiskLimits
from .backtest.engine import Backtester
from .data.synthetic import SyntheticFeed
from .data.csv_feed import CsvFeed
from .execution.simulated import SimulatedBroker
from .optimize import walk_forward
from .strategy.registry import REGISTRY, create


def _feed(args: argparse.Namespace):
    if args.csv:
        # --csv SYMBOL=path.csv (repeatable)
        mapping = {}
        for item in args.csv:
            sym, _, path = item.partition("=")
            mapping[sym] = path
        return CsvFeed(mapping)
    return SyntheticFeed(symbols=["SYN/USD"], bars=args.bars, seed=args.seed)


def _print_metrics(result) -> None:
    m = result.metrics
    print("\n=== Backtest result ===")
    print(f"  start equity   : {m.start_equity:,.2f}")
    print(f"  end equity     : {m.end_equity:,.2f}")
    print(f"  total return   : {m.total_return:+.2%}")
    print(f"  CAGR           : {m.cagr:+.2%}")
    print(f"  Sharpe         : {m.sharpe:.2f}")
    print(f"  max drawdown   : {m.max_drawdown:.2%}")
    print(f"  ann. volatility: {m.volatility_annual:.2%}")
    print(f"  trades         : {m.num_trades}")
    print(f"  win rate       : {m.win_rate:.1%}")
    print(f"  profit factor  : {m.profit_factor:.2f}")
    if result.halted:
        print(f"  ** HALTED: {result.halt_reason} **")
    print("\nNote: simulated results. Past performance does not predict the future,")
    print("and most retail algorithmic strategies lose money after costs.")


def cmd_backtest(args: argparse.Namespace) -> int:
    config = Config(starting_cash=args.cash, periods_per_year=args.periods_per_year)
    strategy = create(args.strategy, **_strategy_params(args))
    bt = Backtester(config, strategy, SimulatedBroker(config.costs))
    result = bt.run(_feed(args))
    _print_metrics(result)
    return 0


def cmd_optimize(args: argparse.Namespace) -> int:
    config = Config(starting_cash=args.cash, periods_per_year=args.periods_per_year)
    if args.strategy == "ma_cross":
        grid = {"fast": [10, 20, 30], "slow": [50, 100, 150]}
    elif args.strategy == "rsi_meanrev":
        grid = {"period": [7, 14, 21], "oversold": [20.0, 30.0], "exit_level": [50.0, 55.0]}
    else:
        print(f"no default grid for '{args.strategy}'", file=sys.stderr)
        return 2
    res = walk_forward(config, args.strategy, grid, _feed(args))
    print("\n=== Walk-forward optimization ===")
    print(f"  best params (chosen in-sample): {res.best_params}")
    print(f"  in-sample Sharpe : {res.in_sample_sharpe:.2f}")
    print(f"  out-sample Sharpe: {res.out_sample_sharpe:.2f}")
    print("  (a big gap between the two = overfitting; prefer stable params)")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    print("Available strategies:")
    for name in sorted(REGISTRY):
        print(f"  - {name}")
    return 0


def _strategy_params(args: argparse.Namespace) -> dict:
    params = {}
    for kv in args.param or []:
        key, _, val = kv.partition("=")
        try:
            params[key] = int(val)
        except ValueError:
            try:
                params[key] = float(val)
            except ValueError:
                params[key] = val
    return params


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="algo_trader", description="Safety-first algo trading (backtest/paper).")
    sub = p.add_subparsers(dest="command", required=True)

    def common(sp):
        sp.add_argument("--strategy", default="ma_cross")
        sp.add_argument("--bars", type=int, default=500)
        sp.add_argument("--seed", type=int, default=7)
        sp.add_argument("--cash", type=float, default=10_000.0)
        sp.add_argument("--periods-per-year", type=int, default=365)
        sp.add_argument("--csv", action="append", help="SYMBOL=path.csv (repeatable)")
        sp.add_argument("--param", action="append", help="name=value strategy param (repeatable)")

    bt = sub.add_parser("backtest", help="run a backtest")
    common(bt)
    bt.set_defaults(func=cmd_backtest)

    opt = sub.add_parser("optimize", help="walk-forward parameter search")
    common(opt)
    opt.set_defaults(func=cmd_optimize)

    ls = sub.add_parser("list-strategies", help="list registered strategies")
    ls.set_defaults(func=cmd_list)
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
