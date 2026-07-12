"""Tool-layer auth + guardrail tests (Epic H3, ASI approval gate)."""
from fastapi.testclient import TestClient

from services.app import app
from services.auth import ROLE_TOKENS
from services.state import reset_state

client = TestClient(app)


def H(role):
    return {"Authorization": f"Bearer {ROLE_TOKENS[role]}"}


def setup_function(_):
    reset_state()


def test_support_cannot_refund_403():
    r = client.post("/payment/refund", json={"order_id": "O1", "amount_cents": 500}, headers=H("support"))
    assert r.status_code == 403


def test_unknown_token_403():
    r = client.get("/menu/items", headers={"Authorization": "Bearer nope"})
    assert r.status_code == 403


def test_small_refund_allowed():
    r = client.post("/payment/refund", json={"order_id": "O1", "amount_cents": 500}, headers=H("payment"))
    assert r.status_code == 200


def test_large_refund_needs_approval():
    r = client.post("/payment/refund", json={"order_id": "O2", "amount_cents": 5000}, headers=H("payment"))
    assert r.status_code == 428
    client.post("/payment/approval/request", json={"order_id": "O2", "amount_cents": 5000}, headers=H("payment"))
    r2 = client.post("/payment/refund", json={"order_id": "O2", "amount_cents": 5000}, headers=H("payment"))
    assert r2.status_code == 200


def test_dispatch_cannot_write_orders():
    r = client.post("/order/upsert", json={"id": "O3", "status": "cancelled"}, headers=H("dispatch"))
    assert r.status_code == 403
