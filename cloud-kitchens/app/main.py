from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.core.exceptions import AppError, app_error_handler
from app.domains.orders.router import router as orders_router
from app.domains.menu.router import router as menu_router
from app.domains.inventory.router import router as inventory_router
from app.domains.kitchen.router import router as kitchen_router
from app.domains.delivery.router import router as delivery_router
from app.domains.payments.router import router as payments_router
from app.domains.ticketing.router import router as ticketing_router
from agents.events.handlers import setup_event_handlers
from app.api.simulation import router as simulation_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_event_handlers()
    yield
    # Shutdown — add cleanup here (close Redis, etc.)


app = FastAPI(
    title="Cloud Kitchens API",
    version="0.1.0",
    description="Cloud kitchens platform with AI agent foundation",
    lifespan=lifespan,
    debug=settings.DEBUG,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AppError, app_error_handler)

API_PREFIX = "/api/v1"
app.include_router(orders_router, prefix=API_PREFIX)
app.include_router(menu_router, prefix=API_PREFIX)
app.include_router(inventory_router, prefix=API_PREFIX)
app.include_router(kitchen_router, prefix=API_PREFIX)
app.include_router(delivery_router, prefix=API_PREFIX)
app.include_router(payments_router, prefix=API_PREFIX)
app.include_router(ticketing_router, prefix=API_PREFIX)


# ── Agent introspection endpoints ─────────────────────────────────────────────
from fastapi import APIRouter
from agents.registry import list_agents

agent_router = APIRouter(prefix=f"{API_PREFIX}/agents", tags=["agents"])

@agent_router.get("/")
async def list_all_agents():
    return list_agents()

app.include_router(agent_router)


app.include_router(simulation_router)

DASHBOARD_DIR = Path(__file__).parent.parent / "dashboard"

@app.get("/dashboard", include_in_schema=False)
async def dashboard():
    return FileResponse(DASHBOARD_DIR / "index.html")


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
