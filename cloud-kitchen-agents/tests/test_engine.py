"""Deterministic engine tests (Epic A)."""
import asyncio

from engine import Simulation, SimConfig
from engine.dispatch_baselines import FIFOStrategy, MatchedStrategy, make_strategy


def test_matched_strategy_binds_identity():
    s = MatchedStrategy()
    # couriers carry their bound order id in Matched mode
    pairs = s.assign(["O1", "O2"], [("C1", "O1"), ("C2", "O3")])
    assert pairs == [("C1", "O1")]


def test_fifo_pairs_earliest_first():
    s = FIFOStrategy()
    pairs = s.assign(["O1", "O2", "O3"], ["C1", "C2"])
    assert pairs == [("C1", "O1"), ("C2", "O2")]


def test_make_strategy_rejects_agentic():
    make_strategy("matched")
    make_strategy("fifo")
    try:
        make_strategy("agentic")
        assert False, "agentic should not be an engine baseline"
    except ValueError:
        pass


def test_simulation_reproducible_given_seed(monkeypatch):
    monkeypatch.setenv("CKA_TIME_SCALE", "0.02")
    cfg = SimConfig(strategy="matched", duration_s=4, rate_per_s=3, seed=7, verbose=False)
    m1 = asyncio.run(Simulation(cfg).run())
    m2 = asyncio.run(Simulation(cfg).run())
    assert m1.sample_count == m2.sample_count
    assert m1.sample_count > 0


def test_both_strategies_produce_metrics():
    cfg_m = SimConfig(strategy="matched", duration_s=4, rate_per_s=3, seed=42, verbose=False)
    cfg_f = SimConfig(strategy="fifo", duration_s=4, rate_per_s=3, seed=42, verbose=False)
    m = asyncio.run(Simulation(cfg_m).run())
    f = asyncio.run(Simulation(cfg_f).run())
    assert m.avg_food_wait_ms >= 0 and f.avg_food_wait_ms >= 0
    assert m.strategy == "matched" and f.strategy == "fifo"
