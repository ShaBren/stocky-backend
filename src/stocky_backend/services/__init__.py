"""
Services module for Stocky Backend

Provides:
- UPCLookupService: fetches product data from a remote UPC lookup service
- fetch_and_update_item: background task for deferred UPC data backfill
"""

from .upc_lookup import UPCLookupService, upc_lookup_service
from .upc_background import fetch_and_update_item, UNKNOWN_PRODUCT_NAME

__all__ = [
    "UPCLookupService",
    "upc_lookup_service",
    "fetch_and_update_item",
    "UNKNOWN_PRODUCT_NAME",
]
