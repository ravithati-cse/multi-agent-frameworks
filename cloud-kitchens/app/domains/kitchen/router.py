import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.domains.kitchen.schemas import KitchenCreate, KitchenOut, KitchenStatusUpdate
from app.domains.kitchen.service import KitchenService

router = APIRouter(prefix="/kitchens", tags=["kitchens"])
DB = Annotated[AsyncSession, Depends(get_db)]


@router.post("/", response_model=KitchenOut, status_code=201)
async def create_kitchen(body: KitchenCreate, db: DB):
    return await KitchenService(db).create(body)


@router.get("/", response_model=list[KitchenOut])
async def list_kitchens(db: DB, active_only: bool = Query(True)):
    return await KitchenService(db).list_all(active_only)


@router.get("/{kitchen_id}", response_model=KitchenOut)
async def get_kitchen(kitchen_id: uuid.UUID, db: DB):
    k = await KitchenService(db).get(kitchen_id)
    if not k:
        raise HTTPException(404, "Kitchen not found")
    return k


@router.patch("/{kitchen_id}/status", response_model=KitchenOut)
async def update_status(kitchen_id: uuid.UUID, body: KitchenStatusUpdate, db: DB):
    k = await KitchenService(db).set_status(kitchen_id, body)
    if not k:
        raise HTTPException(404, "Kitchen not found")
    return k
