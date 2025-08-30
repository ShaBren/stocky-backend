"""
Item management endpoints
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...db.database import get_db
from ...crud.crud import ItemCRUD, LogEntryCRUD
from ...schemas.schemas import ItemCreate, ItemUpdate, ItemResponse
from ...core.security import require_user_role
from ...models.models import LogEntry

router = APIRouter()
item_crud = ItemCRUD()

@router.get("/", response_model=List[ItemResponse])
async def list_items(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=500, description="Number of items to return"),
    db: Session = Depends(get_db),
    current_user = Depends(require_user_role())
):
    """List all items with pagination"""
    items = item_crud.get_multi(db, skip=skip, limit=limit)
    return items

@router.post("/", response_model=ItemResponse)
async def create_item(
    item: ItemCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_user_role("manager"))
):
    """Create a new item"""
    # Check if item with same UPC already exists
    if item.upc:
        existing_item = item_crud.get_by_upc(db, upc=item.upc)
        if existing_item:
            raise HTTPException(
                status_code=400,
                detail=f"Item with UPC {item.upc} already exists"
            )
    
    db_item = item_crud.create(db, obj_in=item, created_by_id=current_user.id)
    # Log creation
    log_crud = LogEntryCRUD()
    log_entry = {
        "message": f"Item created: {db_item.name} (ID: {db_item.id})",
        "level": "INFO",
        "module": "items",
        "function": "create_item",
        "user_id": current_user.id
    }
    log_crud.create(db, obj_in=log_entry)
    return db_item

@router.get("/search", response_model=List[ItemResponse])
async def search_items(
    q: str = Query(..., min_length=1, description="Search query"),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=500, description="Number of items to return"),
    db: Session = Depends(get_db),
    current_user = Depends(require_user_role())
):
    """Search items by name, description, or UPC"""
    items = item_crud.search(db, query=q, skip=skip, limit=limit)
    return items

@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_user_role())
):
    """Get a specific item by ID"""
    item = item_crud.get(db, id=item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@router.put("/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: int,
    item_update: ItemUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_user_role("manager"))
):
    db_item = item_crud.get(db, id=item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Check if updating UPC would conflict with existing item
    if item_update.upc and item_update.upc != db_item.upc:
        existing_item = item_crud.get_by_upc(db, upc=item_update.upc)
        if existing_item and existing_item.id != item_id:
            raise HTTPException(
                status_code=400,
                detail=f"Item with UPC {item_update.upc} already exists"
            )
    
    # Compare changes BEFORE update
    changes = {}
    update_data = item_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        old_value = getattr(db_item, field, None)
        if value != old_value:
            changes[field] = {"old": old_value, "new": value}
    updated_item = item_crud.update(db, db_obj=db_item, obj_in=item_update)
    # Log update with details
    log_crud = LogEntryCRUD()
    log_entry = {
        "message": f"Item updated: {updated_item.name} (ID: {updated_item.id})",
        "level": "INFO",
        "module": "items",
        "function": "update_item",
        "user_id": current_user.id,
        "extra_data": {"changes": changes}
    }
    log_crud.create(db, obj_in=log_entry)
    return updated_item

@router.delete("/{item_id}")
async def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_user_role("admin"))
):
    """Delete an item (admin only)"""
    db_item = item_crud.get(db, id=item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Check for related SKUs
    from ...crud.crud import SKUCRUD
    sku_crud = SKUCRUD()
    related_skus = sku_crud.get_by_item(db, item_id)
    if related_skus:
        raise HTTPException(status_code=409, detail="Cannot delete item: SKUs exist for this item.")

    item_crud.remove(db, id=item_id)
    # Log deletion
    log_crud = LogEntryCRUD()
    log_entry = {
        "message": f"Item deleted: {db_item.name} (ID: {db_item.id})",
        "level": "INFO",
        "module": "items",
        "function": "delete_item",
        "user_id": current_user.id
    }
    log_crud.create(db, obj_in=log_entry)
    return {"message": "Item deleted successfully"}

@router.get("/upc/{upc}", response_model=ItemResponse)
async def get_item_by_upc(
    upc: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_user_role())
):
    """Get an item by UPC code"""
    item = item_crud.get_by_upc(db, upc=upc)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item
