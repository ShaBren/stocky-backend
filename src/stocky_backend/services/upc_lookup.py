"""
UPC Lookup Service - fetches product data from a remote UPC lookup service.
"""

import logging
from typing import Any

import httpx

from ..core.config import settings

logger = logging.getLogger(__name__)


class UPCLookupService:
    """Service for looking up product information by UPC barcode."""

    def __init__(self):
        self.base_url = settings.UPC_SERVICE_BASE_URL
        self.timeout = settings.UPC_SERVICE_TIMEOUT

    def is_available(self) -> bool:
        """Check if the UPC lookup service is configured and available."""
        return bool(self.base_url)

    async def fetch_product(self, upc: str) -> dict[str, Any] | None:
        """Fetch product data from the remote UPC lookup service.

        Args:
            upc: The UPC barcode to look up.

        Returns:
            Full JSON response dict, or None if the lookup failed.
        """
        if not self.is_available():
            logger.debug("UPC service not configured, skipping lookup for %s", upc)
            return None

        url = f"{self.base_url.rstrip('/')}/upc/{upc}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                logger.info("UPC lookup succeeded for %s", upc)
                return data
        except httpx.TimeoutException:
            logger.warning("UPC lookup timed out for %s (timeout=%ds)", upc, self.timeout)
            return None
        except httpx.HTTPStatusError as e:
            logger.warning("UPC lookup HTTP %d for %s", e.response.status_code, upc)
            return None
        except httpx.RequestError as e:
            logger.warning("UPC lookup connection error for %s: %s", upc, e)
            return None
        except Exception as e:
            logger.warning("UPC lookup unexpected error for %s: %s", upc, type(e).__name__)
            return None

    @staticmethod
    def extract_product_name(data: dict[str, Any]) -> str | None:
        """Extract the product name from a UPC lookup response.

        Tries product_name first, falls back to generic_name.

        Args:
            data: The full UPC lookup response dict.

        Returns:
            The product name string, or None if neither field is present.
        """
        name = data.get("product_name")
        if name and isinstance(name, str) and name.strip():
            return name.strip()
        generic = data.get("generic_name")
        if generic and isinstance(generic, str) and generic.strip():
            return generic.strip()
        return None


# Singleton instance
upc_lookup_service = UPCLookupService()
