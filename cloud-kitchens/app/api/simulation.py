"""WebSocket endpoint that runs the simulation and streams events to the dashboard."""
import asyncio
import json
import logging
from pathlib import Path

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from engine.runner import SimRunner

router = APIRouter()
logger = logging.getLogger(__name__)

ORDERS_PATH = Path(__file__).parent.parent.parent / "engine" / "data" / "orders.json"


@router.websocket("/ws/simulation")
async def simulation_ws(ws: WebSocket) -> None:
    await ws.accept()
    try:
        # wait for start command: {strategy, speed, seed}
        raw = await ws.receive_text()
        params = json.loads(raw)
        strategy = params.get("strategy", "fifo")
        speed = float(params.get("speed", 2.0))
        seed = int(params.get("seed", 42))

        async def broadcast(msg: dict) -> None:
            try:
                await ws.send_json(msg)
            except Exception:
                pass

        runner = SimRunner(
            strategy_name=strategy,
            orders_path=ORDERS_PATH,
            seed=seed,
            rate=2.0,
            speed=speed,
            ws_broadcast=broadcast,
        )
        await runner.run()

    except WebSocketDisconnect:
        logger.info("Dashboard disconnected")
    except Exception as e:
        logger.exception("Simulation error: %s", e)
        try:
            await ws.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
