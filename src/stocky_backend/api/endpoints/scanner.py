"""
Scanner interaction endpoints with command processing support.
"""

import json
from datetime import datetime, UTC

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from ...core.security import get_current_user_optional, require_user_role
from ...crud.crud import SKUCRUD, ItemCRUD, LogEntryCRUD
from ...db.database import get_db
from ...models.models import SKU, User
from ...schemas.schemas import (
    ItemCreate,
    QRCommandRequest,
    ScannerCommand,
    ScannerStatus,
    ScanRequest,
    ScanResponse,
)
from ...services.upc_background import UNKNOWN_PRODUCT_NAME, fetch_and_update_item
from ...services.upc_lookup import upc_lookup_service

router = APIRouter()
item_crud = ItemCRUD()
sku_crud = SKUCRUD()
log_crud = LogEntryCRUD()

DEFAULT_SCANNER_STATE = {
    "current_mode": "add",
    "current_location_id": None,
    "associated_ui_id": None,
}


# ── Scanner state helpers ──────────────────────────────────────────


def _get_scanner_state(user: User | None) -> dict:
    """Get scanner state for a user, with defaults."""
    if user and user.scanner_state:
        return {**DEFAULT_SCANNER_STATE, **user.scanner_state}
    return dict(DEFAULT_SCANNER_STATE)


def _save_scanner_state(db: Session, user: User, state: dict) -> None:
    """Persist scanner state to the user's scanner_state column."""
    user.scanner_state = state
    db.commit()


# ── Command parsing ────────────────────────────────────────────────


def _parse_command(scanned_value: str) -> ScannerCommand | None:
    """Try to parse scanned value as a JSON command. Returns None if it's a plain UPC."""
    try:
        data = json.loads(scanned_value)
        if isinstance(data, dict) and "command" in data:
            return ScannerCommand(command=data["command"], payload=data.get("payload"))
    except (json.JSONDecodeError, ValueError):
        pass
    return None


# ── Command handlers ───────────────────────────────────────────────


def _handle_set_mode(user: User, payload: dict | None) -> dict:
    """Handle set_mode command."""
    state = _get_scanner_state(user)
    mode = (payload or {}).get("mode", "add")
    if mode not in ("add", "remove", "move", "lookup"):
        mode = "add"
    state["current_mode"] = mode
    return state


def _handle_set_location(user: User, payload: dict | None) -> dict:
    """Handle set_location command."""
    state = _get_scanner_state(user)
    location_id = (payload or {}).get("location_id")
    state["current_location_id"] = location_id
    return state


def _handle_associate_ui(user: User, payload: dict | None) -> dict:
    """Handle associate_ui command."""
    state = _get_scanner_state(user)
    ui_id = (payload or {}).get("ui_id")
    state["associated_ui_id"] = ui_id
    return state


COMMAND_HANDLERS = {
    "set_mode": _handle_set_mode,
    "set_location": _handle_set_location,
    "associate_ui": _handle_associate_ui,
    "show_view": lambda u, p: _get_scanner_state(u),  # no-op, returns current state
}


# ── Endpoints ──────────────────────────────────────────────────────


