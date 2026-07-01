"""
Background task for UPC lookup — runs after the HTTP response is sent
so scanner performance is never impacted.
"""
import logging
from typing import Optional

from sqlalchemy.orm import Session

from ..db.database import SessionLocal
from ..models.models import Item, LogEntry
from .upc_lookup import upc_lookup_service

logger = logging.getLogger(__name__)

# Placeholder name for items created before UPC data is available
UNKNOWN_PRODUCT_NAME = "Unknown Product"


async def fetch_and_update_item(upc: str, item_id: int) -> None:
    """Background task: fetch UPC data and update the item.

    Creates its own independent DB session so it doesn't interfere
    with the request-scoped session (which is already closed by the
    time BackgroundTasks run).

    On failure, creates a LogEntry visible in the frontend.

    Args:
        upc: The UPC barcode to look up.
        item_id: The ID of the Item to update.
    """
    if not upc_lookup_service.is_available():
        return

    db: Session = SessionLocal()
    try:
        item = db.query(Item).filter(Item.id == item_id).first()
        if not item:
            logger.warning("Background UPC lookup: item %d not found", item_id)
            return

        # Skip if already fetched successfully
        if item.uda_fetched:
            return

        data = await upc_lookup_service.fetch_product(upc)

        if data is None:
            # Lookup failed — mark attempted, log the failure
            item.uda_fetch_attempted = True
            _log_failure(db, upc, item_id, "UPC lookup service returned no data")
            db.commit()
            return

        # Extract product name from response
        product_name = upc_lookup_service.extract_product_name(data)

        # Update the item
        if product_name:
            item.name = product_name
        item.upc_data = data
        item.uda_fetched = True
        item.uda_fetch_attempted = True

        db.commit()
        logger.info("Background UPC lookup: item %d updated with name=%s", item_id, product_name)

    except Exception as e:
        db.rollback()
        logger.exception("Background UPC lookup failed for item %d: %s", item_id, e)
        # Try to at least mark as attempted
        try:
            item = db.query(Item).filter(Item.id == item_id).first()
            if item:
                item.uda_fetch_attempted = True
                _log_failure(db, upc, item_id, str(e))
                db.commit()
        except Exception:
            db.rollback()
    finally:
        db.close()


def _log_failure(db: Session, upc: str, item_id: int, error: str) -> None:
    """Create a LogEntry for a failed UPC lookup, visible in the frontend."""
    log_entry = LogEntry(
        level="WARNING",
        message=f"UPC lookup failed for item {item_id} (UPC: {upc})",
        module="upc_lookup",
        function="fetch_and_update_item",
        extra_data={"upc": upc, "item_id": item_id, "error": error},
    )
    db.add(log_entry)
