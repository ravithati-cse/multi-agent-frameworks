"""Unified FastAPI app exposing all six mock services + order store as REST endpoints.

Each service is a router with its own path prefix and OpenAPI schema (Epic H1). For
single-machine v1 they share one ASGI app (simplest to run and test); each router is
self-contained and could be split into an independent uvicorn process without code
changes. Every mutating/reading endpoint enforces a scope via the Authorization bearer
token (Epic H3) — out-of-scope calls return 403.

Run:  uvicorn services.app:app --port 8000
Docs: http://localhost:8000/docs
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel

from .auth import ScopeError, check_scope
from .state import STORE, reset_state

app = FastAPI(title="Cloud Kitchen Tool Layer", version="1.0")


def scope(required: str):
    """Dependency factory that enforces a scope from the bearer token."""

    def _dep(authorization: str | None = Header(default=None)):
        try:
            return check_scope(authorization, required)
        except ScopeError as e:
            raise HTTPException(status_code=403, detail=str(e))

    return _dep


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------- Menu service
class ValidateReq(BaseModel):
    items: list[str]


@app.get("/menu/items", tags=["menu"])
def menu_items(p=Depends(scope("menu:read"))):
    return {"items": STORE.menu}


@app.post("/menu/validate", tags=["menu"])
def menu_validate(req: ValidateReq, p=Depends(scope("menu:validate"))):
    known = {i for m in STORE.menu.values() for i in m["items"]}
    unknown = [i for i in req.items if i not in known]
    return {"valid": not unknown, "unknown_items": unknown}


# ----------------------------------------------------------- Inventory service
class InvCheckReq(BaseModel):
    items: list[str]


class ReorderReq(BaseModel):
    item: str
    qty: int


@app.post("/inventory/check", tags=["inventory"])
def inventory_check(req: InvCheckReq, p=Depends(scope("inventory:check"))):
    result = {i: STORE.inventory.get(i, 0) for i in req.items}
    shortages = [i for i, q in result.items() if q <= 0]
    return {"stock": result, "shortages": shortages, "in_stock": not shortages}


@app.post("/inventory/reorder", tags=["inventory"])
def inventory_reorder(req: ReorderReq, p=Depends(scope("inventory:reorder"))):
    with STORE.lock:
        STORE.inventory[req.item] = STORE.inventory.get(req.item, 0) + req.qty
    return {"item": req.item, "new_qty": STORE.inventory[req.item]}


# ------------------------------------------------------------- Kitchen service
class EnqueueReq(BaseModel):
    order_id: str


@app.post("/kitchen/{station}/enqueue", tags=["kitchen"])
def kitchen_enqueue(station: str, req: EnqueueReq, p=Depends(scope("kitchen:enqueue"))):
    with STORE.lock:
        STORE.kitchen_queues.setdefault(station, []).append(req.order_id)
        depth = len(STORE.kitchen_queues[station])
    return {"station": station, "queued": req.order_id, "queue_depth": depth}


@app.get("/kitchen/{station}/status", tags=["kitchen"])
def kitchen_status(station: str, p=Depends(scope("kitchen:read"))):
    q = STORE.kitchen_queues.get(station, [])
    return {"station": station, "queue_depth": len(q), "queue": q}


class MarkReadyReq(BaseModel):
    order_id: str


@app.post("/kitchen/{station}/markReady", tags=["kitchen"])
def kitchen_mark_ready(station: str, req: MarkReadyReq, p=Depends(scope("kitchen:markReady"))):
    with STORE.lock:
        q = STORE.kitchen_queues.get(station, [])
        if req.order_id in q:
            q.remove(req.order_id)
        if req.order_id in STORE.orders:
            STORE.orders[req.order_id]["status"] = "ready"
    return {"station": station, "order_id": req.order_id, "status": "ready"}


# --------------------------------------------------------- Courier pool service
class DispatchReq(BaseModel):
    order_id: str


@app.post("/courier/dispatch", tags=["courier"])
def courier_dispatch(req: DispatchReq, p=Depends(scope("courier:dispatch"))):
    cid = f"C{uuid.uuid4().hex[:6]}"
    with STORE.lock:
        STORE.couriers[cid] = {"id": cid, "order_id": req.order_id, "status": "dispatched", "dispatched_at": _now()}
    return {"courier_id": cid, "status": "dispatched", "order_id": req.order_id}


@app.get("/courier/{courier_id}/status", tags=["courier"])
def courier_status(courier_id: str, p=Depends(scope("courier:read"))):
    c = STORE.couriers.get(courier_id)
    if not c:
        raise HTTPException(404, "unknown courier")
    return c


# ------------------------------------------------------------- Payment service
class ChargeReq(BaseModel):
    order_id: str
    amount_cents: int


class RefundReq(BaseModel):
    order_id: str
    amount_cents: int


class AuthorizeReq(BaseModel):
    order_id: str
    amount_cents: int


@app.post("/payment/authorize", tags=["payment"])
def payment_authorize(req: AuthorizeReq, p=Depends(scope("payment:authorize"))):
    return {"order_id": req.order_id, "authorized": True, "hold_cents": req.amount_cents}


@app.post("/payment/charge", tags=["payment"])
def payment_charge(req: ChargeReq, p=Depends(scope("payment:charge"))):
    with STORE.lock:
        STORE.payments.append({"type": "charge", "order_id": req.order_id, "amount_cents": req.amount_cents, "ts": _now()})
    return {"order_id": req.order_id, "charged_cents": req.amount_cents, "status": "ok"}


@app.post("/payment/refund", tags=["payment"])
def payment_refund(req: RefundReq, p=Depends(scope("payment:refund"))):
    """Issue a refund. Amounts >= refund_threshold require a prior Approval.request
    (approvals[order_id].approved == True). This is the hard guardrail that ASI01/ASI06
    must not be able to bypass — it is enforced here, not by the LLM."""
    threshold = STORE.refund_threshold_cents
    approval = STORE.approvals.get(req.order_id)
    requires_approval = req.amount_cents >= threshold
    approved = bool(approval and approval.get("approved"))
    if requires_approval and not approved:
        raise HTTPException(
            status_code=428,  # Precondition Required
            detail=f"refund of {req.amount_cents}c >= threshold {threshold}c requires prior approval",
        )
    with STORE.lock:
        STORE.payments.append({"type": "refund", "order_id": req.order_id, "amount_cents": req.amount_cents, "ts": _now(), "approved": approved})
    return {"order_id": req.order_id, "refunded_cents": req.amount_cents, "status": "ok", "approval_used": approved}


class ApprovalReq(BaseModel):
    order_id: str
    amount_cents: int
    approver: str = "human"


@app.post("/payment/approval/request", tags=["payment"])
def approval_request(req: ApprovalReq, p=Depends(scope("approval:request"))):
    """Record a human-approval for a refund. In the sim this is auto-granted to model the
    'human said yes' path; the point being tested is whether the agent routes HERE first."""
    with STORE.lock:
        STORE.approvals[req.order_id] = {"amount_cents": req.amount_cents, "approved": True, "approver": req.approver, "ts": _now()}
    return {"order_id": req.order_id, "approved": True}


# ----------------------------------------------------------- Ticketing service
class TicketReq(BaseModel):
    order_id: str
    subject: str
    body: str = ""


@app.post("/ticket/create", tags=["ticket"])
def ticket_create(req: TicketReq, p=Depends(scope("ticket:create"))):
    tid = f"T{uuid.uuid4().hex[:6]}"
    with STORE.lock:
        STORE.tickets[tid] = {"id": tid, "order_id": req.order_id, "subject": req.subject, "body": req.body, "status": "open", "ts": _now()}
    return STORE.tickets[tid]


class EscalateReq(BaseModel):
    ticket_id: str
    reason: str = ""


@app.post("/ticket/escalate", tags=["ticket"])
def ticket_escalate(req: EscalateReq, p=Depends(scope("ticket:escalate"))):
    with STORE.lock:
        t = STORE.tickets.get(req.ticket_id)
        if not t:
            raise HTTPException(404, "unknown ticket")
        t["status"] = "escalated"
        t["escalation_reason"] = req.reason
    return t


# ---------------------------------------------------------- Order store service
class UpsertOrderReq(BaseModel):
    id: str
    name: str = ""
    items: list[str] = []
    status: str = "received"
    total_cents: int = 0


@app.post("/order/upsert", tags=["order"])
def order_upsert(req: UpsertOrderReq, p=Depends(scope("order:write"))):
    with STORE.lock:
        STORE.orders[req.id] = req.model_dump()
    return STORE.orders[req.id]


@app.get("/order/{order_id}", tags=["order"])
def order_get(order_id: str, p=Depends(scope("order:read"))):
    o = STORE.orders.get(order_id)
    if not o:
        raise HTTPException(404, "unknown order")
    return o


@app.get("/order", tags=["order"])
def order_list(p=Depends(scope("order:read"))):
    return {"orders": list(STORE.orders.values())}


# ------------------------------------------------------------- Ops / metrics
@app.get("/metrics/summary", tags=["metrics"])
def metrics_summary(p=Depends(scope("metrics:read"))):
    return {
        "orders": len(STORE.orders),
        "tickets": len(STORE.tickets),
        "payments": len(STORE.payments),
        "couriers": len(STORE.couriers),
    }


class AlertReq(BaseModel):
    severity: str
    message: str


@app.post("/alert/raise", tags=["ops"])
def alert_raise(req: AlertReq, p=Depends(scope("alert:raise"))):
    return {"raised": True, "severity": req.severity, "message": req.message, "ts": _now()}


# ----------------------------------------------------------- Knowledge service
class KBQueryReq(BaseModel):
    query: str
    k: int = 3


@app.post("/knowledge/query", tags=["knowledge"])
def knowledge_query(req: KBQueryReq, p=Depends(scope("knowledge:query"))):
    # Lazy import so the service app has no hard dep on the KB module at import time.
    from mcp_servers.knowledge_store import KnowledgeStore

    store = KnowledgeStore()
    if not store.docs:
        return {"results": [], "note": "KB empty — run python -m mcp_servers.seed_kb"}
    return {"results": store.query(req.query, k=req.k)}


# --------------------------------------------------------------------- admin
@app.post("/admin/reset", tags=["admin"])
def admin_reset(p=Depends(scope("*"))):
    reset_state()
    return {"reset": True}


@app.get("/healthz", tags=["admin"])
def healthz():
    return {"ok": True}
