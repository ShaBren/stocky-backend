"""
SKU (inventory) management endpoints
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...db.database import get_db
from ...crud.crud import SKUCRUD
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
    
    updated_sku = sku_crud.update(db, db_obj=db_sku, obj_in=sku_update)
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
    
    # Update only the quantity field
    updated_sku = sku_crud.update_quantity(db, sku_id=sku_id, new_quantity=quantity_update.quantity)
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