@router.post("/scan", response_model=ScanResponse)
async def scanner_scan(
    scan_request: ScanRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional),
):
    """Handle a scan from a barcode scanner.

    Accepts both plain UPC barcodes and command JSON payloads.
    Commands: set_mode, set_location, associate_ui, show_view.

    Fast path: returns immediately. For unknown UPCs with a lookup
    service configured, a stub item is created and enriched in the background.
    """
    scanned = scan_request.upc
    scanner_id = scan_request.scanner_id

    # ── Try command parsing ────────────────────────────────────
    command = _parse_command(scanned)
    if command and current_user:
        handler = COMMAND_HANDLERS.get(command.command)
        if handler:
            new_state = handler(current_user, command.payload)
            new_state["last_scan_timestamp"] = datetime.now(UTC).isoformat()
            _save_scanner_state(db, current_user, new_state)

            mode_desc = {
                "add": "Add mode",
                "remove": "Remove mode",
                "move": "Move mode",
                "lookup": "Lookup mode",
            }
            return ScanResponse(
                success=True,
                message=f"Command accepted: {command.command} — {mode_desc.get(new_state.get('current_mode', ''), '')}",
                mode=new_state.get("current_mode"),
                scanner_state=new_state,
                suggested_actions=[
                    f"Scanner is now in '{new_state.get('current_mode', 'add')}' mode"
                ],
            )

    # ── UPC processing ─────────────────────────────────────────
    upc = scanned
    state = _get_scanner_state(current_user)
    mode = state.get("current_mode", "add")
    location_id = state.get("current_location_id") or scan_request.location_hint

    # Look up item by UPC
    item = item_crud.get_by_upc(db, upc=upc)

    if not item:
        # UPC not found locally
        if upc_lookup_service.is_available():
            stub_create = ItemCreate(name=UNKNOWN_PRODUCT_NAME, description=None, upc=upc)
            creator_id = current_user.id if current_user else 1
            item = item_crud.create(
                db,
                obj_in=stub_create,
                created_by_id=creator_id,
                upc_data=None,
                uda_fetched=False,
                uda_fetch_attempted=False,
            )

            if current_user:
                log_crud.create(
                    db,
                    obj_in={
                        "level": "INFO",
                        "message": f"Unknown UPC scanned, stub item created: {item.id} (UPC: {upc})",
                        "module": "scanner",
                        "function": "scanner_scan",
                        "user_id": current_user.id,
                        "extra_data": {"upc": upc, "scanner_id": scanner_id, "item_id": item.id},
                    },
                )

            background_tasks.add_task(fetch_and_update_item, upc, item.id)

            return ScanResponse(
                success=True,
                message="New item registered, product details loading...",
                item=item,
                skus=[],
                mode=mode,
                scanner_state=state,
            )
        else:
            return ScanResponse(
                success=False, message=f"Unknown UPC: {upc}", mode=mode, scanner_state=state
            )

    # Item found — UPC backfill if needed
    if upc_lookup_service.is_available() and not item.uda_fetched and item.upc:
        background_tasks.add_task(fetch_and_update_item, item.upc, item.id)

    # Mode-aware SKU handling
    skus = sku_crud.get_by_item(db, item_id=item.id)
    suggested: list[str] = []

    if mode == "lookup":
        return ScanResponse(
            success=True,
            message=f"Found: {item.name}",
            item=item,
            skus=skus,
            mode=mode,
            scanner_state=state,
            suggested_actions=[f"Item: {item.name} — {len(skus)} locations with stock"],
        )

    if not location_id:
        suggested.append("Set a location first — scan a set_location command QR")
        return ScanResponse(
            success=True,
            message=f"Found: {item.name} (no location set)",
            item=item,
            skus=skus,
            mode=mode,
            scanner_state=state,
            suggested_actions=suggested,
        )

    location_id = int(location_id)
    existing_sku = sku_crud.get_by_item_location(db, item_id=item.id, location_id=location_id)

    if mode == "add":
        if existing_sku:
            new_qty = existing_sku.quantity + 1
            sku_crud.update_quantity(db, sku_id=existing_sku.id, new_quantity=new_qty)
            suggested.append(f"Incremented {item.name} at location {location_id} (qty: {new_qty})")
        else:
            creator_id = current_user.id if current_user else 1
            new_sku = SKU(
                item_id=item.id, location_id=location_id, quantity=1, created_by=creator_id
            )
            db.add(new_sku)
            db.commit()
            suggested.append(f"Added {item.name} at location {location_id}")

    elif mode == "remove":
        if existing_sku and existing_sku.quantity > 0:
            new_qty = max(0, existing_sku.quantity - 1)
            sku_crud.update_quantity(db, sku_id=existing_sku.id, new_quantity=new_qty)
            suggested.append(f"Decremented {item.name} at location {location_id} (qty: {new_qty})")
        else:
            suggested.append(f"No stock of {item.name} at location {location_id}")

    elif mode == "move":
        # Two-scan flow: first scan sets source, second scan moves
        move_source = state.get("move_source_item_id")
        move_source_loc = state.get("move_source_location_id")
        if move_source and move_source_loc:
            # Second scan — execute the move
            source_sku = sku_crud.get_by_item_location(
                db, item_id=move_source, location_id=move_source_loc
            )
            if source_sku and source_sku.quantity > 0:
                new_qty = source_sku.quantity - 1
                sku_crud.update_quantity(db, sku_id=source_sku.id, new_quantity=new_qty)
                # Add to destination
                creator_id = current_user.id if current_user else 1
                dest_sku = SKU(
                    item_id=move_source, location_id=location_id, quantity=1, created_by=creator_id
                )
                db.add(dest_sku)
                db.commit()
                suggested.append(f"Moved 1 {item.name} to location {location_id}")
            state.pop("move_source_item_id", None)
            state.pop("move_source_location_id", None)
        else:
            # First scan — capture source
            state["move_source_item_id"] = item.id
            state["move_source_location_id"] = location_id
            suggested.append("Move source set — scan destination location/item next")

    # Save updated state
    state["last_scan_timestamp"] = datetime.now(UTC).isoformat()
    if current_user:
        _save_scanner_state(db, current_user, state)

    # Refresh SKUs after mutation
    skus = sku_crud.get_by_item(db, item_id=item.id)

    if current_user:
        log_crud.create(
            db,
            obj_in={
                "level": "INFO",
                "message": f"Item scanned: {item.name} (UPC: {upc}, mode: {mode})",
                "module": "scanner",
                "function": "scanner_scan",
                "user_id": current_user.id,
                "extra_data": {
                    "upc": upc,
                    "item_id": item.id,
                    "mode": mode,
                    "scanner_id": scanner_id,
                },
            },
        )

    return ScanResponse(
        success=True,
        message=f"{item.name}",
        item=item,
        skus=skus,
        mode=mode,
        scanner_state=state,
        suggested_actions=suggested,
    )


