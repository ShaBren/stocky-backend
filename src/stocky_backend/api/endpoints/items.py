"""
Item management endpoints
"""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...core.security import require_user_role
from ...crud.crud import ItemCRUD, LogEntryCRUD
from ...db.database import get_db
from ...models.models import Item
from ...schemas.schemas import ItemCreate, ItemResponse, ItemUpdate
from ...services.upc_background import fetch_and_update_item
from ...services.upc_lookup import upc_lookup_service

router = APIRouter()
item_crud = ItemCRUD()


@router.get("/", response_model=list[ItemResponse])
async def list_items(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=500, description="Number of items to return"),
    db: Session = Depends(get_db),
    current_user=Depends(require_user_role()),
):
    """List all items with pagination"""
    items = item_crud.get_multi(db, skip=skip, limit=limit)
    return items


@router.post("/", response_model=ItemResponse)
async def create_item(
    item: ItemCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(require_user_role("manager")),
):
    """Create a new item.

    If a UPC is provided and the UPC lookup service is available,
    product data will be fetched in the background after the response
    is sent. If no name was provided, a placeholder is used temporarily.
    """
    # Check if item with same UPC already exists
    if item.upc:
        existing_item = item_crud.get_by_upc(db, upc=item.upc)
        if existing_item:
            raise HTTPException(status_code=400, detail=f"Item with UPC {item.upc} already exists")

    # If UPC service is available and no name was provided, use placeholder
    should_fetch_upc = upc_lookup_service.is_available() and item.upc and not item.upc_data

    db_item = item_crud.create(
        db,
        obj_in=item,
        created_by_id=current_user.id,
        upc_data=None,
        uda_fetched=False,
        uda_fetch_attempted=False,
    )

    # Log creation
    log_crud = LogEntryCRUD()
    log_entry = {
        "message": f"Item created: {db_item.name} (ID: {db_item.id})",
        "level": "INFO",
        "module": "items",
        "function": "create_item",
        "user_id": current_user.id,
    }
    log_crud.create(db, obj_in=log_entry)

    # Schedule background UPC lookup if applicable
    if should_fetch_upc:
        background_tasks.add_task(fetch_and_update_item, item.upc, db_item.id)

    return db_item


@router.get("/search", response_model=list[ItemResponse])
async def search_items(
    q: str = Query(..., min_length=1, description="Search query"),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=500, description="Number of items to return"),
    db: Session = Depends(get_db),
    current_user=Depends(require_user_role()),
):
    """Search items by name, description, or UPC"""
    items = item_crud.search(db, query=q, skip=skip, limit=limit)
    return items


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_user_role()),
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
    current_user=Depends(require_user_role("manager")),
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
                detail=f"Item with UPC {item_update.upc} already exists",
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
        "extra_data": {"changes": changes},
    }
    log_crud.create(db, obj_in=log_entry)
    return updated_item


@router.delete("/{item_id}")
async def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_user_role("admin")),
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
        "user_id": current_user.id,
    }
    log_crud.create(db, obj_in=log_entry)
    return {"message": "Item deleted successfully"}


@router.post("/{item_id}/refresh-upc")
async def refresh_upc_data(
    item_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(require_user_role("manager")),
):
    """Manually trigger a UPC lookup refresh for an existing item.

    The refresh runs in the background — this endpoint returns immediately.
    Use this to backfill upc_data for items created before the UPC lookup
    service was configured.
    """
    item = item_crud.get(db, id=item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not item.upc:
        raise HTTPException(status_code=400, detail="Item has no UPC code")
    if not upc_lookup_service.is_available():
        raise HTTPException(status_code=503, detail="UPC lookup service is not configured")

    # Reset fetch flags so the background task will re-fetch
    item.uda_fetched = False
    item.uda_fetch_attempted = False
    db.commit()

    background_tasks.add_task(fetch_and_update_item, item.upc, item.id)

    # Log the manual refresh
    log_crud = LogEntryCRUD()
    log_entry = {
        "message": f"UPC refresh triggered for item {item.name} (ID: {item.id}, UPC: {item.upc})",
        "level": "INFO",
        "module": "items",
        "function": "refresh_upc_data",
        "user_id": current_user.id,
    }
    log_crud.create(db, obj_in=log_entry)

    return {
        "message": f"UPC refresh scheduled for item {item_id}",
        "item_id": item_id,
        "upc": item.upc,
    }


@router.post("/refresh-upc-missing")
async def refresh_missing_upc_data(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(require_user_role("manager")),
):
    """Trigger UPC lookup for ALL items that are missing product data.

    Finds every item that has a UPC but hasn't been enriched yet
    (uda_fetched=False) and schedules a background UPC lookup for each.
    Returns immediately with a count of scheduled refreshes.

    Useful after first configuring the UPC lookup service, or after
    bulk-importing items with UPCs but no product data.
    """
    if not upc_lookup_service.is_available():
        raise HTTPException(status_code=503, detail="UPC lookup service is not configured")

    items = (
        db.query(Item)
        .filter(Item.upc.isnot(None), Item.upc != "", Item.uda_fetched == False)  # noqa: E712
        .all()
    )

    count = 0
    for item in items:
        background_tasks.add_task(fetch_and_update_item, item.upc, item.id)
        count += 1

    # Log the batch refresh
    log_crud = LogEntryCRUD()
    log_entry = {
        "message": f"Batch UPC refresh triggered for {count} items",
        "level": "INFO",
        "module": "items",
        "function": "refresh_missing_upc_data",
        "user_id": current_user.id,
        "extra_data": {"count": count},
    }
    log_crud.create(db, obj_in=log_entry)

    return {
        "message": f"UPC refresh scheduled for {count} items",
        "count": count,
    }


@router.get("/upc/{upc}", response_model=ItemResponse)
async def get_item_by_upc(
    upc: str, db: Session = Depends(get_db), current_user=Depends(require_user_role())
):
    """Get an item by UPC code"""
    item = item_crud.get_by_upc(db, upc=upc)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item
