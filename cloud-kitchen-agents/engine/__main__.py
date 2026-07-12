"""CLI entry point for the standalone Phase 0 engine (matches original take-home rubric).

Usage:
    python -m engine --strategy matched --duration 20 --rate 2 --seed 42
    python -m engine --strategy fifo --orders sample_orders.json --json-out summary.json
"""
from __future__ import annotations

import argparse
import asyncio
import json

from .simulation import SimConfig, Simulation


def main() -> None:
    ap = argparse.ArgumentParser(description="Cloud-kitchen deterministic dispatch engine")
    ap.add_argument("--strategy", choices=["matched", "fifo"], default="matched")
    ap.add_argument("--duration", type=float, default=20.0)
    ap.add_argument("--rate", type=float, default=2.0)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--orders", default=None, help="path to orders JSON file")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--json-out", default=None, help="write final metrics summary JSON here")
    args = ap.parse_args()

    cfg = SimConfig(
        strategy=args.strategy,
        duration_s=args.duration,
        rate_per_s=args.rate,
        seed=args.seed,
        orders_file=args.orders,
        verbose=not args.quiet,
    )
    metrics = asyncio.run(Simulation(cfg).run())
    if args.json_out:
        with open(args.json_out, "w") as f:
            json.dump(metrics.model_dump(), f, indent=2)
        print(f"Wrote summary to {args.json_out}")


if __name__ == "__main__":
    main()