@router.get("/status/{scanner_id}", response_model=ScannerStatus)
async def scanner_status(scanner_id: str, current_user=Depends(require_user_role())):
    """Get scanner status and state."""
    state = _get_scanner_state(current_user)
    return ScannerStatus(
        scanner_id=scanner_id,
        is_associated=bool(state.get("associated_ui_id")),
        associated_user=str(current_user.id),
        last_seen=datetime.now(),
    )


@router.post("/reset/{scanner_id}")
async def reset_scanner_state(
    scanner_id: str, current_user=Depends(require_user_role()), db: Session = Depends(get_db)
):
    """Reset scanner state to defaults."""
    _save_scanner_state(db, current_user, dict(DEFAULT_SCANNER_STATE))
    return {"message": f"Scanner {scanner_id} state reset", "scanner_id": scanner_id}


@router.get("/associations")
async def list_scanner_associations(current_user=Depends(require_user_role("manager"))):
    """List all scanner associations (manager/admin only)."""
    return {"message": "Scanner state is now stored per-user in the scanner_state column"}


@router.post("/qr/command")
async def generate_command_qr(
    qr_request: QRCommandRequest, current_user=Depends(require_user_role())
):
    """Generate a command QR code for a scanner to read."""
    import qrcode
    import io
    from fastapi.responses import StreamingResponse

    payload = json.dumps({"command": qr_request.command, "payload": qr_request.payload or {}})
    img = qrcode.make(payload)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")


@router.post("/lookup/{upc}", response_model=ScanResponse)
async def lookup_upc(
    upc: str, db: Session = Depends(get_db), current_user=Depends(require_user_role())
):
    """Look up item by UPC without scanner (manual lookup)."""
    item = item_crud.get_by_upc(db, upc=upc)
    if not item:
        return ScanResponse(success=False, message=f"Unknown UPC: {upc}", item=None, skus=[])

    skus = sku_crud.get_by_item(db, item_id=item.id)

    log_crud.create(
        db,
        obj_in={
            "level": "INFO",
            "message": f"Manual UPC lookup: {item.name} (UPC: {upc})",
            "module": "scanner",
            "function": "lookup_upc",
            "user_id": current_user.id,
            "extra_data": {"upc": upc, "item_id": item.id},
        },
    )

    return ScanResponse(success=True, message=f"Found item: {item.name}", item=item, skus=skus)
