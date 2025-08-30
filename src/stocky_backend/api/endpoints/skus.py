"""
SKU (inventory) management endpoints
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...db.database import get_db
from ...crud.crud import SKUCRUD, LogEntryCRUD
from ...schemas.schemas import SKUCreate, SKUUpdate, SKUResponse, SKUQuantityUpdate
from ...core.security import require_user_role

router = APIRouter()
sku_crud = SKUCRUD()

@router.get("/", response_model=List[SKUResponse])
async def list_skus(
    skip: int = Query(0, ge=0, description="Number of SKUs to skip"),
    limit: int = Query(100, ge=1, le=500, description="Number of SKUs to return"),
    location_id: int = Query(None, description="Filter by location ID"),
    item_id: int = Query(None, description="Filter by item ID"),
    low_stock: bool = Query(False, description="Only show low stock items"),
    db: Session = Depends(get_db),
    current_user = Depends(require_user_role())
):
    """List all SKUs (inventory items) with filtering options"""
    if location_id:
        skus = sku_crud.get_by_location(db, location_id=location_id, skip=skip, limit=limit)
    elif item_id:
        skus = sku_crud.get_by_item(db, item_id=item_id, skip=skip, limit=limit)
    elif low_stock:
        skus = sku_crud.get_low_stock(db, skip=skip, limit=limit)
    else:
        skus = sku_crud.get_multi(db, skip=skip, limit=limit)
    return skus

@router.post("/", response_model=SKUResponse)
async def create_sku(
    sku: SKUCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_user_role("user"))
):
    """Create a new SKU"""
    # Check if SKU already exists for this item/location combination
    existing_sku = sku_crud.get_by_item_location(db, item_id=sku.item_id, location_id=sku.location_id)
    if existing_sku:
        raise HTTPException(
            status_code=400,
            detail=f"SKU already exists for item {sku.item_id} at location {sku.location_id}"
        )
    
    db_sku = sku_crud.create(db, obj_in=sku, created_by_id=current_user.id)
    # Log creation
    log_crud = LogEntryCRUD()
    log_entry = {
        "message": f"SKU created: Item {db_sku.item_id} at Location {db_sku.location_id} (ID: {db_sku.id})",
        "level": "INFO",
        "module": "skus",
        "function": "create_sku",
        "user_id": current_user.id
    }
    log_crud.create(db, obj_in=log_entry)
    return db_sku

@router.get("/search", response_model=List[SKUResponse])
async def search_skus(
    q: str = Query(..., min_length=1, description="Search query"),
    skip: int = Query(0, ge=0, description="Number of SKUs to skip"),
    limit: int = Query(100, ge=1, le=500, description="Number of SKUs to return"),
    db: Session = Depends(get_db),
    current_user = Depends(require_user_role())
):
    """Search SKUs by item name, location name, or UPC"""
    skus = sku_crud.search(db, query=q, skip=skip, limit=limit)
    return skus

@router.get("/{sku_id}", response_model=SKUResponse)
async def get_sku(
    sku_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_user_role())
):
    """Get a specific SKU by ID"""
    sku = sku_crud.get(db, id=sku_id)
    if not sku:
        raise HTTPException(status_code=404, detail="SKU not found")
    return sku

@router.put("/{sku_id}", response_model=SKUResponse)
async def update_sku(
    sku_id: int,
    sku_update: SKUUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_user_role("user"))
):
    """Update an existing SKU"""
    db_sku = sku_crud.get(db, id=sku_id)
    if not db_sku:
        raise HTTPException(status_code=404, detail="SKU not found")
    
    # Compare changes BEFORE update
    changes = {}
    update_data = sku_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        old_value = getattr(db_sku, field, None)
        if value != old_value:
            changes[field] = {"old": old_value, "new": value}
    updated_sku = sku_crud.update(db, db_obj=db_sku, obj_in=sku_update)
    # Log update
    log_crud = LogEntryCRUD()
    log_entry = {
        "message": f"SKU updated: Item {updated_sku.item_id} at Location {updated_sku.location_id} (ID: {updated_sku.id})",
        "level": "INFO",
        "module": "skus",
        "function": "update_sku",
        "user_id": current_user.id,
        "extra_data": {"changes": changes}
    }
    log_crud.create(db, obj_in=log_entry)
    return updated_sku

@router.put("/{sku_id}/quantity", response_model=SKUResponse)
async def update_quantity(
    sku_id: int,
    quantity_update: SKUQuantityUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_user_role("user"))
):
    """Update SKU quantity (for inventory adjustments)"""
    db_sku = sku_crud.get(db, id=sku_id)
    if not db_sku:
        raise HTTPException(status_code=404, detail="SKU not found")
    
    # Compare quantity BEFORE update
    changes = {}
    old_quantity = db_sku.quantity
    new_quantity = quantity_update.quantity
    if old_quantity != new_quantity:
        changes["quantity"] = {"old": old_quantity, "new": new_quantity}

    # Update only the quantity field
    updated_sku = sku_crud.update_quantity(db, sku_id=sku_id, new_quantity=new_quantity)

    # Log quantity update
    log_crud = LogEntryCRUD()
    log_entry = {
        "message": f"SKU quantity updated: Item {updated_sku.item_id} at Location {updated_sku.location_id} (ID: {updated_sku.id})",
        "level": "INFO",
        "module": "skus",
        "function": "update_quantity",
        "user_id": current_user.id,
        "extra_data": {"changes": changes}
    }
    log_crud.create(db, obj_in=log_entry)
    return updated_sku

@router.delete("/{sku_id}")
async def delete_sku(
    sku_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_user_role("manager"))
):
    """Delete a SKU (manager or admin only)"""
    db_sku = sku_crud.get(db, id=sku_id)
    if not db_sku:
        raise HTTPException(status_code=404, detail="SKU not found")
    
    sku_crud.remove(db, id=sku_id)
    # Log deletion
    log_crud = LogEntryCRUD()
    log_entry = {
        "message": f"SKU deleted: Item {db_sku.item_id} at Location {db_sku.location_id} (ID: {db_sku.id})",
        "level": "INFO",
        "module": "skus",
        "function": "delete_sku",
        "user_id": current_user.id
    }
    log_crud.create(db, obj_in=log_entry)
    return {"message": "SKU deleted successfully"}

@router.get("/low-stock/", response_model=List[SKUResponse])
async def get_low_stock_items(
    skip: int = Query(0, ge=0, description="Number of SKUs to skip"),
    limit: int = Query(100, ge=1, le=500, description="Number of SKUs to return"),
    db: Session = Depends(get_db),
    current_user = Depends(require_user_role())
):
    """Get items with low stock (quantity <= min_quantity)"""
    skus = sku_crud.get_low_stock(db, skip=skip, limit=limit)
    return skus
