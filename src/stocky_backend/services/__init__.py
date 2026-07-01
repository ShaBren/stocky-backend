"""
Services module for Stocky Backend

Provides:
- UPCLookupService: fetches product data from a remote UPC lookup service
- fetch_and_update_item: background task for deferred UPC data backfill
"""

from .upc_background import UNKNOWN_PRODUCT_NAME, fetch_and_update_item
from .upc_lookup import UPCLookupService, upc_lookup_service

__all__ = [
    "UPCLookupService",
    "upc_lookup_service",
    "fetch_and_update_item",
    "UNKNOWN_PRODUCT_NAME",
]
