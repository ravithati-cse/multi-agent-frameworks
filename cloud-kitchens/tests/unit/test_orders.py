import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_create_and_get_order(client: AsyncClient):
    payload = {
        "customer_id": "cust-001",
        "brand_id": "brand-burger",
        "kitchen_id": "kitchen-downtown",
        "items": [{"item_id": "item-001", "qty": 2, "price": 9.99}],
        "delivery_address": {"street": "123 Main St", "city": "SF"},
    }
    r = await client.post("/api/v1/orders/", json=payload)
    assert r.status_code == 201
    order = r.json()
    assert order["status"] == "pending"
    assert float(order["total_amount"]) == pytest.approx(19.98, rel=1e-3)

    r2 = await client.get(f"/api/v1/orders/{order['id']}")
    assert r2.status_code == 200
    assert r2.json()["id"] == order["id"]
