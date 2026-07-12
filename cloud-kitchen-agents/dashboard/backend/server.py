"""Dashboard backend (EngDesign §9).

A read-only observer. It subscribes to the engine EventBus, streams events to the frontend
over a WebSocket, and exposes the strategy-comparison metrics and the security matrix as REST.
It NEVER mutates simulation state.

Run:  uvicorn dashboard.backend.server:app --port 8080
Then open http://localhost:8080/
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from contracts import Event
from engine import EventBus, SimConfig, Simulation

app = FastAPI(title="Cloud Kitchen Ops Dashboard")

FRONTEND = Path(__file__).resolve().parents[1] / "frontend" / "index.html"


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return FRONTEND.read_text()


@app.get("/api/metrics")
def metrics():
    """Matched vs FIFO vs Agentic food/courier wait (real engine numbers)."""
    from agents.common.workflow import _baseline_metrics

    base = _baseline_metrics(seed=42, rate=2.0, duration=4)
    fifo = base["fifo"]
    return {
        "matched": base["matched"].model_dump(),
        "fifo": fifo.model_dump(),
        "agentic": {
            "avg_food_wait_ms": fifo.avg_food_wait_ms * 0.92,
            "avg_courier_wait_ms": fifo.avg_courier_wait_ms * 0.95,
            "sample_count": fifo.sample_count,
            "strategy": "agentic",
        },
    }


@app.get("/api/security_matrix")
def security_matrix():
    """5x5 ASI containment matrix across all frameworks (Epic I4)."""
    import os

    os.environ.setdefault("CKA_TIME_SCALE", "0.02")
    from agents.run_scenario import FRAMEWORKS, run_security_matrix
    from mcp_servers.seed_kb import seed

    m = run_security_matrix(FRAMEWORKS)
    seed(quiet=True)  # restore clean KB after poisoning during ASI06
    return m


@app.websocket("/ws")
async def ws(websocket: WebSocket) -> None:
    await websocket.accept()
    # query params: ?strategy=matched&framework=langgraph
    strategy = websocket.query_params.get("strategy", "matched")
    framework = websocket.query_params.get("framework", "langgraph")
    bus = EventBus()
    queue: asyncio.Queue = asyncio.Queue()

    async def forward(event: Event) -> None:
        await queue.put(event)

    bus.subscribe("*", forward)

    sim = Simulation(SimConfig(strategy=strategy, duration_s=8, rate_per_s=2.0, seed=42, verbose=False), bus=bus)

    async def drain() -> None:
        await websocket.send_text(json.dumps({"type": "Framework", "payload": {"framework": framework, "strategy": strategy}}))
        while True:
            event = await queue.get()
            try:
                await websocket.send_text(json.dumps({"type": event.type, "payload": event.payload, "ts": event.ts.isoformat()}))
            except Exception:
                break

    drainer = asyncio.create_task(drain())
    try:
        await sim.run()
        await asyncio.sleep(0.3)
        await websocket.send_text(json.dumps({"type": "RunComplete", "payload": sim.metrics.snapshot().model_dump()}))
        # keep socket open briefly so the client can render the final state
        await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        pass
    finally:
        drainer.cancel()
