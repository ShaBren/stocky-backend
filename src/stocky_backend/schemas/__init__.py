"""
Schemas module for Stocky Backend
"""

from .schemas import (
    # Alerts
    AlertCreate,
    AlertResponse,
    AlertUpdate,
    # Items
    ItemCreate,
    ItemResponse,
    ItemUpdate,
    # Locations
    LocationCreate,
    LocationResponse,
    LocationUpdate,
    LoginRequest,
    # Scanner
    ScanRequest,
    ScanResponse,
    # Search
    SearchRequest,
    SearchResponse,
    # SKUs
    SKUCreate,
    SKUResponse,
    SKUUpdate,
    # Authentication
    Token,
    TokenData,
    # Users
    UserCreate,
    UserResponse,
    UserUpdate,
)

__all__ = [
    # Authentication
    "Token",
    "TokenData",
    "LoginRequest",
    # Users
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    # Items
    "ItemCreate",
    "ItemUpdate",
    "ItemResponse",
    # Locations
    "LocationCreate",
    "LocationUpdate",
    "LocationResponse",
    # SKUs
    "SKUCreate",
    "SKUUpdate",
    "SKUResponse",
    # Alerts
    "AlertCreate",
    "AlertUpdate",
    "AlertResponse",
    # Scanner
    "ScanRequest",
    "ScanResponse",
    # Search
    "SearchRequest",
    "SearchResponse",
]
