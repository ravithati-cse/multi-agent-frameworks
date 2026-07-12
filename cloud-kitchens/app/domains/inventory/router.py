import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.domains.inventory.schemas import InventoryAdjust, InventoryItemCreate, InventoryItemOut
from app.domains.inventory.service import InventoryService

router = APIRouter(prefix="/inventory", tags=["inventory"])
DB = Annotated[AsyncSession, Depends(get_db)]


@router.post("/", response_model=InventoryItemOut, status_code=201)
async def create_item(body: InventoryItemCreate, db: DB):
    return await InventoryService(db).create(body)


@router.get("/kitchen/{kitchen_id}", response_model=list[InventoryItemOut])
async def list_inventory(kitchen_id: str, db: DB):
    items = await InventoryService(db).list_by_kitchen(kitchen_id)
    svc = InventoryService(db)
    return [
        {**i.__dict__, "is_low": i.quantity <= i.reorder_level} for i in items
    ]


@router.get("/kitchen/{kitchen_id}/low-stock", response_model=list[InventoryItemOut])
async def low_stock(kitchen_id: str, db: DB):
    items = await InventoryService(db).low_stock(kitchen_id)
    return [{**i.__dict__, "is_low": True} for i in items]


@router.post("/{item_id}/adjust", response_model=InventoryItemOut)
async def adjust_stock(item_id: uuid.UUID, body: InventoryAdjust, db: DB):
    item = await InventoryService(db).adjust(item_id, body)
    if not item:
        raise HTTPException(404, "Item not found")
    return {**item.__dict__, "is_low": item.quantity <= item.reorder_level}
