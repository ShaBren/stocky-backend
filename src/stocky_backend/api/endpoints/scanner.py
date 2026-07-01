"""
Scanner interaction endpoints
"""
from datetime import datetime
from typing import Dict
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from ...db.database import get_db
from ...crud.crud import ItemCRUD, SKUCRUD, LogEntryCRUD
from ...schemas.schemas import ScanRequest, ScanResponse, ScannerStatus, ScannerAssociation, ItemCreate
from ...core.security import require_user_role, get_current_user_optional
from ...models.models import LogEntry
from ...services.upc_lookup import upc_lookup_service
from ...services.upc_background import fetch_and_update_item, UNKNOWN_PRODUCT_NAME

router = APIRouter()
item_crud = ItemCRUD()
sku_crud = SKUCRUD()
log_crud = LogEntryCRUD()

# In-memory scanner association store (in production, use Redis or database)
scanner_associations: Dict[str, str] = {}

@router.post("/scan", response_model=ScanResponse)
async def scanner_scan(
    scan_request: ScanRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    """Handle barcode scan from scanner.

    Fast path: returns immediately. If the UPC is unknown and a UPC lookup
    service is configured, a stub item is created instantly and the lookup
    runs as a background task after the response is sent.
    """
    upc = scan_request.upc
    scanner_id = scan_request.scanner_id
    
    # Look up item by UPC
    item = item_crud.get_by_upc(db, upc=upc)
    
    if not item:
        # UPC not found locally
        if upc_lookup_service.is_available():
            # Create a stub item immediately so the scanner is unblocked.
            # The UPC lookup will backfill name + upc_data in the background.
            stub_create = ItemCreate(
                name=UNKNOWN_PRODUCT_NAME,
                upc=upc,
            )
            item = item_crud.create(
                db,
                obj_in=stub_create,
                created_by_id=current_user.id if current_user else 1,
                upc_data=None,
                uda_fetched=False,
                uda_fetch_attempted=False,
            )

            # Log the unknown UPC scan
            if current_user:
                log_entry = LogEntry(
                    level="INFO",
                    message=f"Unknown UPC scanned, stub item created: {item.id} (UPC: {upc})",
                    module="scanner",
                    function="scanner_scan",
                    user_id=current_user.id,
                    extra_data={"upc": upc, "scanner_id": scanner_id, "item_id": item.id}
                )
                db.add(log_entry)
                db.commit()

            # Schedule background UPC lookup — runs after response is sent
            background_tasks.add_task(fetch_and_update_item, upc, item.id)

            return ScanResponse(
                success=True,
                message=f"New item registered, product details loading...",
                item=item,
                skus=[]
            )
        else:
            # No UPC service configured — return unknown as before
            if current_user:
                log_entry = LogEntry(
                    level="INFO",
                    message=f"Unknown UPC scanned: {upc}",
                    module="scanner",
                    function="scanner_scan",
                    user_id=current_user.id,
                    extra_data={"upc": upc, "scanner_id": scanner_id}
                )
                db.add(log_entry)
                db.commit()

            return ScanResponse(
                success=False,
                message=f"Unknown UPC: {upc}",
                item=None,
                skus=[]
            )
    
    # Item found locally — check if we should backfill UPC data
    if upc_lookup_service.is_available() and not item.uda_fetched and item.upc:
        background_tasks.add_task(fetch_and_update_item, item.upc, item.id)

    # Get all SKUs for this item
    skus = sku_crud.get_by_item(db, item_id=item.id)
    
    # Log successful scan
    if current_user:
        log_entry = LogEntry(
            level="INFO",
            message=f"Item scanned: {item.name} (UPC: {upc})",
            module="scanner",
            function="scanner_scan",
            user_id=current_user.id,
            extra_data={
                "upc": upc,
                "item_id": item.id,
                "item_name": item.name,
                "scanner_id": scanner_id,
                "sku_count": len(skus)
            }
        )
        db.add(log_entry)
        db.commit()
    
    return ScanResponse(
        success=True,
        message=f"Found item: {item.name}",
        item=item,
        skus=skus
    )

@router.get("/status/{scanner_id}", response_model=ScannerStatus)
async def scanner_status(
    scanner_id: str,
    current_user = Depends(require_user_role())
):
    """Get scanner status and association"""
    is_associated = scanner_id in scanner_associations
    associated_user = scanner_associations.get(scanner_id)
    
    return ScannerStatus(
        scanner_id=scanner_id,
        is_associated=is_associated,
        associated_user=associated_user,
        last_seen=datetime.utcnow()  # In production, track this properly
    )

@router.post("/associate")
async def associate_scanner(
    association: ScannerAssociation,
    current_user = Depends(require_user_role())
):
    """Associate scanner with user session"""
    scanner_id = association.scanner_id
    user_id = association.user_id or current_user.username
    
    # Store association
    scanner_associations[scanner_id] = user_id
    
    return {
        "message": f"Scanner {scanner_id} associated with user {user_id}",
        "scanner_id": scanner_id,
        "user_id": user_id
    }

@router.delete("/associate/{scanner_id}")
async def disassociate_scanner(
    scanner_id: str,
    current_user = Depends(require_user_role())
):
    """Remove scanner association"""
    if scanner_id in scanner_associations:
        user_id = scanner_associations.pop(scanner_id)
        return {
            "message": f"Scanner {scanner_id} disassociated from user {user_id}",
            "scanner_id": scanner_id
        }
    else:
        raise HTTPException(
            status_code=404,
            detail=f"Scanner {scanner_id} is not currently associated"
        )

@router.get("/associations")
async def list_scanner_associations(
    current_user = Depends(require_user_role("manager"))
):
    """List all current scanner associations (manager/admin only)"""
    return {
        "associations": scanner_associations,
        "count": len(scanner_associations)
    }

@router.post("/lookup/{upc}", response_model=ScanResponse)
async def lookup_upc(
    upc: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_user_role())
):
    """Look up item by UPC without scanner (manual lookup)"""
    item = item_crud.get_by_upc(db, upc=upc)
    
    if not item:
        return ScanResponse(
            success=False,
            message=f"Unknown UPC: {upc}",
            item=None,
            skus=[]
        )
    
    # Get all SKUs for this item
    skus = sku_crud.get_by_item(db, item_id=item.id)
    
    # Log manual lookup
    log_entry = LogEntry(
        level="INFO",
        message=f"Manual UPC lookup: {item.name} (UPC: {upc})",
        module="scanner",
        function="lookup_upc",
        user_id=current_user.id,
        extra_data={
            "upc": upc,
            "item_id": item.id,
            "item_name": item.name,
            "sku_count": len(skus)
        }
    )
    db.add(log_entry)
    db.commit()
    
    return ScanResponse(
        success=True,
        message=f"Found item: {item.name}",
        item=item,
        skus=skus
    )
