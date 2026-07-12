import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.domains.menu.schemas import MenuItemCreate, MenuItemOut, MenuItemUpdate
from app.domains.menu.service import MenuService

router = APIRouter(prefix="/menu", tags=["menu"])
DB = Annotated[AsyncSession, Depends(get_db)]


@router.post("/", response_model=MenuItemOut, status_code=201)
async def create_item(body: MenuItemCreate, db: DB):
    return await MenuService(db).create(body)


@router.get("/brand/{brand_id}", response_model=list[MenuItemOut])
async def list_menu(brand_id: str, db: DB, available_only: bool = Query(False)):
    return await MenuService(db).list_by_brand(brand_id, available_only)


@router.get("/{item_id}", response_model=MenuItemOut)
async def get_item(item_id: uuid.UUID, db: DB):
    item = await MenuService(db).get(item_id)
    if not item:
        raise HTTPException(404, "Item not found")
    return item


@router.patch("/{item_id}", response_model=MenuItemOut)
async def update_item(item_id: uuid.UUID, body: MenuItemUpdate, db: DB):
    item = await MenuService(db).update(item_id, body)
    if not item:
        raise HTTPException(404, "Item not found")
    return item


@router.delete("/{item_id}", status_code=204)
async def delete_item(item_id: uuid.UUID, db: DB):
    ok = await MenuService(db).delete(item_id)
    if not ok:
        raise HTTPException(404, "Item not found")
