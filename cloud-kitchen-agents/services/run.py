"""Launch the REST tool layer.

    python -m services.run            # serves all services on :8000
    uvicorn services.app:app --port 8000 --reload   # equivalent, with autoreload

For v1 all services share one ASGI app on one port (single-machine, EngDesign §8 constraint).
Splitting a service onto its own port later is just `uvicorn services.app:app` with a router
extracted — no code in the routers changes.
"""
from __future__ import annotations

import uvicorn


def main() -> None:
    uvicorn.run("services.app:app", host="127.0.0.1", port=8000, log_level="info")


if __name__ == "__main__":
    main()
